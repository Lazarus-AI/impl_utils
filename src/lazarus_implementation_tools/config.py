import os

from dotenv import load_dotenv

load_dotenv()

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(dir_path, "..")
PROJECT_ROOT_FOLDER = os.path.abspath(dir_path)


def normalize_path(path):
    if path is None:
        msg = "Please configure your WORKING_FOLDER, DOWNLOAD_FOLDER and any other environment variables you may need."
        raise Exception(msg)
    if path[0] in ["/", "~"]:
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(PROJECT_ROOT_FOLDER, path))


# Global variables
DEBUG_MODE = os.environ.get("DEBUG_MODE", "").lower() == "true"


# Local folders
WORKING_FOLDER = normalize_path(os.environ.get("WORKING_FOLDER"))
DOWNLOAD_FOLDER = normalize_path(os.environ.get("DOWNLOAD_FOLDER"))

# Rikai2 Variables
RIKAI2_ORG_ID = os.environ.get("RIKAI2_ORG_ID", "")
RIKAI2_AUTH_KEY = os.environ.get("RIKAI2_AUTH_KEY", "")
RIKAI2_URL = os.environ.get("RIKAI2_URL", "")
RIKAI2_STATUS_URL = os.environ.get("RIKAI2_STATUS_URL", "")

# Riky2 Variables
RIKY2_ORG_ID = os.environ.get("RIKY2_ORG_ID", "")
RIKY2_AUTH_KEY = os.environ.get("RIKY2_AUTH_KEY", "")
RIKY2_URL = os.environ.get("RIKY2_URL", "")
RIKY2_STATUS_URL = os.environ.get("RIKY2_STATUS_URL", "")

# RikyExtract Variables
RIKY_EXTRACT_ORG_ID = os.environ.get("RIKY_EXTRACT_ORG_ID", "")
RIKY_EXTRACT_AUTH_KEY = os.environ.get("RIKY_EXTRACT_AUTH_KEY", "")
RIKY_EXTRACT_URL = os.environ.get("RIKY_EXTRACT_URL", "")
RIKY_EXTRACT_STATUS_URL = os.environ.get("RIKY_EXTRACT_STATUS_URL", "")

# Webhook
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Batch Settings
BATCH_TIMEOUT = int(os.environ.get("BATCH_TIMEOUT", 300))  # 5 minutes in seconds

# Firebase Environment Variables
FIREBASE_STORAGE_URL = os.environ.get("FIREBASE_STORAGE_URL", "")
FIREBASE_WEBHOOK_OUTPUT_FOLDER = os.environ.get("FIREBASE_WEBHOOK_OUTPUT_FOLDER", "")
FIREBASE_PERSONAL_ROOT_FOLDER = os.environ.get("FIREBASE_PERSONAL_ROOT_FOLDER", "")
FIREBASE_KEY = os.path.join(PROJECT_ROOT_FOLDER, os.environ.get("FIREBASE_KEY"))


# PDF Variables
PATH_TO_LIBRE_OFFICE = os.environ.get("PATH_TO_LIBRE_OFFICE", "soffice")
CLOUD_CONVERT_API_KEY = os.environ.get("CLOUD_CONVERT_API_KEY")
