"""
-> Edge Detection dengan Sobel
Implementasikan deteksi tepi menggunakan operator Sobel (gradien X dan Y),
gabungkan jadi magnitude gradien.

Input: image (np.ndarray) - grayscale image, shape (H, W), dtype uint8 atau float.
Output: (np.ndarray) - gradient magnitude image, shape (H, W), dtype uint8
    (dinormalisasi ke rentang 0-255).
    magnitude = sqrt(Gx**2 + Gy**2)
"""

import numpy as np


def sobel_edge_detection(image: np.ndarray) -> np.ndarray:
    """
    Detect edges using the Sobel operator (gradient magnitude).

    Args:
        image (np.ndarray): Grayscale image, shape (H, W).

    Returns:
        np.ndarray: Gradient magnitude image, shape (H, W), dtype uint8,
            normalized to 0-255.

    Raises:
        ValueError: If image is not a 2D (grayscale) array.
    """
    raise NotImplementedError("TODO: implement sobel_edge_detection")


if __name__ == "__main__":
    sample = np.zeros((5, 5), dtype=np.uint8)
    sample[:, 3:] = 255
    print(sobel_edge_detection(sample))
