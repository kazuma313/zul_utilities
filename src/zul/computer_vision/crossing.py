"""
Menghitung orang yang melintasi sebuah garis, misalnya ambang pintu toko.

Gunanya:
    Garis menjawab "apakah orang ini melintas, dan ke arah mana?". Satu
    lintasan hanya dihitung setelah orang itu bertahan di sisi baru selama
    beberapa frame, jadi kotak yang bergetar di garis tidak tercatat masuk
    dan keluar berulang kali. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.crossing import LineCrossing

    door = LineCrossing(start=(1257, 497), end=(225, 203), minimum_frames=3)

    # setiap frame: id track dan satu titik per orang, misalnya titik kepala
    crossed_in, crossed_out = door.update(tracker_ids, anchors)
    door.in_count, door.out_count

Aturannya sama dengan LineZone milik supervision, jadi urutan titik garis
dari config yang sama memberi arah masuk yang sama.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Sequence

import numpy as np

# --------------------------------------------------------------------------
# Penghitung Lintasan
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


class LineCrossing:
    """Lintasan masuk dan keluar per track di satu segmen garis."""

    def __init__(
        self,
        start: Sequence[float],
        end: Sequence[float],
        minimum_frames: int = 3,
    ) -> None:
        self.start = np.asarray(start[:2], dtype=np.float64)
        self.end = np.asarray(end[:2], dtype=np.float64)
        self.minimum_frames = minimum_frames
        self.in_count = 0
        self.out_count = 0
        self._history: dict[int, deque[bool]] = defaultdict(
            lambda: deque(maxlen=max(2, minimum_frames + 1))
        )

    @property
    def midpoint(self) -> np.ndarray:
        """Titik tengah garis, misalnya target arah hadap ke pintu toko."""
        return (self.start + self.end) / 2.0

    def sides(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Untuk setiap titik: apakah di sisi masuk, dan apakah di rentang segmen."""
        points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
        direction = self.end - self.start
        offset = points - self.start
        cross = direction[0] * offset[:, 1] - direction[1] * offset[:, 0]
        length = float(np.linalg.norm(direction))
        if length == 0.0:
            return np.zeros(len(points), dtype=bool), np.zeros(len(points), dtype=bool)
        along = offset @ (direction / length)
        return cross < 0, (along >= 0) & (along <= length)

    def update(
        self, tracker_ids: Sequence[int] | None, points: np.ndarray
    ) -> tuple[list[bool], list[bool]]:
        """Maju satu frame. Mengembalikan, per baris, apakah baru masuk atau keluar."""
        if tracker_ids is None:
            return [], []
        inside, in_band = self.sides(points)
        crossed_in = [False] * len(tracker_ids)
        crossed_out = [False] * len(tracker_ids)

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
