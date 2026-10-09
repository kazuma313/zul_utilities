"""
Timer per track: lama seseorang di sebuah zona, dan lama sebuah kondisi benar.

Gunanya:
    Dua timer yang menerima id track dan hasil uji per frame, lalu
    mengembalikan catatan dengan awal, akhir, dan durasi:

    - ZoneTimer: siapa berada di zona mana, dan berapa lama.
    - ConditionTimer: berapa lama sebuah kondisi benar untuk setiap track,
      misalnya "menghadap rak" atau "wajah terlihat", per zona jika perlu.

    Timer tidak tahu apa pun tentang model atau video, jadi bisa diuji
    dengan track buatan. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.timers import ConditionTimer, ZoneTimer

    visits = ZoneTimer(["rak_a", "rak_b"], grace_s=1.0)
    looking = ConditionTimer(minimum_s=3.0, frame_period_s=1 / 10)

    # setiap frame
    visits.update(frame_number, timestamp_s, ids, membership)
    looking.update(frame_number, timestamp_s, ids, facing, groups=membership)

    # di akhir video
    visits.close_all()
    looking.close_all()

Waktu selalu dalam detik dari awal video, frame dalam nomor frame asli.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Catatan Hasil
# --------------------------------------------------------------------------
#
# Setiap catatan adalah satu kejadian yang selesai. Angka ringkasan, seperti
# jumlah orang per zona, selalu dihitung dari kumpulan catatan dan tidak
# disimpan sebagai kolom, jadi angka di layar dan di CSV selalu sama.
#


@dataclass
class ZoneVisit:
    """Satu kunjungan: seseorang berada di satu zona tanpa jeda panjang."""

    visit_id: int
    track_id: int
    zone_index: int
    zone_name: str
    enter_frame: int
    enter_time_s: float
    exit_frame: int
    exit_time_s: float

    @property
    def duration_s(self) -> float:
        return self.exit_time_s - self.enter_time_s


@dataclass
class Spell:
    """Satu rentang kehadiran track, dan berapa lama kondisinya benar di dalamnya."""

    spell_id: int
    track_id: int
    group: int | None
    group_name: str
    start_frame: int
    start_time_s: float
    end_frame: int
    end_time_s: float
    active_s: float

    @property
    def span_s(self) -> float:
        """Lama track terlihat, termasuk saat kondisinya tidak benar."""
        return self.end_time_s - self.start_time_s


def credit_cap(
    frame_period_s: float, threshold_s: float, periods: int, fraction: float
) -> float:
    """Waktu maksimum yang boleh dikreditkan dari satu jeda antar pengamatan.

    Batasnya ikut ambang: dengan batas tetap, ambang 0,5 detik bisa terpenuhi
    oleh satu frame saja setelah track sempat hilang.
    """
    return min(periods * frame_period_s, fraction * threshold_s)


def _label(labels: Sequence[str] | None, index: int | None) -> str:
    if index is None:
        return ""
    if labels is not None and 0 <= index < len(labels):
        return labels[index]
    return str(index)


# --------------------------------------------------------------------------
# Timer Zona
# --------------------------------------------------------------------------
#
# Kunjungan tetap terbuka selama jeda lebih pendek dari grace, sehingga
# track yang hilang sebentar tidak menjadi dua kunjungan. Waktu keluar
# adalah frame terakhir orang itu terlihat, bukan saat grace habis.
#


@dataclass
class _OpenVisit:
    zone_index: int
    enter_frame: int
    enter_time_s: float
    last_frame: int
    last_time_s: float


class ZoneTimer:
    """Keanggotaan zona per frame menjadi kunjungan yang terpisah dan berdurasi."""

    def __init__(self, zone_labels: Sequence[str], grace_s: float = 1.0) -> None:
        self.zone_labels = list(zone_labels)
        self.grace_s = grace_s
        self.completed: list[ZoneVisit] = []
        self._open: dict[int, _OpenVisit] = {}
        self._next_id = 1
        self._visits = [0] * len(self.zone_labels)
        self._people: list[set[int]] = [set() for _ in self.zone_labels]

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        membership: Sequence[int],
    ) -> list[ZoneVisit]:
        """Maju satu frame. Mengembalikan kunjungan yang selesai di frame ini.

        `membership` berisi indeks zona per baris, -1 untuk di luar semua zona,
        misalnya hasil geometry.zone_membership.
        """
        inside: dict[int, int] = {}
        for track, zone in zip(
            tracker_ids if tracker_ids is not None else [], membership, strict=False
        ):
            if int(zone) >= 0:
                inside[int(track)] = int(zone)

        closed: list[ZoneVisit] = []
        for track, zone in inside.items():
            current = self._open.get(track)
            if current is not None and current.zone_index != zone:
                closed.append(self._close(track, current))
                current = None
            if current is None:
                self._visits[zone] += 1
                self._people[zone].add(track)
                self._open[track] = _OpenVisit(
                    zone, frame_number, timestamp_s, frame_number, timestamp_s
                )
            else:
                current.last_frame, current.last_time_s = frame_number, timestamp_s

        for track, visit in list(self._open.items()):
            if track not in inside and timestamp_s - visit.last_time_s >= self.grace_s:
                closed.append(self._close(track, visit))

        self.completed.extend(closed)
        return closed

    def close_all(self) -> list[ZoneVisit]:
        """Tutup semua kunjungan yang masih terbuka saat video selesai."""
        closed = [
            self._close(track, visit) for track, visit in list(self._open.items())
        ]
        self.completed.extend(closed)
        return closed

    def dwell_s(self, track_id: int, timestamp_s: float) -> float | None:
        """Sudah berapa lama orang ini di zonanya sekarang, atau None."""
        visit = self._open.get(int(track_id))
        return None if visit is None else max(timestamp_s - visit.enter_time_s, 0.0)

    def zone_of(self, track_id: int) -> int | None:
        """Zona orang ini sekarang, atau None jika ia tidak di zona mana pun."""
        visit = self._open.get(int(track_id))
        return visit.zone_index if visit else None

    def unique_visitors(self, zone_index: int) -> int:
        """Jumlah id track berbeda yang pernah berada di zona ini."""
        return len(self._people[zone_index])

    def visit_count(self, zone_index: int) -> int:
        """Jumlah kunjungan ke zona ini, termasuk yang masih terbuka."""
        return self._visits[zone_index]

    def _close(self, track: int, visit: _OpenVisit) -> ZoneVisit:
        self._open.pop(track, None)
        record = ZoneVisit(
            visit_id=self._next_id,
            track_id=track,
            zone_index=visit.zone_index,
            zone_name=_label(self.zone_labels, visit.zone_index),
            enter_frame=visit.enter_frame,
            enter_time_s=round(visit.enter_time_s, 3),
            exit_frame=visit.last_frame,
            exit_time_s=round(visit.last_time_s, 3),
        )
        self._next_id += 1
        return record


# --------------------------------------------------------------------------
# Timer Kondisi
# --------------------------------------------------------------------------
#
# Satu rentang dibuka saat track terlihat, per grup jika `groups` diisi,
# dan waktu aktifnya baru bertambah saat kondisinya benar. Karena itu
# berada di zona dan menghadap zona itu dihitung secara terpisah.
#
# Grace menjaga rentang tetap terbuka selama jeda yang pendek. Batas kredit
# membatasi berapa banyak waktu yang boleh dihitung dari satu pengamatan.
# Keduanya berbeda: grace setahun tidak boleh menjadi setahun perhatian.
#


class ConditionTimer:
    """Berapa lama sebuah kondisi benar untuk setiap track, per grup jika perlu."""

    def __init__(
        self,
        minimum_s: float = 0.0,
        grace_s: float = 1.0,
        frame_period_s: float = 1 / 30,
        max_gap_frame_periods: int = 2,
        max_gap_threshold_fraction: float = 0.25,
        group_labels: Sequence[str] | None = None,
    ) -> None:
        self.minimum_s = minimum_s
        self.grace_s = grace_s
        self.group_labels = list(group_labels) if group_labels is not None else None
        threshold = minimum_s if minimum_s > 0 else float("inf")
        self.credit_cap_s = credit_cap(
            frame_period_s, threshold, max_gap_frame_periods, max_gap_threshold_fraction
        )
        self.completed: list[Spell] = []
        self._open: dict[tuple[int, int | None], Spell] = {}
        self._last_seen: dict[tuple[int, int | None], float] = {}
        self._last_active: dict[tuple[int, int | None], float] = {}
        self._next_id = 1

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        active: Sequence[bool],
        groups: Sequence[int] | None = None,
    ) -> list[Spell]:
        """Maju satu frame. Mengembalikan rentang yang selesai dan memenuhi minimum.

        `active` berisi hasil kondisi per baris. `groups`, misalnya indeks
        zona, memisahkan rentang per grup; baris dengan grup -1 dilewati.
        `tracker_ids` None berarti frame tanpa orang.
        """
        ids = tracker_ids if tracker_ids is not None else []
        for row, track_id in enumerate(ids):
            group = None
            if groups is not None:
                group = int(groups[row]) if row < len(groups) else -1
                if group < 0:
                    continue
            key = (int(track_id), group)
            spell = self._open.get(key)
            if spell is None:
                spell = Spell(
                    spell_id=self._next_id,
                    track_id=int(track_id),
                    group=group,
                    group_name=_label(self.group_labels, group),
                    start_frame=frame_number,
                    start_time_s=timestamp_s,
                    end_frame=frame_number,
                    end_time_s=timestamp_s,
                    active_s=0.0,
                )
                self._open[key] = spell
                self._next_id += 1
            spell.end_frame, spell.end_time_s = frame_number, timestamp_s
            self._last_seen[key] = timestamp_s

            if row < len(active) and active[row]:
                previous = self._last_active.get(key)
                if previous is not None:
                    spell.active_s += min(timestamp_s - previous, self.credit_cap_s)
                self._last_active[key] = timestamp_s

        closed: list[Spell] = []
        for key, last in list(self._last_seen.items()):
            if timestamp_s - last > self.grace_s:
                closed.extend(self._close(key))
        return closed

    def close_all(self) -> list[Spell]:
        """Rentang yang masih terbuka saat video selesai tetap terjadi."""
        return [spell for key in list(self._open) for spell in self._close(key)]

    def active_s(self, track_id: int, group: int | None = None) -> float:
        """Waktu aktif rentang yang sedang terbuka, misalnya untuk label di layar."""
        spell = self._open.get((int(track_id), group))
        return spell.active_s if spell is not None else 0.0

    def reached(self, track_id: int, group: int | None = None) -> bool:
        """Apakah rentang track ini sudah mencapai `minimum_s`, terbuka atau selesai."""
        spell = self._open.get((int(track_id), group))
        if spell is not None and spell.active_s >= self.minimum_s:
            return True
        return any(
            s.track_id == int(track_id) and s.group == group for s in self.completed
        )

    def count(self, group: int | None = None) -> int:
        """Jumlah rentang yang sudah dicatat, untuk satu grup atau semuanya."""
        return len(self._recorded(group))

    def qualified(self, group: int | None = None) -> int:
        """`count`, ditambah rentang terbuka yang sudah mencapai `minimum_s`."""
        live = sum(
            1
            for (_, open_group), spell in self._open.items()
            if (group is None or open_group == group)
            and spell.active_s >= self.minimum_s
        )
        return self.count(group) + live

    def people(self, group: int | None = None) -> int:
        """Jumlah id track berbeda dengan rentang yang sudah dicatat."""
        return len({spell.track_id for spell in self._recorded(group)})

    def seconds(self, group: int | None = None) -> float:
        """Total waktu aktif rentang yang sudah dicatat."""
        return sum(spell.active_s for spell in self._recorded(group))

    def _recorded(self, group: int | None) -> list[Spell]:
        return [s for s in self.completed if group is None or s.group == group]

    def _close(self, key: tuple[int, int | None]) -> list[Spell]:
        spell = self._open.pop(key, None)
        self._last_seen.pop(key, None)
        self._last_active.pop(key, None)
        if spell is None or spell.active_s < self.minimum_s:
            return []
        spell.start_time_s = round(spell.start_time_s, 3)
        spell.end_time_s = round(spell.end_time_s, 3)
        self.completed.append(spell)
        return [spell]
