"""
-> Implementasi Konvolusi 2D dari Nol
Implementasikan fungsi convolve2d(image, kernel) menggunakan numpy saja
(tanpa cv2.filter2D/scipy.signal.convolve2d). Uji dengan kernel blur
(box filter 3x3) dan kernel edge detection (Sobel).

Input:
    image (np.ndarray) - grayscale image, shape (H, W), dtype float atau uint8.
    kernel (np.ndarray) - convolution kernel, shape (kh, kw), dtype float.
Output: (np.ndarray) - hasil konvolusi, shape (H, W) (padding "same",
    ukuran output sama dengan input).
"""

import numpy as np


def convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Convolve a 2D grayscale image with a kernel using "same" zero-padding.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W).
        kernel (np.ndarray): Convolution kernel, shape (kh, kw).

    Returns:
        np.ndarray: Convolved image, shape (H, W), same shape as input.

    Raises:
        ValueError: If kernel has an even height or width (no well-defined
            center for "same" padding).
    """
    raise NotImplementedError("TODO: implement convolve2d")


if __name__ == "__main__":
    sample = np.arange(16, dtype=float).reshape(4, 4)
    box_kernel = np.ones((3, 3)) / 9
    print(convolve2d(sample, box_kernel))
