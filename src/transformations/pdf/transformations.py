import math
import os
import shutil
from typing import Tuple, Union
from uuid import uuid4

import cv2
import numpy as np
import pymupdf
from deskew import determine_skew
from PIL import Image

from file_system.utils import append_to_filename, get_filename, in_tmp, mkdir


class PDFTidy:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.image_files = []
        id = uuid4()
        self.tmp_dir = in_tmp(f"images_{id}")
        mkdir(self.tmp_dir)

    def tidy(self, destination_path=None, deskew=True, auto_crop=True):
        if destination_path is None:
            destination_path = append_to_filename(self.pdf_path, "_tidied")

        self.convert_to_images()
        for image_file in self.image_files:
            if deskew:
                self.deskew(image_file)

            if auto_crop:
                self.auto_crop(image_file)

        self.compile_images_to_pdf(destination_path)
        self.clean()
        return destination_path

    def get_image_name(self, postfix=""):
        filename_without_extension = get_filename(self.pdf_path)
        return f"{filename_without_extension}_{postfix}.png"

    def convert_to_images(self):
        pdf_document = pymupdf.open(self.pdf_path)
        if len(pdf_document) == 0:
            raise Exception("Cannot read PDF")

        image_count = 0
        for page in pdf_document:
            image = page.get_pixmap(dpi=200)  # specify dpi here max 200
            image_name = self.get_image_name(str(image_count))
            image_path = os.path.join(self.tmp_dir, image_name)
            image.save(image_path)
            self.image_files.append(image_path)
            image_count = image_count + 1
        pdf_document.close()
        return self.image_files

    def deskew(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Error: Unable to read the image. Check filepath or filename")
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        angle = determine_skew(grayscale)
        rotated = self.rotate(image, angle, (0, 0, 0))
        cv2.imwrite(image_path, rotated)

    def auto_crop(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        cropped_image = img[y : y + h, x : x + w]
        cv2.imwrite(image_path, cropped_image)

    def rotate(
        self, image: np.ndarray, angle: float, background: Union[int, Tuple[int, int, int]]
    ) -> np.ndarray:
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

    def compile_images_to_pdf(self, destination_path):
        images = []
        for image_file in self.image_files:
            image = Image.open(image_file)
            image.convert("RGB")
            images.append(image)

        image = images.pop(0)
        image.save(destination_path, save_all=True, append_images=images)
        return destination_path

    def clean(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
