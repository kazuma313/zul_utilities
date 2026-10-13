"""
Deteksi orang dan keypoint pose dengan model RF-DETR.

Gunanya:
    Frame masuk, deteksi keluar sebagai Detections, wadah numpy biasa yang
    dibaca oleh semua modul lain, jadi modul itu tidak terikat pada library
    model mana pun. Model dan inference dijalankan lewat zul.adapters.rfdetr
    (Apache 2.0). Model keypoint memberi kotak orang dan 17 keypoint COCO
    sekaligus. Butuh extra detection: `pip install "zul[detection]"`.

Cara pakai:
    from zul.computer_vision.detection import detect, load_model, standardise_frame
    from zul.computer_vision.tracking import ByteTracker

    model = load_model("keypoint")
    tracker = ByteTracker(frame_rate=10)

    prepared, scale = standardise_frame(frame, size=640)
    people = detect(model, prepared, confidence=0.3).rescale(scale)
    people = tracker.update(people)          # hanya track yang sudah dikonfirmasi
    people.xyxy, people.tracker_id, people.keypoints_xy

ByteTracker juga bisa diimpor dari modul ini, untuk kode yang ditulis
sebelum tracking dipisahkan ke zul.computer_vision.tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

from ..adapters import opencv
from .geometry import non_max_suppression
from .tracking import ByteTracker

__all__ = ["ByteTracker", "Detections", "detect", "load_model", "standardise_frame"]

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


# --------------------------------------------------------------------------
# Model Dan Inference
# --------------------------------------------------------------------------
#
# Satu ukuran input untuk semua model: frame diperkecil sekali
# ke ukuran kerja model, dan satu faktor skala mengembalikan
# koordinatnya. Pada proyek toko, langkah ini menaikkan
# kecepatan dari 8,3 menjadi 13,9 frame per detik.
#
# RF-DETR kadang memberi dua kotak yang hampir sama untuk satu orang,
# di proyek toko 9 sampai 12 pasang dari 30 frame. Karena itu hasil
# detect disaring dulu dengan non-max suppression di IoU 0,7.
#


def load_model(
    model: str = "keypoint",
    weights: str | Path | None = None,
    half: bool = True,
    device: str | None = None,
) -> Any:
    """Muat model RF-DETR: keypoint, nano, small, medium, atau large.

    `keypoint` memberi kotak orang dan 17 keypoint COCO. Model lain hanya
    memberi kotak, untuk 80 kelas COCO. Tanpa `weights`, bobot diunduh ke
    folder cache RF-DETR saat pertama dipakai. `half` memakai float16 di GPU.
    """
    from ..adapters import rfdetr as rfdetr_adapter

    return rfdetr_adapter.load_model(model, weights, half=half, device=device)


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
    confidence: float = 0.5,
    classes: list[int] | None = None,
    nms_iou: float | None = 0.7,
) -> Detections:
    """Inference satu frame BGR. Model keypoint juga mengisi keypoint per orang.

    `classes` menyaring id kelas COCO, misalnya `[1]` untuk orang. Kotak
    yang IoU-nya dengan kotak berskor lebih tinggi melebihi `nms_iou`
    dibuang; isi None untuk mematikan penyaringan ini.
    """
    from ..adapters import rfdetr as rfdetr_adapter

    found = Detections.from_arrays(rfdetr_adapter.predict(model, image, confidence))
    if classes is not None:
        found = found[np.isin(found.class_id, classes)]
    if nms_iou is not None and len(found) > 1:
        found = found[non_max_suppression(found.xyxy, found.confidence, nms_iou)]
    return found
