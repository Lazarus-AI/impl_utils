from unittest import mock

from lazarus_implementation_tools.prompting.synchronous import infer_rikai2


class TestSynchronous:
    @mock.patch("builtins.open", mock.mock_open(read_data='{"data": [{"answer": "test answer"}]}'))
    @mock.patch("lazarus_implementation_tools.models.batching.RunAndWait")
    def test_infer_rikai2(self, mock_runner):
        result = infer_rikai2(
            file_path_or_url="file/path/to/pdf.pdf",
            prompt="Query me this:",
        )
        assert result == "test answer"