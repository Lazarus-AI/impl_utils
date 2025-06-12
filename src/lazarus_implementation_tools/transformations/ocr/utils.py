from lazarus_implementation_tools.transformations.ocr.easyocr import read_pdf


def ocr_pdf(file_path, start_page=None, end_page=None):
    """Reads a PDF file and extracts OCR results for each page.

    :param file_path: (str) The path to the PDF file.
    :param start_page: (int) The starting page number to read. If None, reads from the
        first page.
    :param end_page: (int) The ending page number to read. If None, reads to the last
        page.

    :returns: (dict) A dictionary containing the OCR results for each page.

    """
    return read_pdf(file_path, start_page=start_page, end_page=end_page)
