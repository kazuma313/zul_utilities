"""
Membaca dan menulis video serta gambar untuk analisis frame demi frame.

Gunanya:
    Membaca potongan video dengan langkah frame, menulis video beranotasi
    dengan durasi yang sama dengan sumbernya, menyimpan dan membaca file
    gambar, dan mengukur kecepatan proses.
    Dengan `stride=3`, setiap frame ketiga diproses dan video hasil ditulis
    pada fps/3, jadi 10 detik video tetap menjadi 10 detik.
    Butuh extra vision: `pip install "zul[vision]"`.

Cara pakai:
    from zul.computer_vision.video import VideoInfo, VideoWriter, read_frames

    info = VideoInfo.from_path("raw_videos/interior.mp4")
    output = info.slice(start=1000, end=2500, stride=3)    # fps dan jumlah frame hasil

    with VideoWriter("outputs/interior_annotated.mp4", output) as writer:
        for frame_number, timestamp_s, frame in read_frames(
            "raw_videos/interior.mp4", start=1000, end=2500, stride=3
        ):
            writer.write(frame)
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from ..adapters import opencv

# --------------------------------------------------------------------------
# Informasi Video
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class VideoInfo:
    """Ukuran, kecepatan, dan jumlah frame sebuah video."""

    width: int
    height: int
    fps: float
    total_frames: int

    @classmethod
    def from_path(cls, path: str | Path) -> VideoInfo:
        """Info dari file video; FileNotFoundError jika video tidak bisa dibuka."""
        with opencv.VideoReader(path) as reader:
            return cls(reader.width, reader.height, reader.fps, reader.frame_count)

    def slice(
        self, start: int = 0, end: int | None = None, stride: int = 1
    ) -> VideoInfo:
        """Info video hasil: fps dibagi stride, agar durasinya sama dengan sumber."""
        stride = max(int(stride), 1)
        last = self.total_frames if end is None else min(end, self.total_frames)
        frames = max(0, (last - start + stride - 1) // stride)
        return replace(self, fps=self.fps / stride, total_frames=frames)


def read_frames(
    path: str | Path, start: int = 0, end: int | None = None, stride: int = 1
) -> Iterator[tuple[int, float, np.ndarray]]:
    """Frame sebagai `(nomor_frame_asli, detik, frame)`, dari `start` sampai `end`."""
    stride = max(int(stride), 1)
    with opencv.VideoReader(path) as reader:
        if start:
            reader.seek(start)
        frame_number = start
        while end is None or frame_number < end:
            frame = reader.read()
            if frame is None:
                break
            if (frame_number - start) % stride == 0:
                yield frame_number, frame_number / reader.fps, frame
            frame_number += 1


# --------------------------------------------------------------------------
# Menulis Video
# --------------------------------------------------------------------------


class VideoWriter:
    """Penulis mp4 yang ukurannya diambil dari VideoInfo."""

    def __init__(self, path: str | Path, info: VideoInfo, codec: str = "mp4v") -> None:
        self.path = Path(path)
        self.info = info
        self.codec = codec
        self.frames = 0
        self._writer: opencv.VideoFileWriter | None = None

    def __enter__(self) -> VideoWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = opencv.VideoFileWriter(
            self.path, self.info.fps, self.info.width, self.info.height, self.codec
        )
        return self

    def __exit__(self, *exc_info) -> bool:
        if self._writer is not None:
            self._writer.release()
        return False

    def write(self, frame: np.ndarray) -> None:
        if self._writer is None:
            raise RuntimeError("VideoWriter harus dipakai dengan `with`")
        self._writer.write(frame)
        self.frames += 1


# --------------------------------------------------------------------------
# File Gambar
# --------------------------------------------------------------------------


def save_image(path: str | Path, image: np.ndarray) -> Path:
    """Simpan frame BGR sebagai gambar; formatnya mengikuti ekstensi, misalnya .png.

    Folder tujuannya dibuat jika belum ada. Mengembalikan path file itu.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opencv.write_image(path, image)
    return path


def read_image(path: str | Path) -> np.ndarray:
    """Baca file gambar sebagai frame BGR; FileNotFoundError jika tidak bisa dibaca."""
    return opencv.read_image(path)


# --------------------------------------------------------------------------
# Kecepatan Proses
# --------------------------------------------------------------------------
#
# FPS dihitung dari rata-rata waktu proses beberapa frame terakhir, bukan
# dari satu frame, supaya angka di layar tidak melonjak naik dan turun.
# Pacer menahan pratinjau agar tidak lebih cepat dari video aslinya.
#


class FpsMeter:
    """Frame per detik dari rata-rata `window` frame terakhir."""

    def __init__(self, window: int = 30) -> None:
        self.window = window
        self._periods: deque[float] = deque(maxlen=window)
        self._started: float | None = None

    def start(self) -> None:
        self._started = time.perf_counter()

    def stop(self) -> float:
        """Catat lama satu frame dan kembalikan fps rata-rata saat ini."""
        if self._started is not None:
            self._periods.append(time.perf_counter() - self._started)
        return self.fps

    @property
    def fps(self) -> float:
        total = sum(self._periods)
        return len(self._periods) / total if total > 0 else 0.0

    @property
    def full(self) -> bool:
        return len(self._periods) == self.window


class Pacer:
    """Penahan pratinjau: setiap frame menunggu gilirannya, tidak pernah lebih cepat."""

    def __init__(self, fps: float) -> None:
        self.period = 1.0 / fps
        self._deadline = time.perf_counter() + self.period

    def wait_ms(self) -> int:
        """Milidetik menunggu sebelum frame berikutnya, minimal 1 untuk waitKey."""
        remaining = max(int((self._deadline - time.perf_counter()) * 1000), 1)
        self._deadline += self.period
        return remaining
