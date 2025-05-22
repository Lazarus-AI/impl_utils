import json
import os
import re
from uuid import uuid4

import pymupdf
from nicegui import app, events, ui
from PIL import Image

from file_system.utils import file_exists, get_all_files_with_ext, get_filename
from transformations.pdf.utils import get_number_of_pages


class Box:
    def __init__(self, left, top, bottom=None, right=None, color="red"):
        self.left = left
        self.top = top
        self.color = color
        self.bottom = bottom
        self.right = right

    def add_lower_right_corner(self, x, y):
        self.bottom = y
        self.right = x

    def make_svg_string(self):
        # randomly assigning id with uuid
        return (
            f'<rect id="{uuid4()}" x="{self.left}" y="{self.top}" '
            f'width="{self.right - self.left}" height="{self.bottom - self.top}" '
            f'fill="{self.color}" opacity="0.5" stroke="{self.color}" stroke-width="4" '
            f'pointer-events="all" cursor="pointer" />'
        )

    @staticmethod
    def get_coords_from_svg(svg):
        # first break into boxes, then convert each box into a dict for saving
        elements = re.split("[</>]+", svg)[1:-1]  # box svg strings
        boxes = list()
        for element in elements:
            chunks = re.split('="|" ', element)
            keys = chunks[2::2][:4]
            vals = chunks[3::2][:4]
            unpacked = dict(zip(keys, [float(val) for val in vals]))
            bbox = {"left": int(unpacked["x"]), "top": int(unpacked["y"])}
            bbox["right"] = int(bbox["left"] + unpacked["width"])
            bbox["bottom"] = int(bbox["top"] + unpacked["height"])
            boxes.append(bbox)
        return boxes


