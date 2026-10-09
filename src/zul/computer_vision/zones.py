"""
Poligon dan garis penghitung: berapa orang di dalam area, dan berapa yang melintas.

Gunanya:
    Dua alat hitung yang berdiri sendiri. PolygonZone menghitung orang di
    dalam satu poligon, di frame ini dan sepanjang video. LineCounter
    menghitung orang yang melintasi satu garis, per arah. Keduanya menerima
    satu titik per orang, jadi kamu yang memilih titiknya: kepala, tengah
    kotak, atau kaki. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.geometry import box_anchors
    from zul.computer_vision.zones import LineCounter, PolygonZone

    zone = PolygonZone([[100, 100], [500, 100], [500, 400], [100, 400]], "rak")
    line = LineCounter(start=(0, 300), end=(640, 300))

    # setiap frame
    feet = box_anchors(people.xyxy, ratio=1.0)
    inside = zone.update(feet, people.tracker_id)
    crossed_in, crossed_out = line.update(feet, people.tracker_id)

    zone.current_count, zone.total_count, line.in_count, line.out_count

Untuk beberapa poligon sekaligus, misalnya beberapa rak, buat satu
PolygonZone per poligon, atau pakai geometry.zone_membership saat satu
orang hanya boleh masuk ke satu zona.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Sequence

import numpy as np

from .geometry import points_in_polygon, polygon_centroid

# --------------------------------------------------------------------------
# Poligon Penghitung
# --------------------------------------------------------------------------
#
# Hitungan saat ini dihitung ulang setiap frame dari titik yang masuk.
# Hitungan total memakai id track, jadi orang yang berdiri di dalam
# selama 300 frame tetap dihitung satu orang, bukan 300 kotak.
#


class PolygonZone:
    """Satu poligon yang menghitung orang di dalamnya."""

    def __init__(self, polygon: Sequence, label: str = "") -> None:
        self.polygon = np.asarray(polygon, dtype=np.int32).reshape(-1, 2)
        if len(self.polygon) < 3:
            raise ValueError("poligon butuh minimal 3 titik")
        self.label = label
        self.current_count = 0
        self._seen: set[int] = set()

    @property
    def total_count(self) -> int:
        """Jumlah id track berbeda yang pernah berada di dalam poligon."""
        return len(self._seen)

    @property
    def centroid(self) -> np.ndarray:
        """Rata-rata titik sudut poligon, misalnya tempat menulis hitungannya."""
        return polygon_centroid(self.polygon)

    def contains(self, points: np.ndarray) -> np.ndarray:
        """Untuk setiap titik: apakah ia di dalam poligon, tanpa mengubah hitungan."""
        return points_in_polygon(self.polygon, points)

    def update(
        self, points: np.ndarray, tracker_ids: Sequence[int] | None = None
    ) -> np.ndarray:
        """Maju satu frame. Mengembalikan, per baris, apakah titiknya di dalam.

        Tanpa `tracker_ids`, hanya `current_count` yang diperbarui.
        """
        inside = self.contains(points)
        self.current_count = int(inside.sum())
        if tracker_ids is not None and len(tracker_ids):
            ids = np.asarray(tracker_ids)[inside]
            self._seen.update(int(track_id) for track_id in ids)
        return inside


# --------------------------------------------------------------------------
# Garis Penghitung
# --------------------------------------------------------------------------
#
# Sisi titik ditentukan oleh tanda perkalian silang arah garis dengan posisi
# titik dari awal garis. Sisi negatif berarti masuk. Menukar urutan kedua
# titik garis membalik arti masuk dan keluar, tanpa mengubah hal lain.
#
# Garisnya berupa segmen. Titik yang proyeksinya jatuh di luar
# kedua ujung garis diabaikan, sehingga orang yang lewat di
# samping garis tidak ikut dihitung sebagai lintasan.
#


class LineCounter:
    """Satu segmen garis yang menghitung lintasan masuk dan keluar per track."""

    def __init__(
        self,
        start: Sequence[float],
        end: Sequence[float],
        minimum_frames: int = 3,
        label: str = "",
    ) -> None:
        self.start = np.asarray(start[:2], dtype=np.float64)
        self.end = np.asarray(end[:2], dtype=np.float64)
        if float(np.linalg.norm(self.end - self.start)) == 0.0:
            raise ValueError("titik awal dan akhir garis tidak boleh sama")
        self.minimum_frames = minimum_frames
        self.label = label
        self.in_count = 0
        self.out_count = 0
        self._history: dict[int, deque[bool]] = defaultdict(
            lambda: deque(maxlen=max(2, minimum_frames + 1))
        )

    @property
    def midpoint(self) -> np.ndarray:
        """Titik tengah garis, misalnya target arah hadap ke pintu."""
        return (self.start + self.end) / 2.0

    @property
    def in_normal(self) -> np.ndarray:
        """Vektor satuan tegak lurus garis, menunjuk ke sisi masuk."""
        direction = self.end - self.start
        normal = np.array([direction[1], -direction[0]], dtype=np.float64)
        return normal / float(np.linalg.norm(normal))

    def sides(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Untuk setiap titik: apakah di sisi masuk, dan apakah di rentang segmen."""
        points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
        direction = self.end - self.start
        offset = points - self.start
        cross = direction[0] * offset[:, 1] - direction[1] * offset[:, 0]
        length = float(np.linalg.norm(direction))
        along = offset @ (direction / length)
        return cross < 0, (along >= 0) & (along <= length)

    def update(
        self, points: np.ndarray, tracker_ids: Sequence[int] | None
    ) -> tuple[list[bool], list[bool]]:
        """Maju satu frame. Mengembalikan, per baris, apakah baru masuk atau keluar.

        Lintasan baru dihitung setelah track bertahan `minimum_frames` frame
        di sisi baru, jadi kotak yang bergetar di garis tidak dihitung.
        """
        points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
        crossed_in = [False] * len(points)
        crossed_out = [False] * len(points)
        if tracker_ids is None:
            return crossed_in, crossed_out
        inside, in_band = self.sides(points)

        for row, track_id in enumerate(tracker_ids):
            if not in_band[row]:
                continue
            history = self._history[int(track_id)]
            history.append(bool(inside[row]))
            if len(history) < history.maxlen or history.count(history[0]) > 1:
                continue
            if inside[row]:
                self.in_count += 1
                crossed_in[row] = True
            else:
                self.out_count += 1
                crossed_out[row] = True
        return crossed_in, crossed_out
