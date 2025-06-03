import json
import os
import re
import tempfile
from uuid import uuid4

from nicegui import app, events, ui
from pdf2image import convert_from_path

from file_system.utils import file_exists, get_all_files_with_ext, get_filename
from transformations.pdf.utils import get_number_of_pages


class Box:
    """
    Represents a rectangular box with coordinates and color.
    """

    def __init__(self, left, top, bottom=None, right=None, color="red"):
        """
        Initializes the Box with left, top, bottom, right, and color.
        :param left: The left coordinate of the box.
        :param top: The top coordinate of the box.
        :param bottom: The bottom coordinate of the box.
        :param right: The right coordinate of the box.
        :param color: The color of the box.
        """
        self.left = left
        self.top = top
        self.color = color
        self.bottom = bottom
        self.right = right

    def add_lower_right_corner(self, x, y):
        """
        Adds the lower right corner to the box.
        :param x: The x-coordinate of the lower right corner.
        :param y: The y-coordinate of the lower right corner.
        """
        self.bottom = y
        self.right = x

    def make_svg_string(self):
        """
        Generates an SVG string representation of the box.
        :return: The SVG string.
        """
        # randomly assigning id with uuid
        return (
            f'<rect id="{uuid4()}" x="{self.left}" y="{self.top}" '
            f'width="{self.right - self.left}" height="{self.bottom - self.top}" '
            f'fill="{self.color}" opacity="0.5" stroke="{self.color}" stroke-width="4" '
            f'pointer-events="all" cursor="pointer" />'
        )

    @staticmethod
    def get_coords_from_svg(svg):
        """
        Extracts coordinates from an SVG string and returns them as a list of dictionaries.
        :param svg: The SVG string.
        :return: A list of dictionaries with box coordinates.
        """
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
    """
    Handles the annotation of PDF files.
    """

    def __init__(self, pdf_folder):
        """
        Initializes the AnnotationJob with a folder containing PDF files.
        :param pdf_folder: The path to the folder containing PDF files.
        """
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
        """
        Builds the user interface using NiceGUI components.
        """
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
        """
        Returns the current page number and total number of pages.
        :return: The page label string.
        """
        return f"Page Number: {self.current_page + 1} of {self.page_count}"

    @property
    def filename_label(self):
        """
        Returns the current PDF filename.
        :return: The filename label string.
        """
        return f"{self.current_pdf_filename}.pdf"

    @property
    def pdf_index_label(self):
        """
        Returns the current PDF index and total number of PDF files.
        :return: The PDF index label string.
        """
        return f"{self.current_pdf_index+1} of {len(self.pdf_files)}"

    def load_annotations(self):
        """
        Loads annotations from a JSON file.
        """
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
        """
        Saves annotations to a JSON file.
        """
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
        """
        Loads the current PDF file.
        """
        self.current_pdf_filename = get_filename(self.pdf_files[self.current_pdf_index])
        self.page_count = get_number_of_pages(self.pdf_files[self.current_pdf_index])

    def load_page(self):
        """
        Loads the current page of the PDF file.
        """
        self.load_page_image()
        self.current_svg_string = self.load_svg()
        self.current_image_boxes = self.load_image_boxes()

    def load_page_image(self):
        """
        Loads the current page image from the PDF file.
        """
        pdf_path = self.pdf_files[self.current_pdf_index]

        with tempfile.TemporaryDirectory() as path:
            images = convert_from_path(
                pdf_path,
                first_page=self.current_page + 1,  # Convert 0 index to 1 index
                last_page=self.current_page + 1,  # Convert 0 index to 1 index
                output_folder=path,
            )
            self.current_image = images.pop()

    # Buttons
    def next_pdf(self):
        """
        Moves to the next PDF file.
        """
        if self.current_pdf_index + 1 < len(self.pdf_files):
            self.save_annotations()
            self.current_pdf_index = self.current_pdf_index + 1
            self.current_page = 0
            self.load_pdf()
            self.load_page()

    def previous_pdf(self):
        """
        Moves to the previous PDF file.
        """
        if self.current_pdf_index > 0:
            self.save_annotations()
            self.current_pdf_index = self.current_pdf_index - 1
            self.current_page = 0
            self.load_pdf()
            self.load_page()

    def next(self):
        """
        Moves to the next page of the current PDF file.
        """
        if self.current_page + 1 < self.page_count:
            self.dump_svg()
            self.current_page = self.current_page + 1
            self.load_page()

    def previous(self):
        """
        Moves to the previous page of the current PDF file.
        """
        if self.current_page > 0:
            self.dump_svg()
            self.current_page = self.current_page - 1
            self.load_page()

    def done(self):
        """
        Saves the annotations and shuts down the application.
        """
        self.save_annotations()
        app.shutdown()

    def mouse_handler(self, e: events.MouseEventArguments):
        """
        Handles mouse events on the image.
        :param e: The mouse event arguments.
        """
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
        """
        Adds the active box to the current image boxes.
        """
        self.current_image_boxes.append(self.active_box.make_svg_string())
        self.active_box = None

    def remove_box_by_id(self, id):
        """
        Removes a box by its ID.
        :param id: The ID of the box to remove.
        """
        self.current_image_boxes = [
            box for box in self.current_image_boxes if f'id="{id}"' not in box
        ]
        self.rebuild_current_svg_string()

    def rebuild_current_svg_string(self):
        """
        Rebuilds the current SVG string from the current image boxes.
        """
        self.current_svg_string = "".join(self.current_image_boxes)

    def load_svg(self):
        """
        Loads the SVG string for the current page.
        :return: The SVG string.
        """
        if self.current_pdf_filename not in self.svg_strings:
            return ""
        return self.svg_strings[self.current_pdf_filename].get(str(self.current_page), "")

    def dump_svg(self):
        """
        Dumps the current SVG string for the current page.
        """
        if self.current_pdf_filename not in self.svg_strings:
            self.svg_strings[self.current_pdf_filename] = {}
        self.svg_strings[self.current_pdf_filename][str(self.current_page)] = (
            self.current_svg_string
        )

    def load_image_boxes(self):
        """
        Loads the image boxes from the current SVG string.
        :return: A list of SVG strings for each image box.
        """
        # we only stored the svg string, so need to convert them back to individual box svg strings
        return [f"<{element}/>" for element in re.split("[</>]+", self.current_svg_string)]
