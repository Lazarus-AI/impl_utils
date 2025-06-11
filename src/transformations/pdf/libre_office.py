import logging
import subprocess

from config import PATH_TO_LIBRE_OFFICE, PROJECT_ROOT_FOLDER

logger = logging.getLogger(__name__)


def libre_office_convert_file(file_path, output_dir, convert_to="pdf"):
    """Converts a single file to the specified format using LibreOffice.

    :param file_path: (str) The path to the file to convert.
    :param output_dir: (str) The output directory for the converted file.
    :param convert_to: (str) The target format to convert the file to (default is
        "pdf").

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
