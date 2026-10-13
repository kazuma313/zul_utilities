"""
Aturan scene per frame: lintasan garis, kunjungan zona, perhatian, dan kontak.

Gunanya:
    `SceneAnalytics` merangkai blok `zul.computer_vision` sesuai geometri
    kamera: `LineCounter` untuk setiap garis, `ZoneTimer` untuk kunjungan
    zona, `ConditionTimer` untuk lama menghadap target zona, dan
    `PairTimer` untuk orang yang berdekatan. Setiap frame menghasilkan
    `FrameUpdate`: keadaan untuk digambar, dan catatan yang baru selesai
    untuk ditulis ke CSV. Modul ini tidak membaca atau menulis file, jadi
    bisa diuji dengan deteksi buatan.

Cara pakai:
    from cctv.analytics import SceneAnalytics

    analytics = SceneAnalytics(scene, frame_period_s=1 / 10)
    for frame_number, timestamp_s, frame in frames:
        update = analytics.update(frame_number, timestamp_s, people)
        update.finished.visits        # kunjungan zona yang selesai di frame ini
    finished = analytics.finish()     # kunjungan yang masih terbuka di akhir video
    print(analytics.summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from zul.computer_vision.detection import Detections
from zul.computer_vision.distance import Contact, PairTimer, pairs_within
from zul.computer_vision.geometry import box_anchors, zone_membership
from zul.computer_vision.pose import (
    facing_directions,
    facing_zone_targets,
    zone_targets,
)
from zul.computer_vision.timers import ConditionTimer, Spell, ZoneTimer, ZoneVisit
from zul.computer_vision.zones import LineCounter

from .settings import SceneConfig

# --------------------------------------------------------------------------
# Hasil Per Frame
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Crossing:
    """Satu orang melintasi satu garis."""

    frame_number: int
    time_s: float
    track_id: int
    line_name: str
    direction: str


@dataclass
class Finished:
    """Catatan yang selesai: siap ditulis ke CSV."""

    crossings: list[Crossing] = field(default_factory=list)
    visits: list[ZoneVisit] = field(default_factory=list)
    attention: list[Spell] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)


@dataclass
class FrameUpdate:
    """Keadaan satu frame untuk digambar, dan catatan yang selesai di frame itu."""

    people: Detections
    anchors: np.ndarray
    membership: list[int]
    directions: list[np.ndarray | None]
    attentive: list[bool]
    pairs: list[tuple[int, int, float]]
    finished: Finished


# --------------------------------------------------------------------------
# Rangkaian Aturan
# --------------------------------------------------------------------------
#
# Zona dan garis memakai satu titik per orang, biasanya kaki, sehingga orang
# yang tinggi dan orang yang pendek dihitung dengan cara sama. Arah hadap
# baru ada jika model memberi keypoint; tanpa keypoint, perhatian nol.
#


class SceneAnalytics:
    """Semua aturan satu kamera, diperbarui frame demi frame."""

    def __init__(self, scene: SceneConfig, frame_period_s: float) -> None:
        self.scene = scene
        settings = scene.settings
        self.settings = settings
        self.zone_names = [zone.name for zone in scene.zones]
        self.polygons = [zone.polygon for zone in scene.zones]
        anchors = [zone.anchor for zone in scene.zones]
        self.targets = zone_targets(
            self.polygons, anchors if all(anchors) and anchors else None
        )
        self.lines = [
            LineCounter(
                line.start,
                line.end,
                minimum_frames=settings.MIN_CROSSING_FRAMES,
                label=line.name,
            )
            for line in scene.lines
        ]
        self.visits = ZoneTimer(self.zone_names, grace_s=settings.ZONE_GRACE_S)
        self.attention = ConditionTimer(
            minimum_s=settings.ATTENTION_MINIMUM_S,
            grace_s=settings.ZONE_GRACE_S,
            frame_period_s=frame_period_s,
            group_labels=self.zone_names,
        )
        self.contacts = (
            PairTimer(
                minimum_s=settings.CONTACT_MINIMUM_S, grace_s=settings.ZONE_GRACE_S
            )
            if settings.PROXIMITY_METRES > 0
            else None
        )
        self.all_visits: list[ZoneVisit] = []
        self.crossing_count = 0

    def update(
        self, frame_number: int, timestamp_s: float, people: Detections
    ) -> FrameUpdate:
        """Maju satu frame. `people` harus sudah berisi `tracker_id`."""
        ids = [] if people.tracker_id is None else [int(i) for i in people.tracker_id]
        anchors = box_anchors(people.xyxy, self.settings.ANCHOR_RATIO)
        membership = (
            [int(m) for m in zone_membership(self.polygons, anchors)]
            if self.polygons
            else [-1] * len(ids)
        )
        finished = Finished()

        for counter in self.lines:
            crossed_in, crossed_out = counter.update(anchors, ids)
            for row, track_id in enumerate(ids):
                for crossed, direction in (
                    (crossed_in, "masuk"),
                    (crossed_out, "keluar"),
                ):
                    if crossed[row]:
                        finished.crossings.append(
                            Crossing(
                                frame_number,
                                timestamp_s,
                                track_id,
                                counter.label,
                                direction,
                            )
                        )
        self.crossing_count += len(finished.crossings)

        finished.visits = self.visits.update(frame_number, timestamp_s, ids, membership)
        self.all_visits.extend(finished.visits)

        directions, _sources = facing_directions(
            people.keypoints_xy, people.keypoints_conf
        )
        attentive = facing_zone_targets(
            people.xyxy,
            directions,
            membership,
            self.targets,
            cone_deg=self.settings.FACING_CONE_DEG,
        )
        finished.attention = self.attention.update(
            frame_number, timestamp_s, ids, attentive, groups=membership
        )

        pairs: list[tuple[int, int, float]] = []
        if self.contacts is not None:
            pairs = pairs_within(
                people.xyxy,
                self.settings.PROXIMITY_METRES,
                person_height_m=self.settings.PERSON_HEIGHT_METRES,
            )
            finished.contacts = self.contacts.update(
                frame_number, timestamp_s, ids, pairs
            )

        return FrameUpdate(
            people=people,
            anchors=anchors,
            membership=membership,
            directions=list(directions),
            attentive=list(attentive),
            pairs=pairs,
            finished=finished,
        )

    def finish(self) -> Finished:
        """Tutup semua catatan yang masih terbuka saat video selesai."""
        visits = self.visits.close_all()
        self.all_visits.extend(visits)
        return Finished(
            visits=visits,
            attention=self.attention.close_all(),
            contacts=self.contacts.close_all() if self.contacts is not None else [],
        )

    def dwell_s(self, track_id: int, timestamp_s: float) -> float | None:
        """Sudah berapa lama orang ini di zonanya sekarang, untuk label di layar."""
        return self.visits.dwell_s(track_id, timestamp_s)

    # ----------------------------------------------------------------------
    # Ringkasan
    # ----------------------------------------------------------------------

    def summary(self) -> dict:
        """Angka akhir per garis dan per zona. Panggil setelah `finish`."""
        threshold = self.settings.DWELL_THRESHOLD_S
        zones = {}
        for index, name in enumerate(self.zone_names):
            stopped = {
                visit.track_id
                for visit in self.all_visits
                if visit.zone_index == index and visit.duration_s >= threshold
            }
            zones[name] = {
                "pengunjung": self.visits.unique_visitors(index),
                "kunjungan": self.visits.visit_count(index),
                f"berhenti_minimal_{threshold:g}_detik": len(stopped),
                "memperhatikan": self.attention.people(index),
                "detik_memperhatikan": round(self.attention.seconds(index), 1),
            }
        lines = {
            counter.label: {"masuk": counter.in_count, "keluar": counter.out_count}
            for counter in self.lines
        }
        summary = {"kamera": self.scene.name, "garis": lines, "zona": zones}
        if self.contacts is not None:
            summary["kontak"] = len(self.contacts.completed)
        return summary
