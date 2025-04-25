import os
import sys
import threading
from argparse import ArgumentParser, Namespace
from enum import StrEnum, auto

import boto3
from boto3.s3.transfer import TransferConfig
from pydantic import BaseModel # automatically validates and serializes the data 

ENV = os.environ

S3_CLIENT = boto3.client("s3")

S3_TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=1024 * 25,
    max_concurrency=12,
    multipart_chunksize=1024 * 25,
    use_threads=True,
)


class ProgressPercentage(object):
    """
    A callback function that prints the progress of the file transfer.
    """
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)"
                % (self._filename, self._seen_so_far, self._size, percentage)
            )
            sys.stdout.flush()


class S3Transfer(BaseModel):
    # Pydantic requires initialization of all fields here rather than in the __init__ method
    bucket_id: str
    s3_path: str
    local_path: str
    
    def upload(self):
        S3_CLIENT.upload_file(
            self.local_path,
            self.bucket_id,
            self.s3_path,
            Config=S3_TRANSFER_CONFIG,
            Callback=ProgressPercentage(self.local_path),
        )

    def download(self):
        S3_CLIENT.download_file(
            self.bucket_id,
            self.s3_path,
            self.local_path,
            Config=S3_TRANSFER_CONFIG,
        )
