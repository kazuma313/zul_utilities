"""
#1 (Easy, 10 menit) - Grayscale Conversion & Thresholding
Baca gambar berwarna, ubah ke grayscale, lalu terapkan binary thresholding
untuk menghasilkan gambar hitam-putih. Diskusikan cara memilih nilai
threshold (manual vs Otsu).

Catatan diskusi (manual vs Otsu):
    - Manual: kamu tentukan sendiri nilai threshold (0-255). Cocok kalau
      kondisi pencahayaan gambar sudah diketahui/konsisten.
    - Otsu: threshold dipilih otomatis dengan meminimalkan variance
      intra-kelas dari histogram gambar. Cocok untuk gambar dengan
      histogram bimodal (dua puncak jelas: objek vs background), tapi bisa
      kurang optimal kalau pencahayaan tidak merata (butuh adaptive
      thresholding) atau histogram tidak bimodal.

Input (to_grayscale): image (np.ndarray) - color image, shape (H, W, 3), dtype uint8.
Output (to_grayscale): (np.ndarray) - grayscale image, shape (H, W), dtype uint8.

Input (binary_threshold):
    gray_image (np.ndarray) - grayscale image, shape (H, W), dtype uint8.
    threshold (int) - ambang batas manual, 0-255, dipakai jika method="manual".
    method (str) - "manual" atau "otsu", default "manual".
Output (binary_threshold): (np.ndarray) - binary image, shape (H, W), dtype
    uint8, nilai {0, 255}.
"""

import numpy as np
import cv2

def read_image(path:str, widht:int, height:int):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Image not found")
    
    image = cv2.resize(image, (widht, height), interpolation=0)
    return image


def show_image(image):
    cv2.imshow ('Gambar', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert a color image to grayscale.

    Args:
        image (np.ndarray): Color image, shape (H, W, 3), dtype uint8.

    Returns:
        np.ndarray: Grayscale image, shape (H, W), dtype uint8.

    Raises:
        ValueError: If image does not have exactly 3 channels.
    """
    image_grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_grayscale = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image_grayscale


def binary_threshold(
    gray_image: np.ndarray,
    threshold: int = 127,
    method: str = "manual",
) -> np.ndarray:
    """
    Binarize a grayscale image, either with a manual threshold or with Otsu's
    automatic method.

    Args:
        gray_image (np.ndarray): Grayscale image, shape (H, W), dtype uint8.
        threshold (int): Manual threshold value, 0-255. Ignored when
            method="otsu". Defaults to 127.
        method (str): "manual" or "otsu". Defaults to "manual".

    Returns:
        np.ndarray: Binary image, shape (H, W), dtype uint8, values in {0, 255}.

    Raises:
        ValueError: If method is not "manual" or "otsu", or if threshold is
            not in the range 0-255 when method="manual".
    """
    if method == "manual":
        gray_image[gray_image>=127]=255 
        gray_image[gray_image<127]=0
        return gray_image
    elif method == "otsu":
        retrival, gray_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_OTSU)
        return gray_image
    else:
        gray_image
    
    


if __name__ == "__main__":
    import sys
    import cv2
    from pathlib import Path

    image_dir = Path(__file__).resolve().parent.parent
    image_path = sys.argv[1] if len(sys.argv) > 1 else str(image_dir / "rog.jpg")
    output_dir = image_dir / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    img = read_image(image_path, widht=640, height=640)
    img = to_grayscale(image=img)
    img = binary_threshold(img, threshold=127, method="manual")
    # print(img[0])
    show_image(image=img)

    # manual = binary_threshold(gray, threshold=127, method="manual")
    # otsu = binary_threshold(gray, method="otsu")

    # cv2.imwrite(str(output_dir / "01_gray.jpg"), gray)
    # cv2.imwrite(str(output_dir / "01_threshold_manual.jpg"), manual)
    # cv2.imwrite(str(output_dir / "01_threshold_otsu.jpg"), otsu)
    # print(f"saved grayscale & threshold results to {output_dir}")
