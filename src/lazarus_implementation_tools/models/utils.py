from typing import List, Optional, Union

from lazarus_implementation_tools.models.apis import (
    Forms,
    ModelAPI,
    Pii,
    Rikai2,
    RikaiExtract,
    Riky2,
)
from lazarus_implementation_tools.models.batching import Batcher


def query_rikai2(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
    return_file_name: Optional[str] = None,
    advanced_explainability: Optional[bool] = False,
    advanced_vision: Optional[bool] = False,
    force_ocr: Optional[bool] = False,
    verbose: Optional[bool] = True,
) -> List[ModelAPI]:
    """Queries the Rikai2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Rikai2 model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.
    :param return_file_name: The name you want to give the return file (No Extension),
        Optional defaults to FILENAME_MODEL
    :param advanced_explainability: Whether to user advanced_explainability, Optional
        defaults to False
    :param advanced_vision: Whether to user advanced_vision, Optional defaults to False
    :param force_ocr: Whether to force ocr, Optional defaults to False
    :param verbose: Whether to return verbose output, Optional defaults to True

    """
    model_api = Rikai2(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    if return_file_name:
        model_api.return_file_name = return_file_name
    model_api.advanced_explainability = advanced_explainability
    model_api.advanced_vision = advanced_vision
    model_api.force_ocr = force_ocr
    model_api.verbose = verbose
    batch = Batcher(model_api, file_path, prompt)
    return batch.run()


def query_riky2(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
    return_file_name: Optional[str] = None,
) -> List[ModelAPI]:
    """Queries the Riky2 model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the Riky2 model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.
    :param return_file_name: The name you want to give the return file (No Extension),
        Optional defaults to FILENAME_MODEL

    """
    model_api = Riky2(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    if return_file_name:
        model_api.return_file_name = return_file_name
    batch = Batcher(model_api, file_path, prompt)
    return batch.run()


def query_rikai_extract(
    file_path: Union[str, list],
    prompt: str,
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    webhook: Optional[str] = None,
    return_file_name: Optional[str] = None,
    return_confidence: Optional[bool] = True,
) -> List[ModelAPI]:
    """Queries the RikaiExtract model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the RikaiExtract model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.
    :param return_file_name: The name you want to give the return file (No Extension),
        Optional defaults to FILENAME_MODEL
    :param return_confidence: Whether to return confidence scores, Optional defaults to
        True

    """
    model_api = RikaiExtract(url=url, org_id=org_id, auth_key=auth_key, webhook=webhook)
    if return_file_name:
        model_api.return_file_name = return_file_name
    model_api.return_confidence = return_confidence
    batch = Batcher(model_api, file_path, prompt)
    return batch.run()


def query_pii(
    file_path: Union[str, list],
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    return_file_name: Optional[str] = None,
) -> List[ModelAPI]:
    """Queries the PII model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the RikaiExtract model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.
    :param return_file_name: The name you want to give the return file (No Extension),
        Optional defaults to FILENAME_MODEL

    """
    model_api = Pii(url=url, org_id=org_id, auth_key=auth_key)
    if return_file_name:
        model_api.return_file_name = return_file_name
    batch = Batcher(model_api, file_path)
    return batch.run()


def query_forms(
    file_path: Union[str, list],
    url: Optional[str] = None,
    org_id: Optional[str] = None,
    auth_key: Optional[str] = None,
    return_file_name: Optional[str] = None,
) -> List[ModelAPI]:
    """Queries the PII model API for the given file path(s) and prompt.

    :param file_path: The path to a single file or a list of file paths.
    :param prompt: The prompt to pass to the RikaiExtract model API.
    :param url: Model url, Optional defaults to environment file.
    :param org_id: Org ID for request, Optional defaults to environment file.
    :param auth_key: Auth Key for request, Optional defaults to environment file.
    :param webhook: Webhook url for request, Optional defaults to environment file.
    :param return_file_name: The name you want to give the return file (No Extension),
        Optional defaults to FILENAME_MODEL

    """
    model_api = Forms(url=url, org_id=org_id, auth_key=auth_key)
    if return_file_name:
        model_api.return_file_name = return_file_name
    batch = Batcher(model_api, file_path)
    return batch.run()
