import pytest

from lazarus_implementation_tools.file_system.utils import get_filename_from_url, is_url

url_cases = [
    ("bar", False),
    ("http://lazarus.ai", True),
    ("https://lazarus.ai", True),
    ("lazarus.ai", False),
]


@pytest.mark.parametrize("possible_url,expected", url_cases)
def test_is_url(possible_url, expected):
    assert is_url(possible_url) == expected


url_filename_cases = [
    ("bar", "bar"),
    ("http://lazarus.ai", ""),
    ("https://lazarus.ai/file.pdf", "file.pdf"),
    ("https://lazarus.ai/file.pdf?var=foo&var2=bar", "file.pdf"),
    ("http://lazarus.ai/file.pdf?var=foo&var2=bar", "file.pdf"),
]


@pytest.mark.parametrize("possible_url,expected", url_filename_cases)
def test_get_filename_from_url(possible_url, expected):
    if expected == "":
        assert get_filename_from_url(possible_url).startswith("file_url_")
    else:
        assert get_filename_from_url(possible_url) == expected
