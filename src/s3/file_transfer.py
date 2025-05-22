import os
import sys
import threading
from argparse import ArgumentParser, Namespace
from enum import StrEnum, auto

import boto3
from boto3.s3.transfer import TransferConfig

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


class S3Transfer:
    
    @staticmethod
    def upload(local_path: str, bucket_id: str, s3_path: str):
        S3_CLIENT.upload_file(
            local_path,
            bucket_id,
            s3_path,
            Config=S3_TRANSFER_CONFIG,
            Callback=ProgressPercentage(local_path),
        )

    @staticmethod
    def download(bucket_id: str, s3_path: str, local_path: str):
        S3_CLIENT.download_file(
            bucket_id,
            s3_path,
            local_path,
            Config=S3_TRANSFER_CONFIG,
        )
