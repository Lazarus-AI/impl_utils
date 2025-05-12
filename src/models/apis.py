import base64
import json
from http import HTTPStatus

import requests

from config import (
    RIKAI2_AUTH_KEY,
    RIKAI2_ORG_ID,
    RIKAI2_URL,
    RIKY2_AUTH_KEY,
    RIKY2_ORG_ID,
    RIKY2_URL,
    RIKY_EXTRACT_AUTH_KEY,
    RIKY_EXTRACT_ORG_ID,
    RIKY_EXTRACT_URL,
    WEBHOOK_URL,
)
from file_system.utils import get_filename
from models.constants import POST


class ModelAPI:
    def __init__(self):
        self.method = POST
        self.url = ""
        self.org_id = ""
        self.auth_key = ""
        self.webhook = WEBHOOK_URL

        self.file = None
        self.return_file_name = None
        self.prompt = ''

    @property
    def name(self):
        return self.__class__.__name__

    def get_headers(self):
        return {"orgId": self.org_id, "authKey": self.auth_key, "Content-Type": "application/json"}

    def _get_file_base64(self, path):
        with open(self.file, "rb") as file:
            encoded_string = base64.b64encode(file.read())
            return encoded_string.decode("utf-8")

    def add_file_to_payload(self, payload):
        raise NotImplementedError

    def build_payload(self):
        raise NotImplementedError

    def set_file(self, file):
        self.file = file
        self.return_file_name = f"{get_filename(file)}_{self.name}"

    def set_return_file_name(self, file_name):
        self.return_file_name = file_name

    def run(self, file=None, prompt=None):
        if file:
            self.set_file(file)

        if prompt:
            self.prompt = prompt

        payload = self.build_payload()
        response = requests.request(
            self.method, self.url, headers=self.get_headers(), data=json.dumps(payload)
        )
        if response.status_code != HTTPStatus.OK:
            print(response.status_code, response.json())

        return response.json()


class Rikai2(ModelAPI):
    def __init__(self):
        super().__init__()
        self.url = RIKAI2_URL
        self.org_id = RIKAI2_ORG_ID
        self.auth_key = RIKAI2_AUTH_KEY
        self.webhook = WEBHOOK_URL

        # Settings
        self.advanced_explainability = False
        self.advanced_vision = False
        self.force_ocr = False
        self.verbose = True

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
            webhook = f"{webhook}?filename={self.return_file_name}"

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
    def __init__(self):
        super().__init__()
        self.url = RIKY2_URL
        self.org_id = RIKY2_ORG_ID
        self.auth_key = RIKY2_AUTH_KEY
        self.webhook = WEBHOOK_URL

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
            webhook = f"{webhook}?filename={self.return_file_name}"

        payload = {
            "outputUrl": webhook,
            "question": self.prompt,
            "webhook": webhook,
        }

        payload = self.add_file_to_payload(payload)
        return payload


class RikaiExtract(ModelAPI):
    def __init__(self):
        super().__init__()
        self.url = RIKY_EXTRACT_URL
        self.org_id = RIKY_EXTRACT_ORG_ID
        self.auth_key = RIKY_EXTRACT_AUTH_KEY
        self.webhook = WEBHOOK_URL

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
            webhook = f"{webhook}?filename={self.return_file_name}"

        payload = {
            "outputUrl": webhook,
            "question": self.prompt,
            "settings": {"returnConfidence": self.return_confidence},
            "webhook": webhook,
        }
        payload = self.add_file_to_payload(payload)
        return payload
