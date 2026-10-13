"""
Tracking ByteTrack: id yang sama untuk orang yang sama di setiap frame.

Gunanya:
    Detektor hanya melihat satu frame. Tracker memasangkan deteksi frame ini
    dengan track dari frame sebelumnya, jadi setiap orang punya satu id
    selama ia terlihat. Algoritmanya ByteTrack (Zhang dkk., 2022): deteksi
    berskor tinggi dipasangkan lebih dulu, lalu deteksi berskor rendah
    dipakai untuk menyambung track yang tertutup sebagian. Ditulis sendiri
    di Zul dengan numpy; pemasangan memakai zul.adapters.lap. Butuh extra
    tracking: `pip install "zul[tracking]"`.

Cara pakai:
    from zul.computer_vision.tracking import ByteTracker

    tracker = ByteTracker(frame_rate=10)
    people = tracker.update(people)      # Detections dengan tracker_id terisi
    people.tracker_id

ByteTracker menerima objek apa pun yang punya xyxy, confidence, dan
class_id sebagai array, bisa dipotong dengan indeks, dan berupa dataclass,
misalnya Detections dari zul.computer_vision.detection.
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum
from typing import Any

import numpy as np

from ..adapters import lap as lap_adapter
from .geometry import box_iou

# --------------------------------------------------------------------------
# Filter Kalman
# --------------------------------------------------------------------------
#
# Setiap track disimpan sebagai pusat kotak, rasio lebar per tinggi, dan
# tinggi, ditambah kecepatan keempatnya. Filter Kalman menebak posisi
# di frame berikutnya, lalu mengoreksinya dengan deteksi yang cocok.
#
# Ketidakpastian dibuat sebanding dengan tinggi kotak, jadi orang di
# dekat kamera boleh bergeser lebih banyak piksel dibanding orang
# yang jauh. Bobotnya 1/20 untuk posisi, 1/160 untuk kecepatan.
#

POSITION_WEIGHT = 1 / 20
VELOCITY_WEIGHT = 1 / 160


def _to_xyah(xyxy: np.ndarray) -> np.ndarray:
    width, height = xyxy[2] - xyxy[0], xyxy[3] - xyxy[1]
    centre = (xyxy[:2] + xyxy[2:]) / 2
    return np.array([centre[0], centre[1], width / max(height, 1e-6), height])


def _to_xyxy(xyah: np.ndarray) -> np.ndarray:
    height = xyah[3]
    width = xyah[2] * height
    return np.array(
        [
            xyah[0] - width / 2,
            xyah[1] - height / 2,
            xyah[0] + width / 2,
            xyah[1] + height / 2,
        ]
    )


class KalmanFilter:
    """Filter Kalman kecepatan tetap untuk kotak berformat (x, y, rasio, tinggi)."""

    def __init__(self) -> None:
        self.motion = np.eye(8)
        self.motion[:4, 4:] = np.eye(4)
        self.observation = np.eye(4, 8)

    def initiate(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Keadaan awal dari satu pengukuran: posisi diketahui, kecepatan nol."""
        height = measurement[3]
        std = [
            2 * POSITION_WEIGHT * height,
            2 * POSITION_WEIGHT * height,
            1e-2,
            2 * POSITION_WEIGHT * height,
            10 * VELOCITY_WEIGHT * height,
            10 * VELOCITY_WEIGHT * height,
            1e-5,
            10 * VELOCITY_WEIGHT * height,
        ]
        mean = np.concatenate([measurement, np.zeros(4)])
        return mean, np.diag(np.square(std))

    def predict(
        self, mean: np.ndarray, covariance: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Keadaan satu frame ke depan."""
        height = mean[3]
        std = [
            POSITION_WEIGHT * height,
            POSITION_WEIGHT * height,
            1e-2,
            POSITION_WEIGHT * height,
            VELOCITY_WEIGHT * height,
            VELOCITY_WEIGHT * height,
            1e-5,
            VELOCITY_WEIGHT * height,
        ]
        mean = self.motion @ mean
        covariance = self.motion @ covariance @ self.motion.T + np.diag(np.square(std))
        return mean, covariance

    def update(
        self, mean: np.ndarray, covariance: np.ndarray, measurement: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Keadaan setelah dikoreksi oleh satu pengukuran."""
        height = mean[3]
        noise = np.diag(
            np.square(
                [
                    POSITION_WEIGHT * height,
                    POSITION_WEIGHT * height,
                    1e-1,
                    POSITION_WEIGHT * height,
                ]
            )
        )
        projected_mean = self.observation @ mean
        projected_cov = self.observation @ covariance @ self.observation.T + noise
        gain = np.linalg.solve(projected_cov, (covariance @ self.observation.T).T).T
        mean = mean + (measurement - projected_mean) @ gain.T
        covariance = covariance - gain @ projected_cov @ gain.T
        return mean, covariance


# --------------------------------------------------------------------------
# Track
# --------------------------------------------------------------------------


class TrackState(Enum):
    """Keadaan sebuah track: sedang terlihat, hilang sementara, atau dihapus."""

    TRACKED = "tracked"
    LOST = "lost"
    REMOVED = "removed"


class Track:
    """Satu orang yang dilacak: keadaan Kalman, skor, dan deteksi terakhirnya."""

    def __init__(self, xyxy: np.ndarray, score: float, class_id: int, row: int):
        self.measurement = _to_xyah(np.asarray(xyxy, dtype=np.float64))
        self.score = float(score)
        self.class_id = int(class_id)
        self.row = row
        self.track_id = 0
        self.state = TrackState.TRACKED
        self.is_activated = False
        self.mean: np.ndarray | None = None
        self.covariance: np.ndarray | None = None
        self.start_frame = 0
        self.frame_id = 0

    @property
    def xyxy(self) -> np.ndarray:
        """Kotak track sekarang: hasil filter Kalman, atau deteksi pertamanya."""
        return _to_xyxy(self.mean[:4] if self.mean is not None else self.measurement)

    def activate(self, kalman: KalmanFilter, track_id: int, frame_id: int) -> None:
        self.track_id = track_id
        self.mean, self.covariance = kalman.initiate(self.measurement)
        self.state = TrackState.TRACKED
        self.is_activated = frame_id == 1
        self.start_frame = self.frame_id = frame_id

    def update(self, kalman: KalmanFilter, detection: Track, frame_id: int) -> None:
        """Koreksi dengan deteksi yang cocok; track dianggap terlihat lagi."""
        self.mean, self.covariance = kalman.update(
            self.mean, self.covariance, detection.measurement
        )
        self.score, self.class_id, self.row = (
            detection.score,
            detection.class_id,
            detection.row,
        )
        self.state = TrackState.TRACKED
        self.is_activated = True
        self.frame_id = frame_id


# --------------------------------------------------------------------------
# ByteTrack
# --------------------------------------------------------------------------
#
# Satu frame melewati empat pemasangan. Track yang terlihat atau hilang
# dipasangkan dengan deteksi berskor tinggi, lalu sisa track dengan
# deteksi berskor rendah. Track yang baru muncul satu frame hanya
# dipasangkan dengan sisa deteksi berskor tinggi, lalu deteksi
# yang masih tersisa menjadi track baru jika skornya cukup.
#
# Track baru belum dikembalikan sampai cocok lagi di frame berikutnya,
# kecuali di frame pertama. Satu deteksi yang hanya muncul sekali
# tidak pernah menjadi orang tambahan di hitungan berikutnya.
#


class ByteTracker:
    """ByteTrack: id yang bertahan antar frame untuk setiap deteksi."""

    def __init__(
        self,
        frame_rate: float = 30.0,
        high_threshold: float = 0.35,
        low_threshold: float = 0.1,
        new_track_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        match_threshold: float = 0.8,
    ) -> None:
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.new_track_threshold = new_track_threshold
        self.match_threshold = match_threshold
        self.max_lost_frames = int(round(lost_track_buffer * frame_rate / 30.0))
        self.kalman = KalmanFilter()
        self.frame_id = 0
        self.tracked: list[Track] = []
        self.lost: list[Track] = []
        self._next_id = 1

    def update(self, detections: Any) -> Any:
        """Deteksi frame ini yang punya id track; yang belum dikonfirmasi dibuang.

        Kotak di hasil diganti kotak hasil filter Kalman, dan semua kolom
        lain, termasuk keypoint, tetap sejajar dengan kotaknya.
        """
        tracks = self.step(
            np.asarray(detections.xyxy, dtype=np.float64).reshape(-1, 4),
            np.asarray(detections.confidence, dtype=np.float64),
            np.asarray(detections.class_id),
        )
        if not tracks:
            empty = detections[np.zeros(len(detections.xyxy), dtype=bool)]
            return replace(empty, tracker_id=np.empty(0, dtype=int))
        tracked = detections[np.array([track.row for track in tracks], dtype=int)]
        tracked.xyxy = np.array([track.xyxy for track in tracks], dtype=np.float64)
        tracked.tracker_id = np.array([track.track_id for track in tracks], dtype=int)
        return tracked

    def step(
        self, xyxy: np.ndarray, scores: np.ndarray, class_ids: np.ndarray
    ) -> list[Track]:
        """Maju satu frame dengan array mentah. Mengembalikan track aktif."""
        self.frame_id += 1
        high = scores >= self.high_threshold
        low = (scores > self.low_threshold) & ~high
        strong = [
            Track(xyxy[i], scores[i], class_ids[i], int(i))
            for i in np.flatnonzero(high)
        ]
        weak = [
            Track(xyxy[i], scores[i], class_ids[i], int(i)) for i in np.flatnonzero(low)
        ]

        confirmed = [t for t in self.tracked if t.is_activated]
        unconfirmed = [t for t in self.tracked if not t.is_activated]
        pool = confirmed + [t for t in self.lost if t not in confirmed]
        for track in pool:
            if track.state is not TrackState.TRACKED:
                track.mean[7] = 0.0
            track.mean, track.covariance = self.kalman.predict(
                track.mean, track.covariance
            )

        activated: list[Track] = []
        found_again: list[Track] = []
        lost_now: list[Track] = []
        removed_now: list[Track] = []

        cost = _fuse_score(_iou_cost(pool, strong), strong)
        matches, free_tracks, free_strong = lap_adapter.assign(
            cost, self.match_threshold
        )
        for row, col in matches:
            self._refresh(pool[row], strong[col], activated, found_again)

        remaining = [
            pool[i] for i in free_tracks if pool[i].state is TrackState.TRACKED
        ]
        matches, free_remaining, _ = lap_adapter.assign(_iou_cost(remaining, weak), 0.5)
        for row, col in matches:
            self._refresh(remaining[row], weak[col], activated, found_again)
        for row in free_remaining:
            track = remaining[row]
            if track.state is not TrackState.LOST:
                track.state = TrackState.LOST
                lost_now.append(track)

        leftovers = [strong[i] for i in free_strong]
        cost = _fuse_score(_iou_cost(unconfirmed, leftovers), leftovers)
        matches, free_unconfirmed, free_leftovers = lap_adapter.assign(cost, 0.7)
        for row, col in matches:
            unconfirmed[row].update(self.kalman, leftovers[col], self.frame_id)
            activated.append(unconfirmed[row])
        for row in free_unconfirmed:
            unconfirmed[row].state = TrackState.REMOVED
            removed_now.append(unconfirmed[row])

        for col in free_leftovers:
            track = leftovers[col]
            if track.score < self.new_track_threshold:
                continue
            track.activate(self.kalman, self._next_id, self.frame_id)
            self._next_id += 1
            activated.append(track)

        for track in self.lost:
            if self.frame_id - track.frame_id > self.max_lost_frames:
                track.state = TrackState.REMOVED
                removed_now.append(track)

        self.tracked = _unique(
            [t for t in self.tracked if t.state is TrackState.TRACKED]
            + activated
            + found_again
        )
        lost = [t for t in self.lost if t not in self.tracked] + lost_now
        self.lost = [t for t in _unique(lost) if t not in removed_now]
        self.tracked, self.lost = _drop_duplicates(self.tracked, self.lost)
        return [t for t in self.tracked if t.is_activated]

    def _refresh(
        self,
        track: Track,
        detection: Track,
        activated: list[Track],
        found_again: list[Track],
    ) -> None:
        was_tracked = track.state is TrackState.TRACKED
        track.update(self.kalman, detection, self.frame_id)
        (activated if was_tracked else found_again).append(track)


def _iou_cost(tracks: list[Track], detections: list[Track]) -> np.ndarray:
    if not tracks or not detections:
        return np.zeros((len(tracks), len(detections)))
    first = np.array([track.xyxy for track in tracks])
    second = np.array([detection.xyxy for detection in detections])
    return 1.0 - box_iou(first, second)


def _fuse_score(cost: np.ndarray, detections: list[Track]) -> np.ndarray:
    """Gabungkan IoU dengan skor deteksi: deteksi yang yakin lebih mudah cocok."""
    if cost.size == 0:
        return cost
    scores = np.array([detection.score for detection in detections])
    return 1.0 - (1.0 - cost) * scores[None, :]


def _unique(tracks: list[Track]) -> list[Track]:
    seen: set[int] = set()
    result = []
    for track in tracks:
        if id(track) not in seen:
            seen.add(id(track))
            result.append(track)
    return result


def _drop_duplicates(
    tracked: list[Track], lost: list[Track]
) -> tuple[list[Track], list[Track]]:
    """Buang track kembar antara daftar terlihat dan hilang; yang lebih tua menang."""
    if not tracked or not lost:
        return tracked, lost
    overlap = 1.0 - _iou_cost(tracked, lost)
    drop_tracked, drop_lost = set(), set()
    for p, q in zip(*np.nonzero(overlap > 0.85), strict=True):
        age_p = tracked[p].frame_id - tracked[p].start_frame
        age_q = lost[q].frame_id - lost[q].start_frame
        if age_p > age_q:
            drop_lost.add(q)
        else:
            drop_tracked.add(p)
    return (
        [t for i, t in enumerate(tracked) if i not in drop_tracked],
        [t for i, t in enumerate(lost) if i not in drop_lost],
    )
