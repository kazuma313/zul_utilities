"""
Detektor orang: frame BGR masuk, `Detections` keluar.

Gunanya:
    Pipeline hanya memanggil `detector(frame)`, jadi model bisa diganti
    tanpa mengubah pipeline: RF-DETR lewat `zul.computer_vision.detection`
    untuk dipakai sungguhan, atau detektor palsu di test. Frame diperkecil
    ke `DETECT_SIZE` sebelum inference, lalu kotaknya dikembalikan ke ukuran
    frame asli.

Cara pakai:
    from cctv.detector import load_detector

    detector = load_detector(scene.settings)      # memuat RF-DETR
    people = detector(frame)                      # Detections untuk satu frame
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from zul.computer_vision.detection import (
    Detections,
    detect,
    load_model,
    standardise_frame,
)

from .settings import Settings

Detector = Callable[[np.ndarray], Detections]


@dataclass
class RfDetrDetector:
    """RF-DETR yang hanya mengembalikan kelas orang."""

    model: Any
    confidence: float
    size: int
    person_class_id: int

    def __call__(self, frame: np.ndarray) -> Detections:
        prepared, scale = standardise_frame(frame, self.size)
        found = detect(
            self.model,
            prepared,
            confidence=self.confidence,
            classes=[self.person_class_id],
        )
        return found.rescale(scale)


def load_detector(settings: Settings) -> RfDetrDetector:
    """Muat RF-DETR sesuai pengaturan. Bobot diunduh saat pertama dipakai."""
    model = load_model(
        settings.MODEL,
        weights=settings.WEIGHTS or None,
        half=settings.HALF,
        device=settings.DEVICE or None,
    )
    return RfDetrDetector(
        model=model,
        confidence=settings.CONFIDENCE,
        size=settings.DETECT_SIZE,
        person_class_id=settings.PERSON_CLASS_ID,
    )
