"""
Deteksi orang, pose, dan tracking dengan model YOLO.

Gunanya:
    Frame masuk, deteksi yang punya id track keluar. Hasilnya berupa
    Detections, wadah numpy biasa yang dibaca oleh semua modul lain,
    jadi modul itu tidak terikat pada library model mana pun. Model,
    inference, dan tracker dijalankan lewat zul.adapters.ultralytics.
    Butuh extra yolo: `pip install "zul[yolo]"`.

Cara pakai:
    from zul.computer_vision.detection import (
        ByteTracker, detect, load_model, standardise_frame,
    )

    model = load_model("models/yolo11m-pose.pt")
    tracker = ByteTracker(frame_rate=10)

    prepared, scale = standardise_frame(frame, size=640)
    people = detect(model, prepared, confidence=0.2).rescale(scale)
    people = tracker.update(people)          # hanya track yang sudah dikonfirmasi
    people.xyxy, people.tracker_id, people.keypoints_xy

YOLO-World mendeteksi kelas dari teks, misalnya ["person", "person wearing
a red apron"], tetapi butuh paket CLIP dari ultralytics (lihat load_model).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

from ..adapters import opencv

# --------------------------------------------------------------------------
# Wadah Deteksi
# --------------------------------------------------------------------------
#
# Semua kolom sejajar per baris: baris ke-i di xyxy, confidence, id track,
# dan keypoint ialah orang yang sama. Indeks boolean maupun daftar indeks
# memotong semua kolom sekaligus, jadi pasangan itu tak pernah bergeser.
#


@dataclass
class Detections:
    """Deteksi satu frame sebagai array numpy yang sejajar per baris."""

    xyxy: np.ndarray = field(default_factory=lambda: np.empty((0, 4)))
    confidence: np.ndarray = field(default_factory=lambda: np.empty(0))
    class_id: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=int))
    tracker_id: np.ndarray | None = None
    keypoints_xy: np.ndarray | None = None
    keypoints_conf: np.ndarray | None = None

    def __len__(self) -> int:
        return len(self.xyxy)

    def __getitem__(self, index: Any) -> Detections:
        def take(values: np.ndarray | None) -> np.ndarray | None:
            return None if values is None else values[index]

        return Detections(
            xyxy=self.xyxy[index],
            confidence=self.confidence[index],
            class_id=self.class_id[index],
            tracker_id=take(self.tracker_id),
            keypoints_xy=take(self.keypoints_xy),
            keypoints_conf=take(self.keypoints_conf),
        )

    def rescale(self, scale: float) -> Detections:
        """Koordinat dari frame yang diperkecil dikembalikan ke ukuran frame asli."""
        if scale == 1.0 or len(self) == 0:
            return self
        keypoints = None if self.keypoints_xy is None else self.keypoints_xy / scale
        return replace(self, xyxy=self.xyxy / scale, keypoints_xy=keypoints)

    @classmethod
    def from_arrays(cls, arrays: dict[str, np.ndarray | None]) -> Detections:
        """Deteksi dari dict array, misalnya hasil adapter model."""
        return cls(
            xyxy=arrays["xyxy"],
            confidence=arrays["confidence"],
            class_id=arrays["class_id"],
            keypoints_xy=arrays.get("keypoints_xy"),
            keypoints_conf=arrays.get("keypoints_conf"),
        )

    @classmethod
    def from_ultralytics(cls, result: Any) -> Detections:
        """Deteksi dari satu `Results` ultralytics, plus keypoint dari model pose."""
        from ..adapters import ultralytics as yolo

        return cls.from_arrays(yolo.result_arrays(result))


# --------------------------------------------------------------------------
# Model Dan Inference
# --------------------------------------------------------------------------
#
# Satu ukuran input untuk semua model: frame diperkecil sekali
# ke ukuran latih model, dan satu faktor skala mengembalikan
# koordinatnya. Pada proyek toko, langkah ini menaikkan
# kecepatan dari 8,3 menjadi 13,9 frame per detik.
#


def load_model(weights: str | Path, prompts: list[str] | None = None) -> Any:
    """Muat model YOLO atau model pose; dengan `prompts`, YOLO-World berkelas teks.

    YOLO-World butuh paket `clip` dari ultralytics. Tanpa paket itu,
    fungsi ini berhenti dengan ImportError berisi cara meng-install-nya.
    """
    from ..adapters import ultralytics as yolo

    return yolo.load_model(weights, prompts)


def standardise_frame(image: np.ndarray, size: int = 640) -> tuple[np.ndarray, float]:
    """Perkecil frame ke `size` piksel di sisi terpanjang, dengan rasio tetap.

    Mengembalikan frame dan skalanya. Frame yang sudah lebih kecil tidak
    diperbesar, skalanya 1.
    """
    height, width = image.shape[:2]
    scale = size / max(width, height)
    if scale >= 1.0:
        return image, 1.0
    resized = opencv.resize(image, round(width * scale), round(height * scale))
    return resized, scale


def detect(
    model: Any,
    image: np.ndarray,
    confidence: float = 0.20,
    iou: float = 0.5,
    imgsz: int = 640,
    device: str | None = None,
    classes: list[int] | None = None,
) -> Detections:
    """Inference satu frame. Model pose mengisi `keypoints_xy` dan `keypoints_conf`.

    Confidence bawaan 0,20 lebih rendah dari bawaan ultralytics (0,25),
    karena skor YOLO-World lebih dingin daripada skor detektor COCO.
    """
    from ..adapters import ultralytics as yolo

    arrays = yolo.predict(model, image, confidence, iou, imgsz, device, classes)
    return Detections.from_arrays(arrays)


# --------------------------------------------------------------------------
# Tracking
# --------------------------------------------------------------------------
#
# Ambang bawaan ultralytics mengandaikan skor detektor COCO lebih dari 0,9.
# Untuk skor YOLO-World yang lebih rendah, ambang 0,25 dan 0,35 menaikkan
# jumlah deteksi di satu frame dari proyek toko dari 2 menjadi 6 orang.
#
# Track baru hanya dikembalikan setelah cocok di frame berikutnya, jadi satu
# deteksi yang muncul sekali tidak pernah menjadi orang tambahan. Hitungan
# aturan selalu memakai id track, bukan jumlah kotak di setiap frame.
#


class ByteTracker:
    """ByteTrack: id yang bertahan antar frame untuk setiap deteksi."""

    def __init__(
        self,
        frame_rate: float = 30.0,
        high_threshold: float = 0.35,
        low_threshold: float = 0.1,
        new_track_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        match_threshold: float = 0.8,
    ) -> None:
        from ..adapters import ultralytics as yolo

        self._yolo = yolo
        self._tracker = yolo.create_tracker(
            frame_rate,
            high_threshold,
            low_threshold,
            new_track_threshold,
            lost_track_buffer,
            match_threshold,
        )

    def update(self, detections: Detections) -> Detections:
        """Deteksi frame ini yang punya id track; yang belum dikonfirmasi dibuang."""
        rows = self._yolo.track(
            self._tracker,
            detections.xyxy,
            detections.confidence,
            detections.class_id,
        )
        if len(rows) == 0:
            empty = detections[np.zeros(len(detections), dtype=bool)]
            return replace(empty, tracker_id=np.empty(0, dtype=int))
        tracked = detections[rows[:, 7].astype(int)]
        tracked.xyxy = rows[:, :4].astype(np.float64)
        tracked.tracker_id = rows[:, 4].astype(int)
        return tracked
