"""
Membaca dan menulis video untuk analisis frame demi frame.

Gunanya:
    Membaca potongan video dengan langkah frame, menulis video beranotasi
    dengan durasi yang sama dengan sumbernya, dan mengukur kecepatan proses.
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

import cv2
import numpy as np

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
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise FileNotFoundError(f"video tidak bisa dibuka: {path}")
        try:
            return cls(
                width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                fps=float(capture.get(cv2.CAP_PROP_FPS)) or 30.0,
                total_frames=int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            )
        finally:
            capture.release()

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
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise FileNotFoundError(f"video tidak bisa dibuka: {path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS)) or 30.0
    stride = max(int(stride), 1)
    try:
        if start:
            capture.set(cv2.CAP_PROP_POS_FRAMES, start)
        frame_number = start
        while end is None or frame_number < end:
            ok, frame = capture.read()
            if not ok:
                break
            if (frame_number - start) % stride == 0:
                yield frame_number, frame_number / fps, frame
            frame_number += 1
    finally:
        capture.release()


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
        self._writer: cv2.VideoWriter | None = None

    def __enter__(self) -> VideoWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self._writer = cv2.VideoWriter(
            str(self.path), fourcc, self.info.fps, (self.info.width, self.info.height)
        )
        if not self._writer.isOpened():
            raise OSError(f"video tidak bisa ditulis: {self.path} (codec {self.codec})")
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
        """Milidetik menunggu sebelum frame berikutnya, minimal 1 untuk cv2.waitKey."""
        remaining = max(int((self._deadline - time.perf_counter()) * 1000), 1)
        self._deadline += self.period
        return remaining
