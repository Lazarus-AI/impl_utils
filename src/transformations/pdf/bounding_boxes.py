from typing import List

import pymupdf

from general.pydantic_models import BoundingBox

COLOR = {
    "red": (1.0, 0, 0),
    "blue": (0, 0, 1.0),
    "green": (0, 1.0, 0),
}


def draw_box_on_pdf(
    input_pdf_path,
    output_pdf_path,
    bounding_boxes: List[BoundingBox],
    color=(1.0, 0, 0),
    line_width=1,
):
    """
    Draws a rectangle on a specified PDF page and saves it as a new PDF.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_pdf_path (str): Path to save the modified PDF file.
        bounding_box (BoundingBox): Page number and Bounding box from the LLM.
        color (tuple, optional): RGB color of the rectangle (0-1 range). Defaults to red (1.0, 0, 0).
        line_width (int, optional): Width of the rectangle's border. Defaults to 1.
    """
    doc = pymupdf.open(input_pdf_path)

    for bounding_box in bounding_boxes:
        # Note page number is 1 indexed. docs is 0 indexed
        if bounding_box.page_number < 1 or bounding_box.page_number > len(doc):
            return
        page_number = bounding_box.page_number - 1

        page = doc[page_number]
        rectangle = (
            bounding_box.box["top_left_x"],
            bounding_box.box["top_left_y"],
            bounding_box.box["bottom_right_x"],
            bounding_box.box["bottom_right_y"],
        )
        shape = page.new_shape()
        shape.draw_rect(rectangle)
        shape.finish(color=color, width=line_width, fill=None, stroke_opacity=1)
        shape.commit()

    doc.save(output_pdf_path)
    doc.close()
