"""
Jarak antar orang dalam meter, dengan tinggi kotak setiap orang sebagai penggaris.

Gunanya:
    Jarak dalam piksel tidak bisa diubah ke meter dengan satu angka, karena
    orang yang jauh tampak kecil. Modul ini memakai tinggi kotak setiap
    orang, sekitar 1,7 meter untuk orang dewasa, sebagai penggaris di tempat
    ia berdiri. Tanpa kalibrasi kamera. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.distance import PairTimer, distance_m, pairs_within

    distance_m(people.xyxy[0], people.xyxy[1])        # misalnya 1.48

    # semua pasangan dalam 2 meter, lalu lama setiap pasangan berdekatan
    contacts = PairTimer(minimum_s=1.0)
    pairs = pairs_within(people.xyxy, max_distance_m=2.0)
    contacts.update(frame_number, timestamp_s, people.tracker_id, pairs)

Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh dari
sebenarnya, karena kotaknya lebih pendek. Angkanya perkiraan.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from .geometry import box_heights, foot_points

DEFAULT_PERSON_HEIGHT_M = 1.7

# --------------------------------------------------------------------------
# Jarak
# --------------------------------------------------------------------------
#
# Jarak diukur dari kaki ke kaki, lalu dibagi rata-rata skala kedua orang.
# Skala satu orang adalah tinggi kotaknya dibagi tinggi badan, jadi satu
# meter di dekat kamera lebih banyak pikselnya daripada di ujung jauh.
#


def pixels_per_metre(
    boxes: np.ndarray, person_height_m: float = DEFAULT_PERSON_HEIGHT_M
) -> np.ndarray:
    """Skala setiap orang: berapa piksel satu meter di tempat ia berdiri."""
    return box_heights(boxes) / person_height_m


def distance_m(
    first_box: Sequence[float],
    second_box: Sequence[float],
    person_height_m: float = DEFAULT_PERSON_HEIGHT_M,
) -> float:
    """Jarak kaki ke kaki antara dua orang dalam meter; NaN jika kotaknya rata."""
    boxes = np.asarray([first_box[:4], second_box[:4]], dtype=np.float64)
    scale = float(pixels_per_metre(boxes, person_height_m).mean())
    if scale <= 0:
        return float("nan")
    feet = foot_points(boxes)
    return float(np.linalg.norm(feet[0] - feet[1])) / scale


def pairs_within(
    boxes: np.ndarray,
    max_distance_m: float = 2.0,
    first: Sequence[bool] | None = None,
    second: Sequence[bool] | None = None,
    person_height_m: float = DEFAULT_PERSON_HEIGHT_M,
) -> list[tuple[int, int, float]]:
    """`(baris_a, baris_b, meter)` untuk setiap pasangan yang jaraknya dalam batas.

    Tanpa `first` dan `second`, semua pasangan dihitung sekali. Dengan
    keduanya, misalnya staf dan pelanggan, `baris_a` selalu dari `first`
    dan `baris_b` dari `second`.
    """
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    count = len(boxes)
    group_a = _rows(first, count)
    group_b = _rows(second, count)
    symmetric = first is None and second is None
    feet = foot_points(boxes)
    scale = pixels_per_metre(boxes, person_height_m)

    pairs = []
    for a in group_a:
        for b in group_b:
            if a == b or (symmetric and b < a):
                continue
            local = (scale[a] + scale[b]) / 2.0
            if local <= 0:
                continue
            metres = float(np.linalg.norm(feet[a] - feet[b])) / local
            if metres <= max_distance_m:
                pairs.append((int(a), int(b), metres))
    return pairs


def _rows(mask: Sequence[bool] | None, count: int) -> np.ndarray:
    if mask is None:
        return np.arange(count)
    return np.flatnonzero(np.asarray(mask, dtype=bool)[:count])


# --------------------------------------------------------------------------
# Lama Berdekatan
# --------------------------------------------------------------------------
#
# Satu pasangan yang berdekatan di 60 frame berturut-turut adalah
# satu kontak selama dua detik, bukan 60 kontak. Grace menjaga
# kontak tetap terbuka saat salah satu track sempat hilang.
#


@dataclass
class Contact:
    """Satu kontak: dua track berdekatan tanpa jeda panjang."""

    contact_id: int
    first_id: int
    second_id: int
    start_frame: int
    start_time_s: float
    end_frame: int
    end_time_s: float
    closest_m: float

    @property
    def duration_s(self) -> float:
        return self.end_time_s - self.start_time_s


class PairTimer:
    """Pasangan dari `pairs_within` per frame menjadi kontak yang berdurasi."""

    def __init__(
        self, minimum_s: float = 1.0, grace_s: float = 1.0, ordered: bool = False
    ) -> None:
        self.minimum_s = minimum_s
        self.grace_s = grace_s
        self.ordered = ordered
        self.completed: list[Contact] = []
        self._open: dict[tuple[int, int], Contact] = {}
        self._last_seen: dict[tuple[int, int], float] = {}
        self._next_id = 1

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        pairs: Iterable[tuple[int, int, float]],
    ) -> list[Contact]:
        """Buka atau perpanjang kontak untuk setiap pasangan; tutup yang sudah sepi.

        Dengan `ordered=False`, pasangan (a, b) dan (b, a) adalah kontak
        yang sama. Pakai `ordered=True` saat urutannya bermakna, misalnya
        staf selalu di `first_id`.
        """
        for row_a, row_b, metres in pairs if tracker_ids is not None else []:
            key = (int(tracker_ids[row_a]), int(tracker_ids[row_b]))
            if not self.ordered:
                key = (min(key), max(key))
            contact = self._open.get(key)
            if contact is None:
                self._open[key] = Contact(
                    self._next_id, key[0], key[1], frame_number, timestamp_s,
                    frame_number, timestamp_s, float(metres),
                )  # fmt: skip
                self._next_id += 1
            else:
                contact.end_frame, contact.end_time_s = frame_number, timestamp_s
                contact.closest_m = min(contact.closest_m, float(metres))
            self._last_seen[key] = timestamp_s

        closed: list[Contact] = []
        for key, last in list(self._last_seen.items()):
            if timestamp_s - last > self.grace_s:
                closed.extend(self._close(key))
        return closed

    def close_all(self) -> list[Contact]:
        """Kontak yang masih terbuka saat video selesai tetap terjadi."""
        return [contact for key in list(self._open) for contact in self._close(key)]

    def contacts_per_track(self) -> dict[int, int]:
        """Jumlah kontak tercatat per id track, dari kedua sisi pasangan."""
        counts: dict[int, int] = {}
        for contact in self.completed:
            for track_id in (contact.first_id, contact.second_id):
                counts[track_id] = counts.get(track_id, 0) + 1
        return counts

    def _close(self, key: tuple[int, int]) -> list[Contact]:
        contact = self._open.pop(key, None)
        self._last_seen.pop(key, None)
        if contact is None or contact.duration_s < self.minimum_s:
            return []
        self.completed.append(contact)
        return [contact]
