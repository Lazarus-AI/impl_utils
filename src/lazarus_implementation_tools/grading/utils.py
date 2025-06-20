import json
import os

from nicegui import ui

from lazarus_implementation_tools.general.pydantic_models import BoundingBox
from lazarus_implementation_tools.grading.pdf_highlighter import AnnotationJob
from lazarus_implementation_tools.transformations.pdf.utils import draw_bounding_boxes


def run_annotate_ui(folder_path):
    """Runs the annotation UI for the specified folder.

    :param folder_path: The path to the folder containing PDF files to be annotated.

    """
    AnnotationJob(folder_path)
    ui.run()


def apply_annotations_to_pdf(folder_path):
    """Applies annotations to PDF files in the specified folder.

    :param folder_path: The path to the folder containing PDF files and an
        "annotations.json" file.

    """
    annotation_path = os.path.join(folder_path, "annotations.json")
    with open(annotation_path, "r") as file:
        folder_annotations = json.loads(file.read())

    for filename, file_annotations in folder_annotations.items():
        file_path = os.path.join(folder_path, f"{filename}.pdf")
        boxes = []
        for page_number, annotation_boxes in file_annotations.items():
            for annotation_box in annotation_boxes:
                box_dict = {
                    "top_left_x": annotation_box["left"],
                    "top_left_y": annotation_box["top"],
                    "bottom_right_x": annotation_box["right"],
                    "bottom_right_y": annotation_box["bottom"],
                }
                new_box = BoundingBox(
                    page_number=int(page_number) + 1,
                    box=box_dict,
                )
                boxes.append(new_box)

        if boxes:
            draw_bounding_boxes(file_path, bounding_boxes=boxes)
