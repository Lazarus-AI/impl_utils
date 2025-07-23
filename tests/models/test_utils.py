import os
from unittest import mock

from lazarus_implementation_tools.models.utils import (
    query_rikai2,
    query_rikai_extract,
    query_riky2,
)


class TestQueryRikai2:
    """We're just going to test config and basic set up. We don't want to reach out to the service

    These tests do all the batching and file prep. The only part it does not do is run
    and wait for the results.

    """

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_rikai2_defaults(self, mock_runner):
        results = query_rikai2(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
        )
        result = results.pop(0)
        assert result.url == os.environ["RIKAI2_URL"]
        assert result.org_id == os.environ["RIKAI2_ORG_ID"]
        assert result.auth_key == os.environ["RIKAI2_AUTH_KEY"]
        assert result.webhook == os.environ["WEBHOOK_URL"]
        assert result.return_file_name == "pdf_Rikai2"
        assert result.return_file_path == "file/path/to/pdf_Rikai2.json"
        assert result.advanced_explainability is False
        assert result.advanced_vision is False
        assert result.force_ocr is False
        assert result.verbose is True

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_rikai2_custom_values(self, mock_runner):
        url = "fake_url"
        org_id = "org_id"
        auth_key = "auth_key"
        webhook = "webhook"
        advanced_explainability = True
        advanced_vision = True
        force_ocr = True
        verbose = False

        results = query_rikai2(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
            url=url,
            org_id=org_id,
            auth_key=auth_key,
            webhook=webhook,
            advanced_explainability=advanced_explainability,
            advanced_vision=advanced_vision,
            force_ocr=force_ocr,
            verbose=verbose,
        )
        result = results.pop(0)
        assert result.url == url
        assert result.org_id == org_id
        assert result.auth_key == auth_key
        assert result.webhook == webhook
        assert result.return_file_name == "pdf_Rikai2"
        assert result.return_file_path == "file/path/to/pdf_Rikai2.json"
        assert result.advanced_explainability is advanced_explainability
        assert result.advanced_vision is advanced_vision
        assert result.force_ocr is force_ocr
        assert result.verbose is verbose


class TestQueryRiky2:
    """We're just going to test config and basic set up. We don't want to reach out to the service

    These tests do all the batching and file prep. The only part it does not do is run
    and wait for the results.

    """

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_riky2_defaults(self, mock_runner):
        results = query_riky2(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
        )
        result = results.pop(0)
        assert result.url == os.environ["RIKY2_URL"]
        assert result.org_id == os.environ["RIKY2_ORG_ID"]
        assert result.auth_key == os.environ["RIKY2_AUTH_KEY"]
        assert result.webhook == os.environ["WEBHOOK_URL"]
        assert result.return_file_name == "pdf_Riky2"
        assert result.return_file_path == "file/path/to/pdf_Riky2.json"

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_riky2_custom_values(self, mock_runner):
        url = "fake_url"
        org_id = "org_id"
        auth_key = "auth_key"
        webhook = "webhook"

        results = query_riky2(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
            url=url,
            org_id=org_id,
            auth_key=auth_key,
            webhook=webhook,
        )
        result = results.pop(0)
        assert result.url == url
        assert result.org_id == org_id
        assert result.auth_key == auth_key
        assert result.webhook == webhook
        assert result.return_file_name == "pdf_Riky2"
        assert result.return_file_path == "file/path/to/pdf_Riky2.json"


class TestQueryRikaiExtract:
    """We're just going to test config and basic set up. We don't want to reach out to the service

    These tests do all the batching and file prep. The only part it does not do is run
    and wait for the results.

    """

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_rikai_extract_defaults(self, mock_runner):
        results = query_rikai_extract(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt={},
        )
        result = results.pop(0)
        assert result.url == os.environ["RIKAI2_EXTRACT_URL"]
        assert result.org_id == os.environ["RIKAI2_EXTRACT_ORG_ID"]
        assert result.auth_key == os.environ["RIKAI2_EXTRACT_AUTH_KEY"]
        assert result.webhook == os.environ["WEBHOOK_URL"]
        assert result.return_file_name == "pdf_RikaiExtract"
        assert result.return_file_path == "file/path/to/pdf_RikaiExtract.json"
        assert result.return_confidence is True

    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_query_rikai_extract_custom_values(self, mock_runner):
        url = "fake_url"
        org_id = "org_id"
        auth_key = "auth_key"
        webhook = "webhook"
        return_confidence = False

        results = query_rikai_extract(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
            url=url,
            org_id=org_id,
            auth_key=auth_key,
            webhook=webhook,
            return_confidence=return_confidence,
        )
        result = results.pop(0)
        assert result.url == url
        assert result.org_id == org_id
        assert result.auth_key == auth_key
        assert result.webhook == webhook
        assert result.return_file_name == "pdf_RikaiExtract"
        assert result.return_file_path == "file/path/to/pdf_RikaiExtract.json"
        assert result.return_confidence is return_confidence
