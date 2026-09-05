"""
-> Histogram & Histogram Equalization
Hitung histogram intensitas pixel dari gambar grayscale, lalu implementasikan
histogram equalization untuk meningkatkan kontras.

Input (compute_histogram): image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
Output (compute_histogram): (np.ndarray) - shape (256,), dtype int, jumlah pixel per intensitas 0-255.

Input (histogram_equalization): image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
Output (histogram_equalization): (np.ndarray) - grayscale image ter-equalize, shape (H, W), dtype uint8.
"""

import numpy as np


def compute_histogram(image: np.ndarray) -> np.ndarray:
    """
    Compute the pixel-intensity histogram of a grayscale image.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.

    Returns:
        np.ndarray: Shape (256,), dtype int, counts per intensity level 0-255.
    """
    raise NotImplementedError("TODO: implement compute_histogram")


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    Apply histogram equalization to increase contrast of a grayscale image.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.

    Returns:
        np.ndarray: Equalized grayscale image, shape (H, W), dtype uint8.
    """
    raise NotImplementedError("TODO: implement histogram_equalization")


if __name__ == "__main__":
    sample = np.array([[0, 64], [128, 255]], dtype=np.uint8)
    print(compute_histogram(sample))
    print(histogram_equalization(sample))
