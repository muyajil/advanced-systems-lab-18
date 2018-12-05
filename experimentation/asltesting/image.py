import os
import numpy as np

from PIL import Image


def merge_images(image_files, target_file):
    thumb_width = 640
    thumb_height = 480
    image_files = list(filter(lambda x: 'all.png' not in x, image_files))
    num_images = len(image_files)
    num_cols = 4
    num_rows = int(np.ceil(num_images / num_cols))
    result = Image.new("RGB", (thumb_width*num_cols, thumb_height*num_rows))

    for index, file in enumerate(image_files):
        img = Image.open(file)
        img.thumbnail((thumb_width, thumb_height), Image.ANTIALIAS)
        top = int(thumb_height * np.floor(index / num_cols))
        left = thumb_width * (index % num_cols)
        bottom = int(top + thumb_height)
        right = left + thumb_width
        result.paste(img, (left, top, right, bottom))

    result.save(target_file)
