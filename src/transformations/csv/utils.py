from typing import cast

from transformations.csv.builder import CSVBuilder, xls_to_csvs_and_concat


def build_csv_from_json_files(file_path, columns, destination_path=None):
    if not destination_path:
        destination_path = f"{file_path}.csv"

    builder = CSVBuilder()
    builder.add_file(file_path)
    for column in columns:
        builder.add_column(column[0], column[1])
    builder.export(destination_path)
    return destination_path


def excel_to_csv(
    input_path: str,
    output_dir: str = None,
    output_as_one_file: bool = False,
) -> list[str]:
    """
    Convert an Excel file to CSV files and optionally concatenate them.

    :param input_path (str): The path to the input Excel file.
    :param output_dir (str, optional): The directory to save the CSV files. If not provided, the directory of the input file will be used.
    :param output_as_one_file (bool, optional): If True, all CSVs will be concatenated into a single CSV file. Default is False.
    :return list[str]: A list of paths to the saved CSV files.
    :raises Exception: If output_as_one_file = True and there are no common columns across the sheets
    """
    return cast(list[str], xls_to_csvs_and_concat(input_path, output_dir, output_as_one_file))
