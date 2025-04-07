import os.path

from config import (
    DOWNLOAD_FOLDER,
    FIREBASE_PERSONAL_ROOT_FOLDER,
    FIREBASE_STORAGE_URL,
    WORKING_FOLDER,
)
from sync.firebase.client import FirebaseStorageManager


def list_files(firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER, recursive=False):
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.list_all_files_in_path(firebase_path, recursive=recursive)


def upload(local_path=WORKING_FOLDER, firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER, recursive=False):
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    if os.path.isdir(local_path):
        return firebase_manager.upload_folder_to_path(
            firebase_path, local_path, recursive=recursive
        )

    return firebase_manager.upload_file_to_path(firebase_path, local_path)


def download(local_path=DOWNLOAD_FOLDER, firebase_path=FIREBASE_PERSONAL_ROOT_FOLDER):
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.download_all_files_from_path(firebase_path, local_path)


def copy(firebase_source_path, firebase_destination_path):
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.copy_files(firebase_source_path, firebase_destination_path)


def delete(firebase_path):
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.delete_files_in_path(firebase_path)


def get_url(firebase_path):
    firebase_path = os.path.join(FIREBASE_PERSONAL_ROOT_FOLDER, firebase_path)
    firebase_manager = FirebaseStorageManager(FIREBASE_STORAGE_URL)
    return firebase_manager.get_presigned_url(firebase_path)
