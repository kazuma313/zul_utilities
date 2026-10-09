"""
Aturan perilaku: dari deteksi per frame menjadi kejadian yang bisa dihitung.

Gunanya:
    Empat pelacak yang menerima id track dan hasil uji per frame, lalu
    mengubahnya menjadi catatan dengan awal, akhir, dan durasi:

    - ZoneVisitTracker: siapa berada di zona mana, dan berapa lama.
    - AttentionTracker: siapa menghadap zona tempat ia berdiri, berapa lama.
    - ProximityLog: kapan anggota satu kelompok dekat dengan kelompok lain,
      misalnya staf dengan pelanggan, dalam meter tanpa kalibrasi kamera.
    - InterestTracker: siapa menunjukkan minat, lalu masuk atau lewat saja.

    Pelacak tidak tahu apa pun tentang model atau video, jadi bisa diuji
    dengan track buatan. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.analytics import AttentionTracker

    attention = AttentionTracker(["rak_a", "rak_b"], minimum_s=3.0)
    for frame_number, timestamp_s, ids, membership, looking in frames:
        for spell in attention.update(frame_number, timestamp_s, ids,
                                      membership, looking):
            print(spell.track_id, spell.zone_name, spell.looking_s)
    attention.close_all()          # perhatian yang masih terbuka di akhir video

Waktu selalu dalam detik dari awal video, frame dalam nomor frame asli.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

import numpy as np

from .geometry import box_heights, foot_points

# --------------------------------------------------------------------------
# Catatan Hasil
# --------------------------------------------------------------------------
#
# Setiap catatan adalah satu kejadian yang selesai. Angka ringkasan, seperti
# jumlah orang per zona, selalu dihitung dari kumpulan catatan dan tidak
# disimpan sebagai kolom, jadi angka di layar dan di CSV selalu sama.
#


@dataclass
class Visit:
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
class Attention:
    """Satu rentang perhatian: seseorang di zona, sebagian waktunya menghadap zona."""

    attention_id: int
    track_id: int
    zone_index: int
    zone_name: str
    start_frame: int
    start_time_s: float
    end_frame: int
    end_time_s: float
    looking_s: float

    @property
    def span_s(self) -> float:
        """Lama berada di zona, termasuk saat tidak menghadapnya."""
        return self.end_time_s - self.start_time_s


@dataclass
class Contact:
    """Satu kontak: anggota kelompok utama dekat orang lain tanpa jeda panjang."""

    subject_id: int
    other_id: int
    start_frame: int
    start_time_s: float
    end_frame: int
    end_time_s: float

    @property
    def duration_s(self) -> float:
        return self.end_time_s - self.start_time_s


@dataclass
class InterestRecord:
    """Satu orang yang memenuhi syarat minat, dan apakah ia kemudian melintas masuk."""

    track_id: int
    outcome: str
    qualified_frame: int
    qualified_time_s: float
    crossed_frame: int | None
    crossed_time_s: float | None

    @property
    def entered(self) -> bool:
        return self.crossed_frame is not None


@dataclass
class InterestCounts:
    """Jumlah orang yang berminat: yang masuk, dan yang lewat saja."""

    entered: int = 0
    passed_by: int = 0

    @property
    def total(self) -> int:
        return self.entered + self.passed_by


def credit_cap(
    frame_period_s: float, threshold_s: float, periods: int, fraction: float
) -> float:
    """Waktu maksimum yang boleh dikreditkan dari satu jeda antar pengamatan.

    Batasnya ikut ambang: dengan batas tetap, ambang 0,5 detik bisa terpenuhi
    oleh satu frame saja setelah track sempat hilang.
    """
    return min(periods * frame_period_s, fraction * threshold_s)


# --------------------------------------------------------------------------
# Kunjungan Zona
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


class ZoneVisitTracker:
    """Keanggotaan zona per frame menjadi kunjungan yang terpisah dan berdurasi."""

    def __init__(self, zone_labels: Sequence[str], grace_s: float = 1.0) -> None:
        self.zone_labels = list(zone_labels)
        self.grace_s = grace_s
        self.completed: list[Visit] = []
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
    ) -> list[Visit]:
        """Maju satu frame. Mengembalikan kunjungan yang selesai di frame ini."""
        inside: dict[int, int] = {}
        for track, zone in zip(
            tracker_ids if tracker_ids is not None else [], membership, strict=False
        ):
            if int(zone) >= 0:
                inside[int(track)] = int(zone)

        closed: list[Visit] = []
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

    def close_all(self) -> list[Visit]:
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
        visit = self._open.get(int(track_id))
        return visit.zone_index if visit else None

    def unique_visitors(self, zone_index: int) -> int:
        return len(self._people[zone_index])

    def visit_count(self, zone_index: int) -> int:
        return self._visits[zone_index]

    def _close(self, track: int, visit: _OpenVisit) -> Visit:
        self._open.pop(track, None)
        record = Visit(
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


def _label(labels: Sequence[str], index: int) -> str:
    return labels[index] if 0 <= index < len(labels) else str(index)


# --------------------------------------------------------------------------
# Perhatian Ke Zona
# --------------------------------------------------------------------------
#
# Berada di sebuah zona belum berarti memperhatikannya: orang yang melintasi
# lorong menempati poligon yang sama dengan orang yang membaca label harga.
# Waktu perhatian baru bertambah saat orang itu menghadap target zonanya.
#
# Grace menjaga rentang tetap terbuka selama jeda yang pendek. Batas kredit
# membatasi berapa banyak waktu yang boleh dihitung dari satu pengamatan.
# Keduanya berbeda: grace setahun tidak boleh menjadi setahun perhatian.
#


class AttentionTracker:
    """Perhatian per zona: siapa menghadap zona mana, dan berapa lama."""

    def __init__(
        self,
        zone_labels: Sequence[str],
        minimum_s: float = 3.0,
        grace_s: float = 1.0,
        frame_period_s: float = 1 / 30,
        max_gap_frame_periods: int = 2,
        max_gap_threshold_fraction: float = 0.25,
    ) -> None:
        self.zone_labels = list(zone_labels)
        self.minimum_s = minimum_s
        self.grace_s = grace_s
        self.credit_cap_s = credit_cap(
            frame_period_s, minimum_s, max_gap_frame_periods, max_gap_threshold_fraction
        )
        self.completed: list[Attention] = []
        self._open: dict[tuple[int, int], Attention] = {}
        self._last_seen: dict[tuple[int, int], float] = {}
        self._last_looking: dict[tuple[int, int], float] = {}
        self._next_id = 1

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        membership: Sequence[int],
        looking: Sequence[bool],
    ) -> list[Attention]:
        """Maju satu frame. Mengembalikan rentang yang selesai dan memenuhi ambang.

        `tracker_ids` None berarti frame tanpa orang: rentang yang lama tetap ditutup.
        """
        for row, track_id in enumerate(tracker_ids if tracker_ids is not None else []):
            zone = int(membership[row]) if row < len(membership) else -1
            if zone < 0:
                continue
            key = (int(track_id), zone)
            spell = self._open.get(key)
            if spell is None:
                spell = Attention(
                    attention_id=self._next_id,
                    track_id=int(track_id),
                    zone_index=zone,
                    zone_name=_label(self.zone_labels, zone),
                    start_frame=frame_number,
                    start_time_s=timestamp_s,
                    end_frame=frame_number,
                    end_time_s=timestamp_s,
                    looking_s=0.0,
                )
                self._open[key] = spell
                self._next_id += 1
            spell.end_frame, spell.end_time_s = frame_number, timestamp_s
            self._last_seen[key] = timestamp_s

            if row < len(looking) and looking[row]:
                previous = self._last_looking.get(key)
                if previous is not None:
                    spell.looking_s += min(timestamp_s - previous, self.credit_cap_s)
                self._last_looking[key] = timestamp_s

        closed: list[Attention] = []
        for key, last in list(self._last_seen.items()):
            if timestamp_s - last > self.grace_s:
                closed.extend(self._close(key))
        return closed

    def close_all(self) -> list[Attention]:
        """Rentang yang masih terbuka saat video selesai tetap terjadi."""
        return [spell for key in list(self._open) for spell in self._close(key)]

    def looking_s(self, track_id: int, zone_index: int) -> float:
        """Waktu perhatian yang sedang berjalan, untuk label di layar."""
        spell = self._open.get((int(track_id), int(zone_index)))
        return spell.looking_s if spell is not None else 0.0

    def count(self, zone_index: int) -> int:
        """Rentang yang sudah tercatat di zona ini."""
        return sum(1 for spell in self.completed if spell.zone_index == zone_index)

    def qualified(self, zone_index: int) -> int:
        """Rentang di zona ini yang memenuhi ambang, termasuk yang masih terbuka."""
        live = sum(
            1
            for (_, zone), spell in self._open.items()
            if zone == zone_index and spell.looking_s >= self.minimum_s
        )
        return self.count(zone_index) + live

    def people(self, zone_index: int) -> int:
        return len({s.track_id for s in self.completed if s.zone_index == zone_index})

    def seconds(self, zone_index: int) -> float:
        return sum(s.looking_s for s in self.completed if s.zone_index == zone_index)

    def _close(self, key: tuple[int, int]) -> list[Attention]:
        spell = self._open.pop(key, None)
        self._last_seen.pop(key, None)
        self._last_looking.pop(key, None)
        if spell is None or spell.looking_s < self.minimum_s:
            return []
        self.completed.append(spell)
        return [spell]


# --------------------------------------------------------------------------
# Kontak Antar Kelompok
# --------------------------------------------------------------------------
#
# Jarak piksel tidak dapat diubah ke meter dengan satu angka, karena orang
# yang jauh tampak kecil. Tinggi kotak setiap orang menjadi penggarisnya:
# orang dewasa sekitar 1,7 meter, jadi tanpa kalibrasi atau homografi.
#
# Kelompok utama, seperti staf, dicatat begitu terlihat, berinteraksi
# atau tidak. Staf tanpa kontak tetap masuk ke penyebut rata-rata,
# karena tanpa mereka rata-rata menghitung sesuatu yang lain.
#


def proximity_pairs(
    boxes: np.ndarray,
    is_subject: Sequence[bool],
    max_distance_m: float = 2.0,
    person_height_m: float = 1.7,
    exclude: Sequence[bool] | None = None,
) -> list[tuple[int, int, float]]:
    """`(baris_subject, baris_lain, meter)` untuk setiap pasangan dalam jangkauan.

    Jarak diukur dari kaki ke kaki, dibagi rata-rata skala kedua orang.
    Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh.
    """
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    subject = np.asarray(is_subject, dtype=bool)
    if len(boxes) == 0 or not subject.any():
        return []
    eligible = np.ones(len(boxes), dtype=bool)
    if exclude is not None and len(exclude) == len(boxes):
        eligible &= ~np.asarray(exclude, dtype=bool)

    feet = foot_points(boxes)
    scale = box_heights(boxes) / person_height_m
    pairs = []
    for s in np.flatnonzero(subject & eligible):
        for o in np.flatnonzero(~subject & eligible):
            local = (scale[s] + scale[o]) / 2.0
            if local <= 0:
                continue
            metres = float(np.linalg.norm(feet[s] - feet[o])) / local
            if metres <= max_distance_m:
                pairs.append((int(s), int(o), metres))
    return pairs


class ProximityLog:
    """Kontak per anggota kelompok utama: berapa kali, berapa lama, dan kapan."""

    def __init__(self, minimum_s: float = 1.0, grace_s: float = 1.0) -> None:
        self.minimum_s = minimum_s
        self.grace_s = grace_s
        self.subjects_seen: dict[int, float] = {}
        self.completed: list[Contact] = []
        self._open: dict[tuple[int, int], Contact] = {}
        self._last_seen: dict[tuple[int, int], float] = {}

    def note_subjects(
        self,
        tracker_ids: Sequence[int] | None,
        is_subject: Sequence[bool],
        timestamp_s: float,
    ) -> None:
        """Catat setiap anggota kelompok utama yang terlihat, ada kontak atau tidak."""
        if tracker_ids is None:
            return
        for row in np.flatnonzero(np.asarray(is_subject, dtype=bool)):
            self.subjects_seen.setdefault(int(tracker_ids[row]), timestamp_s)

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        pairs: Iterable[tuple[int, int, float]],
    ) -> list[Contact]:
        """Perpanjang atau buka kontak untuk setiap pasangan; tutup yang sudah sepi."""
        for subject_row, other_row, _ in pairs if tracker_ids is not None else []:
            key = (int(tracker_ids[subject_row]), int(tracker_ids[other_row]))
            contact = self._open.get(key)
            if contact is None:
                self._open[key] = Contact(
                    key[0], key[1], frame_number, timestamp_s, frame_number, timestamp_s
                )
            else:
                contact.end_frame, contact.end_time_s = frame_number, timestamp_s
            self._last_seen[key] = timestamp_s

        closed: list[Contact] = []
        for key, last in list(self._last_seen.items()):
            if timestamp_s - last > self.grace_s:
                closed.extend(self._close(key))
        return closed

    def close_all(self) -> list[Contact]:
        """Kontak yang masih terbuka saat video selesai tetap terjadi."""
        return [contact for key in list(self._open) for contact in self._close(key)]

    def contacts_per_subject(self) -> dict[int, int]:
        """Jumlah kontak untuk setiap anggota yang terlihat, termasuk yang nol."""
        counts = dict.fromkeys(self.subjects_seen, 0)
        for contact in self.completed:
            counts[contact.subject_id] = counts.get(contact.subject_id, 0) + 1
        return counts

    def seconds_per_subject(self) -> dict[int, float]:
        seconds = dict.fromkeys(self.subjects_seen, 0.0)
        for contact in self.completed:
            seconds[contact.subject_id] = (
                seconds.get(contact.subject_id, 0.0) + contact.duration_s
            )
        return seconds

    def idle_subjects(self) -> list[int]:
        return sorted(
            s for s, count in self.contacts_per_subject().items() if count == 0
        )

    def average_contacts(self) -> float:
        """Rata-rata kontak per anggota, dibagi SEMUA anggota yang terlihat."""
        counts = self.contacts_per_subject()
        return sum(counts.values()) / len(counts) if counts else 0.0

    def _close(self, key: tuple[int, int]) -> list[Contact]:
        contact = self._open.pop(key, None)
        self._last_seen.pop(key, None)
        if contact is None or contact.duration_s < self.minimum_s:
            return []
        self.completed.append(contact)
        return [contact]


# --------------------------------------------------------------------------
# Minat Dan Konversi
# --------------------------------------------------------------------------
#
# Waktu minat baru bertambah saat tiga syarat terpenuhi bersamaan: orang itu
# ada di zona minat, wajahnya terlihat, dan kepalanya menunjuk ke target.
# Hasil yang sudah diberikan, masuk atau lewat, tak pernah diturunkan.
#


@dataclass
class _TrackInterest:
    track_id: int
    looking_s: float = 0.0
    last_seen_s: float | None = None
    qualified_s: float | None = None
    qualified_frame: int | None = None
    crossed_s: float | None = None
    crossed_frame: int | None = None
    outcome: str | None = None
    history: list[str] = field(default_factory=list)


class InterestTracker:
    """Waktu menghadap per orang, lalu hasilnya: masuk atau lewat saja."""

    ENTERED = "entered"
    PASSED_BY = "passed_by"

    def __init__(
        self,
        threshold_s: float = 2.0,
        frame_period_s: float = 1 / 30,
        max_gap_frame_periods: int = 2,
        max_gap_threshold_fraction: float = 0.25,
    ) -> None:
        self.threshold_s = threshold_s
        self.max_gap_s = credit_cap(
            frame_period_s,
            threshold_s,
            max_gap_frame_periods,
            max_gap_threshold_fraction,
        )
        self.tracks: dict[int, _TrackInterest] = {}

    def update(
        self,
        frame_number: int,
        timestamp_s: float,
        tracker_ids: Sequence[int] | None,
        looking: Sequence[bool],
        in_zone: Sequence[bool] | None = None,
        facing: Sequence[bool] | None = None,
    ) -> list[int]:
        """Maju satu frame. Mengembalikan id yang baru saja memenuhi syarat minat.

        `looking` biasanya "wajah terlihat", `facing` "kepala menunjuk target";
        keduanya, dan `in_zone`, harus benar agar waktu bertambah.
        """
        if tracker_ids is None:
            return []
        count = len(looking)
        in_zone = in_zone if in_zone is not None else [True] * count
        facing = facing if facing is not None else [True] * count

        newly: list[int] = []
        for track_id, seen, zone_ok, facing_ok in zip(
            tracker_ids, looking, in_zone, facing, strict=False
        ):
            track = self.tracks.setdefault(int(track_id), _TrackInterest(int(track_id)))
            elapsed = 0.0
            if track.last_seen_s is not None:
                elapsed = min(timestamp_s - track.last_seen_s, self.max_gap_s)
            track.last_seen_s = timestamp_s
            if seen and zone_ok and facing_ok:
                track.looking_s += elapsed
            if (
                self._reclassify(track, timestamp_s, frame_number)
                and track.qualified_s == timestamp_s
            ):
                newly.append(track.track_id)
        return newly

    def mark_crossed(
        self, tracker_ids: Iterable[int], frame_number: int, timestamp_s: float
    ) -> None:
        """Catat bahwa orang-orang ini melintasi garis masuk."""
        for track_id in tracker_ids:
            track = self.tracks.setdefault(int(track_id), _TrackInterest(int(track_id)))
            if track.crossed_s is None:
                track.crossed_s, track.crossed_frame = timestamp_s, frame_number
            self._reclassify(track, timestamp_s, frame_number)

    def counts(self) -> InterestCounts:
        counts = InterestCounts()
        for track in self.tracks.values():
            if track.outcome == self.ENTERED:
                counts.entered += 1
            elif track.outcome == self.PASSED_BY:
                counts.passed_by += 1
        return counts

    def outcome_of(self, track_id: int) -> str | None:
        track = self.tracks.get(int(track_id))
        return track.outcome if track else None

    def looking_s(self, track_id: int) -> float:
        track = self.tracks.get(int(track_id))
        return track.looking_s if track else 0.0

    def label(self, track_id: int) -> str:
        """Keterangan singkat per track untuk video beranotasi."""
        track = self.tracks.get(int(track_id))
        if track is None or track.looking_s == 0.0:
            return ""
        if track.outcome is None:
            return f"look {track.looking_s:.1f}/{self.threshold_s:g}s"
        return f"INTERESTED:{track.outcome}"

    def records(self) -> list[InterestRecord]:
        """Satu catatan per orang yang berminat: masuk atau lewat, dan kapan."""
        return [
            InterestRecord(
                track_id=track.track_id,
                outcome=track.outcome,
                qualified_frame=track.qualified_frame or 0,
                qualified_time_s=round(track.qualified_s or 0.0, 3),
                crossed_frame=track.crossed_frame,
                crossed_time_s=(
                    round(track.crossed_s, 3) if track.crossed_s is not None else None
                ),
            )
            for track in sorted(self.tracks.values(), key=lambda t: t.track_id)
            if track.outcome is not None
        ]

    def _reclassify(
        self, track: _TrackInterest, timestamp_s: float, frame_number: int
    ) -> bool:
        if track.looking_s >= self.threshold_s:
            outcome = self.ENTERED if track.crossed_s is not None else self.PASSED_BY
        else:
            outcome = track.outcome
        if outcome == track.outcome:
            return False
        if track.outcome is None:
            track.qualified_s, track.qualified_frame = timestamp_s, frame_number
        track.history.append(f"{timestamp_s:.2f}s {outcome}")
        track.outcome = outcome
        return True
