from file_system.utils import in_working
from transformations.pdf.utils import get_number_of_pages, merge_pdfs, trim_pdf

if __name__ == "__main__":
    file = in_working("lazarus/employee_handbook.pdf")
    page_count = get_number_of_pages(file)

    _, alpha = trim_pdf(file, 1, 1)
    _, omega = trim_pdf(file, page_count, page_count)
    print(alpha, omega)
    result = merge_pdfs([alpha, omega])
    print(f"Merged pdf: {result}")
