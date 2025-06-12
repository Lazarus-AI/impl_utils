from lazarus_implementation_tools.transformations.csv.builder import (
    CSVBuilder,
    xls_to_csvs_and_concat,
)


def build_csv_from_json_files(file_path, columns, destination_path=None):
    """Builds a CSV file from JSON files.

    :param file_path: (str) The path to the JSON file.
    :param columns: (list) A list of tuples containing column names and JSON data maps.
    :param destination_path: (str) The path to save the CSV file. If None, the CSV file
        will be saved with the same name as the JSON file but with a .csv extension.

    :returns: (str) The path to the saved CSV file.

    """
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
    """Convert an Excel file to CSV files and optionally concatenate them.

    :param input_path: Path to excel file
    :param output_dir: path to the folder we want to put the results
    :param output_as_one_file: (bool) If true concatenate all the sheets into one file.

    :returns list[str]: A list of paths to the saved CSV files.

    :raises Exception: If output_as_one_file = True and there are no common columns
        across the sheets

    """
    return xls_to_csvs_and_concat(input_path, output_dir, output_as_one_file)  # type: ignore
