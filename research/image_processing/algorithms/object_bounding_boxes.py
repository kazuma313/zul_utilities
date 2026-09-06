"""
#7 (Bonus, Hard, 25 menit) - Simple Object Tracking / Bounding Box
Dari hasil deteksi kontur pada soal #5, gambar bounding box di sekitar tiap
objek yang terdeteksi (cv2.boundingRect + cv2.rectangle), dan urutkan objek
dari yang terbesar ke terkecil berdasarkan area.

Input (find_bounding_boxes): mask (np.ndarray) - binary mask, shape (H, W),
    dtype uint8, nilai {0, 255} (misalnya hasil dari soal #5).
Output (find_bounding_boxes): (list[tuple[int, int, int, int]]) - daftar
    bounding box (x, y, w, h), satu per objek terdeteksi, diurutkan dari
    area (w*h) terbesar ke terkecil.

Input (draw_bounding_boxes):
    image (np.ndarray) - image, shape (H, W, 3), dtype uint8.
    boxes (list[tuple[int, int, int, int]]) - daftar bounding box (x, y, w, h).
    color (tuple[int, int, int]) - warna garis kotak, default (0, 255, 0).
    thickness (int) - ketebalan garis, default 2.
Output (draw_bounding_boxes): (np.ndarray) - salinan image dengan bounding
    box tergambar, shape sama dengan input.
"""

import numpy as np


def find_bounding_boxes(mask: np.ndarray) -> list:
    """
    Find the bounding box of every connected white region in a binary mask
    (e.g. via cv2.findContours + cv2.boundingRect), sorted by area (largest
    first).

    Args:
        mask (np.ndarray): Binary mask, shape (H, W), dtype uint8, values
            in {0, 255}.

    Returns:
        list[tuple[int, int, int, int]]: (x, y, w, h) boxes, sorted by
            w*h descending.
    """
    raise NotImplementedError("TODO: implement find_bounding_boxes")


def draw_bounding_boxes(
    image: np.ndarray,
    boxes: list,
    color: tuple = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw each (x, y, w, h) bounding box as a rectangle on a copy of the image
    (e.g. via cv2.rectangle).

    Args:
        image (np.ndarray): Image, shape (H, W, 3), dtype uint8.
        boxes (list[tuple[int, int, int, int]]): (x, y, w, h) boxes to draw.
        color (tuple[int, int, int]): Rectangle color. Defaults to (0, 255, 0).
        thickness (int): Line thickness. Defaults to 2.

    Returns:
        np.ndarray: Copy of image with the boxes drawn, same shape as input.
    """
    raise NotImplementedError("TODO: implement draw_bounding_boxes")


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    # TODO: baca gambar dari image_path, dapatkan mask (mis. dari
    # detect_and_count_colored_objects di soal #5), panggil
    # find_bounding_boxes lalu draw_bounding_boxes di atas, lalu simpan
    # atau tampilkan hasilnya.
