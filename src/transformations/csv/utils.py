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


def concatenate_excel_to_csvs(
    file_name: str,
    input_dir: str = None,
    output_dir: str = None,
    store_intermediate_files: bool = True,
):
    """
    Converts an Excel file to a CSV file, concatenating data from all sheets.

    :param file_name: The name of the Excel file to convert.
    :param input_dir: The directory containing the input Excel file. If None, uses the value from the environment variable "WORKING_FOLDER".
    :param output_dir: The directory where the output CSV file will be saved. If None, uses the value from the environment variable "DOWNLOAD_FOLDER".
    :param store_intermediate_files: If True, stores intermediate CSV files for each sheet in the output directory.
    :raises Exception: If there are no common columns across sheets.
    """
    xls_to_csvs_and_concat(file_name, input_dir, output_dir, store_intermediate_files)
