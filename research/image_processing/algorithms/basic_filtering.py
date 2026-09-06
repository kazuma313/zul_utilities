"""
#2 (Easy, 15 menit) - Basic Filtering
Terapkan Gaussian blur dan median blur pada gambar, bandingkan hasilnya, dan
jelaskan kapan masing-masing lebih cocok dipakai (misal median blur lebih
baik untuk salt-and-pepper noise).

Catatan diskusi:
    - Gaussian blur: rata-rata berbobot (kernel Gaussian) dari tetangga
      piksel. Bagus untuk noise Gaussian/umum dan smoothing halus, tapi
      noise "outlier" ekstrem (salt-and-pepper) tetap ikut ter-blur ke
      sekitarnya, bukan dihilangkan.
    - Median blur: mengambil nilai median dari tetangga piksel. Karena
      median tahan terhadap outlier, teknik ini jauh lebih efektif
      menghilangkan salt-and-pepper noise (titik hitam/putih acak) sambil
      tetap menjaga tepi lebih tajam dibanding Gaussian blur.

Input (apply_gaussian_blur / apply_median_blur):
    image (np.ndarray) - image, shape (H, W) atau (H, W, 3), dtype uint8.
    ksize (int) - ukuran kernel (harus ganjil dan >= 3), default 5.
Output: (np.ndarray) - image hasil blur, shape sama dengan input, dtype uint8.
"""

import numpy as np
import cv2

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


def apply_gaussian_blur(image: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    Smooth an image with a Gaussian blur.

    Args:
        image (np.ndarray): Image, shape (H, W) or (H, W, 3), dtype uint8.
        ksize (int): Kernel size, must be odd and >= 3. Defaults to 5.

    Returns:
        np.ndarray: Blurred image, same shape as input.

    Raises:
        ValueError: If ksize is not odd or is less than 3.
    """
    image = cv2.GaussianBlur(image, (ksize, ksize), 0)
    return image
    


def apply_median_blur(image: np.ndarray, ksize: int = 5) -> np.ndarray:
    """
    Smooth an image with a median blur (replaces each pixel with the median
    of its neighborhood).

    Args:
        image (np.ndarray): Image, shape (H, W) or (H, W, 3), dtype uint8.
        ksize (int): Kernel size, must be odd and >= 3. Defaults to 5.

    Returns:
        np.ndarray: Blurred image, same shape as input.

    Raises:
        ValueError: If ksize is not odd or is less than 3.
    """
    image = cv2.medianBlur(image, ksize, 0)
    return image


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "rog.jpg"
    img = read_image(image_path, widht=640, height=640)
    img_gausian = apply_gaussian_blur(image=img)
    img_median = apply_median_blur(image=img)
    # print(img[0])
    show_image(name= "gausian", image=img_gausian)
    show_image(name= "median", image=img_median)
