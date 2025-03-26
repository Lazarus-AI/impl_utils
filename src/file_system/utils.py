import os

from config import WORKING_FOLDER


def in_working(file_path=""):
    return os.path.join(WORKING_FOLDER, file_path)


def get_extension(file_path):
    if "." in file_path:
        return os.path.splitext(file_path)[1].strip(".")
    return ""


def append_to_filename(file_path, append_text):
    extension = get_extension(file_path)
    if extension:
        file_path = file_path.replace(f".{extension}", f"{append_text}.{extension}")

    return file_path
