import os

import PyPDF2
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

from config import WORKING_FOLDER
from file_system.utils import append_to_filename
from transformations.pdf.libre_office import convert_file_to_pdf, convert_folder_to_pdf


def convert_to_pdf(path, output_dir=WORKING_FOLDER, recursive=False):
    results = []
    if not os.path.exists(path):
        return results

    if path.startswith("."):
        return results

    if os.path.isfile(path):
        return convert_file_to_pdf(path, output_dir)

    return convert_folder_to_pdf(path, output_dir, recursive=recursive)


def merge_pdfs(pdf_paths, output_path=None):
    if not output_path:
        output_path = append_to_filename(pdf_paths[0], "_merged_file")
    merger = PdfMerger()
    for pdf in pdf_paths:
        try:
            merger.append(pdf)
        except PyPDF2.errors.EmptyFileError:
            print(f"Skipping empty PDF file: {pdf}")
        except PyPDF2.errors.PdfReadError:
            print(f"Skipping corrupted PDF file: {pdf}")

    merger.write(output_path)
    merger.close()
    return output_path


def trim_pdf(input_path, start_page, end_page, output_path=None):
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

    return input_path, output_path


def get_number_of_pages(pdf_path):
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
        print(f"Error: {e}")
        return None
