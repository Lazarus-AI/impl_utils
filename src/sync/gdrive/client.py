import io
import logging
from typing import Optional

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from file_system.utils import get_extension, get_filename_with_ext

FILE = "file"
FOLDER = "folder"
UNKNOWN = "unknown"


logger = logging.getLogger(__name__)


def get_info_from_google_url(url: str) -> dict:
    """Parses a Google Drive URL and returns information about the resource.

    :param str url: The URL of the Google Drive resource.

    :returns: A dictionary containing the type, sub-type, and file ID of the resource.
    :rtype: dict

    """
    file_indicators = ["presentation", "document", "spreadsheets"]
    folder_indicators = ["folders"]

    fluff = ["http:", "https:", "d", "drive", "docs.google.com", "drive.google.com", ""]
    url_parts = url.split("/")
    details = [part.lower() for part in url_parts if part not in fluff]

    type_indicator = details[0]
    file_id = details[1]
    type = FILE
    sub_type = UNKNOWN
    if type_indicator in folder_indicators:
        type = FOLDER
        sub_type = FOLDER
    elif type_indicator in file_indicators:
        type = FILE
        sub_type = type_indicator

    return {
        "type": type,
        "sub_type": sub_type,
        "file_id": file_id,
    }


def download_file(file_id: str, destination_path: str) -> bool:
    """Downloads a file from Google Drive.

    :param str file_id: The ID of the file to download.
    :param str destination_path: The path where the file should be saved.

    :returns: True if the file was downloaded successfully, False otherwise.
    :rtype: bool

    """
    creds, _ = google.auth.default()

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)

        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.debug(f"Download {int(status.progress() * 100)} of {file_id}.")

        with open(destination_path, "wb") as destination_file:
            destination_file.write(file.getvalue())
        return True

    except HttpError as error:
        logger.error(f"An error occurred: {error}")

    return False


def upload_file(file_path: str) -> Optional[str]:
    """Uploads a file to Google Drive.

    :param str file_path: The path of the file to upload.

    :returns: The ID of the uploaded file, or None if an error occurred.
    :rtype: Optional[str]

    """
    file_name = get_filename_with_ext(file_path)
    mimetype = get_mimetype_by_extension(file_name)
    creds, _ = google.auth.default()

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": file_name}
        media = MediaFileUpload(file_path, mimetype=mimetype)
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        file_id = file.get("id")  # type: str
        logger.info(f"File ID: {file_id}")
        return file_id

    except HttpError as error:
        logger.info(f"An error occurred: {error}")

    return None


def get_mimetype_by_extension(filename: str) -> str:
    file_extension_mimetypes = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pdf": "application/pdf",
        ".csv": "text/csv",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    extension = get_extension(filename)
    return file_extension_mimetypes.get(extension.lower())
