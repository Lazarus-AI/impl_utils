import pandas as pd

from file_system.utils import (
    get_all_files_with_ext,
    get_filename,
    is_dir,
    load_json_from_file,
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
