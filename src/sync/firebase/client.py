import glob
import os

import requests
from firebase_admin import credentials, delete_app, get_app, initialize_app, storage

from config import FIREBASE_KEY, WORKING_FOLDER

cred = credentials.Certificate(FIREBASE_KEY)


class FirebaseStorageManager:
    def __init__(self, storage_url):
        """
        Initializes a new instance of the FirebaseStorageManager class.

        Args:
        storage_url (str): The URL of the Firebase storage bucket.
        """

        try:
            initialize_app(cred)
        except Exception:
            pass

        self.storage_url = storage_url
        self.bucket = storage.bucket(name=self.storage_url)

    def is_folder(self, blob):
        return blob.name.endswith("/")

    def exists(self, data_path):
        blob = self.bucket.blob(data_path)
        return blob.exists()

    def list_all_files_in_path(self, data_path, recursive=False):
        blobs = self.bucket.list_blobs()
        file_paths = []
        for blob in blobs:
            if blob.name.startswith(data_path):
                file_path = blob.name.replace(data_path, "")
                if not recursive and "/" in file_path:
                    continue

                file_paths.append(file_path)
        return list(set(file_paths))

    def download_all_files_from_path(self, data_path, local_folder):
        results = []
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)

        blobs = self.bucket.list_blobs()
        for blob in blobs:
            if not blob.name.startswith(data_path) or self.is_folder(blob):
                continue
            local_file_path = os.path.join(local_folder, os.path.basename(blob.name))
            results.append((blob.name, local_file_path))
            blob.download_to_filename(local_file_path)
        return results

    def upload_file_to_path(self, data_path, local_file_path):
        relative_dir_path = local_file_path.replace(WORKING_FOLDER, "").strip("/")
        upload_path = str(os.path.join(data_path, relative_dir_path))
        blob = self.bucket.blob(upload_path)
        blob.upload_from_filename(local_file_path)
        return local_file_path, blob.name

    def upload_folder_to_path(self, data_path, local_folder, recursive=False):
        results = []
        if not os.path.exists(local_folder):
            return results

        files = glob.glob(f"{local_folder}/**", recursive=recursive)
        for file in files:
            if file.startswith("."):
                continue
            if not os.path.isfile(file):
                continue
            input_file, destination = self.upload_file_to_path(data_path, file)
            results.append((input_file, destination))
        return results

    def delete_files_in_path(self, data_path):
        results = []
        blobs = self.bucket.list_blobs()
        for blob in blobs:
            if not blob.name.startswith(data_path):
                continue
            results.append(blob.name)
            blob.delete()
        return results

    def get_presigned_url(self, data_path, expiration=3600):
        if data_path.endswith("/"):
            return None

        presigned_url = None
        bucket = storage.bucket(self.storage_url)
        blobs = bucket.list_blobs()
        for blob in blobs:
            if not blob.name == data_path:
                continue
            presigned_url = blob.generate_signed_url(version="v4", expiration=expiration)
        return presigned_url

    # Read content of a file from a presigned URL
    def read_file_from_presigned_url(self, presigned_url):
        """
        Reads content of a file from a presigned URL.

        Args:
        presigned_url (str): The presigned URL of the file to be read.

        Returns:
        str: The content of the file, or an error message.

        Raises:
        requests.exceptions.RequestException: If an error occurs during the HTTP request.
        """
        try:
            response = requests.get(presigned_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}, 500

    def copy_files(self, data_path, destination_folder):
        results = []
        destination_bucket = storage.bucket(name=self.storage_url)

        blobs = self.bucket.list_blobs(prefix=data_path)
        for blob in blobs:
            if not blob.name.startswith(data_path):
                continue

            source_blob_name = blob.name[len(data_path) :]
            source_blob = self.bucket.blob(blob.name)
            destination_blob_name = f"{destination_folder}{source_blob_name}"
            destination_blob = destination_bucket.blob(destination_blob_name)
            destination_blob.upload_from_string(source_blob.download_as_bytes())
            results.append((source_blob_name, destination_blob_name))

        return results

        return {"message": "All files copied successfully"}

    # Close the Firebase connection
    def close_connection(self):
        """
        Closes the Firebase connection.

        Returns:
        None
        """
        try:
            app = get_app()
            delete_app(app)
            print("Firebase connection closed.")
        except ValueError:
            print("No active Firebase app to close.")
