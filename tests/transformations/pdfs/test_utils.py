import tempfile

import pytest

from lazarus_implementation_tools.file_system.utils import in_working
from lazarus_implementation_tools.transformations.pdf.utils import (
    convert_to_pdf,
    get_number_of_pages,
)

test_files = [
    ("word_processing/Sherlock_Holmes_Fan_Club_Newsletter.docx", 2),
    ("powerpoint/Sherlock_Holmes_Fan_Club_Newsletter.pptx", 3),
    ("spreadsheets/sherlock_holmes_fan_club.xlsx", 1),
    ("message/Sherlock_Holmes_Fan_Club.msg", 7),
    ("images/Sherlock_Holmes_Fan_Club_Flyer.png", 1),
]


@pytest.mark.parametrize("file_path,page_count", test_files)
def test_convert_to_pdf(file_path, page_count):
    doc_path = in_working(file_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        converted_files = convert_to_pdf(doc_path, tmp_dir)
        actual_file = converted_files.pop(0)
        # Get page count confirms it opens as a pdf
        # and gets a sense if all the pages are there.
        assert get_number_of_pages(actual_file) == page_count
