from transformations.csv.builder import CSVBuilder
import pandas as pd
import os

def build_csv_from_json_files(file_path, columns, destination_path=None):
    if not destination_path:
        destination_path = f"{file_path}.csv"

    builder = CSVBuilder()
    builder.add_file(file_path)
    for column in columns:
        builder.add_column(column[0], column[1])
    builder.export(destination_path)
    return destination_path

def xls_to_csvs_and_concat(input_path, output_path):
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

    return output_path
