"""
-> Deteksi & Hitung Objek Sederhana (Color-based Masking)
Diberi gambar dengan beberapa objek berwarna solid di atas background berbeda,
buat mask untuk mendeteksi objek dengan warna tertentu (misal semua objek merah)
menggunakan HSV color space, lalu hitung berapa banyak objek dengan connected
component labeling.

Input:
    image (np.ndarray) - RGB image, shape (H, W, 3), dtype uint8.
    hsv_lower (tuple[int, int, int]) - batas bawah (H, S, V).
    hsv_upper (tuple[int, int, int]) - batas atas (H, S, V).
Output: tuple(mask, count)
    mask (np.ndarray) - binary mask, shape (H, W), dtype uint8, nilai {0, 255}.
    count (int) - jumlah connected component (objek) pada mask.
"""

import numpy as np


def detect_and_count_colored_objects(
    image: np.ndarray,
    hsv_lower: tuple,
    hsv_upper: tuple,
) -> tuple:
    """
    Build a color mask in HSV space and count connected components on it.

    Args:
        image (np.ndarray): RGB image, shape (H, W, 3), dtype uint8.
        hsv_lower (tuple[int, int, int]): Lower HSV bound.
        hsv_upper (tuple[int, int, int]): Upper HSV bound.

    Returns:
        tuple[np.ndarray, int]: (mask of shape (H, W) with values {0, 255},
            number of detected objects/connected components).

    Raises:
        ValueError: If hsv_lower is not element-wise <= hsv_upper.
    """
    raise NotImplementedError("TODO: implement detect_and_count_colored_objects")


if __name__ == "__main__":
    sample = np.zeros((4, 4, 3), dtype=np.uint8)
    sample[0:2, 0:2] = [255, 0, 0]
    mask, count = detect_and_count_colored_objects(sample, (0, 100, 100), (10, 255, 255))
    print(mask, count)
