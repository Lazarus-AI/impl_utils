from file_system.utils import append_to_filename, in_working
from transformations.pdf.utils import tidy_pdf

if __name__ == "__main__":
    file = in_working("lazarus/employee_handbook.pdf")
    result = tidy_pdf(file, append_to_filename(file, "_deskewed_and_cropped"))
    print(f"{file} tidied to: {result}")
