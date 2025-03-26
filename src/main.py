from config import WORKING_FOLDER
from transformations.pdf.utils import convert_to_pdf

if __name__ == "__main__":
    folder = WORKING_FOLDER

    results = convert_to_pdf(folder, recursive=True)
    for result in results:
        print(f"Converted: {result[0]} to {result[1]}")
