import os

from config import WORKING_FOLDER
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
