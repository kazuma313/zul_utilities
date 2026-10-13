"""
Gambar overlay satu frame: area yang diabaikan, zona, garis, orang, dan ringkasan.

Gunanya:
    Semua gambar memakai `zul.computer_vision.draw`, jadi warna dan bentuk
    sama dengan contoh di dokumentasi Zul. Setiap orang diberi kotak dan
    id track; orang di zona juga diberi lama ia berada di sana, orang yang
    menghadap target zonanya diberi panah, dan orang yang berdekatan
    dihubungkan dengan garis berketerangan jarak.

Cara pakai:
    from cctv.render import Overlay

    overlay = Overlay(scene)
    annotated = overlay.draw(frame.copy(), update, analytics, timestamp_s, fps)
"""

from __future__ import annotations

import numpy as np
from zul.computer_vision import draw
from zul.computer_vision.geometry import box_anchor, foot_points

from .analytics import FrameUpdate, SceneAnalytics
from .settings import SceneConfig

HEAD_ANCHOR_RATIO = 1 / 6
ARROW_LENGTH_RATIO = 0.6


class Overlay:
    """Penggambar overlay untuk satu kamera, dengan jejak gerak yang tersimpan."""

    def __init__(self, scene: SceneConfig) -> None:
        self.scene = scene
        self.settings = scene.settings
        self.trace = draw.TrackTrace(length=self.settings.TRACE_LENGTH)

    def draw(
        self,
        frame: np.ndarray,
        update: FrameUpdate,
        analytics: SceneAnalytics,
        timestamp_s: float,
        fps: float,
    ) -> np.ndarray:
        """Gambar semuanya di `frame`, lalu kembalikan frame yang sama."""
        settings, people = self.settings, update.people
        ids = [] if people.tracker_id is None else [int(i) for i in people.tracker_id]

        draw.draw_polygons(
            frame, self.scene.ignore_polygons, settings.IGNORE_COLOR, fill_alpha=0.35
        )
        draw.draw_polygons(
            frame,
            [z.polygon for z in self.scene.zones],
            settings.ZONE_COLOR,
            fill_alpha=0.15,
        )
        for zone in self.scene.zones:
            draw.draw_label(frame, zone.name, zone.polygon[0], settings.ZONE_COLOR)
        for counter in analytics.lines:
            draw.draw_line_counter(frame, counter, color=settings.LINE_COLOR)

        self.trace.update(foot_points(people.xyxy), ids)
        draw.draw_traces(frame, self.trace)
        if settings.SHOW_SKELETON and people.keypoints_xy is not None:
            for row in range(len(people)):
                confidence = (
                    None
                    if people.keypoints_conf is None
                    else people.keypoints_conf[row]
                )
                draw.draw_skeleton(frame, people.keypoints_xy[row], confidence)

        for row, track_id in enumerate(ids):
            box = people.xyxy[row]
            label = f"#{track_id}"
            dwell = analytics.dwell_s(track_id, timestamp_s)
            if dwell is not None:
                label += f" {dwell:.0f}s"
            draw.draw_labelled_box(frame, box, label, draw.track_color(track_id))
            direction = update.directions[row] if row < len(update.directions) else None
            if direction is not None and update.attentive[row]:
                height = float(box[3] - box[1])
                draw.draw_arrow(
                    frame,
                    box_anchor(box, HEAD_ANCHOR_RATIO),
                    direction,
                    settings.ATTENTION_COLOR,
                    length=height * ARROW_LENGTH_RATIO,
                )

        feet = foot_points(people.xyxy)
        for first, second, metres in update.pairs:
            draw.draw_link(
                frame,
                feet[first],
                feet[second],
                settings.CONTACT_COLOR,
                label=f"{metres:.1f} m",
            )

        draw.draw_corner_text(frame, self._summary_lines(analytics, len(ids)))
        draw.draw_corner_text(frame, [f"{fps:.1f} fps"], corner=draw.Corner.TOP_RIGHT)
        return frame

    def _summary_lines(self, analytics: SceneAnalytics, people_now: int) -> list[str]:
        lines = [f"{self.scene.name}: {people_now} orang"]
        for counter in analytics.lines:
            lines.append(
                f"{counter.label}: {counter.in_count} masuk, {counter.out_count} keluar"
            )
        for index, name in enumerate(analytics.zone_names):
            visitors = analytics.visits.unique_visitors(index)
            attentive = analytics.attention.qualified(index)
            lines.append(f"{name}: {visitors} pengunjung, {attentive} memperhatikan")
        return lines
