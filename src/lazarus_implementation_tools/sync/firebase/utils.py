import os.path

from lazarus_implementation_tools.config import (
    DOWNLOAD_FOLDER,
    FIREBASE_PERSONAL_ROOT_FOLDER,
    FIREBASE_STORAGE_URL,
    WORKING_FOLDER,
)
from lazarus_implementation_tools.sync.firebase.client import FirebaseStorageManager


def list_files(firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER, recursive=False):
    """Lists all files in the specified Firebase path.

    :param firebase_path: (str) The Firebase path to list files from.
    :param recursive: (bool) If True, include subdirectories; otherwise, only list files
        in the specified directory.

    :returns: (list) A list of file paths.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.list_all_files_in_path(firebase_path, recursive=recursive)


def file_exists(firebase_path):
    """Checks if a file or folder exists in the specified Firebase path.

    :param firebase_path: (str) The Firebase path to check.

    :returns: (bool) True if the file or folder exists, False otherwise.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.exists(firebase_path)


def upload(local_path=WORKING_FOLDER, firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER, recursive=False):
    """Uploads a local file or folder to the specified Firebase path.

    :param local_path: (str) The local file or folder path to upload.
    :param firebase_path: (str) The Firebase path to upload the file or folder to.
    :param recursive: (bool) If True, upload subdirectories; otherwise, only upload
        files in the specified directory.

    :returns: (list) A list of tuples containing the input file path and the destination
        blob name.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    if os.path.isdir(local_path):
        return firebase_manager.upload_folder_to_path(
            firebase_path, local_path, recursive=recursive
        )

    return firebase_manager.upload_file_to_path(firebase_path, local_path)


def download(local_path=DOWNLOAD_FOLDER, firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER):
    """Downloads files from the specified Firebase path to the local folder.

    :param local_path: (str) The local folder to download files to.
    :param firebase_path: (str) The Firebase path to download files from.

    :returns: (list) A list of tuples containing the original file path and the local
        file path.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.download_all_files_from_path(firebase_path, local_path)


def copy(firebase_source_path, firebase_destination_path):
    """Copies files from the specified Firebase source path to the specified Firebase destination path.

    :param firebase_source_path: (str) The Firebase source path to copy files from.
    :param firebase_destination_path: (str) The Firebase destination path to copy files
        to.

    :returns: (list) A list of tuples containing the source file name and the
        destination file name.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.copy_files(firebase_source_path, firebase_destination_path)


def delete(firebase_path):
    """Deletes all files in the specified Firebase path.

    :param firebase_path: (str) The Firebase path to delete files from.

    :returns: (list) A list of deleted file names.

    """
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.delete_files_in_path(firebase_path)


def get_url(firebase_path):
    """Generates a presigned URL for accessing a file in the specified Firebase path.

    :param firebase_path: (str) The Firebase path to the file.

    :returns: (str) The presigned URL, or None if the file does not exist.

    """
    firebase_path = os.path.join(FIREBASE_PERSONAL_ROOT_FOLDER, firebase_path)
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.get_presigned_url(firebase_path)
