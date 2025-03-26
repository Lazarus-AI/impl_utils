import os

from dotenv import load_dotenv

load_dotenv()

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(dir_path, "..")
PROJECT_ROOT_FOLDER = os.path.abspath(dir_path)


def normalize_path(path):
    if path[0] in ["/", "~"]:
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(PROJECT_ROOT_FOLDER, path))


# Local folders
WORKING_FOLDER = normalize_path(os.environ.get("WORKING_FOLDER"))
DOWNLOAD_FOLDER = normalize_path(os.environ.get("DOWNLOAD_FOLDER"))
TEMP_FOLDER = normalize_path(os.environ.get("TEMP_FOLDER"))

# Firebase Environment Variables
FIREBASE_STORAGE_URL = os.environ.get("FIREBASE_STORAGE_URL", "")
FIREBASE_WEBHOOK_OUTPUT_FOLDER = os.environ.get("FIREBASE_WEBHOOK_OUTPUT_FOLDER", "")
FIREBASE_PERSONAL_ROOT_FOLDER = os.environ.get("FIREBASE_PERSONAL_ROOT_FOLDER", "")
FIREBASE_KEY = os.path.join(PROJECT_ROOT_FOLDER, os.environ.get("FIREBASE_KEY"))
