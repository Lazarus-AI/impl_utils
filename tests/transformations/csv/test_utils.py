import tempfile

from lazarus_implementation_tools.file_system.utils import in_working
from lazarus_implementation_tools.transformations.csv.utils import excel_to_csv


def test_excel_to_csv():
    xls_path = in_working("spreadsheets/sherlock_holmes_fan_club.xlsx")

    with tempfile.TemporaryDirectory() as tmp_path:
        csv_paths = excel_to_csv(xls_path, output_dir=tmp_path)

        # There are two sheets and thus two outputs
        assert len(csv_paths) == 2
        with open(csv_paths[0]) as file1:
            contents = file1.read()
            assert "Holly,Skunes" in contents

        with open(csv_paths[1]) as file2:
            contents = file2.read()
            assert "Jim Morrison" in contents


def test_excel_to_csv_one_file():
    xls_path = in_working("spreadsheets/sherlock_holmes_fan_club.xlsx")

    with tempfile.TemporaryDirectory() as tmp_path:
        csv_paths = excel_to_csv(xls_path, output_dir=tmp_path, output_as_one_file=True)

        # There are two sheets and thus two outputs
        assert len(csv_paths) == 1
        with open(csv_paths[0]) as file:
            contents = file.read()
            assert "Holly,Skunes" in contents
            assert "Jim Morrison" in contents
