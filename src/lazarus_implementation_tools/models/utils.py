from typing import Union

from lazarus_implementation_tools.models.apis import Rikai2, RikaiExtract, Riky2
from lazarus_implementation_tools.models.batching import Batcher


def query_rikai2(file_path: Union[str, list], prompt: str):
    """Queries the Rikai2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Rikai2 model API.

    """
    model_api = Rikai2()
    batch = Batcher(model_api, file_path, prompt)
    batch.run()


def query_riky2(file_path: Union[str, list], prompt: str):
    """Queries the Riky2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Riky2 model API.

    """
    model_api = Riky2()
    batch = Batcher(model_api, file_path, prompt)
    batch.run()


def query_rikai_extract(file_path: Union[str, list], prompt: str):
    """Queries the RikaiExtract model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the RikaiExtract model API.

    """
    model_api = RikaiExtract()
    batch = Batcher(model_api, file_path, prompt)
    batch.run()
