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
import cv2
from matplotlib import pyplot as plt


def read_image(path:str, widht:int, height:int):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Image not found")
    
    image = cv2.resize(image, (widht, height), interpolation=0)
    return image


def show_image(image, name="gambar"):
    cv2.imshow (name, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def compute_histogram(image: np.ndarray) -> np.ndarray:
    """
    Compute the pixel-intensity histogram of a grayscale image.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.

    Returns:
        np.ndarray: Shape (256,), dtype int, counts per intensity level 0-255.
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cal_hist = cv2.calcHist([image], [0], None, [256], [0, 256])
    plt.plot(cal_hist, color='b')
    plt.title('Image Histogram For Blue Channel GFG')
    plt.show()
    


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    Apply histogram equalization to increase contrast of a grayscale image.

    Args:
        image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.

    Returns:
        np.ndarray: Equalized grayscale image, shape (H, W), dtype uint8.
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist_equa = cv2.equalizeHist(image)
    res = np.hstack((image, hist_equa))
    plt.figure(figsize=(10, 5))
    plt.imshow(res, cmap='gray')  
    plt.title("Original vs Equalized Image")
    plt.axis('off')  
    plt.show()


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    image = read_image(image_path, widht=640, height=640)
    compute_histogram(image=image)
    histogram_equalization(image=image)
