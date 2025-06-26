import logging
import os
from typing import List, Optional, Union

import PyPDF2
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

from lazarus_implementation_tools.file_system.utils import (
    append_to_filename,
    get_filename,
    get_folder,
    mkdir,
)
from lazarus_implementation_tools.general.core import COLOR
from lazarus_implementation_tools.general.pydantic_models import (
    BoundingBox,
    Polygon,
    TextBox,
)
from lazarus_implementation_tools.transformations.pdf.bounding_boxes import (
    draw_box_on_pdf,
    draw_polygon_on_pdf,
    draw_text_on_pdf,
)
from lazarus_implementation_tools.transformations.pdf.core import (
    convert_file_to_pdf,
    convert_folder_to_pdf,
)
from lazarus_implementation_tools.transformations.pdf.core import (
    merge_pdfs as core_merge_pdfs,
)
from lazarus_implementation_tools.transformations.pdf.transformations import PDFTidy

logger = logging.getLogger(__name__)


def convert_to_pdf(
    path: Union[str, List], output_dir: Optional[str] = None, recursive=False
) -> List[str]:
    """Converts a file or directory of files to PDF.

    :param path: The file or directory path to convert.
    :param output_dir: The output directory for the converted PDF files. If None, uses
        the same directory as the input files.
    :param recursive: If True, recursively convert files in subdirectories.

    :returns: A list of paths to the converted PDF files.

    """
    results = []
    if isinstance(path, list):
        for path_item in path:
            results.append(convert_file_to_pdf(path_item, output_dir))
            return results

    if isinstance(path, str):
        if not os.path.exists(path):
            return results

        if path.startswith("."):
            return results

        if os.path.isfile(path):
            return [convert_file_to_pdf(path, output_dir)]

        return convert_folder_to_pdf(path, output_dir, recursive=recursive)  # type: ignore

    return results


def merge_pdfs(pdf_paths: List, output_path: Optional[str] = None) -> str:
    """Merges multiple PDF files into one"""
    return core_merge_pdfs(pdf_paths, output_path)


def trim_pdf(
    input_path: str, start_page: int, end_page: int, output_path: Optional[str] = None
) -> str:
    """Trims a PDF file to the specified start and end pages.

    :param input_path: The path to the input PDF file.
    :param start_page: The starting page number (1-based).
    :param end_page: The ending page number (1-based).
    :param output_path: The output path for the trimmed PDF file. If None, uses a
        default name.

    :returns: The path to the trimmed PDF file.

    """
    if output_path is None:
        output_path = append_to_filename(input_path, f"_{start_page}-{end_page}")

    num_pages = get_number_of_pages(input_path)
    if end_page > num_pages:
        end_page = num_pages
    # Ensure the page numbers are zero-indexed
    start_page -= 1
    end_page -= 1

    # Read the input PDF
    reader = PdfReader(input_path)

    # Create a PDF writer object
    writer = PdfWriter()

    # Add pages to the writer from the input range
    for page_num in range(start_page, end_page + 1):
        writer.add_page(reader.pages[page_num])

    # Write the trimmed PDF to the output path
    with open(output_path, "wb") as output_pdf:
        writer.write(output_pdf)

    return output_path


def get_number_of_pages(pdf_path: str) -> Optional[int]:
    """Returns the number of pages in a PDF file.

    :param pdf_path: The file path of the PDF file.

    :returns: The number of pages in the PDF file.

    """
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
    except Exception as e:
        logging.error(f"Error: {e}")
        return None


def tidy_pdf(
    pdf_path: str,
    destination_path: Optional[str] = None,
    deskew: bool = True,
    auto_crop: bool = True,
) -> str:
    """Tidies a PDF file by deskewing and/or auto-cropping.

    :param pdf_path: The path to the input PDF file.
    :param destination_path: The output path for the tidied PDF file. If None, uses a
        default name.
    :param deskew: If True, deskews the PDF.
    :param auto_crop: If True, auto-crops the PDF.

    :returns: The path to the tidied PDF file.

    """
    tidier = PDFTidy(pdf_path)
    return tidier.tidy(destination_path=destination_path, deskew=deskew, auto_crop=auto_crop)  # type: ignore


