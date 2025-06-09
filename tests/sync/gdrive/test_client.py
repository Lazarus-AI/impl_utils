import pytest

from sync.gdrive.client import get_info_from_google_url

STATIC_UUID = "42580b66-66f8-4d23-9382-df7cd0ca8161"


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (
            f"https://docs.google.com/presentation/d/{STATIC_UUID}/edit?slide=id.g35fb13fc036_0_0#slide=id.g35fb13fc036_0_0",
            {
                "type": "file",
                "sub_type": "presentation",
                "file_id": STATIC_UUID,
            },
        ),
        (
            f"https://docs.google.com/document/d/{STATIC_UUID}/edit?tab=t.0",
            {
                "type": "file",
                "sub_type": "document",
                "file_id": STATIC_UUID,
            },
        ),
        (
            f"https://docs.google.com/spreadsheets/d/{STATIC_UUID}/edit?gid=1657135752#gid=1657135752",
            {
                "type": "file",
                "sub_type": "spreadsheets",
                "file_id": STATIC_UUID,
            },
        ),
        (
            f"https://drive.google.com/drive/folders/{STATIC_UUID}",
            {
                "type": "folder",
                "sub_type": "folder",
                "file_id": STATIC_UUID,
            },
        ),
        (
            f"https://drive.google.com/file/d/{STATIC_UUID}/view",
            {
                "type": "file",
                "sub_type": "unknown",
                "file_id": STATIC_UUID,
            },
        ),
    ],
)
def test_get_info_from_google_url(given, expected):
    result = get_info_from_google_url(given)
    assert result == expected
