"""
Menyembunyikan bagian frame: menghitamkan area, mengaburkan, atau memikselkan kotak.

Gunanya:
    Masker poligon menghitamkan area sebelum frame masuk ke model, jadi
    orang di area itu tidak pernah terdeteksi. Blur dan pixelate menyamarkan
    kotak di frame hasil, misalnya wajah atau badan orang sebelum videonya
    dibagikan. Butuh extra vision: `pip install "zul[vision]"`.

Cara pakai:
    from zul.computer_vision import masks

    # sekali di awal: hitamkan semua di luar area yang diukur
    mask = masks.polygon_mask(areas, width, height, keep_inside=True)

    # setiap frame
    people = detect(model, masks.apply_mask(frame, mask))
    masks.blur_boxes(scene, people.xyxy)               # samarkan orangnya
"""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

# --------------------------------------------------------------------------
# Masker Area
# --------------------------------------------------------------------------
#
# Area yang diabaikan dihitamkan sebelum frame masuk ke model,
# jadi deteksi yang tidak diinginkan tidak pernah ada dan
# tidak bisa dihitung dua kali. Masker digambar sekali
# di awal, lalu setiap frame cukup satu bitwise_and.
#


def polygon_mask(
    polygons: Sequence[Sequence], width: int, height: int, keep_inside: bool = False
) -> np.ndarray | None:
    """Masker seukuran frame: hitamkan poligon, atau hitamkan semua di luar poligon."""
    shapes = [
        np.asarray(p, dtype=np.int32).reshape(-1, 2)
        for p in (polygons or [])
        if len(p) >= 3
    ]
    if not shapes:
        return None
    fill = 255 if keep_inside else 0
    mask = np.full((height, width, 3), 255 - fill, dtype=np.uint8)
    cv2.fillPoly(mask, shapes, (fill, fill, fill))
    return mask


def combine_masks(*masks: np.ndarray | None) -> np.ndarray | None:
    """Gabungkan beberapa masker menjadi satu, agar setiap frame cukup satu operasi."""
    present = [mask for mask in masks if mask is not None]
    if not present:
        return None
    combined = present[0]
    for mask in present[1:]:
        combined = cv2.bitwise_and(combined, mask)
    return combined


def apply_mask(image: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    """Salinan frame dengan area masker dihitamkan; frame asli jika tidak ada masker."""
    return image if mask is None else cv2.bitwise_and(image, mask)


# --------------------------------------------------------------------------
# Menyamarkan Kotak
# --------------------------------------------------------------------------
#
# Blur dan pixelate mengubah frame secara langsung, hanya di dalam
# kotak. Kotak yang keluar dari tepi frame dipotong lebih dulu,
# dan kotak yang tersisa tanpa luas dilewati tanpa error.
#


def _regions(scene: np.ndarray, boxes: np.ndarray):
    height, width = scene.shape[:2]
    for x1, y1, x2, y2 in np.asarray(boxes, dtype=np.float64).reshape(-1, 4):
        left, top = max(int(x1), 0), max(int(y1), 0)
        right, bottom = min(int(np.ceil(x2)), width), min(int(np.ceil(y2)), height)
        if right > left and bottom > top:
            yield slice(top, bottom), slice(left, right)


def blur_boxes(scene: np.ndarray, boxes: np.ndarray, kernel: int = 25) -> np.ndarray:
    """Kaburkan isi setiap kotak; `kernel` lebih besar berarti lebih kabur."""
    size = max(int(kernel), 1)
    for rows, cols in _regions(scene, boxes):
        scene[rows, cols] = cv2.blur(scene[rows, cols], (size, size))
    return scene


def pixelate_boxes(
    scene: np.ndarray, boxes: np.ndarray, pixel_size: int = 12
) -> np.ndarray:
    """Ubah isi setiap kotak menjadi blok-blok seukuran `pixel_size` piksel."""
    size = max(int(pixel_size), 1)
    for rows, cols in _regions(scene, boxes):
        region = scene[rows, cols]
        height, width = region.shape[:2]
        small = cv2.resize(
            region,
            (max(width // size, 1), max(height // size, 1)),
            interpolation=cv2.INTER_LINEAR,
        )
        scene[rows, cols] = cv2.resize(
            small, (width, height), interpolation=cv2.INTER_NEAREST
        )
    return scene
