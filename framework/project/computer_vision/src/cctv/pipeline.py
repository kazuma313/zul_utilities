"""
Perulangan frame: deteksi, pelacakan, aturan scene, gambar, dan keluaran.

Gunanya:
    `run` membaca potongan video, menghitamkan area yang diabaikan, mencari
    orang, memberi id track, menjalankan aturan scene, lalu menulis video
    beranotasi, pratinjau, CSV, dan ringkasan JSON. Detektor diberikan dari
    luar, jadi pipeline yang sama dipakai dengan RF-DETR sungguhan maupun
    detektor palsu di test.

    Keluaran di `output_dir/<kamera>/`:
        annotated.mp4    video beranotasi (mode save atau both)
        crossings.csv    setiap lintasan garis
        visits.csv       setiap kunjungan zona
        attention.csv    setiap rentang menghadap target zona
        contacts.csv     setiap kontak antar orang (jika PROXIMITY_METRES > 0)
        summary.json     angka akhir per garis dan per zona

Cara pakai:
    from cctv.detector import load_detector
    from cctv.pipeline import RunOptions, run

    summary = run(scene, load_detector(scene.settings), RunOptions(mode="save"))
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from zul.computer_vision.distance import Contact
from zul.computer_vision.masks import apply_mask, polygon_mask
from zul.computer_vision.report import RecordWriter
from zul.computer_vision.timers import Spell, ZoneVisit
from zul.computer_vision.tracking import ByteTracker
from zul.computer_vision.video import (
    FpsMeter,
    Preview,
    VideoInfo,
    VideoWriter,
    read_frames,
)

from .analytics import Crossing, Finished, SceneAnalytics
from .detector import Detector
from .render import Overlay
from .settings import SceneConfig

Mode = Literal["live", "save", "both"]


@dataclass(frozen=True)
class RunOptions:
    """Bagian video yang diproses dan bentuk keluarannya."""

    mode: Mode = "save"
    start: int = 0
    end: int | None = None
    stride: int = 1
    output_dir: Path = Path("outputs")


def run(scene: SceneConfig, detector: Detector, options: RunOptions) -> dict:
    """Proses satu kamera; mengembalikan ringkasan yang juga ditulis ke summary.json.

    Raises:
        FileNotFoundError: video sumber tidak ada.
    """
    if not scene.source.exists():
        raise FileNotFoundError(f"video sumber tidak ada: {scene.source}")
    info = VideoInfo.from_path(scene.source)
    output = info.slice(options.start, options.end, options.stride)
    folder = Path(options.output_dir) / scene.name
    settings = scene.settings

    tracker = ByteTracker(
        frame_rate=output.fps,
        high_threshold=settings.TRACK_HIGH_THRESHOLD,
        new_track_threshold=settings.TRACK_NEW_THRESHOLD,
        lost_track_buffer=settings.LOST_TRACK_BUFFER,
    )
    analytics = SceneAnalytics(scene, frame_period_s=1.0 / output.fps)
    overlay = Overlay(scene)
    mask = polygon_mask(scene.ignore_polygons, info.width, info.height)
    meter = FpsMeter()
    processed = 0

    with ExitStack() as stack:
        writers = {
            "crossings": stack.enter_context(
                RecordWriter(folder / "crossings.csv", Crossing)
            ),
            "visits": stack.enter_context(
                RecordWriter(folder / "visits.csv", ZoneVisit)
            ),
            "attention": stack.enter_context(
                RecordWriter(folder / "attention.csv", Spell)
            ),
        }
        if analytics.contacts is not None:
            writers["contacts"] = stack.enter_context(
                RecordWriter(folder / "contacts.csv", Contact)
            )
        video = (
            stack.enter_context(VideoWriter(folder / "annotated.mp4", output))
            if options.mode in ("save", "both")
            else None
        )
        preview = (
            stack.enter_context(Preview(scene.name, output.fps))
            if options.mode in ("live", "both")
            else None
        )

        for frame_number, timestamp_s, frame in read_frames(
            scene.source, options.start, options.end, options.stride
        ):
            meter.start()
            processed += 1
            people = tracker.update(detector(apply_mask(frame, mask)))
            update = analytics.update(frame_number, timestamp_s, people)
            _write(writers, update.finished)
            meter.stop()
            annotated = overlay.draw(
                frame.copy(), update, analytics, timestamp_s, meter.fps
            )
            if video is not None:
                video.write(annotated)
            if preview is not None and not preview.show(annotated):
                break

        _write(writers, analytics.finish())

    summary = analytics.summary()
    summary["frame_diproses"] = processed
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def _write(writers: dict[str, RecordWriter], finished: Finished) -> None:
    writers["crossings"].write(finished.crossings)
    writers["visits"].write(finished.visits)
    writers["attention"].write(finished.attention)
    if "contacts" in writers:
        writers["contacts"].write(finished.contacts)
