import glob
import os
import subprocess

from config import PATH_TO_LIBRE_OFFICE, PROJECT_ROOT_FOLDER, WORKING_FOLDER


def libre_office_convert_file(file_path, output_dir, convert_to="pdf"):
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


def convert_file_to_pdf(file_path, output_dir):
    supported_extensions = ["doc", "docx", "xlsx", "xls", "ppt", "pptx", "txt", "odt", "ods", "odp"]
    file_extension = os.path.splitext(file_path)[1].strip(".")
    if file_extension not in supported_extensions:
        return file_path, None

    libre_office_convert_file(file_path, output_dir, convert_to="pdf")
    return file_path, output_dir


def convert_folder_to_pdf(dir_path, output_dir=WORKING_FOLDER, recursive=False):
    # if dir: create blob and do all files
    # else just do the one file
    results = []
    if not os.path.exists(dir_path):
        return results

    files = glob.glob(f"{dir_path}/**", recursive=recursive)
    for file in files:
        if file.startswith("."):
            continue
        if not os.path.isfile(file):
            continue

        destination_folder = os.path.dirname(file).replace(dir_path, output_dir)
        input_file, destination = convert_file_to_pdf(file, destination_folder)
        results.append((input_file, destination))

    return results
