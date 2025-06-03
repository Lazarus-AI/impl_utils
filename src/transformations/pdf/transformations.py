import math
import tempfile
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
from deskew import determine_skew
from pdf2image import convert_from_path
from PIL import Image

from file_system.utils import append_to_filename
from general.core import log_timing


class PDFTidy:
    """
    A class to tidy up PDF files by converting them to images, deskewing, cropping, and then recompiling them into a PDF.
    """

    def __init__(self, pdf_path):
        """
        Initializes the PDFTidy object with the path to a PDF file.
        :param pdf_path: The path to the PDF file.
        """
        self.pdf_path = pdf_path
        self.image_files = []

    @log_timing
    def tidy(
        self, destination_path: Optional[str] = None, deskew: bool = True, auto_crop: bool = True
    ) -> str:
        """
        Tidies the PDF file by converting it to images, optionally deskewing and cropping, and then recompiling them into a PDF.
        :param destination_path: The destination path for the tidied PDF file. If None, the original filename with "_tidied" appended is used.
        :param deskew: If True, the images will be deskewed.
        :param auto_crop: If True, the images will be automatically cropped.
        :return: The path to the tidied PDF file.
        """
        if destination_path is None:
            destination_path = append_to_filename(self.pdf_path, "_tidied")

        with tempfile.TemporaryDirectory() as path:
            image_files = convert_from_path(self.pdf_path, output_folder=path)
            for image_file in image_files:
                if deskew:
                    self.deskew(image_file)

                if auto_crop:
                    self.auto_crop(image_file)

            compile_images_to_pdf(image_files, destination_path)

        return destination_path

    def deskew(self, image: Image):
        """
        Deskews the image by correcting its orientation.
        :param image: The PIL Image to deskew.
        """
        image = cv2.imread(image)
        if image is None:
            raise Exception("Error: Unable to read the image. Check filepath or filename")
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        rotated = self.rotate(image, angle, (0, 0, 0))
        cv2.imwrite(image, rotated)

    def auto_crop(self, image: Image):
        """
        Automatically crops the image to remove unnecessary whitespace.
        :param image: The PIL Image to crop.
        """
        img = cv2.imread(image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        cropped_image = img[y : y + h, x : x + w]
        cv2.imwrite(image, cropped_image)

    def rotate(
        self, image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]
    ) -> np.ndarray:
        """
        Rotates the image by the specified angle.
        :param image: The numpy array representing the image.
        :param angle: The angle to rotate the image by.
        :param background: The background color to use for the rotated image.
        :return: The rotated numpy array image.
        """
        old_width, old_height = image.shape[:2]
        angle_radian = math.radians(angle)
        width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
        height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        rot_mat[1, 2] += (width - old_width) / 2
        rot_mat[0, 2] += (height - old_height) / 2
        return cv2.warpAffine(
            image,
            rot_mat,
            (int(round(height)), int(round(width))),
            borderValue=background,
        )


def compile_images_to_pdf(image_files: List[Image], destination_path: str):
    """
    Compiles a list of images into a PDF file.
    :param image_files: The list of PIL Image objects to compile.
    :param destination_path: The destination path for the compiled PDF file.
    :return: The path to the compiled PDF file.
    """
    images = []
    for image_file in image_files:
        image = Image.open(image_file)
        image.convert("RGB")
        images.append(image)

    image = images.pop(0)
    image.save(destination_path, save_all=True, append_images=images)
    return destination_path