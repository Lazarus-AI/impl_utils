import warnings

import easyocr

from file_system.utils import get_all_files_with_ext, get_extension, get_filename
from transformations.pdf.bounding_boxes import BoundingBox
from transformations.pdf.utils import convert_pdf_to_images


def format_ocr_results(results, page_number):
    # Example results:
    # (
    #     [
    #         [np.int32(1052), np.int32(285)],
    #         [np.int32(1661), np.int32(285)],
    #         [np.int32(1661), np.int32(386)],
    #         [np.int32(1052), np.int32(386)]
    #     ],
    #     'LAZARUS',
    #     np.float64(0.9106397069581507)
    # ),
    output = []
    for result in results:
        coordinates = result[0]
        data = result[1]
        confidence = float(result[2])
        box_values = {
            "top_left_x": int(coordinates[0][0]),
            "top_left_y": int(coordinates[0][1]),
            "bottom_right_x": int(coordinates[2][0]),
            "bottom_right_y": int(coordinates[2][1]),
        }
        box = BoundingBox(page_number=page_number, box=box_values)
        output.append({"data": data, "confidence": confidence, "bounding_box": box.model_dump()})
    return output


def read_pdf(file_path, start_page=None, end_page=None):
    image_folder = convert_pdf_to_images(file_path, start_page=start_page, end_page=end_page)
    image_paths = get_all_files_with_ext(image_folder, "jpg")

    reader = easyocr.Reader(["en"])  # this needs to run only once to load the model into memory
    results = {}
    page_number = start_page
    for image_path in image_paths:
        file_name = f"{get_filename(image_path)}.{get_extension(image_path)}"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = reader.readtext(image_path)
            results[file_name] = format_ocr_results(result, page_number)

        page_number = page_number + 1
    return results
