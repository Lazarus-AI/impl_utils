import os

import pandas as pd

from file_system.utils import (
    get_all_files_with_ext,
    get_filename,
    is_dir,
    load_json_from_file,
)
from general.core import jupyter_src_path_fix
from general.utils import get_data_from_json_map


class CSVBuilder:
    def __init__(self):
        self.files = []
        self.columns = []
        self.data = []

    def add_column(self, name, json_data_map):
        self.columns.append((name, json_data_map))

    def add_file(self, file_path):
        if is_dir(file_path):
            file_paths = get_all_files_with_ext(file_path, "json")
            self.files.extend(file_paths)
        else:
            self.files.append(file_path)

    def build_data(self):
        self.data = []
        for file in self.files:
            row = {"File": get_filename(file)}
            json_data = load_json_from_file(file)
            for column in self.columns:
                row[column[0]] = get_data_from_json_map(json_data, column[1])
            self.data.append(row)
        return self.data

    def save_to_csv(self, file_path):
        results = sorted(self.data, key=lambda item: item["File"])
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)

    def export(self, file_path):
        self.build_data()
        self.save_to_csv(file_path)


@jupyter_src_path_fix
def xls_to_csvs_and_concat(
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
    os.makedirs(output_dir, exist_ok=True)

    # Load excel
    xls = pd.ExcelFile(os.path.join(input_dir, file_name))

    # Read all sheets into DataFrames
    dataframes = {
        sheet_name: pd.read_excel(xls, sheet_name=sheet_name, engine="openpyxl")
        for sheet_name in xls.sheet_names
    }

    # Stores intermediate files if bool is set to True
    if store_intermediate_files:
        for sheet_name, df in dataframes.items():
            output_path = os.path.join(output_dir, f"{file_name}_{sheet_name}.csv")
            df.to_csv(output_path, index=False)

    # Find shared columns across all sheets
    common_columns_set = set.intersection(*(set(df.columns) for df in dataframes.values()))
    if not common_columns_set:
        raise ValueError("No common columns across sheets!")

    common_columns = list(common_columns_set)  # preserve order

    # Subset and concatenate rows by shared columns
    subset_dfs = [df[common_columns] for df in dataframes.values()]
    combined_df = pd.concat(subset_dfs, ignore_index=True)

    # Write final output
    combined_df.to_csv(os.path.join(output_dir, f"{file_name}_combined.csv"), index=False)

    return