def rasterize_pdf(
    pdf_path: str,
    destination_path: Optional[str] = None,
):
    """Rasterizes a PDF file to images.

    :param pdf_path: The path to the input PDF file.
    :param destination_path: The output path for the rasterized images. If None, uses a
        default name.

    """
    tidier = PDFTidy(pdf_path)
    return tidier.tidy(destination_path=destination_path, deskew=False, auto_crop=False)  # type: ignore


def draw_bounding_boxes(
    pdf_path: str, bounding_boxes: List[BoundingBox], destination_path: Optional[str] = None
) -> Optional[str]:
    """Draws bounding boxes on a PDF file.

    :param pdf_path: The path to the input PDF file.
    :param bounding_boxes: A list of bounding boxes to draw.
    :param destination_path: The output path for the PDF with bounding boxes. If None,
        uses a default name.

    :returns: The path to the PDF with bounding boxes, or None if no bounding boxes are
        provided.

    """
    if not bounding_boxes:
        return None

    if destination_path is None:
        destination_path = append_to_filename(pdf_path, f"_bounding_boxes")

    draw_box_on_pdf(
        input_pdf_path=pdf_path,
        output_pdf_path=destination_path,
        bounding_boxes=bounding_boxes,
    )

    return destination_path


def draw_polygons(
    pdf_path: str,
    polygons: List[Polygon],
    destination_path: Optional[str] = None,
    border_color=COLOR["red"],
    fill_color=COLOR["transparent"],
) -> Optional[str]:
    """Draws Polygons on a PDF file.

    :param pdf_path: The path to the input PDF file.
    :param polygons: A list of polygons to draw.
    :param destination_path: The output path for the PDF with bounding boxes. If None,
        uses a default name.

    :returns: The path to the PDF with bounding boxes, or None if no bounding boxes are
        provided.

    """
    if not polygons:
        return None

    if destination_path is None:
        destination_path = append_to_filename(pdf_path, f"_polygons")

    draw_polygon_on_pdf(
        input_pdf_path=pdf_path,
        output_pdf_path=destination_path,
        polygons=polygons,
        border_color=border_color,
        fill_color=fill_color,
    )

    return destination_path


def draw_text_boxes(
    pdf_path: str,
    text_boxes: List[TextBox],
    destination_path: Optional[str] = None,
    color=COLOR["black"],
) -> Optional[str]:
    """Draws Polygons on a PDF file.

    :param pdf_path: The path to the input PDF file.
    :param text_boxes: A list of text boxes to draw.
    :param destination_path: The output path for the PDF with bounding boxes. If None,
        uses a default name.
    :param color: Text color

    :returns: The path to the PDF with bounding boxes, or None if no bounding boxes are
        provided.

    """
    if not text_boxes:
        return None

    if destination_path is None:
        destination_path = append_to_filename(pdf_path, f"_text_boxes")

    draw_text_on_pdf(
        input_pdf_path=pdf_path,
        output_pdf_path=destination_path,
        text_boxes=text_boxes,
        color=color,
    )

    return destination_path


def convert_pdf_to_images(
    pdf_path: str,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    output_folder: Optional[str] = None,
) -> str:
    """Converts a PDF file to images.

    :param pdf_path: The path to the input PDF file.
    :param start_page: The starting page number (1-based) to convert. If None, converts
        all pages.
    :param end_page: The ending page number (1-based) to convert. If None, converts all
        pages.
    :param output_folder: The output folder for the images. If None, uses a default
        name.

    :returns: The path to the output folder containing the images.

    """
    if not output_folder:
        filename = get_filename(pdf_path)
        folder = get_folder(pdf_path)
        folder = f"{folder}/{filename}_images"
        mkdir(folder)
        output_folder = folder

    convert_from_path(
        pdf_path=pdf_path,
        dpi=300,
        first_page=start_page,
        last_page=end_page,
        fmt="jpeg",
        output_folder=output_folder,
        output_file="page_",
    )
    return output_folder
