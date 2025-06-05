import glob
import os
import subprocess
from typing import List, Optional

from config import PATH_TO_LIBRE_OFFICE, PROJECT_ROOT_FOLDER
from file_system.utils import get_filename, get_folder


def libre_office_convert_file(file_path, output_dir, convert_to="pdf"):
    """
    Converts a single file to the specified format using LibreOffice.

    :param file_path:  (str) The path to the file to convert.
    :param output_dir:  (str) The output directory for the converted file.
    :param convert_to:  (str) The target format to convert the file to (default is "pdf").
    """
    command = [
        PATH_TO_LIBRE_OFFICE,
        "--headless",
        "--convert-to",
        convert_to,
        "--outdir",
        output_dir,
        file_path,
    ]
    subprocess.run(command, capture_output=True, text=True, cwd=PROJECT_ROOT_FOLDER)


def convert_file_to_pdf(file_path: str, output_dir: Optional[str]) -> Optional[str]:
    """
    Converts a single file to PDF using LibreOffice.

    :param file_path:  (str) The path to the file to convert.
    :param output_dir:  (Optional[str]) The output directory for the converted PDF. If None, uses the same directory as the input file.
    :return:  (Optional[str]) The path to the converted PDF file, or None if the conversion fails.
    """
    if output_dir is None:
        output_dir = get_folder(file_path)

    supported_extensions = ["doc", "docx", "xlsx", "xls", "ppt", "pptx", "txt", "odt", "ods", "odp"]
    file_extension = os.path.splitext(file_path)[1].strip(".")
    if file_extension not in supported_extensions:
        return None

    libre_office_convert_file(file_path, output_dir, convert_to="pdf")
    output_file = f"{output_dir}/{get_filename(file_path)}.pdf"
    return output_file


def convert_folder_to_pdf(
    dir_path: str, output_dir: Optional[str] = None, recursive: bool = False
) -> List[str]:
    """
    Converts all supported files in a directory to PDF using LibreOffice.

    :param dir_path:  (str) The path to the directory containing the files to convert.
    :param output_dir:  (Optional[str]) The output directory for the converted PDFs. If None, uses the same directory as the input files.
    :param recursive:  (bool) If True, recursively convert files in subdirectories.
    :return:  (List[str]) A list of paths to the converted PDF files.
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
