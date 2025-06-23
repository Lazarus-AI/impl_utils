import logging
import tempfile
from typing import List

from pdf2image import convert_from_path
from PIL import ImageDraw, ImageFont

from lazarus_implementation_tools.file_system.utils import file_exists
from lazarus_implementation_tools.general.core import COLOR
from lazarus_implementation_tools.general.pydantic_models import (
    BoundingBox,
    Polygon,
    TextBox,
)
from lazarus_implementation_tools.transformations.pdf.transformations import (
    compile_images_to_pdf,
)

logger = logging.getLogger(__name__)


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
        dpi = 200
        images = convert_from_path(input_pdf_path, output_folder=path, dpi=dpi)

        for bounding_box in bounding_boxes:
            # Note page number is 1 indexed. images is 0 indexed
            if bounding_box.page_number < 1 or bounding_box.page_number > len(images):
                return
            page_number = bounding_box.page_number - 1

            image = images[page_number]
            scale = dpi if bounding_box.unit.lower() == "inch" else 1
            rectangle = (
                bounding_box.box["top_left_x"] * scale,
                bounding_box.box["top_left_y"] * scale,
                bounding_box.box["bottom_right_x"] * scale,
                bounding_box.box["bottom_right_y"] * scale,
            )
            draw = ImageDraw.Draw(image)
            draw.rectangle(rectangle, outline=color)

        compile_images_to_pdf(images, output_pdf_path)


def draw_polygon_on_pdf(
    input_pdf_path,
    output_pdf_path,
    polygons: List[Polygon],
    border_color=COLOR["red"],
    fill_color=COLOR["transparent"],
):
    """Draws a polygon on a specified PDF page and saves it as a new PDF.

    :param polygons: List of polygon objects (page number + x,y coordinates) to draw
    :param input_pdf_path: (str) Path to the input PDF file.
    :param output_pdf_path: (str) Path to save the modified PDF file.
    :param color: (tuple, optional) RGB color of the rectangle (0-1 range). Defaults to
        red (1.0, 0, 0).

    """
    if not file_exists(input_pdf_path):
        logger.error(f"File not found: {input_pdf_path}")

    with tempfile.TemporaryDirectory() as path:
        dpi = 200
        images = convert_from_path(input_pdf_path, output_folder=path, dpi=dpi)

        for polygon in polygons:
            # Note page number is 1 indexed. images is 0 indexed
            if polygon.page_number < 1 or polygon.page_number > len(images):
                return
            page_number = polygon.page_number - 1

            image = images[page_number]
            draw = ImageDraw.Draw(image)
            if polygon.unit.lower() == "inch":
                polygon = scale_polygon(polygon, dpi)
            draw.polygon(polygon.vertices, outline=border_color, fill=fill_color)

        compile_images_to_pdf(images, output_pdf_path)


def draw_text_on_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    text_boxes: list[TextBox],
    color=COLOR["black"],
):
    """Draws a polygon on a specified PDF page and saves it as a new PDF.

    :param input_pdf_path: (str) Path to the input PDF file.
    :param output_pdf_path: (str) Path to save the modified PDF file.
    :param text: text to put on the page
    :param position: Tuple of x,y coordinates
    :param color: (tuple, optional) RGB color of the rectangle (0-255 range). Defaults
        to red (0, 0, 0).

    """
    if not file_exists(input_pdf_path):
        logger.error(f"File not found: {input_pdf_path}")

    with tempfile.TemporaryDirectory() as path:
        dpi = 200
        images = convert_from_path(input_pdf_path, output_folder=path, dpi=dpi)

        for text_box in text_boxes:
            # Note page number is 1 indexed. images is 0 indexed
            if text_box.page_number < 1 or text_box.page_number > len(images):
                return
            page_number = text_box.page_number - 1

            image = images[page_number]
            draw = ImageDraw.Draw(image)
            coordinates = text_box.coordinates
            if text_box.unit.lower() == "inch":
                coordinates = (
                    text_box.coordinates[0] * dpi,
                    text_box.coordinates[1] * dpi,
                )

            font = text_box.font
            if not font:
                font = ImageFont.load_default()
            draw.text(coordinates, text_box.text, fill=color, font=font)

        compile_images_to_pdf(images, output_pdf_path)


def scale_polygon(polygon: Polygon, dpi: int) -> Polygon:
    new_vertices = []
    for coordinate in polygon.vertices:
        vertice = (coordinate[0] * dpi, coordinate[1] * dpi)
        new_vertices.append(vertice)

    return Polygon(page_number=polygon.page_number, vertices=new_vertices, unit="pixel")
