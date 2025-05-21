from transformations.ocr.easyocr import read_pdf


def ocr_pdf(file_path, start_page=None, end_page=None):
    return read_pdf(file_path, start_page=start_page, end_page=end_page)
