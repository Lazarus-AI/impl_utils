import base64
import json
import logging
import uuid
from http import HTTPStatus
from typing import Optional

import requests

from lazarus_implementation_tools.config import (
    FORMS_AUTH_KEY,
    FORMS_ORG_ID,
    FORMS_URL,
    PII_AUTH_KEY,
    PII_ORG_ID,
    PII_URL,
    RIKAI2_AUTH_KEY,
    RIKAI2_EXTRACT_AUTH_KEY,
    RIKAI2_EXTRACT_ORG_ID,
    RIKAI2_EXTRACT_URL,
    RIKAI2_ORG_ID,
    RIKAI2_URL,
    RIKY2_AUTH_KEY,
    RIKY2_ORG_ID,
    RIKY2_URL,
    WEBHOOK_URL,
)
from lazarus_implementation_tools.file_system.utils import get_filename, get_folder
from lazarus_implementation_tools.models.constants import POST

logger = logging.getLogger(__name__)


class ModelAPI:
    """Base class for interacting with various APIs."""

    def __init__(self):
        self.method = POST
        self.url = ""
        self.org_id = ""
        self.auth_key = ""
        self.webhook = WEBHOOK_URL

        self.file = None
        self.return_file_name = None
        self.return_file_path = None
        self.prompt = ""
        self.response = None

        self.is_async = True

    @property
    def name(self):
        """Returns the name of the class.

        :returns: The name of the class.

        """
        return self.__class__.__name__

    def get_headers(self):
        """Returns the headers for the request.

        :returns: A dictionary of headers.

        """
        return {"orgId": self.org_id, "authKey": self.auth_key, "Content-Type": "application/json"}

    def _get_file_base64(self, path):
        """Encodes a file as base64.

        :param path: The path to the file.

        :returns: The base64 encoded string.

        """
        with open(self.file, "rb") as file:
            encoded_string = base64.b64encode(file.read())
            return encoded_string.decode("utf-8")

    def add_file_to_payload(self, payload):
        """Adds the file to the payload.

        :param payload: The payload dictionary.

        :returns: The modified payload dictionary.

        """
        raise NotImplementedError

    def build_payload(self):
        """Builds the payload for the request.

        :returns: The payload dictionary.

        """
        raise NotImplementedError

    def set_file(self, file):
        """Sets the file for the API request.

        :param file: The path to the file.

        """
        self.file = file
        self.return_file_name = f"{get_filename(file)}_{self.name}"
        self.set_firebase_file_name()

        self.download_folder = get_folder(self.file)
        self.return_file_path = f"{self.download_folder}/{self.return_file_name}.json"

    def set_firebase_file_name(self, file_name: Optional[str] = None):
        """Sets the return file name.

        :param file_name: The name of the return file.

        """
        if not file_name:
            file_name = str(uuid.uuid4())
        self.firebase_file_name = file_name

    def run(self, file=None, prompt=None):
        """Runs the API request.

        :param file: The path to the file.
        :param prompt: The prompt for the API.

        :returns: The response from the API.

        """
        if file:
            self.set_file(file)

        if prompt:
            self.prompt = prompt

        payload = self.build_payload()
        self.response = requests.request(
            self.method, self.url, headers=self.get_headers(), data=json.dumps(payload)
        )
        if self.response.status_code != HTTPStatus.OK:
            logging.info(f"{self.response.status_code}: {self.response.json()}")

        return self.response


class Rikai2(ModelAPI):
    """Class for interacting with the Rikai2 API."""

    def __init__(
        self,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        auth_key: Optional[str] = None,
        webhook: Optional[str] = None,
    ):
        super().__init__()
        self.url = url or RIKAI2_URL
        self.org_id = org_id or RIKAI2_ORG_ID
        self.auth_key = auth_key or RIKAI2_AUTH_KEY
        self.webhook = webhook or WEBHOOK_URL

        # Settings
        self.advanced_explainability = False
        self.advanced_vision = False
        self.force_ocr = False
        self.verbose = True

    def add_file_to_payload(self, payload):
        """Adds the file to the payload for Rikai2.

        :param payload: The payload dictionary.

        :returns: The modified payload dictionary.

        """
        if not self.file:
            raise Exception("No file set")

        if self.file.startswith("http"):
            payload["inputURL"] = self.file
            return payload

        # Assume local file
        payload["base64"] = self._get_file_base64(self.file)
        return payload

    def build_payload(self):
        """Builds the payload for the Rikai2 API request.

        :returns: The payload dictionary.

        """
        webhook = self.webhook
        if self.return_file_name:
            webhook = f"{webhook}?filename={self.firebase_file_name}"

        payload = {
            "forceOCR": self.force_ocr,
            "outputUrl": webhook,
            "question": self.prompt,
            "settings": {
                "advanced_explainability": self.advanced_explainability,
                "advanced_vision": self.advanced_vision,
                "verbose": self.verbose,
            },
            "webhook": webhook,
        }
        payload = self.add_file_to_payload(payload)
        return payload


