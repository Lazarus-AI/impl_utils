import pandas as pd

from file_system.utils import (
    get_all_files_with_ext,
    get_filename,
    is_dir,
    load_json_from_file,
)
from general.utils import get_data_from_json_map


class CSVBuilder:
    """A class for building a CSV file from JSON data."""

    def __init__(self):
        """Initializes a new instance of the CSVBuilder class."""
        self.files = []
        self.columns = []
        self.data = []

    def add_column(self, name, json_data_map):
        """Adds a column to the CSV file with the specified name and JSON data map.

        :param name: (str) The name of the column.
        :param json_data_map: (str) The JSON data map to use for extracting data.

        """
        self.columns.append((name, json_data_map))

    def add_file(self, file_path):
        """Adds a file or directory of files to the list of files to process.

        :param file_path: (str) The file or directory path to add.

        """
        if is_dir(file_path):
            file_paths = get_all_files_with_ext(file_path, "json")
            self.files.extend(file_paths)
        else:
            self.files.append(file_path)

    def build_data(self):
        """Builds the data for the CSV file by extracting data from the specified files.

        :returns: (list) A list of dictionaries representing the rows of the CSV file.

        """
        self.data = []
        for file in self.files:
            row = {"File": get_filename(file)}
            json_data = load_json_from_file(file)
            for column in self.columns:
                row[column[0]] = get_data_from_json_map(json_data, column[1])
            self.data.append(row)
        return self.data

    def save_to_csv(self, file_path):
        """Saves the built data to a CSV file.

        :param file_path: (str) The path to save the CSV file.

        """
        results = sorted(self.data, key=lambda item: item["File"])
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)

    def export(self, file_path):
        """Exports the CSV file to the specified file path.

        :param file_path: (str) The path to save the CSV file.

        """
        self.build_data()
        self.save_to_csv(file_path)
