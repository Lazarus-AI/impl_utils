import logging
import tempfile
from typing import List

from pdf2image import convert_from_path
from PIL import ImageDraw

from lazarus_implementation_tools.file_system.utils import file_exists
from lazarus_implementation_tools.general.pydantic_models import BoundingBox
from lazarus_implementation_tools.transformations.pdf.transformations import (
    compile_images_to_pdf,
)

logger = logging.getLogger(__name__)

COLOR = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
}


def draw_box_on_pdf(
    input_pdf_path, output_pdf_path, bounding_boxes: List[BoundingBox], color=(255, 0, 0)
):
    """Draws a rectangle on a specified PDF page and saves it as a new PDF.

    :param bounding_boxes: Boxes to apply to the pdf
    :param input_pdf_path: (str) Path to the input PDF file.
    :param output_pdf_path: (str) Path to save the modified PDF file.
    :param color: (tuple, optional) RGB color of the rectangle (0-1 range). Defaults to
        red (1.0, 0, 0).

    """
    if not file_exists(input_pdf_path):
        logger.error(f"File not found: {input_pdf_path}")

    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(input_pdf_path, output_folder=path)

        for bounding_box in bounding_boxes:
            # Note page number is 1 indexed. images is 0 indexed
            if bounding_box.page_number < 1 or bounding_box.page_number > len(images):
                return
            page_number = bounding_box.page_number - 1

            image = images[page_number]
            rectangle = (
                bounding_box.box["top_left_x"],
                bounding_box.box["top_left_y"],
                bounding_box.box["bottom_right_x"],
                bounding_box.box["bottom_right_y"],
            )
            draw = ImageDraw.Draw(image)
            draw.rectangle(rectangle, outline=color)

        compile_images_to_pdf(images, output_pdf_path)
