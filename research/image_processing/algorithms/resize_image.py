"""
-> Resize Gambar dengan Interpolasi Manual
Implementasikan nearest-neighbor atau bilinear interpolation untuk resize
gambar tanpa fungsi built-in resize.

Input:
    image (np.ndarray) - image, shape (H, W) atau (H, W, C), dtype uint8.
    new_height (int) - tinggi target.
    new_width (int) - lebar target.
    method (str) - "nearest" atau "bilinear", default "nearest".
Output: (np.ndarray) - image hasil resize, shape (new_height, new_width)
    atau (new_height, new_width, C), dtype uint8.
"""

import numpy as np


def resize_image(
    image: np.ndarray,
    new_height: int,
    new_width: int,
    method: str = "nearest",
) -> np.ndarray:
    """
    Resize an image using manual nearest-neighbor or bilinear interpolation.

    Args:
        image (np.ndarray): Image, shape (H, W) or (H, W, C), dtype uint8.
        new_height (int): Target height.
        new_width (int): Target width.
        method (str): "nearest" or "bilinear". Defaults to "nearest".

    Returns:
        np.ndarray: Resized image, shape (new_height, new_width[, C]).

    Raises:
        ValueError: If method is not "nearest" or "bilinear", or if
            new_height/new_width is not a positive integer.
    """
    raise NotImplementedError("TODO: implement resize_image")


if __name__ == "__main__":
    sample = np.array([[10, 20], [30, 40]], dtype=np.uint8)
    print(resize_image(sample, 4, 4, method="nearest"))
