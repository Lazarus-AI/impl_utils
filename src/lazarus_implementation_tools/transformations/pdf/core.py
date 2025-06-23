import glob
import logging
import os
import shutil
import tempfile
from typing import List, Optional

import extract_msg
import PyPDF2
from fpdf import FPDF
from PyPDF2 import PdfMerger
from xhtml2pdf import pisa

from lazarus_implementation_tools.file_system.utils import (
    append_to_filename,
    get_filename,
    get_folder,
    in_working,
)
from lazarus_implementation_tools.general.core import sanitize_string
from lazarus_implementation_tools.transformations.pdf.libre_office import (
    libre_office_convert_file,
    logger,
)
from lazarus_implementation_tools.transformations.pdf.transformations import (
    compile_image_files_to_pdf,
)


def convert_file_to_pdf(file_path: str, output_dir: Optional[str]) -> Optional[str]:
    """Converts a single file to PDF using LibreOffice.

    :param file_path: (str) The path to the file to convert.
    :param output_dir: (Optional[str]) The output directory for the converted PDF. If
        None, uses the same directory as the input file.

    :returns: (Optional[str]) The path to the converted PDF file, or None if the
        conversion fails.

    """
    if output_dir is None:
        output_dir = get_folder(file_path)

    file_extension = os.path.splitext(file_path)[1].strip(".").lower()

    if file_extension == "pdf":
        return file_path

    supported_office_extensions = [
        "doc",
        "docx",
        "xlsx",
        "xls",
        "ppt",
        "pptx",
        "txt",
        "odt",
        "ods",
        "odp",
    ]
    if file_extension in supported_office_extensions:
        convert_to = "pdf"
        if file_extension in ["xlsx", "xls", "ods"]:
            convert_to = (
                'pdf:draw_pdf_Export:{"SinglePageSheets":{"type":"boolean","value":"true"}}'
            )

        libre_office_convert_file(file_path, output_dir, convert_to=convert_to)
        output_file = f"{output_dir}/{get_filename(file_path)}.pdf"
        return output_file

    email_extensions = ["msg"]
    if file_extension in email_extensions:
        output_file = f"{output_dir}/{get_filename(file_path)}.pdf"
        convert_msg_to_pdf(file_path, output_file)
        return output_file

    image_extensions = ["jpg", "jpeg", "gif", "tif", "tiff", "png"]
    if file_extension in image_extensions:
        output_file = f"{output_dir}/{get_filename(file_path)}.pdf"
        compile_image_files_to_pdf([file_path], output_file)
        return output_file

    image_extensions = ["txt", "csv"]
    if file_extension in image_extensions:
        output_file = f"{output_dir}/{get_filename(file_path)}.pdf"
        with open(file_path, "w") as file:
            file_contents = file.read()
        create_pdf_from_string(file_contents, output_file)
        return output_file

    return None


def convert_folder_to_pdf(
    dir_path: str, output_dir: Optional[str] = None, recursive: bool = False
) -> List[str]:
    """Converts all supported files in a directory to PDF using LibreOffice.

    :param dir_path: (str) The path to the directory containing the files to convert.
    :param output_dir: (Optional[str]) The output directory for the converted PDFs. If
        None, uses the same directory as the input files.
    :param recursive: (bool) If True, recursively convert files in subdirectories.

    :returns: (List[str]) A list of paths to the converted PDF files.

    """
    # if dir: create blob and do all files
    # else just do the one file
    results = []  # type: List
    if not os.path.exists(dir_path):
        return results

    files = glob.glob(f"{dir_path}/**", recursive=recursive)
    for file in files:
        if file.startswith("."):
            continue
        if not os.path.isfile(file):
            continue

        output_file = convert_file_to_pdf(file, output_dir=output_dir)
        if output_file:
            results.append(output_file)

    return results


def convert_msg_to_pdf(file_path: str, destination_path: str = None) -> Optional[str]:
    if destination_path is None:
        destination_path = f"{get_folder(file_path)}/{get_filename(file_path)}.pdf"

    # Extract message parts
    msg = extract_msg.Message(file_path)
    msg_body = msg.body or ""
    msg_html_body = msg.htmlBody or ""
    msg_subject = msg.subject or "No Subject"
    msg_sender = msg.sender or "Unknown Sender"
    msg_date = msg.date or "Unknown Date"

    # Clean the extracted text
    msg_subject = sanitize_string(msg_subject)
    msg_sender = sanitize_string(msg_sender)
    msg_date = sanitize_string(msg_date)
    msg_body = sanitize_string(msg_body)
    msg_html_body = sanitize_string(msg_html_body)

    # Prepare text content
    content = [
        f"Subject: {msg_subject}",
        f"From: {msg_sender}",
        f"Date: {msg_date}",
        "",
    ]

    files = []
    with tempfile.TemporaryDirectory() as path:
        # Create the PDF using the content list
        message_path = os.path.join(path, "message.pdf")
        if msg_body:
            content.append(msg_body)
            create_pdf_from_string("\n".join(content), message_path)
        else:
            content.append(msg_html_body)
            create_pdf_from_html("<br>".join(content), message_path)
        files.append(message_path)

        msg.saveAttachments(customPath=path, skipHidden=True)
        for attachment in msg.attachments:
            if attachment.longFilename:
                attachment_file = os.path.join(path, attachment.longFilename)
                # Not sure why we end up with these in the file name, but they need to be stripped.
                attachment_file = attachment_file.replace("\x00", "")
                files.append(attachment_file)
            else:
                logger.info("Skipping attachment with None filename.")

        pdf_files = []
        if files:
            for file in files:
                try:
                    pdf_file = convert_file_to_pdf(file, path)
                    if pdf_file:
                        pdf_files.append(pdf_file)
                    shutil.copy(file, in_working(f"message/{os.path.basename(file)}"))
                except FileNotFoundError:
                    pass
        merge_pdfs(pdf_files, destination_path)

    return destination_path


def create_pdf_from_html(content: str, destination_path: str) -> Optional[str]:
    """Converts html content to a pdf"""
    with open(destination_path, "wb") as pdf_file:
        status = pisa.CreatePDF(content, dest=pdf_file)

    return destination_path if status else None


def create_pdf_from_string(content: str, destination_path: str) -> Optional[str]:
    """Given a list of strings, creates a PDF with the text and saves it to file_name."""
    # Encoding to latin-1
    # In the future if we want to support utf-8, we'll need to include a font set that will do this.
    content = content.encode("latin-1", errors="replace").decode("latin-1")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    max_width = pdf.w - 2 * pdf.l_margin

    # content = sanitize_string(content)
    try:
        height = pdf.font_size
        width = pdf.get_string_width(content)
        if width > max_width:
            pdf.multi_cell(max_width, height, content)
        else:
            pdf.cell(0, height, txt=content, ln=True)
        # Add some extra vertical spacing
        pdf.ln(10)
    except Exception as e:
        logger.error(f"Error creating PDF for {destination_path}: {e}")
        return None

    try:
        pdf.output(destination_path)
        return destination_path
    except Exception as e:
        logger.error(f"Error saving PDF for {destination_path}: {e}")
        return None


def merge_pdfs(pdf_paths: List, output_path: Optional[str] = None) -> str:
    """Merges multiple PDF files into a single PDF file.

    :param pdf_paths: A list of paths to the PDF files to merge.
    :param output_path: The output path for the merged PDF file. If None, uses a default
        name.

    :returns: The path to the merged PDF file.

    """
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
