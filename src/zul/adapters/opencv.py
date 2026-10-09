"""
Adapter OpenCV: menggambar, mengubah ukuran, membaca dan menulis gambar serta video.

Gunanya:
    Semua pemakaian cv2 di Zul lewat fungsi-fungsi di sini. Setiap fungsi
    menerima dan mengembalikan array NumPy berformat BGR, koordinat sebagai
    tuple int, dan warna sebagai tuple BGR, jadi modul gambar dan video
    tidak perlu tahu nama konstanta OpenCV seperti LINE_AA.

Cara pakai:
    from zul.adapters import opencv

    opencv.line(scene, (0, 0), (100, 50), (0, 0, 255), thickness=2)
    small = opencv.resize(frame, 640, 360)
    with opencv.VideoReader("videos/toko.mp4") as reader:
        frame = reader.read()

Semua garis digambar dengan anti-aliasing, dan teks dengan font
FONT_HERSHEY_SIMPLEX. Untuk mengganti keduanya, ubah file ini saja.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np

Point = tuple[int, int]
BGR = tuple[int, int, int]

FONT = cv2.FONT_HERSHEY_SIMPLEX
SMOOTH = cv2.LINE_AA

COLORMAPS = {
    "jet": cv2.COLORMAP_JET,
    "turbo": cv2.COLORMAP_TURBO,
    "inferno": cv2.COLORMAP_INFERNO,
    "viridis": cv2.COLORMAP_VIRIDIS,
    "hot": cv2.COLORMAP_HOT,
}

INTERPOLATIONS = {
    "linear": cv2.INTER_LINEAR,
    "nearest": cv2.INTER_NEAREST,
    "area": cv2.INTER_AREA,
}

# --------------------------------------------------------------------------
# Teks Dan Garis
# --------------------------------------------------------------------------


def text_size(text: str, scale: float, thickness: int) -> tuple[int, int]:
    """Lebar dan tinggi teks dalam piksel, tanpa bagian di bawah garis dasar."""
    (width, height), _ = cv2.getTextSize(text, FONT, scale, thickness)
    return width, height


def put_text(
    image: np.ndarray,
    text: str,
    origin: Point,
    scale: float,
    color: BGR,
    thickness: int,
) -> None:
    """Tulis teks dengan `origin` di kiri garis dasarnya."""
    cv2.putText(image, text, origin, FONT, scale, color, thickness, SMOOTH)


def line(
    image: np.ndarray, start: Point, end: Point, color: BGR, thickness: int
) -> None:
    """Satu garis lurus."""
    cv2.line(image, start, end, color, thickness, SMOOTH)


def arrow(
    image: np.ndarray,
    start: Point,
    tip: Point,
    color: BGR,
    thickness: int,
    tip_ratio: float,
) -> None:
    """Panah dari `start` ke `tip`; `tip_ratio` adalah panjang kepala panah."""
    cv2.arrowedLine(image, start, tip, color, thickness, SMOOTH, tipLength=tip_ratio)


def rectangle(
    image: np.ndarray, top_left: Point, bottom_right: Point, color: BGR, thickness: int
) -> None:
    """Persegi panjang; `thickness` -1 mengisinya penuh."""
    line_type = SMOOTH if thickness > 0 else cv2.LINE_8
    cv2.rectangle(image, top_left, bottom_right, color, thickness, line_type)


def circle(
    image: np.ndarray,
    centre: Point,
    radius: int,
    color: BGR | float,
    thickness: int = -1,
) -> None:
    """Lingkaran; `thickness` -1 mengisinya penuh. Bisa di array float."""
    value = (color,) if isinstance(color, float | int) else color
    cv2.circle(image, centre, radius, value, thickness)


def polylines(
    image: np.ndarray,
    shapes: Sequence[np.ndarray],
    closed: bool,
    color: BGR,
    thickness: int,
) -> None:
    """Garis yang menyambung titik-titik setiap bentuk, tertutup jika `closed`."""
    curves = [np.asarray(shape, dtype=np.int32).reshape(-1, 1, 2) for shape in shapes]
    cv2.polylines(image, curves, closed, color, thickness, SMOOTH)


def fill_polygons(
    image: np.ndarray, shapes: Sequence[np.ndarray], color: BGR | Sequence[int]
) -> None:
    """Isi penuh setiap poligon dengan satu warna."""
    polygons = [np.asarray(shape, dtype=np.int32).reshape(-1, 2) for shape in shapes]
    cv2.fillPoly(image, polygons, tuple(int(channel) for channel in color))


# --------------------------------------------------------------------------
# Operasi Gambar
# --------------------------------------------------------------------------


def blend(overlay: np.ndarray, alpha: float, image: np.ndarray) -> None:
    """Campur `overlay` ke `image` langsung: alpha × overlay + (1 − alpha) × image."""
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, dst=image)


def resize(
    image: np.ndarray, width: int, height: int, interpolation: str = "linear"
) -> np.ndarray:
    """Gambar baru `width` × `height`; interpolasi linear, nearest, atau area."""
    return cv2.resize(
        image, (int(width), int(height)), interpolation=INTERPOLATIONS[interpolation]
    )


def box_blur(image: np.ndarray, size: int) -> np.ndarray:
    """Rata-rata setiap piksel dengan tetangganya dalam kotak `size` × `size`."""
    return cv2.blur(image, (size, size))


def gaussian_blur(image: np.ndarray, sigma: float) -> np.ndarray:
    """Blur Gaussian dengan simpangan baku `sigma` piksel."""
    return cv2.GaussianBlur(image, (0, 0), sigmaX=sigma)


def bitwise_and(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """AND per bit antara dua gambar berukuran sama, misalnya gambar dan masker."""
    return cv2.bitwise_and(first, second)


def colorize(level: np.ndarray, colormap: str = "jet") -> np.ndarray:
    """Gambar BGR dari array uint8 satu kanal, memakai peta warna bernama."""
    if colormap not in COLORMAPS:
        names = ", ".join(sorted(COLORMAPS))
        raise ValueError(
            f"colormap '{colormap}' tidak dikenal; pilih salah satu: {names}"
        )
    return cv2.applyColorMap(level, COLORMAPS[colormap])


# --------------------------------------------------------------------------
# File Gambar
# --------------------------------------------------------------------------


def read_image(path: str | Path) -> np.ndarray:
    """Baca file gambar sebagai array BGR.

    Raises:
        FileNotFoundError: file tidak ada atau bukan gambar yang bisa dibaca.
    """
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"gambar tidak bisa dibaca: {path}")
    return image


def write_image(path: str | Path, image: np.ndarray) -> None:
    """Simpan array BGR sebagai file gambar; formatnya mengikuti ekstensi."""
    if not cv2.imwrite(str(path), image):
        raise OSError(f"gambar tidak bisa ditulis: {path}")


# --------------------------------------------------------------------------
# Video
# --------------------------------------------------------------------------
#
# Pembaca dan penulis video dibungkus sebagai context manager, sehingga
# file selalu ditutup, termasuk saat terjadi error. Video yang gagal
# dibuka langsung menjadi error Python biasa, bukan objek kosong.
#


class VideoReader:
    """Pembaca video frame demi frame, dengan ukuran dan FPS-nya."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._capture = cv2.VideoCapture(str(path))
        if not self._capture.isOpened():
            raise FileNotFoundError(f"video tidak bisa dibuka: {path}")
        self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(self._capture.get(cv2.CAP_PROP_FPS)) or 30.0
        self.frame_count = int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT))

    def __enter__(self) -> VideoReader:
        return self

    def __exit__(self, *exc_info) -> bool:
        self.release()
        return False

    def seek(self, frame_number: int) -> None:
        """Lompat ke frame ke-`frame_number`, mulai dari 0."""
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

    def read(self) -> np.ndarray | None:
        """Frame berikutnya, atau None jika video sudah habis."""
        ok, frame = self._capture.read()
        return frame if ok else None

    def release(self) -> None:
        self._capture.release()


class VideoFileWriter:
    """Penulis video dengan ukuran dan FPS tetap."""

    def __init__(
        self, path: str | Path, fps: float, width: int, height: int, codec: str = "mp4v"
    ) -> None:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        self._writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
        if not self._writer.isOpened():
            raise OSError(f"video tidak bisa ditulis: {path} (codec {codec})")

    def write(self, frame: np.ndarray) -> None:
        self._writer.write(frame)

    def release(self) -> None:
        self._writer.release()
