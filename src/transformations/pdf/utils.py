import logging
import os
from typing import List, Optional, Union

import PyPDF2
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

from file_system.utils import append_to_filename, get_filename, get_folder, mkdir
from general.pydantic_models import BoundingBox
from transformations.pdf.bounding_boxes import draw_box_on_pdf
from transformations.pdf.libre_office import convert_file_to_pdf, convert_folder_to_pdf
from transformations.pdf.transformations import PDFTidy


logger = logging.getLogger(__name__)

def convert_to_pdf(
    path: Union[str, List], output_dir: Optional[str] = None, recursive=False
) -> List[str]:
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
    if not output_path:
        output_path = append_to_filename(pdf_paths[0], "_merged_file")
    merger = PdfMerger()
    for pdf in pdf_paths:
        try:
            merger.append(pdf)
        except PyPDF2.errors.EmptyFileError:
            logging.info(f"Skipping empty PDF file: {pdf}")
        except PyPDF2.errors.PdfReadError:
            logging.info(f"Skipping corrupted PDF file: {pdf}")

    merger.write(output_path)
    merger.close()
    return output_path


def trim_pdf(
    input_path: str, start_page: int, end_page: int, output_path: Optional[str] = None
) -> str:
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
    """
    Returns the number of pages in a PDF file.

    :param pdf_path: The file path of the PDF file.
    :return: The number of pages in the PDF file.
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
    tidier = PDFTidy(pdf_path)
    return tidier.tidy(destination_path=destination_path, deskew=deskew, auto_crop=auto_crop)  # type: ignore


def draw_bounding_boxes(
    pdf_path: str, bounding_boxes: List[BoundingBox], destination_path: Optional[str] = None
) -> Optional[str]:
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


def convert_pdf_to_images(
    pdf_path: str,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    output_folder: Optional[str] = None,
) -> str:
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
