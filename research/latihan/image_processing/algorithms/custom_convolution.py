"""
#6 (Medium, 20 menit) - Custom Convolution dengan filter2D
Definisikan kernel custom (misal sharpening kernel atau emboss kernel),
terapkan dengan cv2.filter2D, dan jelaskan apa yang dilakukan tiap nilai
dalam kernel tersebut.

Penjelasan kernel bawaan:
    SHARPEN_KERNEL = [[ 0, -1,  0],
                       [-1,  5, -1],
                       [ 0, -1,  0]]
    Nilai tengah (5) memperkuat piksel itu sendiri, nilai -1 di keempat
    tetangga (atas/bawah/kiri/kanan) menekan kontribusi mereka. Efeknya:
    selisih antara piksel dan tetangganya dipertajam -> tepi/detail terlihat
    lebih tajam. Jumlah semua nilai kernel = 1, jadi kecerahan rata-rata
    gambar tetap terjaga.

    EMBOSS_KERNEL = [[-2, -1,  0],
                     [-1,  1,  1],
                     [ 0,  1,  2]]
    Nilai negatif di kiri-atas dan positif di kanan-bawah menonjolkan
    perbedaan intensitas pada satu arah diagonal, menghasilkan efek
    "timbul" (emboss) seperti relief 3D searah cahaya diagonal tersebut.

Input (apply_kernel):
    image (np.ndarray) - grayscale atau color image, shape (H, W) atau
        (H, W, 3), dtype uint8.
    kernel (np.ndarray) - kernel konvolusi custom, shape (kh, kw) ganjil,
        dtype float.
Output (apply_kernel): (np.ndarray) - image hasil konvolusi ("same" padding),
    shape sama dengan input, dtype uint8 (hasil di-clip ke 0-255).
"""

import numpy as np

SHARPEN_KERNEL = np.array(
    [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0],
    ],
    dtype=float,
)

EMBOSS_KERNEL = np.array(
    [
        [-2, -1, 0],
        [-1, 1, 1],
        [0, 1, 2],
    ],
    dtype=float,
)


def apply_kernel(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Apply a custom convolution kernel to an image (e.g. via cv2.filter2D),
    using "same" padding so the output has the same shape as the input.

    Args:
        image (np.ndarray): Image, shape (H, W) or (H, W, 3), dtype uint8.
        kernel (np.ndarray): Convolution kernel, shape (kh, kw), odd
            dimensions, dtype float.

    Returns:
        np.ndarray: Convolved image, same shape as input, dtype uint8
            (values clipped to 0-255).

    Raises:
        ValueError: If kernel has an even height or width.
    """
    raise NotImplementedError("TODO: implement apply_kernel")


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    # TODO: baca gambar dari image_path, panggil apply_kernel di atas
    # dengan SHARPEN_KERNEL dan EMBOSS_KERNEL, lalu simpan atau tampilkan
    # hasilnya.
