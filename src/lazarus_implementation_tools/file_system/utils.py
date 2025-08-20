import glob
import json
import os
import zipfile
from urllib.parse import urlparse
from uuid import uuid4
from pathlib import Path

from lazarus_implementation_tools.config import DOWNLOAD_FOLDER, WORKING_FOLDER


def in_working(file_path=""):
    """Returns the path to a file within the working directory.

    :param file_path: The relative path to the file within the working directory.

    :returns: The full path to the file.

    """
    return os.path.join(WORKING_FOLDER, file_path)


def in_downloads(file_path=""):
    """Returns the path to a file within the download directory.

    :param file_path: The relative path to the file within the download directory.

    :returns: The full path to the file.

    """
    return os.path.join(DOWNLOAD_FOLDER, file_path)


def is_dir(file_path=""):
    """Checks if the given file path is a directory.

    :param file_path: The path to check.

    :returns: True if the path is a directory, False otherwise.

    """
    return os.path.isdir(file_path)


def file_exists(file_path):
    """Checks if the given file path exists.

    :param file_path: The path to check.

    :returns: True if the path exists, False otherwise.

    """
    return os.path.exists(file_path)


def mkdir(file_path):
    """Creates a directory if it does not already exist.

    :param file_path: The path of the directory to create.

    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def get_folder(file_path):
    """Returns the directory containing the given file path.

    :param file_path: The file path.

    :returns: The directory of the file path.

    """
    return os.path.dirname(file_path)


def get_filename(file_path):
    """Returns the filename without the extension from the given file path.

    :param file_path: The file path.

    :returns: The filename without the extension.

    """
    # Get filename without extension
    return os.path.splitext(os.path.basename(file_path))[0]


def get_filename_with_ext(file_path: str) -> str:
    """Returns the filename with the extension from the given file path.

    :param file_path: The file path.

    :returns: The filename with the extension.

    """
    return os.path.basename(file_path)


def get_extension(file_path):
    """Returns the extension of the given file path.

    :param file_path: The file path.

    :returns: The file extension (without the dot).

    """
    if "." in file_path:
        return os.path.splitext(file_path)[1].strip(".").lower()
    return ""


def append_to_filename(file_path, append_text):
    """Appends text to the filename of the given file path.

    :param file_path: The file path.
    :param append_text: The text to append to the filename.

    :returns: The modified file path with appended text.

    """
    extension = get_extension(file_path)
    if extension:
        file_path = file_path.replace(f".{extension}", f"{append_text}.{extension}")

    return file_path


def get_all_files(dir, recursive=False):
    """Returns a list of all files in the given directory.

    :param dir: The directory path.
    :param recursive: If True, includes subdirectories.

    :returns: A list of file paths.

    """
    return glob.glob(dir + "/*", recursive=recursive)


def get_all_files_with_ext(path, ext):
    """Returns a list of all files with a specific extension in the given directory.

    :param path: The directory path.
    :param ext: The file extension.

    :returns: A list of file paths with the specified extension.

    """
    return glob.glob(path + f"/**/*.{ext}", recursive=True)


def unzip(path, recursive=False, delete=False):
    """Unzips a file to a specified directory and optionally deletes the original zip file.

    :param path: The path to the zip file.
    :param recursive: If True, recursively unzips any subfiles that may be zipped.
    :param delete: If True, deletes the original zip file after extraction.

    """
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
    """Tidies all JSON files in the given directory by formatting them with proper indentation.

    :param path: The directory path.

    """
    # iterates through all json files and tidies them by
    # loading the json and reformatting them all pretty like.
    json_files = get_all_files_with_ext(path, "json")
    for json_file in json_files:
        tidy_json_file(json_file)


def tidy_json_file(file_path):
    """Tidies a single JSON file by formatting it with proper indentation.

    :param file_path: The path to the JSON file.

    """
    with open(file_path, "r") as file:
        data = file.read()
        json_data = json.loads(data)

    pretty_json = json.dumps(json_data, indent=4)
    with open(file_path, "w") as file:
        file.write(pretty_json)


def tidy_text_files(path):
    """Tidies all text files in the given directory by removing escape characters.

    :param path: The directory path.

    """
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
    """Loads and returns the data from a JSON file.

    :param json_file: The path to the JSON file.

    :returns: The data loaded from the JSON file.

    """
    with open(json_file, "r") as file:
        data = file.read()
        json_data = json.loads(data)
        return json_data


def is_url(url):
    """Is this a url? :param url: Url to test"""
    return url.lower().startswith("http")


def get_filename_from_url(url):
    """Extracts the filename from a given URL.

    :param url: URL to parse

    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    if not filename:
        short_uuid = str(uuid4())[:8]
        filename = f"file_url_{short_uuid}"
    return filename

def get_absolute_path(file_path: str) -> str:
    """Returns the absolute path of a given file path.

    If the file path is relative, it will be made absolute.
    If the file path is absolute, it will be returned as is.

    :param file_path: The file path.

    :returns: The absolute path of the file path.

    """
    return Path(file_path).resolve()
