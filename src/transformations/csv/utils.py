from transformations.csv.builder import CSVBuilder


def build_csv_from_json_files(file_path, columns, destination_path=None):
    if not destination_path:
        destination_path = f"{file_path}.csv"

    builder = CSVBuilder()
    builder.add_file(file_path)
    for column in columns:
        builder.add_column(column[0], column[1])
    builder.export(destination_path)
    return destination_path
