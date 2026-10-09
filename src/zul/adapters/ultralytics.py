"""
Adapter ultralytics: model YOLO, inference, tracking, dan unduhan bobot.

Gunanya:
    Satu-satunya file Zul yang mengimpor ultralytics. Hasil inference keluar
    sebagai array NumPy biasa, dan tracker ByteTrack dipakai lewat kelas
    turunan ZulBYTETracker, jadi perilakunya bisa diubah di sini tanpa
    mengubah ultralytics. Butuh extra yolo: `pip install "zul[yolo]"`.

Cara pakai:
    from zul.adapters import ultralytics as yolo

    model = yolo.load_model("models/yolo11m-pose.pt")
    arrays = yolo.predict(model, frame, confidence=0.2)    # dict array NumPy
    tracker = yolo.create_tracker(frame_rate=10)
    rows = yolo.track(tracker, arrays["xyxy"], arrays["confidence"], arrays["class_id"])

Zul memakai dua bagian internal ultralytics: BYTETracker dan
attempt_download_asset. Keduanya bisa berubah antar versi, karena itu
versi ultralytics dikunci di pyproject.toml dan diuji di tests.

Lisensi ultralytics adalah AGPL-3.0. ZulBYTETracker turunan dari kode
AGPL, jadi perubahan di kelas itu ikut aturan AGPL saat dibagikan.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from ultralytics import YOLO, YOLOWorld
from ultralytics.trackers.byte_tracker import BYTETracker
from ultralytics.utils.downloads import attempt_download_asset

CLIP_INSTALL_HINT = (
    "YOLO-World butuh CLIP: pip install ftfy regex "
    '"clip @ git+https://github.com/ultralytics/CLIP.git"'
)

# --------------------------------------------------------------------------
# Model Dan Inference
# --------------------------------------------------------------------------


def load_model(weights: str | Path, prompts: list[str] | None = None) -> Any:
    """Model YOLO atau model pose; dengan `prompts`, YOLO-World berkelas teks.

    Objek yang dikembalikan hanya untuk diteruskan ke `predict`.

    Raises:
        ImportError: `prompts` diisi tetapi paket CLIP belum ter-install.
            Tanpa pemeriksaan ini, ultralytics meng-install CLIP sendiri dari
            git saat pertama dipakai.
    """
    if not prompts:
        return YOLO(str(weights))
    if importlib.util.find_spec("clip") is None:
        raise ImportError(CLIP_INSTALL_HINT)
    model = YOLOWorld(str(weights))
    model.set_classes(list(prompts))
    return model


def predict(
    model: Any,
    image: np.ndarray,
    confidence: float,
    iou: float = 0.5,
    imgsz: int = 640,
    device: str | None = None,
    classes: list[int] | None = None,
) -> dict[str, np.ndarray | None]:
    """Inference satu frame, hasilnya sebagai array NumPy (lihat `result_arrays`)."""
    options: dict[str, Any] = {
        "conf": confidence,
        "iou": iou,
        "imgsz": imgsz,
        "verbose": False,
    }
    if device is not None:
        options["device"] = device
    if classes is not None:
        options["classes"] = classes
    return result_arrays(model.predict(image, **options)[0])


def result_arrays(result: Any) -> dict[str, np.ndarray | None]:
    """Satu `Results` ultralytics sebagai dict array NumPy.

    Kuncinya xyxy `(n, 4)`, confidence `(n,)`, class_id `(n,)`, serta
    keypoints_xy `(n, 17, 2)` dan keypoints_conf `(n, 17)` untuk model
    pose, atau None untuk model lain.
    """
    arrays: dict[str, np.ndarray | None] = {
        "xyxy": np.empty((0, 4)),
        "confidence": np.empty(0),
        "class_id": np.empty(0, dtype=int),
        "keypoints_xy": None,
        "keypoints_conf": None,
    }
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return arrays
    arrays["xyxy"] = boxes.xyxy.cpu().numpy().astype(np.float64)
    arrays["confidence"] = boxes.conf.cpu().numpy().astype(np.float64)
    arrays["class_id"] = boxes.cls.cpu().numpy().astype(int)
    keypoints = getattr(result, "keypoints", None)
    if keypoints is not None and keypoints.xy is not None and len(keypoints.xy):
        arrays["keypoints_xy"] = keypoints.xy.cpu().numpy().astype(np.float64)
        if keypoints.conf is not None:
            arrays["keypoints_conf"] = keypoints.conf.cpu().numpy().astype(np.float64)
    return arrays


# --------------------------------------------------------------------------
# Tracking
# --------------------------------------------------------------------------
#
# BYTETracker membaca deteksi dari objek mirip Results: conf, cls, xywh,
# xyxy, dan potongan boolean. TrackInput menyediakan bentuk itu dari
# array NumPy, jadi Zul tidak perlu membuat Results sungguhan.
#
# ZulBYTETracker adalah tempat mengubah perilaku tracker. Turunkan method
# di sana, misalnya get_dists yang menentukan cara mencocokkan deteksi
# dengan track, alih-alih mengubah file di dalam paket ultralytics.
#


class TrackInput:
    """Deteksi satu frame dalam bentuk yang dibaca BYTETracker."""

    def __init__(self, xyxy: np.ndarray, conf: np.ndarray, cls: np.ndarray) -> None:
        self.xyxy = np.asarray(xyxy, dtype=np.float32).reshape(-1, 4)
        self.conf = np.asarray(conf, dtype=np.float32)
        self.cls = np.asarray(cls, dtype=np.float32)
        wh = self.xyxy[:, 2:4] - self.xyxy[:, 0:2]
        self.xywh = np.concatenate([self.xyxy[:, 0:2] + wh / 2, wh], axis=1)

    def __len__(self) -> int:
        return len(self.conf)

    def __getitem__(self, index: Any) -> TrackInput:
        return TrackInput(self.xyxy[index], self.conf[index], self.cls[index])


class ZulBYTETracker(BYTETracker):
    """BYTETracker milik ultralytics, dengan Zul sebagai kelas turunannya.

    Belum ada method yang diubah. Untuk mengubah perilaku tracker, turunkan
    method BYTETracker di kelas ini, misalnya `get_dists` atau `init_track`.
    """


def create_tracker(
    frame_rate: float,
    high_threshold: float,
    low_threshold: float,
    new_track_threshold: float,
    lost_track_buffer: int,
    match_threshold: float,
) -> ZulBYTETracker:
    """Tracker baru; `lost_track_buffer` dalam frame pada 30 FPS, lalu disesuaikan."""
    args = SimpleNamespace(
        track_high_thresh=high_threshold,
        track_low_thresh=low_threshold,
        new_track_thresh=new_track_threshold,
        track_buffer=int(round(lost_track_buffer * frame_rate / 30.0)),
        match_thresh=match_threshold,
        fuse_score=True,
    )
    return ZulBYTETracker(args)


def track(
    tracker: ZulBYTETracker,
    xyxy: np.ndarray,
    confidence: np.ndarray,
    class_id: np.ndarray,
) -> np.ndarray:
    """Maju satu frame. Mengembalikan baris track yang aktif, `(m, 8)`.

    Kolomnya x1, y1, x2, y2, id track, skor, kelas, dan indeks baris
    deteksi asalnya. Frame tanpa deteksi tetap harus diteruskan, supaya
    tracker tahu waktu berjalan.
    """
    rows = tracker.update(TrackInput(xyxy, confidence, class_id))
    return np.asarray(rows, dtype=np.float64).reshape(-1, 8)


# --------------------------------------------------------------------------
# Unduhan Bobot
# --------------------------------------------------------------------------


def download_asset(path: str | Path) -> None:
    """Unduh file bobot rilis ultralytics ke `path`, jika namanya dikenal."""
    attempt_download_asset(str(path))
