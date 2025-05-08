import re
import json
from uuid import uuid4
from nicegui import ui, events
from PIL import Image
from glob import glob




class Box:
    def __init__(self, left, top, bottom=None, right=None, color='red'):
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
        return (f'<rect id="{uuid4()}" x="{self.left}" y="{self.top}" '
                f'width="{self.right - self.left}" height="{self.bottom - self.top}" '
                f'fill="{self.color}" opacity="0.5" stroke="red" stroke-width="4" '
                f'pointer-events="all" cursor="pointer" />')


    @staticmethod
    def get_coords_from_svg(svg):
        # first break into boxes, then convert each box into a dict for saving
        elements = re.split('[</>]+', svg)[1:-1]  # box svg strings
        boxes = list()
        for element in elements:
            chunks = re.split('="|" ', element)
            keys = chunks[2::2][:4]
            vals = chunks[3::2][:4]
            unpacked = dict(zip(keys, [float(val) for val in vals]))
            bbox = {'left': int(unpacked['x']), 'top': int(unpacked['y'])}
            bbox['right'] = int(bbox['left'] + unpacked['width'])
            bbox['bottom'] = int(bbox['top'] + unpacked['height'])
            boxes.append(bbox)
        return boxes




class AnnotationJob:
    def __init__(self, image_folder):
        self.image_folder = image_folder
        *_, self.image_folder_name = image_folder.split('/')
        image_files = glob(f'{image_folder}/*.tiff')
        with open(f'{image_folder}/{self.image_folder_name}_annotations.json') as f:
            self.previous_annotations = json.load(f)
        #self.image_files = [file for file in image_files if file not in self.previous_annotations.keys()]
        self.image_files = image_files  # ToDo: uncomment hack
        self.num_images = len(self.image_files)
        self.current_image_index = 0
        self.svg_strings = dict()
        self.current_image = self.load_image()
        self.current_svg_string = self.load_svg()
        self.current_image_boxes = list()  # list of box svg strings
        self.active_box = None  # Box instance
        with ui.row().classes('w-full border'):
            ui.button('Previous', color='grey').on_click(self.previous)
            ui.button('Next').on_click(self.next)
            ui.space()
            ui.button('Done').on_click(self.save_annotations)


        self.display_image = ui.interactive_image(source=self.current_image,
                                                  content=self.current_svg_string,
                                                  events=['mousedown', 'mouseup'],
                                                  on_mouse=self.mouse_handler,
                                                  cross=True
                                                  )
        self.display_image.bind_source(self, 'current_image')
        self.display_image.bind_content(self, 'current_svg_string')
        self.display_image.on('svg:pointerdown', lambda e: self.remove_box_by_id(e.args['element_id']))


    def next(self):
        if self.current_image_index == self.num_images - 1:
            # there is no next image...
            ui.notify("You're done!")
        else:
            self.dump_svg()
            self.current_image_index += 1
            self.current_image = self.load_image()
            self.current_svg_string = self.load_svg()
            self.current_image_boxes = self.load_image_boxes()


    def previous(self):
        if self.current_image_index == 0:
            # there is no previous image...
            ui.notify("Sorry- can't go back!")
        else:
            self.dump_svg()
            self.current_image_index -= 1
            self.current_image = self.load_image()
            self.current_svg_string = self.load_svg()
            self.current_image_boxes = self.load_image_boxes()


    def mouse_handler(self, e: events.MouseEventArguments):
        x = e.image_x
        y = e.image_y
        if e.type == 'mousedown':
            # mark the spot! this will get cleaned out once 'content' is rebuilt
            self.current_svg_string += f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="red" stroke-width="4"/>'
            # initialize a box
            self.active_box = Box(left=x, top=y)
        elif e.type == 'mouseup':
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
        self.current_image_boxes = [box for box in self.current_image_boxes if f'id="{id}"' not in box]
        self.rebuild_current_svg_string()


    def rebuild_current_svg_string(self):
        self.current_svg_string = ''.join(self.current_image_boxes)


    def load_image(self):
        return Image.open(self.image_files[self.current_image_index])


    def load_svg(self):
        return self.svg_strings.get(self.current_image_index, '')


    def dump_svg(self):
        self.svg_strings[self.current_image_index] = self.current_svg_string


    def load_image_boxes(self):
        # we only stored the svg string, so need to convert them back to individual box svg strings
        return [f'<{element}/>' for element in re.split('[</>]+', self.current_svg_string)]


    def save_annotations(self):
        ui.notify('dumping')
        self.dump_svg()
        annotations = dict()
        for index, svg_string in self.svg_strings.items():
            annotations[self.image_files[index]] = Box.get_coords_from_svg(svg_string)
        self.previous_annotations.update(annotations)
        with open(f'{self.image_folder}/{self.image_folder_name}_annotations_final.json', 'w') as f:
            json.dump(self.previous_annotations, f)


job = AnnotationJob('/home/brian/Documents/documents_to_label')
ui.run()
