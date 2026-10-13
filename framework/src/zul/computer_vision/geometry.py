"""
Hitungan geometri untuk kotak deteksi, titik, poligon, dan arah.

Gunanya:
    Bahan dasar aturan perilaku di video: titik jangkar seseorang, apakah
    titik itu ada di dalam zona, zona mana yang ia tempati, dan apakah
    arah kepalanya menunjuk ke sebuah target. Hanya butuh numpy, jadi
    aturan bisa diuji tanpa model, tanpa video, dan tanpa OpenCV.

Cara pakai:
    import numpy as np
    from zul.computer_vision.geometry import (
        box_anchors, zone_membership, points_toward,
    )

    boxes = np.array([[100, 50, 160, 230], [400, 80, 450, 260]])
    anchors = box_anchors(boxes, ratio=1 / 6)       # 1/6 dari atas kotak
    zones = [np.array([[0, 0], [300, 0], [300, 300], [0, 300]])]
    zone_membership(zones, anchors)                  # array([ 0, -1])

    points_toward((1, 0), origin=(0, 0), target=(10, 2), cone_deg=30)  # True

Semua koordinat memakai sistem gambar: x ke kanan, y ke bawah.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

EPSILON = 1e-6

# --------------------------------------------------------------------------
# Kotak
# --------------------------------------------------------------------------
#
# Kotak selalu berformat xyxy: (x1, y1, x2, y2). Seseorang diwakili sebuah
# titik di kotaknya, karena aturan menghitung orang, bukan kotak. Rasio
# 1/6 dari atas jatuh di sekitar kepala, dan rasio 1 berada di kaki.
#


def box_anchor(xyxy: Sequence[float], ratio: float = 0.5) -> np.ndarray:
    """Satu titik di kotak: tengah secara horizontal, `ratio` dari atas."""
    x1, y1, x2, y2 = (float(value) for value in xyxy[:4])
    return np.array([(x1 + x2) / 2.0, y1 + (y2 - y1) * ratio], dtype=np.float64)


def box_anchors(boxes: np.ndarray, ratio: float = 0.5) -> np.ndarray:
    """`box_anchor` untuk array `(n, 4)`, hasilnya `(n, 2)`."""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    x1, y1, x2, y2 = boxes.T
    return np.stack([(x1 + x2) / 2.0, y1 + (y2 - y1) * ratio], axis=1)


def foot_points(boxes: np.ndarray) -> np.ndarray:
    """Titik tengah bawah setiap kotak: tempat orang menyentuh lantai."""
    return box_anchors(boxes, ratio=1.0)


def box_heights(boxes: np.ndarray) -> np.ndarray:
    """Tinggi setiap kotak dalam piksel."""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    return boxes[:, 3] - boxes[:, 1]


def shrink_to_point(points: np.ndarray, size: float = 1.0) -> np.ndarray:
    """Kotak kecil di sekeliling setiap titik, untuk alat yang hanya menerima kotak."""
    points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    return np.column_stack(
        [
            points[:, 0] - size,
            points[:, 1] - size,
            points[:, 0] + size,
            points[:, 1] + size,
        ]
    )


# --------------------------------------------------------------------------
# Tumpang Tindih Kotak
# --------------------------------------------------------------------------
#
# IoU ialah luas irisan dua kotak dibagi luas gabungannya: 1 untuk kotak
# yang sama persis, 0 untuk kotak yang terpisah. Tracker menggunakan
# IoU untuk memasangkan track dengan deteksi di frame berikutnya.
#


def box_iou(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Matriks IoU `(n, m)` antara setiap kotak `first` dan setiap kotak `second`."""
    a = np.asarray(first, dtype=np.float64).reshape(-1, 4)
    b = np.asarray(second, dtype=np.float64).reshape(-1, 4)
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    top_left = np.maximum(a[:, None, :2], b[None, :, :2])
    bottom_right = np.minimum(a[:, None, 2:], b[None, :, 2:])
    sides = np.clip(bottom_right - top_left, 0, None)
    inter = sides[..., 0] * sides[..., 1]
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    union = area_a[:, None] + area_b[None, :] - inter
    return np.divide(inter, union, out=np.zeros_like(inter), where=union > 0)


def non_max_suppression(
    boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.7
) -> np.ndarray:
    """Indeks kotak yang dipertahankan, dari skor tertinggi, tanpa kotak kembar.

    Kotak yang IoU-nya dengan kotak berskor lebih tinggi melebihi
    `iou_threshold` dibuang. Indeksnya urut naik, sesuai urutan masukan.
    """
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    order = np.argsort(-np.asarray(scores, dtype=np.float64), kind="stable")
    overlap = box_iou(boxes, boxes)
    keep: list[int] = []
    removed = np.zeros(len(boxes), dtype=bool)
    for index in order:
        if removed[index]:
            continue
        keep.append(int(index))
        removed |= overlap[index] > iou_threshold
    return np.array(sorted(keep), dtype=int)


# --------------------------------------------------------------------------
# Poligon
# --------------------------------------------------------------------------
#
# Titik yang tepat berada di garis tepi dihitung di dalam, sama dengan
# cv2.pointPolygonTest. Pengujian memakai ray casting, sehingga satu
# panggilan dapat memeriksa banyak titik sekaligus tanpa OpenCV.
#


def as_polygon(polygon: Sequence) -> np.ndarray:
    """Poligon sebagai array `(n, 2)` float, dari list atau array apa pun."""
    return np.asarray(polygon, dtype=np.float64).reshape(-1, 2)


def polygon_centroid(polygon: Sequence) -> np.ndarray:
    """Rata-rata titik sudut sebuah poligon."""
    return as_polygon(polygon).mean(axis=0)


