"""
#3 (Medium, 20 menit) - Edge Detection
Terapkan Canny edge detection dan Sobel edge detection pada gambar yang sama,
bandingkan hasil dan parameter yang memengaruhi sensitivitas deteksi tepi.

Catatan diskusi:
    - Sobel: menghasilkan gradien (magnitude) kontinu per piksel; parameter
      utamanya adalah ksize (ukuran kernel turunan) - ksize besar lebih
      sensitif ke tepi halus/noise, ksize kecil lebih fokus ke tepi tajam.
      Hasilnya bukan biner, butuh thresholding tambahan kalau mau garis
      tepi yang jelas.
    - Canny: menghasilkan peta tepi biner langsung (0/255), memakai dua
      threshold (threshold1, threshold2) untuk hysteresis - piksel di atas
      threshold2 pasti tepi, di antara threshold1-threshold2 hanya jadi
      tepi kalau terhubung ke tepi kuat. Threshold rendah -> lebih sensitif
      (banyak tepi, termasuk noise); threshold tinggi -> lebih selektif
      (hanya tepi kuat yang tampil).

Input (sobel_edge_detection):
    image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
    ksize (int) - ukuran kernel Sobel (ganjil, mis. 3 atau 5), default 3.
Output (sobel_edge_detection): (np.ndarray) - gradient magnitude image,
    shape (H, W), dtype uint8, dinormalisasi ke 0-255.

Input (canny_edge_detection):
    image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
    threshold1 (int) - lower threshold untuk hysteresis, default 100.
    threshold2 (int) - upper threshold untuk hysteresis, default 200.
Output (canny_edge_detection): (np.ndarray) - binary edge map, shape (H, W),
    dtype uint8, nilai {0, 255}.
"""

import numpy as np


def sobel_edge_detection(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    """
    Detect edges using the Sobel operator (gradient magnitude).

    Args:
        image (np.ndarray): Grayscale image, shape (H, W).
        ksize (int): Sobel kernel size (odd, e.g. 3 or 5). Defaults to 3.

    Returns:
        np.ndarray: Gradient magnitude image, shape (H, W), dtype uint8,
            normalized to 0-255.

    Raises:
        ValueError: If image is not a 2D (grayscale) array.
    """
    raise NotImplementedError("TODO: implement sobel_edge_detection")


def canny_edge_detection(
    image: np.ndarray,
    threshold1: int = 100,
    threshold2: int = 200,
) -> np.ndarray:
    """
    Detect edges using the Canny edge detector.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W).
        threshold1 (int): Lower hysteresis threshold. Defaults to 100.
        threshold2 (int): Upper hysteresis threshold. Defaults to 200.

    Returns:
        np.ndarray: Binary edge map, shape (H, W), dtype uint8, values in
            {0, 255}.

    Raises:
        ValueError: If image is not a 2D (grayscale) array, or if
            threshold1 >= threshold2.
    """
    raise NotImplementedError("TODO: implement canny_edge_detection")


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    # TODO: baca gambar dari image_path (grayscale), panggil
    # sobel_edge_detection & canny_edge_detection di atas, lalu simpan atau
    # tampilkan hasilnya.