class AnnotationJob:
    def __init__(self, pdf_folder):
        self.pdf_folder = pdf_folder
        self.pdf_files = get_all_files_with_ext(self.pdf_folder, "pdf")
        self.annotation_file = os.path.join(self.pdf_folder, "annotations.json")
        self.box_color = "red"

        self.pdf_count = len(self.pdf_files)
        self.current_pdf_index = 0
        # 0 Index paging
        self.current_page = 0
        self.current_image_boxes = list()  # list of box svg strings
        self.active_box = None  # Box instance

        self.svg_strings = {}
        self.load_annotations()
        self.load_pdf()
        self.load_page()
        self.build_ui()

    def build_ui(self):
        with ui.row().classes("w-full"):
            ui.button("<", color="grey").on_click(self.previous_pdf)
            ui.label().classes("text-4xl font-extrabold").bind_text_from(self, "pdf_index_label")
            ui.button(">", color="grey").on_click(self.next_pdf)
            ui.label().classes("text-4xl font-extrabold").bind_text_from(self, "filename_label")
            ui.space()
            ui.button("Done").on_click(self.done)

        with ui.row().classes("w-full border"):
            ui.button("<", color="grey").on_click(self.previous)
            ui.label().classes(
                "inline-flex items-center items-middle text-2xl font-bold"
            ).bind_text_from(self, "page_label")
            ui.button(">").on_click(self.next)
            ui.space()

        self.display_image = ui.interactive_image(
            source=self.current_image,
            content=self.current_svg_string,
            events=["mousedown", "mouseup"],
            on_mouse=self.mouse_handler,
            cross=True,
        )
        self.display_image.bind_source(self, "current_image")
        self.display_image.bind_content(self, "current_svg_string")
        self.display_image.on(
            "svg:pointerdown", lambda e: self.remove_box_by_id(e.args["element_id"])
        )

    @property
    def page_label(self):
        return f"Page Number: {self.current_page + 1} of {self.page_count}"

    @property
    def filename_label(self):
        return f"{self.current_pdf_filename}.pdf"

    @property
    def pdf_index_label(self):
        return f"{self.current_pdf_index+1} of {len(self.pdf_files)}"

    def load_annotations(self):
        self.annotations = {}
        if file_exists(self.annotation_file):
            with open(self.annotation_file) as file:
                self.annotations = json.load(file)
        else:
            with open(self.annotation_file, "w") as file:
                file.write(json.dumps({}))

        # Build svg_strings from annotations
        for pdf_filename, page_dict in self.annotations.items():
            if not self.svg_strings.get(pdf_filename):
                self.svg_strings[pdf_filename] = {}
            for page_number, coordinates in page_dict.items():
                for coordinate_set in coordinates:
                    box = Box(
                        left=coordinate_set["left"],
                        top=coordinate_set["top"],
                        right=coordinate_set["right"],
                        bottom=coordinate_set["bottom"],
                    )
                    self.svg_strings[pdf_filename][page_number] = box.make_svg_string()

    def save_annotations(self):
        ui.notify("Saving Annotations")
        self.dump_svg()
        for pdf_filename, page_dict in self.svg_strings.items():
            if not self.annotations.get(pdf_filename):
                self.annotations[pdf_filename] = {}
            for page_number, svg_string in page_dict.items():
                self.annotations[pdf_filename][page_number] = Box.get_coords_from_svg(svg_string)
        with open(self.annotation_file, "w") as file:
            file.write(json.dumps(self.annotations, indent=2))

    def load_pdf(self):
        self.current_pdf_filename = get_filename(self.pdf_files[self.current_pdf_index])
        self.page_count = get_number_of_pages(self.pdf_files[self.current_pdf_index])

    def load_page(self):
        self.load_page_image()
        self.current_svg_string = self.load_svg()
        self.current_image_boxes = self.load_image_boxes()

    def load_page_image(self):
        pdf_path = self.pdf_files[self.current_pdf_index]
        doc = pymupdf.open(pdf_path)
        page = doc[self.current_page]
        pix = page.get_pixmap()
        self.current_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Buttons
    def next_pdf(self):
        if self.current_pdf_index + 1 < len(self.pdf_files):
            self.save_annotations()
            self.current_pdf_index = self.current_pdf_index + 1
            self.current_page = 0
            self.load_pdf()
            self.load_page()

    def previous_pdf(self):
        if self.current_pdf_index > 0:
            self.save_annotations()
            self.current_pdf_index = self.current_pdf_index - 1
            self.current_page = 0
            self.load_pdf()
            self.load_page()

    def next(self):
        if self.current_page + 1 < self.page_count:
            self.dump_svg()
            self.current_page = self.current_page + 1
            self.load_page()

    def previous(self):
        if self.current_page > 0:
            self.dump_svg()
            self.current_page = self.current_page - 1
            self.load_page()

    def done(self):
        self.save_annotations()
        app.shutdown()

    def mouse_handler(self, e: events.MouseEventArguments):
        x = e.image_x
        y = e.image_y
        if e.type == "mousedown":
            # mark the spot! this will get cleaned out once 'content' is rebuilt
            self.current_svg_string += f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="{self.box_color}" stroke-width="4"/>'
            # initialize a box
            self.active_box = Box(left=x, top=y, color=self.box_color)
        elif e.type == "mouseup":
            if self.active_box:
                self.active_box.add_lower_right_corner(x, y)
                self.add_active_box()
                self.active_box = None
                self.rebuild_current_svg_string()
            else:
                self.rebuild_current_svg_string()

    def add_active_box(self):
        self.current_image_boxes.append(self.active_box.make_svg_string())
        self.active_box = None

    def remove_box_by_id(self, id):
        self.current_image_boxes = [
            box for box in self.current_image_boxes if f'id="{id}"' not in box
        ]
        self.rebuild_current_svg_string()

    def rebuild_current_svg_string(self):
        self.current_svg_string = "".join(self.current_image_boxes)

    def load_svg(self):
        if self.current_pdf_filename not in self.svg_strings:
            return ""
        return self.svg_strings[self.current_pdf_filename].get(str(self.current_page), "")

    def dump_svg(self):
        if self.current_pdf_filename not in self.svg_strings:
            self.svg_strings[self.current_pdf_filename] = {}
        self.svg_strings[self.current_pdf_filename][str(self.current_page)] = (
            self.current_svg_string
        )

    def load_image_boxes(self):
        # we only stored the svg string, so need to convert them back to individual box svg strings
        return [f"<{element}/>" for element in re.split("[</>]+", self.current_svg_string)]