class Riky2(ModelAPI):
    """Class for interacting with the Riky2 API."""

    def __init__(
        self,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        auth_key: Optional[str] = None,
        webhook: Optional[str] = None,
    ):
        super().__init__()
        self.url = url or RIKY2_URL
        self.org_id = org_id or RIKY2_ORG_ID
        self.auth_key = auth_key or RIKY2_AUTH_KEY
        self.webhook = webhook or WEBHOOK_URL

    def add_file_to_payload(self, payload):
        """Adds the file to the payload for Riky2.

        :param payload: The payload dictionary.

        :returns: The modified payload dictionary.

        """
        if not self.file:
            raise Exception("No file set")

        if self.file.startswith("http"):
            payload["inputURL"] = self.file
            return payload

        # Assume local file
        payload["base64"] = self._get_file_base64(self.file)
        return payload

    def build_payload(self):
        """Builds the payload for the Riky2 API request.

        :returns: The payload dictionary.

        """
        webhook = self.webhook
        if self.return_file_name:
            webhook = f"{webhook}?filename={self.firebase_file_name}"

        payload = {
            "outputUrl": webhook,
            "question": self.prompt,
            "webhook": webhook,
        }

        payload = self.add_file_to_payload(payload)
        return payload


class RikaiExtract(ModelAPI):
    def __init__(
        self,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        auth_key: Optional[str] = None,
        webhook: Optional[str] = None,
    ):
        super().__init__()
        self.url = url or RIKAI2_EXTRACT_URL
        self.org_id = org_id or RIKAI2_EXTRACT_ORG_ID
        self.auth_key = auth_key or RIKAI2_EXTRACT_AUTH_KEY
        self.webhook = webhook or WEBHOOK_URL

        # Settings
        self.return_confidence = True

    def add_file_to_payload(self, payload):
        if not self.file:
            raise Exception("No file set")

        if self.file.startswith("http"):
            payload["inputURL"] = self.file
            return payload

        # Assume local file
        payload["base64"] = self._get_file_base64(self.file)
        return payload

    def build_payload(self):
        webhook = self.webhook
        if self.return_file_name:
            webhook = f"{webhook}?filename={self.firebase_file_name}"

        payload = {
            "outputUrl": webhook,
            "question": self.prompt,
            "settings": {"returnConfidence": self.return_confidence},
            "webhook": webhook,
        }
        payload = self.add_file_to_payload(payload)
        return payload


class Pii(ModelAPI):
    def __init__(
        self,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        auth_key: Optional[str] = None,
        webhook: Optional[str] = None,
    ):
        super().__init__()
        self.url = url or PII_URL
        self.org_id = org_id or PII_ORG_ID
        self.auth_key = auth_key or PII_AUTH_KEY
        self.webhook = webhook or WEBHOOK_URL

        self.is_async = False

    def add_file_to_payload(self, payload):
        if not self.file:
            raise Exception("No file set")

        if self.file.startswith("http"):
            payload["inputURL"] = self.file
            return payload

        # Assume local file
        payload["base64"] = self._get_file_base64(self.file)
        return payload

    def build_payload(self):
        payload = {}
        payload = self.add_file_to_payload(payload)
        return payload


class Forms(ModelAPI):
    def __init__(
        self,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        auth_key: Optional[str] = None,
        webhook: Optional[str] = None,
    ):
        super().__init__()
        self.url = url or FORMS_URL
        self.org_id = org_id or FORMS_ORG_ID
        self.auth_key = auth_key or FORMS_AUTH_KEY
        self.webhook = webhook or WEBHOOK_URL

        self.is_async = False

    def add_file_to_payload(self, payload):
        if not self.file:
            raise Exception("No file set")

        if self.file.startswith("http"):
            payload["inputURL"] = self.file
            return payload

        # Assume local file
        payload["base64"] = self._get_file_base64(self.file)
        return payload

    def build_payload(self):
        payload = {}
        payload = self.add_file_to_payload(payload)
        return payload
