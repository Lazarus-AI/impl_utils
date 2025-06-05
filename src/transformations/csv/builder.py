import os

import pandas as pd

from file_system.utils import (
    get_all_files_with_ext,
    get_filename,
    get_folder,
    is_dir,
    load_json_from_file,
    mkdir,
)
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


def xls_to_csvs_and_concat(
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

    # Load excel
    xls = pd.ExcelFile(input_path)
    file_name = get_filename(input_path)
    if not output_dir:
        output_dir = get_folder(input_path)

    # Read all sheets into DataFrames
    dataframes = {
        sheet_name: pd.read_excel(xls, sheet_name=sheet_name, engine="openpyxl")
        for sheet_name in xls.sheet_names
    }

    # Concatenates files if bool is True, else just transforms each individual spreadsheet into a csv
    if not output_as_one_file:
        mkdir(output_dir)
        final_spreadsheet_list: list[str] = []
        for sheet_name, df in dataframes.items():
            output_path = os.path.join(output_dir, f"{file_name}_{sheet_name}.csv")
            df.to_csv(output_path, index=False)
            final_spreadsheet_list.append(output_path)
        return final_spreadsheet_list
    else:
        # Find shared columns across all sheets
        common_columns_set = set.intersection(*(set(df.columns) for df in dataframes.values()))
        if not common_columns_set:
            raise ValueError("No common columns across sheets")
        common_columns = list(common_columns_set)  # preserve order
        # Subset and concatenate rows by shared columns
        subset_dfs = [df[common_columns] for df in dataframes.values()]
        combined_df = pd.concat(subset_dfs, ignore_index=True)

        mkdir(output_dir)
        combined_df.to_csv(os.path.join(output_dir, f"{file_name}_combined.csv"), index=False)
        return [os.path.join(output_dir, f"{file_name}_combined.csv")]
