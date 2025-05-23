import logging
import threading
import time
from math import floor
from typing import Optional, Union

from config import BATCH_TIMEOUT, FIREBASE_WEBHOOK_OUTPUT_FOLDER
from file_system.utils import get_all_files, get_folder, is_dir, tidy_json_file
from general.core import log_timing
from models.apis import ModelAPI
from sync.firebase.utils import delete, download, file_exists

logger = logging.getLogger(__name__)


class Batcher:
    def __init__(
        self,
        model_api: ModelAPI,
        file_path: Union[list, str],
        prompt: Optional[str] = None,
    ):
        self.model_api = model_api
        self.file_path = file_path
        self.prompt = prompt

    def get_files(self):
        if isinstance(self.file_path, list):
            files = self.file_path
        elif is_dir(self.file_path):
            files = get_all_files(self.file_path)
        else:
            files = [self.file_path]
        return files

    def run(self):
        files = self.get_files()
        threads = []
        for file in files:
            client = self.model_api
            client.set_file(file)
            client.prompt = self.prompt
            runner = RunAndWait(client)
            thread = threading.Thread(target=runner.run)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


class RunAndWait:
    def __init__(self, model_api: ModelAPI):
        self.model_api = model_api
        self.data_path = f"{FIREBASE_WEBHOOK_OUTPUT_FOLDER}{self.model_api.return_file_name}.json"

    def send(self):
        logging.info(f"Processing: {self.model_api.file}")
        self.model_api.run()

    @log_timing
    def wait(self) -> bool:
        # Wait until the file shows up in firebase
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
        download_folder = get_folder(self.model_api.file)
        download(download_folder, self.data_path)
        delete(self.data_path)
        file_name = f"{download_folder}/{self.model_api.return_file_name}.json"
        tidy_json_file(file_name)
        logging.info(f"Saved response to: {file_name}")

    def run(self):
        self.send()
        self.wait()
        self.save_file()
