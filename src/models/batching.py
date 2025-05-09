import threading
import time
from math import floor

from config import BATCH_TIMEOUT, FIREBASE_WEBHOOK_OUTPUT_FOLDER
from file_system.utils import get_all_files, get_folder, is_dir
from sync.firebase.utils import delete, download, file_exists


class Batcher:
    def __init__(self, model_api, file_path=None, prompts=None):
        self.model_api = model_api
        self.file_path = file_path
        self.prompts = prompts

    def get_files(self):
        if is_dir(self.file_path):
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
            client.prompts = self.prompts
            runner = RunAndWait(client)
            thread = threading.Thread(target=runner.run)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


class RunAndWait:
    def __init__(self, model_api):
        self.model_api = model_api
        self.data_path = f"{FIREBASE_WEBHOOK_OUTPUT_FOLDER}{self.model_api.return_file_name}.json"

    def send(self):
        print(f"Processing: {self.model_api.file}")
        self.model_api.run()

    def wait(self):
        # Wait until the file shows up in firebase
        check_period = 5
        iterations = floor(BATCH_TIMEOUT / check_period)
        is_successful = False
        print(f"Looking for: {self.data_path}")
        print("Waiting", end="")
        elapsed = 0
        for i in range(iterations):
            if file_exists(self.data_path):
                is_successful = True
                break
            time.sleep(check_period)
            print(".", end="")
            elapsed = i * check_period
        print(f"{elapsed}s")
        return is_successful

    def save_file(self):
        download_folder = get_folder(self.model_api.file)
        download(download_folder, self.data_path)
        delete(self.data_path)
        print(f"Saved file to: {download_folder}/{self.model_api.return_file_name}.json")

    def run(self):
        self.send()
        self.wait()
        self.save_file()
