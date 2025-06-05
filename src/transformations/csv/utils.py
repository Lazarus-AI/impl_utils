import os
from transformations.csv.builder import CSVBuilder, xls_to_csvs_and_concat

import pandas as pd

from transformations.csv.builder import CSVBuilder


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


def xls_to_csvs_and_concat(input_path, output_path):
    """Converts an Excel file to CSV files and concatenates them.

    :param input_path: (str) The path to the input Excel file.
    :param output_path: (str) The path to save the concatenated CSV file.

    :returns: (str) The path to the saved concatenated CSV file.

    """
    # Load Excel file
    xls = pd.ExcelFile(input_path)

    # Read all sheets into DataFrames
    dataframes = {
        sheet_name: pd.read_excel(xls, sheet_name=sheet_name, engine="openpyxl")
        for sheet_name in xls.sheet_names
    }

    # Find shared columns across all sheets
    common_columns = set.intersection(*(set(df.columns) for df in dataframes.values()))
    if not common_columns:
        raise ValueError("No common columns across sheets!")

    common_columns = list(common_columns)  # preserve order

    # Subset and concatenate rows by shared columns
    subset_dfs = [df[common_columns] for df in dataframes.values()]
    combined_df = pd.concat(subset_dfs, ignore_index=True)

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write final output
    combined_df.to_csv(output_path, index=False)

    
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
    return xls_to_csvs_and_concat(input_path, output_dir, output_as_one_file)  # type: ignore
