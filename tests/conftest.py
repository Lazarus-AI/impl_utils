import os

FIXTURE_ROOT = os.path.join(os.path.dirname(__file__), "fixtures")

# Set all ENV variables with bogus defaults for testing
os.environ["WORKING_FOLDER"] = FIXTURE_ROOT
os.environ["DOWNLOAD_FOLDER"] = FIXTURE_ROOT

# Rikai2
os.environ["RIKAI2_ORG_ID"] = "rikai2_org_id"
os.environ["RIKAI2_AUTH_KEY"] = "rikai2_auth_key"
os.environ["RIKAI2_URL"] = "https://api.lazarusforms.com/api/rikai/bulk/rikai2"
os.environ["RIKAI2_STATUS_URL"] = "https://api.lazarusai.com/api/rikai/zip/async/"
os.environ["WEBHOOK_URL"] = "https://localhost"

# Riky2
os.environ["RIKY2_ORG_ID"] = "riky2_org_id"
os.environ["RIKY2_AUTH_KEY"] = "riky2_auth_key"
os.environ["RIKY2_URL"] = "https://api.lazarusforms.com/api/rikai/bulk/riky2"
os.environ["RIKY2_STATUS_URL"] = "https://api.lazarusai.com/api/rikai/zip/async/"

# RikyExtract
os.environ["RIKAI2_EXTRACT_ORG_ID"] = "rikai2_extract_org_id"
os.environ["RIKAI2_EXTRACT_AUTH_KEY"] = "rikai2_extract_auth_key"
os.environ["RIKAI2_EXTRACT_URL"] = "https://api.lazarusforms.com/api/rikai/bulk/rikai2-extract"
os.environ["RIKAI2_EXTRACT_STATUS_URL"] = "https://api.lazarusai.com/api/rikai/zip/async/"

# PII
os.environ["PII_ORG_ID"] = "pii_org_id"
os.environ["PII_AUTH_KEY"] = "pii_auth_key"
os.environ["PII_RIKAI2_URL"] = "https://api.lazarusai.com/api/forms/pii"
os.environ["PII_RIKAI2_STATUS_URL"] = "https://api.lazarusai.com/api/pii/zip/async/"

# Forms
os.environ["FORMS_ORG_ID"] = "form_org_id"
os.environ["FORMS_AUTH_KEY"] = "form_auth_key"
os.environ["FORMS_URL"] = "https://api.lazarusai.com/api/forms/generic"


# Firebase Environment Variables
os.environ["FIREBASE_STORAGE_URL"] = "lazarus-implementation-dev.firebasestorage.app"
os.environ["FIREBASE_PERSONAL_ROOT_FOLDER"] = "imp-dev/"
os.environ["FIREBASE_WEBHOOK_OUTPUT_FOLDER"] = "imp-dev/"
os.environ["FIREBASE_KEY"] = ".secrets/firebase_key.json"

# PDF Environment Variables
os.environ["CLOUD_CONVERT_API_KEY"] = ""

# Third party services
##gmaps
os.environ["GMAPS_API_KEY"] = ""

##smarty
os.environ["SMARTY_AUTH_ID"] = ""
os.environ["SMARTY_AUTH_TOKEN"] = ""
os.environ["SMARTY_LICENSE"] = ""

##onedrive
os.environ["ONE_DRIVE_CLIENT_ID"] = ""  # Application (client) ID from Azure
os.environ["ONE_DRIVE_CLIENT_SECRET"] = ""  # Client secret value from Azure
os.environ["ONE_DRIVE_TENANT_ID"] = ""  # Use "common" for personal Microsoft accounts
os.environ["ONE_DRIVE_REDIRECT_URI"] = ""  # Must match Azure registration

##gdrive
os.environ["GOOGLE_DRIVE_CREDENTIALS_PATH"] = ""
os.environ["GOOGLE_DRIVE_TOKEN_PATH"] = ""