def points_in_polygon(polygon: Sequence, points: np.ndarray) -> np.ndarray:
    """Untuk setiap titik: apakah ia di dalam poligon, atau tepat di tepinya."""
    vertices = as_polygon(polygon)
    points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    if len(vertices) < 3 or len(points) == 0:
        return np.zeros(len(points), dtype=bool)

    x, y = points[:, :1], points[:, 1:]
    x1, y1 = vertices[:, 0][None, :], vertices[:, 1][None, :]
    x2, y2 = np.roll(vertices[:, 0], -1)[None, :], np.roll(vertices[:, 1], -1)[None, :]

    cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    within = (
        (np.minimum(x1, x2) - EPSILON <= x)
        & (x <= np.maximum(x1, x2) + EPSILON)
        & (np.minimum(y1, y2) - EPSILON <= y)
        & (y <= np.maximum(y1, y2) + EPSILON)
    )
    on_edge = ((np.abs(cross) <= EPSILON) & within).any(axis=1)

    straddles = (y1 > y) != (y2 > y)
    height = np.where(y2 == y1, 1.0, y2 - y1)
    crossing_x = x1 + (y - y1) * (x2 - x1) / height
    inside = ((straddles & (x < crossing_x)).sum(axis=1) % 2) == 1
    return inside | on_edge


def point_in_polygon(polygon: Sequence, point: Sequence[float]) -> bool:
    """Apakah satu titik ada di dalam poligon, atau tepat di tepinya?"""
    return bool(points_in_polygon(polygon, np.asarray(point, dtype=np.float64))[0])


def zone_membership(polygons: Sequence[Sequence], points: np.ndarray) -> np.ndarray:
    """Indeks zona pertama yang memuat setiap titik; -1 jika di luar semua zona.

    Urutan poligon berarti: titik di area yang tumpang tindih masuk ke zona
    yang ditulis lebih dulu.
    """
    points = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    membership = np.full(len(points), -1, dtype=int)
    for index, polygon in enumerate(polygons or []):
        unclaimed = membership < 0
        if not unclaimed.any():
            break
        inside = points_in_polygon(polygon, points[unclaimed])
        membership[np.flatnonzero(unclaimed)[inside]] = index
    return membership


def count_per_zone(zone_count: int, membership: np.ndarray) -> list[int]:
    """Berapa orang ada di setiap zona saat ini."""
    membership = np.asarray(membership, dtype=int)
    return [int((membership == index).sum()) for index in range(zone_count)]


def as_polygon_list(value: Sequence | None) -> list[np.ndarray]:
    """Satu poligon atau daftar poligon, dari config, menjadi daftar poligon int32.

    Poligon dengan kurang dari tiga titik dibuang, karena tidak punya isi.
    """
    if value is None or len(value) == 0:
        return []
    first = value[0]
    single = len(first) == 2 and not isinstance(first[0], list | tuple | np.ndarray)
    polygons = [value] if single else list(value)
    return [
        np.asarray(p, dtype=np.int32).reshape(-1, 2) for p in polygons if len(p) >= 3
    ]


def line_midpoint(points: Sequence[Sequence[float]] | None) -> np.ndarray | None:
    """Titik tengah sebuah garis dua titik, atau None jika garis tidak ada."""
    if points is None or len(points) < 2:
        return None
    start = np.asarray(points[0][:2], dtype=np.float64)
    end = np.asarray(points[1][:2], dtype=np.float64)
    return (start + end) / 2.0


# --------------------------------------------------------------------------
# Arah
# --------------------------------------------------------------------------
#
# Arah adalah vektor satuan. Arah yang panjangnya nol tidak punya makna,
# jadi fungsi di sini mengembalikan None atau NaN, bukan arah tebakan,
# sehingga aturan di atasnya bisa menganggapnya sebagai tidak tahu.
#


def unit(vector: Sequence[float]) -> np.ndarray | None:
    """Vektor dengan panjang 1, atau None jika vektor tidak punya arah."""
    array = np.asarray(vector, dtype=np.float64)
    norm = float(np.linalg.norm(array))
    if norm < EPSILON:
        return None
    return array / norm


def angle_between(first: Sequence[float], second: Sequence[float]) -> float:
    """Sudut dalam derajat antara dua vektor, 0-180; NaN jika salah satunya nol."""
    a, b = unit(first), unit(second)
    if a is None or b is None:
        return float("nan")
    return float(np.degrees(np.arccos(np.clip(float(np.dot(a, b)), -1.0, 1.0))))


def points_toward(
    direction: Sequence[float] | None,
    origin: Sequence[float],
    target: Sequence[float],
    cone_deg: float = 90.0,
) -> bool:
    """Apakah `direction` dari `origin` jatuh dalam `cone_deg` dari arah ke `target`?

    Orang yang berdiri tepat di target dianggap menghadapnya, karena arah ke
    target tidak bisa dihitung.
    """
    if direction is None:
        return False
    bearing = np.asarray(target, dtype=np.float64) - np.asarray(
        origin, dtype=np.float64
    )
    if unit(bearing) is None:
        return True
    return angle_between(direction, bearing) <= cone_deg


def euclidean(first: Sequence[float], second: Sequence[float]) -> float:
    """Jarak garis lurus antara dua titik, dalam satuan titik itu."""
    difference = np.asarray(first, dtype=np.float64) - np.asarray(
        second, dtype=np.float64
    )
    return float(np.linalg.norm(difference))


def direction_angle(direction: Sequence[float] | None) -> float | None:
    """Sudut arah dalam derajat di ruang gambar: 0 kanan, 90 bawah, 180 kiri."""
    if direction is None:
        return None
    return float(np.degrees(np.arctan2(direction[1], direction[0])))
