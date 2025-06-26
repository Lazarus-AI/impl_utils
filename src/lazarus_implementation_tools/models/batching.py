import json
import logging
import threading
import time
from http import HTTPStatus
from math import floor
from shutil import move
from typing import List, Optional, Union

from lazarus_implementation_tools.config import (
    BATCH_TIMEOUT,
    FIREBASE_WEBHOOK_OUTPUT_FOLDER,
)
from lazarus_implementation_tools.file_system.utils import (
    get_all_files,
    get_folder,
    is_dir,
    tidy_json_file,
)
from lazarus_implementation_tools.general.core import log_timing
from lazarus_implementation_tools.models.apis import ModelAPI
from lazarus_implementation_tools.sync.firebase.utils import (
    delete,
    download,
    file_exists,
)

logger = logging.getLogger(__name__)


class Batcher:
    """A class for batching files and processing them using a specified model API."""

    def __init__(
        self,
        model_api: ModelAPI,
        file_path: Union[list, str],
        prompt: Optional[str] = None,
    ):
        """Initializes the Batcher with a model API and one or more file paths.

        :param model_api: The model API to use for processing.
        :param file_path: The path to a single file or a list of file paths.
        :param prompt: An optional prompt to pass to the model API.

        """
        self.model_api = model_api
        self.file_path = file_path
        self.prompt = prompt
        self.responses = []  # type: ignore

    def get_files(self):
        """Retrieves the list of files to process.

        :returns: A list of file paths.

        """
        if isinstance(self.file_path, list):
            files = self.file_path
        elif is_dir(self.file_path):
            files = get_all_files(self.file_path)
        else:
            files = [self.file_path]
        return files

    def run(self) -> List[ModelAPI]:
        """Runs the batching process by processing each file in a separate thread."""
        files = self.get_files()
        threads = []
        clients = []
        for file in files:
            client = self.model_api
            client.set_file(file)
            client.prompt = self.prompt
            if client.is_async:
                runner = RunAndWait(client)  # type: Runner
            else:
                runner = RunSync(client)  # type: ignore[no-redef]
            clients.append(client)
            thread = threading.Thread(target=runner.run)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        for client in clients:
            self.responses.append(client.response)

        return clients


class Runner:
    """Interface for runners"""

    def run(self):
        raise NotImplementedError


class RunAndWait(Runner):
    """A class for running a model API request and waiting for the async response.

    This is currently highly opinionated towards firebase storage. TODO: Extend this
    object to use other storage systems.

    """

    def __init__(self, model_api: ModelAPI):
        """Initializes the RunAndWait with a model API.

        :param model_api: The model API to use for the request.

        """
        self.model_api = model_api
        self.data_path = f"{FIREBASE_WEBHOOK_OUTPUT_FOLDER}{self.model_api.firebase_file_name}.json"

    def send(self):
        """Sends the model API request."""
        logging.info(f"Processing: {self.model_api.file}")
        return self.model_api.run()

    @log_timing
    def wait(self) -> bool:
        """Waits for the response file to appear in Firebase.

        :returns: True if the file was successfully downloaded, False otherwise.

        """
        check_period = 5
        iterations = floor(BATCH_TIMEOUT / check_period)
        is_successful = False
        logging.info(f"Waiting to download: {self.data_path}")
        for i in range(iterations):
            if file_exists(self.data_path):
                is_successful = True
                break
            time.sleep(check_period)
        return is_successful

    def save_file(self):
        """Saves the downloaded response file to the local filesystem."""
        download_folder = get_folder(self.model_api.file)
        download(download_folder, self.data_path)
        delete(self.data_path)
        raw_file_name = f"{download_folder}/{self.model_api.firebase_file_name}.json"
        self.model_api.return_file_path = (
            f"{download_folder}/{self.model_api.return_file_name}.json"
        )
        move(raw_file_name, self.model_api.return_file_path)
        tidy_json_file(self.model_api.return_file_path)
        logging.info(f"Saved response to: {self.model_api.return_file_path}")

    def run(self):
        """Runs the send, wait, and save_file methods in sequence."""
        response = self.send()
        if response.status_code != HTTPStatus.OK:
            # Don't wait for the file if the API call failed.
            return
        is_successful = self.wait()
        if is_successful:
            self.save_file()
        else:
            logger.error("Request timed out")


class RunSync(Runner):
    """A class for running a model API request and waiting for the response.

    This is currently highly opinionated towards firebase storage. TODO: Extend this
    object to use other storage systems.

    """

    def __init__(self, model_api: ModelAPI):
        """Initializes the RunAndWait with a model API.

        :param model_api: The model API to use for the request.

        """
        self.model_api = model_api

    def send(self):
        """Sends the model API request."""
        logging.info(f"Processing: {self.model_api.file}")
        return self.model_api.run()

    def save_file(self):
        """Saves the downloaded response file to the local filesystem."""
        download_folder = get_folder(self.model_api.file)
        self.model_api.return_file_path = (
            f"{download_folder}/{self.model_api.return_file_name}.json"
        )
        with open(self.model_api.return_file_path, "w") as file:
            file.write(json.dumps(self.model_api.response.json()))
        tidy_json_file(self.model_api.return_file_path)
        logging.info(f"Saved response to: {self.model_api.return_file_path}")

    def run(self):
        """Runs the send, wait, and save_file methods in sequence."""
        response = self.send()
        if response.status_code != HTTPStatus.OK:
            # Don't wait for the file if the API call failed.
            return
        self.save_file()
