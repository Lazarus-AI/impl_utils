from typing import Optional, Union

from lazarus_implementation_tools.models.apis import Rikai2, RikaiExtract, Riky2
from lazarus_implementation_tools.models.batching import Batcher


def query_rikai2(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
):
    """Queries the Rikai2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Rikai2 model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.

    """
    model_api = Rikai2(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    batch = Batcher(model_api, file_path, prompt)
    batch.run()


def query_riky2(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
):
    """Queries the Riky2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Riky2 model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.

    """
    model_api = Riky2(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    batch = Batcher(model_api, file_path, prompt)
    batch.run()


def query_rikai_extract(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
):
    """Queries the RikaiExtract model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the RikaiExtract model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.

    """
    model_api = RikaiExtract(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    batch = Batcher(model_api, file_path, prompt)
    batch.run()
