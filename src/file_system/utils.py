import glob
import json
import os
import zipfile

from config import DOWNLOAD_FOLDER, TEMP_FOLDER, WORKING_FOLDER


def in_working(file_path=""):
    return os.path.join(WORKING_FOLDER, file_path)


def in_downloads(file_path=""):
    return os.path.join(DOWNLOAD_FOLDER, file_path)


def in_tmp(file_path=""):
    return os.path.join(TEMP_FOLDER, file_path)


def is_dir(file_path=""):
    return os.path.isdir(file_path)

def file_exists(file_path):
    return os.path.exists(file_path)

def mkdir(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def get_folder(file_path):
    return os.path.dirname(file_path)


def get_filename(file_path):
    # Get filename without extension
    return os.path.splitext(os.path.basename(file_path))[0]


def get_extension(file_path):
    if "." in file_path:
        return os.path.splitext(file_path)[1].strip(".").lower()
    return ""


def append_to_filename(file_path, append_text):
    extension = get_extension(file_path)
    if extension:
        file_path = file_path.replace(f".{extension}", f"{append_text}.{extension}")

    return file_path


def get_all_files(dir, recursive=False):
    return glob.glob(dir + "/*", recursive=recursive)


def get_all_files_with_ext(path, ext):
    return glob.glob(path + f"/**/*.{ext}", recursive=True)


def unzip(path, recursive=False, delete=False):
    if not path.endswith(".zip"):
        return

    extract_folder = path[0:-4]
    if os.path.isdir(extract_folder):
        return

    with zipfile.ZipFile(path, "r") as zip_reference:
        zip_reference.extractall(extract_folder)

    if delete:
        try:
            os.remove(path)
        except Exception:
            pass

    if recursive:
        # Look for any subfiles that may be zipped
        zip_files = get_all_files_with_ext(extract_folder, "zip")
        for zip_file in zip_files:
            unzip(zip_file, delete=True)


def tidy_json_files(path):
    # iterates through all json files and tidies them by
    # loading the json and reformatting them all pretty like.
    json_files = get_all_files_with_ext(path, "json")
    for json_file in json_files:
        tidy_json_file(json_file)


def tidy_json_file(file_path):
    with open(file_path, "r") as file:
        data = file.read()
        json_data = json.loads(data)

    pretty_json = json.dumps(json_data, indent=4)
    with open(file_path, "w") as file:
        file.write(pretty_json)


def tidy_text_files(path):
    # iterates through all text files and tidies them
    txt_files = get_all_files_with_ext(path, "txt")
    for txt_file in txt_files:
        with open(txt_file, "r") as file:
            data = file.read()

        try:
            txt = data.encode("utf-8").decode("unicode_escape")
            with open(txt_file, "w") as file:
                file.write(txt)
        except UnicodeDecodeError:
            pass


def load_json_from_file(json_file):
    with open(json_file, "r") as file:
        data = file.read()
        json_data = json.loads(data)
        return json_data
