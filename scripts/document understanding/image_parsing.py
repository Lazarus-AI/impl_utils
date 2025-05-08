import cv2
import numpy as np
from scipy.ndimage import minimum_filter, maximum_filter
from components import Components
from component_ocr import predict_character
from config import *
from os.path import join
from pdf2image import convert_from_path

import easyocr

def structure_smear(structure_image, smear_radius=20):
    # structure_image should be in negative
    assert(structure_image.mean() < 255/2)
    # vertical and horizontal lines survive (except small checkboxes)
    h_smear = minimum_filter(structure_image, size=2 * smear_radius, axes=0)
    h_smear[smear_radius:, :] = np.maximum(h_smear[:-smear_radius, :], h_smear[smear_radius:, :])
    h_smear[:-smear_radius, :] = np.maximum(h_smear[:-smear_radius, :], h_smear[smear_radius:, :])
    v_smear = minimum_filter(structure_image, size=2 * smear_radius, axes=1)
    v_smear[:, smear_radius:] = np.maximum(v_smear[:, :-smear_radius], v_smear[:, smear_radius:])
    v_smear[:, :-smear_radius] = np.maximum(v_smear[:, :-smear_radius], v_smear[:, smear_radius:])
    return np.maximum(h_smear, v_smear)


"""
This will focus on starting with a raw numpy array representing a single page of a document.
The array is assumed to be 2 or 3-dimensional (bw vs color).

1) finding linear structures like bounding boxes and h_lines
2) break out each bounded region (cell)

"""

testDoc = join(document_directory,document_name)
print(f'testDoc: {testDoc}')
# raw_image = cv2.imread(testDoc)

# Convert only the first page of the PDF to an image
pages = convert_from_path(testDoc, dpi=150, first_page=1, last_page=1)

# Convert the first page (PIL Image) to OpenCV format
raw_image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)


cv2.imwrite(join(output_directory,'raw_image.jpg'),raw_image)
# make binary image
binarization_threshold = 200  # heuristic (can be tuned)
grey_image = cv2.cvtColor(raw_image, cv2.COLOR_RGB2GRAY)
cv2.imwrite(join(output_directory,'grey_image.jpg'),grey_image)
_, binary_image = cv2.threshold(grey_image, binarization_threshold, 255, cv2.THRESH_BINARY_INV)
cv2.imwrite(join(output_directory,'binary_image.jpg'),binary_image)


# crop grey/binary images
crop_buffer_pixels = 4  # improves cell capture for unbounded cells
_, column_content = np.nonzero(binary_image)
binary_image_cropped = binary_image[:, (column_content.min() + crop_buffer_pixels):(column_content.max() - crop_buffer_pixels)]
cv2.imwrite(join(output_directory,'binary_image_cropped.jpg'),binary_image_cropped)
grey_image_cropped = grey_image[:, (column_content.min() + crop_buffer_pixels):(column_content.max() - crop_buffer_pixels)]
cv2.imwrite(join(output_directory,'grey_image_cropped.jpg'),grey_image_cropped)

# get raw components for document parsing
raw_components = Components(binary_image)

# get image properties
max_char_scale_inch = 0.25  # heuristic (can be tuned)
image_height, image_width, *_ = raw_image.shape
estimated_dpi = image_width / 8.5
max_char_scale = max_char_scale_inch * estimated_dpi
min_char_scale = 8

# ToDo: deal with dark banners

# identify candidate characters
is_candidate_character =  (raw_components.scale <= max_char_scale) & (min_char_scale <= raw_components.scale)
candidate_character_indices, = np.nonzero(is_candidate_character)


is_candidate_line = (raw_components.density >= 95) & (raw_components.scale >= max_char_scale)
candidate_line_indices, = np.nonzero(is_candidate_line)


# identify candidate structure (bounding for some cell)
is_candidate_structure = ~(is_candidate_character | is_candidate_line)
candidate_structure_indices, = np.nonzero(is_candidate_structure)
candidate_structure_image = np.isin(raw_components.mask, [i for i in candidate_structure_indices if i])
structure_image = structure_smear(candidate_structure_image, smear_radius=20)
#cv2.imwrite('example_images/structure_image.jpg', 255 * structure_image.astype('uint8'))

# recover characters removed from candidate structure
extra_image = candidate_structure_image & ~structure_image  # these should be added back to candidate characters
extra_components = Components(255 * extra_image.astype('uint8'))
is_candidate_extra_character = (extra_components.scale <= max_char_scale) & (min_char_scale <= extra_components.scale)
candidate_extra_character_indices, = np.nonzero(is_candidate_extra_character)

# define cells
cell_components = Components(255 * (~structure_image).astype('uint8'))

# create easyOCR reader for English language
reader = easyocr.Reader(['en'])  # this needs to run only once to load the model into memory

for cell_id in range(len(cell_components.components)):
    cell_data = cell_components.components[cell_id]
    cell_mask = cell_components.mask[cell_data['top']:cell_data['bottom'], cell_data['left']:cell_data['right']]
    cell_window = 255 - binary_image[cell_data['top']:cell_data['bottom'], cell_data['left']:cell_data['right']]
    cell_image = np.where(cell_mask == cell_id, cell_window, 255).astype('uint8')
    cv2.imwrite(join(output_directory,f'cell_{cell_id}_image.jpg'), cell_image)
    cell_content = reader.readtext(cell_image.astype('uint8'), detail=True, paragraph=False)
    this_textFileName = join(output_directory,f'cell_{cell_id}_text.txt')
    with open(this_textFileName, 'w') as output:
        if len(cell_content)==0:
            cell_content_str = '<no text found>'
        else:
            cell_content_str = '\n'.join(str(x[1]) for x in cell_content)
        output.write(cell_content_str)
        print(f'wrote text output to file {this_textFileName}')

"""
Next steps:
1) associate content within a cell (dark pixel content, not ocr yet)
2) ocr mixture of experts (machine-text-only vs opensource)
3) build xml-style content per-cell
4) create 'retriever' which grabs cell(s) relevant for user query and returns xml content 
"""
