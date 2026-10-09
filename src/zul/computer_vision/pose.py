"""
Arah hadap seseorang, dibaca dari keypoint pose COCO-17.

Gunanya:
    Menjawab "ke mana orang ini menghadap?" dari keluaran model pose
    seperti yolo11m-pose. Arah kepala dibaca dari hidung dan telinga.
    Saat wajah tidak terlihat, misalnya orang membelakangi kamera, arah
    badan dibaca dari garis bahu. Hanya butuh numpy.

Cara pakai:
    from zul.computer_vision.pose import facing_directions, facing_target

    # keypoints_xy: (n, 17, 2), keypoints_conf: (n, 17), dari model pose
    directions, sources = facing_directions(keypoints_xy, keypoints_conf)
    sources             # ["head", "body", ""]: sumber arah per orang

    # apakah setiap orang menghadap titik target, misalnya pintu toko?
    facing_target(boxes, directions, target=(640, 400), cone_deg=90)

Keypoint dengan confidence di bawah `min_confidence` diabaikan, karena
keypoint tebakan lebih buruk daripada tidak tahu arahnya.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .geometry import box_anchor, points_toward, polygon_centroid, unit

# --------------------------------------------------------------------------
# Indeks Keypoint COCO-17
# --------------------------------------------------------------------------

NOSE, LEFT_EYE, RIGHT_EYE, LEFT_EAR, RIGHT_EAR = 0, 1, 2, 3, 4
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
FACE_KEYPOINTS = (NOSE, LEFT_EYE, RIGHT_EYE, LEFT_EAR, RIGHT_EAR)

SKELETON_EDGES = (
    (15, 13), (13, 11), (16, 14), (14, 12), (11, 12), (5, 11), (6, 12),
    (5, 6), (5, 7), (6, 8), (7, 9), (8, 10), (1, 2), (0, 1), (0, 2),
    (1, 3), (2, 4), (3, 5), (4, 6),
)  # fmt: skip

DEFAULT_MIN_CONFIDENCE = 0.35
DEFAULT_MIN_SHOULDER_SPAN_PX = 4.0
DEFAULT_ANCHOR_RATIO = 1 / 6


def _visible(confidence: Sequence[float] | None, index: int, minimum: float) -> bool:
    return confidence is None or float(confidence[index]) >= minimum


# --------------------------------------------------------------------------
# Arah Satu Orang
# --------------------------------------------------------------------------
#
# Arah badan adalah garis bahu yang diputar 90 derajat. Model pose memberi
# label bahu secara anatomis, jadi orang yang menghadap kamera dan orang
# yang membelakanginya menghasilkan arah berlawanan tanpa cabang if.
#


def face_direction(
    xy: np.ndarray,
    confidence: Sequence[float] | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> np.ndarray | None:
    """Arah kepala sebagai vektor satuan: dari tengah telinga ke hidung."""
    if not _visible(confidence, NOSE, min_confidence):
        return None
    ears = [i for i in (LEFT_EAR, RIGHT_EAR) if _visible(confidence, i, min_confidence)]
    if not ears:
        return None
    nose = np.asarray(xy[NOSE], dtype=np.float64)
    return unit(nose - np.mean([xy[i] for i in ears], axis=0))


def body_direction(
    xy: np.ndarray,
    confidence: Sequence[float] | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    min_shoulder_span_px: float = DEFAULT_MIN_SHOULDER_SPAN_PX,
) -> np.ndarray | None:
    """Arah badan dari garis bahu, untuk orang yang wajahnya tidak terlihat.

    Bahu yang jaraknya kurang dari `min_shoulder_span_px` tidak dipakai,
    karena orang yang terlihat dari samping tidak punya garis bahu yang jelas.
    """
    if xy is None or len(xy) <= RIGHT_SHOULDER:
        return None
    if not (
        _visible(confidence, LEFT_SHOULDER, min_confidence)
        and _visible(confidence, RIGHT_SHOULDER, min_confidence)
    ):
        return None
    span = np.asarray(xy[RIGHT_SHOULDER], dtype=np.float64) - np.asarray(
        xy[LEFT_SHOULDER], dtype=np.float64
    )
    if float(np.linalg.norm(span)) < min_shoulder_span_px:
        return None
    return unit(np.array([span[1], -span[0]], dtype=np.float64))


def facing_direction(
    xy: np.ndarray,
    confidence: Sequence[float] | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    min_shoulder_span_px: float = DEFAULT_MIN_SHOULDER_SPAN_PX,
) -> tuple[np.ndarray | None, str]:
    """Arah terbaik untuk satu orang, dan sumbernya: "head", "body", atau ""."""
    head = face_direction(xy, confidence, min_confidence)
    if head is not None:
        return head, "head"
    body = body_direction(xy, confidence, min_confidence, min_shoulder_span_px)
    if body is not None:
        return body, "body"
    return None, ""


def face_box(
    xy: np.ndarray,
    confidence: Sequence[float] | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> np.ndarray | None:
    """Kotak xyxy di sekeliling keypoint wajah yang terlihat, atau None."""
    visible = [i for i in FACE_KEYPOINTS if _visible(confidence, i, min_confidence)]
    if len(visible) < 2:
        return None
    points = np.asarray([xy[i] for i in visible], dtype=np.float64)
    return np.concatenate([points.min(axis=0), points.max(axis=0)])


# --------------------------------------------------------------------------
# Arah Semua Orang Di Satu Frame
# --------------------------------------------------------------------------


def facing_directions(
    keypoints_xy: np.ndarray | None,
    keypoints_conf: np.ndarray | None = None,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    min_shoulder_span_px: float = DEFAULT_MIN_SHOULDER_SPAN_PX,
) -> tuple[list[np.ndarray | None], list[str]]:
    """`facing_direction` untuk setiap orang: daftar arah dan daftar sumbernya.

    `keypoints_xy` boleh None, misalnya frame tanpa orang: hasilnya kosong.
    """
    directions, sources = [], []
    for row in range(len(keypoints_xy) if keypoints_xy is not None else 0):
        confidence = keypoints_conf[row] if keypoints_conf is not None else None
        direction, source = facing_direction(
            keypoints_xy[row], confidence, min_confidence, min_shoulder_span_px
        )
        directions.append(direction)
        sources.append(source)
    return directions, sources


def match_poses_to_boxes(boxes: np.ndarray, keypoints_xy: np.ndarray) -> dict[int, int]:
    """Pasangan indeks kotak ke indeks pose: kotak mana yang memuat hidung pose itu.

    Dipakai saat orang dideteksi oleh satu model dan pose oleh model lain.
    Setiap pose hanya dipasangkan sekali, ke kotak pertama yang memuatnya.
    """
    pairing: dict[int, int] = {}
    taken: set[int] = set()
    for box_index, (x1, y1, x2, y2) in enumerate(np.asarray(boxes).reshape(-1, 4)):
        for pose_index in range(len(keypoints_xy)):
            if pose_index in taken:
                continue
            nose_x, nose_y = keypoints_xy[pose_index][NOSE][:2]
            if x1 <= nose_x <= x2 and y1 <= nose_y <= y2:
                pairing[box_index] = pose_index
                taken.add(pose_index)
                break
    return pairing


def by_box(pairing: dict[int, int], values: Sequence, count: int, empty=None) -> list:
    """Susun ulang nilai per pose menjadi per kotak; `empty` untuk kotak tanpa pose."""
    per_box = [empty] * count
    for box_index, pose_index in pairing.items():
        if 0 <= box_index < count and 0 <= pose_index < len(values):
            per_box[box_index] = values[pose_index]
    return per_box


# --------------------------------------------------------------------------
# Menghadap Target
# --------------------------------------------------------------------------
#
# Arah diukur dari titik kepala, yaitu 1/6 dari atas kotak, ke
# target. Kerucut 90 derajat sama dengan setengah bidang di
# depan orang itu; kerucut yang lebih sempit memotong
# waktu menghadap yang dihitung aturan di atasnya.
#


def facing_target(
    boxes: np.ndarray,
    directions: Sequence[np.ndarray | None],
    target: Sequence[float] | None,
    cone_deg: float = 90.0,
    anchor_ratio: float = DEFAULT_ANCHOR_RATIO,
) -> list[bool]:
    """Apakah kepala setiap orang menunjuk ke satu `target`?"""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    if target is None:
        return [False] * len(boxes)
    flags = []
    for row, box in enumerate(boxes):
        direction = directions[row] if row < len(directions) else None
        head = box_anchor(box, anchor_ratio)
        flags.append(points_toward(direction, head, target, cone_deg))
    return flags


def zone_targets(
    polygons: Sequence[Sequence], anchors: Sequence[Sequence[float]] | None = None
) -> list[np.ndarray]:
    """Titik yang harus dihadapi per zona: `anchors` jika lengkap, selain itu centroid.

    Centroid hanya tepat jika poligon menutupi objeknya, misalnya rak,
    bukan lantai di depannya. Untuk poligon lantai, isi `anchors`.
    """
    if anchors is not None and len(anchors) == len(polygons):
        return [np.asarray(point[:2], dtype=np.float64) for point in anchors]
    return [polygon_centroid(polygon) for polygon in polygons]


def facing_zone_targets(
    boxes: np.ndarray,
    directions: Sequence[np.ndarray | None],
    membership: Sequence[int],
    targets: Sequence[Sequence[float]],
    cone_deg: float = 90.0,
    anchor_ratio: float = DEFAULT_ANCHOR_RATIO,
) -> list[bool]:
    """Apakah setiap orang menghadap target zona tempat ia berdiri?"""
    boxes = np.asarray(boxes, dtype=np.float64).reshape(-1, 4)
    flags = []
    for row, box in enumerate(boxes):
        zone = int(membership[row]) if row < len(membership) else -1
        direction = directions[row] if row < len(directions) else None
        if zone < 0 or zone >= len(targets) or direction is None:
            flags.append(False)
            continue
        head = box_anchor(box, anchor_ratio)
        flags.append(points_toward(direction, head, targets[zone], cone_deg))
    return flags
