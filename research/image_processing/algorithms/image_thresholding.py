"""
-> Image Thresholding / Binarization
Implementasikan binary thresholding manual: pixel di atas ambang batas jadi
255 (putih), di bawah jadi 0 (hitam).

Input:
    image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
    threshold (int) - ambang batas, 0-255.
Output: (np.ndarray) - binary image, shape (H, W), dtype uint8, nilai {0, 255}.
"""

import numpy as np


def threshold_image(image: np.ndarray, threshold: int) -> np.ndarray:
    """
    Binarize a grayscale image using a manual threshold.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.
        threshold (int): Threshold value, 0-255. Pixels strictly above become
            255 (white); pixels at or below become 0 (black).

    Returns:
        np.ndarray: Binary image, shape (H, W), dtype uint8, values in {0, 255}.

    Raises:
        ValueError: If threshold is not in the range 0-255.
    """
    raise NotImplementedError("TODO: implement threshold_image")


if __name__ == "__main__":
    sample = np.array([[10, 200], [128, 50]], dtype=np.uint8)
    print(threshold_image(sample, 127))
