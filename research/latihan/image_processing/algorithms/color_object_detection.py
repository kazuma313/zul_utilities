"""
#5 (Medium, 25 menit) - Deteksi & Hitung Objek Berdasarkan Warna
Diberi gambar dengan beberapa objek berwarna solid di atas background
berbeda, buat mask di HSV color space untuk mendeteksi objek dengan warna
tertentu (misal semua objek merah), bersihkan noise dengan morphological
operations, lalu hitung jumlah objek dengan cv2.findContours atau
cv2.connectedComponentsWithStats. Ini pola soal yang sangat umum: color
masking + counting.

Langkah yang diharapkan:
    1. Konversi image ke HSV, buat mask dengan cv2.inRange(hsv_lower, hsv_upper).
    2. Bersihkan noise pada mask dengan morphological opening/closing
       (mis. cv2.morphologyEx) supaya speck 1-2 piksel tidak ikut terhitung
       sebagai objek.
    3. Hitung jumlah komponen (objek) pada mask yang sudah bersih, mis.
       dengan cv2.findContours atau cv2.connectedComponentsWithStats.

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
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    # TODO: baca gambar dari image_path, panggil
    # detect_and_count_colored_objects di atas dengan hsv_lower/hsv_upper
    # pilihanmu (mis. untuk menangkap neon merah), lalu simpan atau
    # tampilkan mask & count-nya.
