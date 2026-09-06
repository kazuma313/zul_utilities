"""
#4 (Medium, 20 menit) - Histogram & Contrast Enhancement
Hitung dan plot histogram intensitas gambar grayscale, lalu terapkan
histogram equalization untuk meningkatkan kontras.

Catatan diskusi (kapan histogram equalization bisa gagal/tidak membantu):
    - Gambar yang histogramnya sudah tersebar merata (kontras sudah tinggi):
      equalization nyaris tidak mengubah apa-apa, karena CDF-nya sudah
      mendekati linear.
    - Gambar dengan noise: equalization ikut meregangkan noise, jadi noise
      yang tadinya halus bisa terlihat jauh lebih mencolok setelah kontras
      diperbesar.
    - Gambar dengan area besar warna seragam (mis. langit polos) bisa
      menghasilkan efek "posterization"/band karena sebagian besar piksel
      dipetakan ke rentang intensitas yang sempit.

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
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    # TODO: baca gambar dari image_path (grayscale), panggil
    # compute_histogram & histogram_equalization di atas, lalu simpan atau
    # tampilkan hasilnya (mis. plot histogram-nya).
