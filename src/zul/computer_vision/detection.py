"""
Deteksi orang, pose, dan tracking dengan model YOLO dari ultralytics.

Gunanya:
    Frame masuk, deteksi yang punya id track keluar. Hasilnya berupa
    Detections, wadah numpy biasa yang dibaca oleh semua modul aturan,
    jadi aturan tidak terikat pada ultralytics. Model pose juga mendeteksi
    orang, jadi satu model pose cukup untuk kotak dan arah hadap sekaligus.
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

import importlib.util
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import cv2
import numpy as np

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
    def from_ultralytics(cls, result: Any) -> Detections:
        """Deteksi dari satu `Results` ultralytics, plus keypoint dari model pose."""
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return cls()
        detections = cls(
            xyxy=boxes.xyxy.cpu().numpy().astype(np.float64),
            confidence=boxes.conf.cpu().numpy().astype(np.float64),
            class_id=boxes.cls.cpu().numpy().astype(int),
        )
        keypoints = getattr(result, "keypoints", None)
        if keypoints is not None and keypoints.xy is not None and len(keypoints.xy):
            detections.keypoints_xy = keypoints.xy.cpu().numpy().astype(np.float64)
            if keypoints.conf is not None:
                detections.keypoints_conf = (
                    keypoints.conf.cpu().numpy().astype(np.float64)
                )
        return detections


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
    ultralytics akan meng-install-nya sendiri dari git saat pertama dipakai,
    jadi fungsi ini berhenti lebih dulu dengan pesan cara meng-install-nya.
    """
    from ultralytics import YOLO, YOLOWorld

    if not prompts:
        return YOLO(str(weights))
    if importlib.util.find_spec("clip") is None:
        raise ImportError(
            "YOLO-World butuh CLIP: pip install ftfy regex "
            '"clip @ git+https://github.com/ultralytics/CLIP.git"'
        )
    model = YOLOWorld(str(weights))
    model.set_classes(list(prompts))
    return model


def standardise_frame(image: np.ndarray, size: int = 640) -> tuple[np.ndarray, float]:
    """Perkecil frame ke `size` piksel di sisi terpanjang, dengan rasio tetap.

    Mengembalikan frame dan skalanya. Frame yang sudah lebih kecil tidak
    diperbesar, skalanya 1.
    """
    height, width = image.shape[:2]
    scale = size / max(width, height)
    if scale >= 1.0:
        return image, 1.0
    resized = cv2.resize(
        image,
        (round(width * scale), round(height * scale)),
        interpolation=cv2.INTER_LINEAR,
    )
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
    options = {"conf": confidence, "iou": iou, "imgsz": imgsz, "verbose": False}
    if device is not None:
        options["device"] = device
    if classes is not None:
        options["classes"] = classes
    result = model.predict(image, **options)[0]
    return Detections.from_ultralytics(result)


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


class _TrackInput:
    """Bentuk yang dibaca BYTETracker: conf, cls, xywh, xyxy, dan potongan boolean."""

    def __init__(self, xyxy: np.ndarray, conf: np.ndarray, cls: np.ndarray) -> None:
        self.xyxy = np.asarray(xyxy, dtype=np.float32).reshape(-1, 4)
        self.conf = np.asarray(conf, dtype=np.float32)
        self.cls = np.asarray(cls, dtype=np.float32)
        wh = self.xyxy[:, 2:4] - self.xyxy[:, 0:2]
        self.xywh = np.concatenate([self.xyxy[:, 0:2] + wh / 2, wh], axis=1)

    def __len__(self) -> int:
        return len(self.conf)

    def __getitem__(self, index: Any) -> _TrackInput:
        return _TrackInput(self.xyxy[index], self.conf[index], self.cls[index])


class ByteTracker:
    """ByteTrack dari ultralytics: id yang bertahan antar frame untuk setiap deteksi."""

    def __init__(
        self,
        frame_rate: float = 30.0,
        high_threshold: float = 0.35,
        low_threshold: float = 0.1,
        new_track_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        match_threshold: float = 0.8,
    ) -> None:
        from ultralytics.trackers.byte_tracker import BYTETracker

        args = SimpleNamespace(
            track_high_thresh=high_threshold,
            track_low_thresh=low_threshold,
            new_track_thresh=new_track_threshold,
            track_buffer=int(round(lost_track_buffer * frame_rate / 30.0)),
            match_thresh=match_threshold,
            fuse_score=True,
        )
        self._tracker = BYTETracker(args)

    def update(self, detections: Detections) -> Detections:
        """Deteksi frame ini yang punya id track; yang belum dikonfirmasi dibuang."""
        if len(detections) == 0:
            self._tracker.update(
                _TrackInput(np.empty((0, 4)), np.empty(0), np.empty(0))
            )
            return replace(detections, tracker_id=np.empty(0, dtype=int))
        rows = self._tracker.update(
            _TrackInput(detections.xyxy, detections.confidence, detections.class_id)
        )
        if len(rows) == 0:
            empty = detections[np.zeros(len(detections), dtype=bool)]
            return replace(empty, tracker_id=np.empty(0, dtype=int))
        index = rows[:, 7].astype(int)
        tracked = detections[index]
        tracked.xyxy = rows[:, :4].astype(np.float64)
        tracked.tracker_id = rows[:, 4].astype(int)
        return tracked
