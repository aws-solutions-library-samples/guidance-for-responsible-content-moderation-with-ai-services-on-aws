#  Copyright 2022 Amazon.com and its affiliates; all rights reserved.
#  This file is Amazon Web Services Content and may not be duplicated or distributed without permission.

import io
import logging
import os
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
from PIL import Image
from albumentations.augmentations.dropout.cutout import Cutout
from albumentations.augmentations.utils import (
    is_grayscale_image,
)

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()


class ImageAugmentor:
    def __init__(self, selected_category_ids, image_folder, label_folder):
        """
        Albumentations is an Augmentation lib.
        https://github.com/albumentations-team/albumentations/

        Augmentation Methods:
            1 HorizontalFlip
            2 VerticalFlip
            3 ShiftScaleRotate
            4 GridDistortion
            4 ElasticTransform
            5 PiecewiseAffine
            6 PixelDropout
            7 SafeRotate
            8 RandomBrightnessContrast
            9 AdvancedBlur
            10 CLAHE
            11 ISONoise
            12 Solarize
            13 Sharpen
            14 Cutout
        """
        self.transform = A.Compose(
            [
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.ShiftScaleRotate(p=0.6, rotate_limit=2),
                A.OneOf([A.GridDistortion(p=0.1), A.ElasticTransform(p=0.1)], p=0.1),
                A.PiecewiseAffine(p=0.1),
                A.PixelDropout(dropout_prob=0.01, p=0.3),
                A.SafeRotate(p=0.3),
                A.RandomBrightnessContrast(p=0.3),
                A.AdvancedBlur(p=0.3),
                A.CLAHE(p=0.3),
                A.ISONoise(p=0.3),
                A.Solarize(p=0.3),
                A.Sharpen(p=0.3),
                Cutout(num_holes=4, max_h_size=80, max_w_size=80, fill_value=0, p=0.3),
            ],
            bbox_params=A.BboxParams(format="yolo", label_fields=["category_ids"]),
            p=1
        )

        self.selected_category_ids = selected_category_ids.keys()
        self.per_image_aug_category = selected_category_ids
        self.image_folder = image_folder
        self.label_folder = label_folder
        Path(self.image_folder).mkdir(parents=True, exist_ok=True)
        Path(self.label_folder).mkdir(parents=True, exist_ok=True)


    def _save_image(self, img, image_file_name):
        im = Image.fromarray(img)
        im.save(os.path.join(self.image_folder, image_file_name))
        return

    def _save_label(self, category_ids, bboxes, label_file_name):

        with io.open(
            os.path.join(self.label_folder, label_file_name), "w", encoding="utf-8"
        ) as _writer:
            for i in range(len(category_ids)):
                try:
                    _writer.write(
                        "{} {:.6f} {:.6f} {:.6f} {:.6f}\r".format(
                            category_ids[i],
                            bboxes[i][0],
                            bboxes[i][1],
                            bboxes[i][2],
                            bboxes[i][3],
                        )
                    )
                except Exception as e:
                    logger.error(f'error when write augmented label: {e}')

    def _get_original_labels(self, label_file):
        bboxes = []
        category_ids = []
        aug_count = 0

        with io.open(label_file, "r") as _reader:
            for line in _reader.readlines():
                bbox = line.split(" ")
                category_ids.append(int(bbox[0]))
                bboxes.append(
                    [float(bbox[1]), float(bbox[2]), float(bbox[3]), float(bbox[4])]
                )
                if int(bbox[0]) in self.selected_category_ids:
                    aug_count = self.per_image_aug_category.get(int(bbox[0]))

        return aug_count, category_ids, bboxes

    def bbox_augmentation(self, image_file, bboxes_body, forced_aug_nums=0):
        try:
            aug_count, category_ids, bboxes = self._get_original_labels(bboxes_body)
            if aug_count:

                im = cv2.imread(image_file)
                im = cv2.cvtColor(np.asarray(im), cv2.COLOR_BGR2RGB)
                if is_grayscale_image(im):
                    return

                forced_aug_nums = max(forced_aug_nums, aug_count)

                for i in range(forced_aug_nums):

                    transformed = self.transform(
                        image=im, bboxes=bboxes, category_ids=category_ids
                    )

                    file_base = Path(image_file).stem
                    extension = Path(image_file).suffix

                    self._save_image(
                        transformed["image"], f"aug_{file_base}_{i}{extension}"
                    )
                    self._save_label(
                        category_ids, transformed["bboxes"], f"aug_{file_base}_{i}.txt"
                    )

        except Exception as e:
            logger.error(f'error when augmentation: {e}')