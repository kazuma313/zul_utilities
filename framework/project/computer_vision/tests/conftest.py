"""
Data buatan untuk test: config scene, video sintetis, dan detektor palsu.

Gunanya:
    Test tidak butuh video asli, bobot model, atau GPU. Video dibuat dari
    frame polos, dan detektor palsu mengembalikan kotak yang posisinya
    ditentukan test untuk setiap frame.

Cara pakai:
    def test_contoh(scene_files, fake_video):
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from zul.computer_vision.detection import Detections

PROJECT = Path(__file__).resolve().parents[1]
BASE_CONFIG = PROJECT / "configs" / "base.yaml"

SCENE_YAML = """\
SOURCE_VIDEO_PATH: {video}
IGNORE_POLYGONS: []
ZONES:
  - name: depan
    polygon: [[0, 0], [320, 0], [320, 90], [0, 90]]
LINES:
  - name: pintu
    start: [0, 120]
    end: [320, 120]
settings:
  PROXIMITY_METRES: {proximity}
"""

Boxes = Callable[[int], list[list[float]]]


class FakeDetector:
    """Detektor palsu: `boxes(n)` menentukan kotak untuk panggilan ke-n."""

    def __init__(self, boxes: Boxes) -> None:
        self.boxes = boxes
        self.calls = 0

    def __call__(self, frame: np.ndarray) -> Detections:
        found = np.asarray(self.boxes(self.calls), dtype=np.float64).reshape(-1, 4)
        self.calls += 1
        return Detections(
            xyxy=found,
            confidence=np.full(len(found), 0.9),
            class_id=np.ones(len(found), dtype=int),
        )


def people(boxes: list[list[float]], ids: list[int]) -> Detections:
    """Deteksi yang sudah dilacak, untuk menguji aturan tanpa tracker."""
    xyxy = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    return Detections(
        xyxy=xyxy,
        confidence=np.full(len(xyxy), 0.9),
        class_id=np.ones(len(xyxy), dtype=int),
        tracker_id=np.asarray(ids, dtype=int),
    )


@pytest.fixture
def write_scene(tmp_path) -> Callable[..., Path]:
    """Tulis config kamera sementara dengan satu zona dan satu garis."""

    def write(video: Path | str = "videos/contoh.mp4", proximity: float = 0.0) -> Path:
        path = tmp_path / "contoh.yaml"
        path.write_text(
            SCENE_YAML.format(video=Path(video).as_posix(), proximity=proximity),
            encoding="utf-8",
        )
        return path

    return write


@pytest.fixture
def fake_video(tmp_path) -> Path:
    """Video sintetis 40 frame, 320x240, 10 fps."""
    from zul.computer_vision.video import VideoInfo, VideoWriter

    path = tmp_path / "videos" / "contoh.mp4"
    path.parent.mkdir()
    with VideoWriter(path, VideoInfo(320, 240, 10.0, 40)) as writer:
        for _ in range(40):
            writer.write(np.full((240, 320, 3), 80, dtype=np.uint8))
    return path
