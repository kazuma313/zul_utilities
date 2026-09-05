"""
-> Grayscale Conversion Manual
Diberi array numpy RGB image, implementasikan konversi ke grayscale TANPA
memakai fungsi built-in cv2/PIL untuk grayscale (pakai rumus weighted sum manual).

Input: image (np.ndarray) - RGB image, shape (H, W, 3), dtype uint8.
Output: (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
    Formula: gray = 0.299*R + 0.587*G + 0.114*B
"""

import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert an RGB image to grayscale using a manual weighted-sum formula.

    Args:
        image (np.ndarray): RGB image, shape (H, W, 3), dtype uint8.

    Returns:
        np.ndarray: Grayscale image, shape (H, W), dtype uint8.

    Raises:
        ValueError: If image does not have exactly 3 channels (shape (H, W, 3)).
    """
    raise NotImplementedError("TODO: implement to_grayscale")


if __name__ == "__main__":
    sample = np.zeros((2, 2, 3), dtype=np.uint8)
    sample[0, 0] = [255, 0, 0]
    print(to_grayscale(sample))
