"""
Menggambar hasil analisis di atas frame video dengan OpenCV.

Gunanya:
    Kotak orang, label, panel teks di sudut, zona, panah arah hadap,
    kerangka pose, dan masker area yang diabaikan. Aturan yang tidak
    terlihat sulit diperiksa, jadi semua yang dipakai aturan bisa digambar.
    Butuh extra vision: `pip install "zul[vision]"`.

Cara pakai:
    from zul.computer_vision import draw

    scene = frame.copy()
    draw.draw_polygons(scene, zones, "#00d4ff", fill_alpha=0.2)
    for box, track_id in zip(boxes, tracker_ids):
        draw.draw_labelled_box(scene, box, f"#{track_id}", draw.track_color(track_id))
    draw.draw_text_block(scene, ["orang di rak = 3"], top=58)

Warna boleh ditulis "#RRGGBB" atau tuple BGR seperti (0, 230, 118).
"""

from __future__ import annotations

import colorsys
from collections.abc import Sequence
from enum import Enum

import cv2
import numpy as np

from .pose import SKELETON_EDGES

FONT = cv2.FONT_HERSHEY_SIMPLEX
GOLDEN_ANGLE_DEG = 137.508

Color = str | tuple[int, int, int]


def bgr(color: Color) -> tuple[int, int, int]:
    """Warna "#RRGGBB" atau tuple BGR sebagai tuple BGR untuk OpenCV."""
    if isinstance(color, str):
        value = color.lstrip("#")
        red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
        return blue, green, red
    return tuple(int(channel) for channel in color[:3])


def track_color(track_id: int, saturation: float = 0.85) -> tuple[int, int, int]:
    """Warna BGR yang tetap untuk satu id track, dan berbeda dari id tetangganya."""
    hue = (int(track_id) * GOLDEN_ANGLE_DEG) % 360.0
    red, green, blue = colorsys.hsv_to_rgb(hue / 360.0, saturation, 1.0)
    return round(blue * 255), round(green * 255), round(red * 255)


def text_size(text: str, scale: float = 0.5, thickness: int = 1) -> tuple[int, int]:
    """Lebar dan tinggi teks dalam piksel, seperti yang digambar OpenCV."""
    (width, height), _ = cv2.getTextSize(text, FONT, scale, thickness)
    return width, height


# --------------------------------------------------------------------------
# Kotak Dan Label
# --------------------------------------------------------------------------


class BoxStyle(str, Enum):
    """Cara sebuah kotak digambar."""

    CORNER = "corner"
    RECT = "rect"
    DASHED = "dashed"
    FILLED = "filled"


def draw_box(
    scene: np.ndarray,
    xyxy: Sequence[float],
    color: Color,
    style: BoxStyle = BoxStyle.CORNER,
    thickness: int = 2,
    corner_length: int = 14,
    fill_alpha: float = 0.25,
    dash: int = 8,
) -> np.ndarray:
    """Satu kotak dengan gaya yang diminta."""
    x1, y1, x2, y2 = (int(round(float(v))) for v in xyxy[:4])
    color = bgr(color)

    if style is BoxStyle.RECT:
        cv2.rectangle(scene, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
        return scene
    if style is BoxStyle.FILLED:
        overlay = scene.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, fill_alpha, scene, 1 - fill_alpha, 0, dst=scene)
        cv2.rectangle(scene, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
        return scene
    if style is BoxStyle.DASHED:
        for x in range(x1, x2, dash * 2):
            cv2.line(
                scene, (x, y1), (min(x + dash, x2), y1), color, thickness, cv2.LINE_AA
            )
            cv2.line(
                scene, (x, y2), (min(x + dash, x2), y2), color, thickness, cv2.LINE_AA
            )
        for y in range(y1, y2, dash * 2):
            cv2.line(
                scene, (x1, y), (x1, min(y + dash, y2)), color, thickness, cv2.LINE_AA
            )
            cv2.line(
                scene, (x2, y), (x2, min(y + dash, y2)), color, thickness, cv2.LINE_AA
            )
        return scene

    length = max(1, min(corner_length, (x2 - x1) // 2, (y2 - y1) // 2))
    for cx, cy, dx, dy in (
        (x1, y1, 1, 1),
        (x2, y1, -1, 1),
        (x1, y2, 1, -1),
        (x2, y2, -1, -1),
    ):
        cv2.line(scene, (cx, cy), (cx + dx * length, cy), color, thickness, cv2.LINE_AA)
        cv2.line(scene, (cx, cy), (cx, cy + dy * length), color, thickness, cv2.LINE_AA)
    return scene


def draw_label(
    scene: np.ndarray,
    text: str,
    anchor: Sequence[float],
    color: Color,
    text_color: Color = (0, 0, 0),
    scale: float = 0.4,
    thickness: int = 1,
    padding: int = 2,
    above: bool = True,
) -> np.ndarray:
    """Teks di atas pelat berwarna, di atas `anchor` secara bawaan."""
    if not text:
        return scene
    width, height = text_size(text, scale, thickness)
    plate_h = height + padding * 2
    x, y = int(anchor[0]), int(anchor[1])
    top = max(0, min(y - plate_h if above else y, scene.shape[0] - plate_h))
    left = max(0, min(x, scene.shape[1] - (width + padding * 2)))
    cv2.rectangle(
        scene, (left, top), (left + width + padding * 2, top + plate_h), bgr(color), -1
    )
    cv2.putText(
        scene, text, (left + padding, top + height + padding - 1), FONT, scale,
        bgr(text_color), thickness, cv2.LINE_AA,
    )  # fmt: skip
    return scene


def draw_labelled_box(
    scene: np.ndarray,
    xyxy: Sequence[float],
    label: str,
    color: Color,
    style: BoxStyle = BoxStyle.CORNER,
    **box_options,
) -> np.ndarray:
    """Kotak dan keterangannya sekaligus, keterangan di atas sudut kiri atas."""
    draw_box(scene, xyxy, color, style=style, **box_options)
    return draw_label(scene, label, (xyxy[0], xyxy[1]), color)


# --------------------------------------------------------------------------
# Teks Di Sudut Frame
# --------------------------------------------------------------------------


class Corner(str, Enum):
    """Sudut tempat blok teks menempel."""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


def draw_text_block(
    scene: np.ndarray,
    lines: Sequence[str],
    corner: Corner = Corner.TOP_LEFT,
    color: Color = (255, 255, 255),
    scale: float = 0.55,
    thickness: int = 1,
    margin: int = 12,
    line_height: int = 26,
    top: int | None = None,
    background: Color | None = (0, 0, 0),
) -> np.ndarray:
    """Susun beberapa baris teks menempel ke satu sudut frame.

    `top` menggeser baris pertama ke bawah, misalnya agar tidak menutupi
    cap waktu yang sudah tertulis di video CCTV.
    """
    if not lines:
        return scene
    height, width = scene.shape[:2]
    right = corner in (Corner.TOP_RIGHT, Corner.BOTTOM_RIGHT)
    bottom = corner in (Corner.BOTTOM_LEFT, Corner.BOTTOM_RIGHT)
    first_y = (
        height - margin - (len(lines) - 1) * line_height
        if bottom
        else top if top is not None else margin + line_height
    )
    for row, line in enumerate(lines):
        if not line:
            continue
        text_w, text_h = text_size(line, scale, thickness)
        x = width - margin - text_w if right else margin
        y = first_y + row * line_height
        if background is not None:
            cv2.rectangle(
                scene,
                (x - 4, y - text_h - 4),
                (x + text_w + 4, y + 6),
                bgr(background),
                -1,
            )
        cv2.putText(
            scene, line, (x, y), FONT, scale, bgr(color), thickness, cv2.LINE_AA
        )
    return scene


# --------------------------------------------------------------------------
# Bentuk
# --------------------------------------------------------------------------


def draw_polygons(
    scene: np.ndarray,
    polygons: Sequence[Sequence],
    color: Color,
    thickness: int = 2,
    fill_alpha: float = 0.0,
) -> np.ndarray:
    """Beberapa zona, diwarnai dalam satu kali blend, bukan satu blend per zona."""
    shapes = [np.asarray(p, dtype=np.int32).reshape(-1, 1, 2) for p in (polygons or [])]
    if not shapes:
        return scene
    color = bgr(color)
    if fill_alpha > 0:
        overlay = scene.copy()
        cv2.fillPoly(overlay, shapes, color)
        cv2.addWeighted(overlay, fill_alpha, scene, 1 - fill_alpha, 0, dst=scene)
    if thickness > 0:
        cv2.polylines(scene, shapes, True, color, thickness, cv2.LINE_AA)
    return scene


def draw_line(
    scene: np.ndarray,
    start: Sequence[float],
    end: Sequence[float],
    color: Color,
    thickness: int = 2,
) -> np.ndarray:
    """Satu garis, misalnya garis masuk toko."""
    a = (int(round(start[0])), int(round(start[1])))
    b = (int(round(end[0])), int(round(end[1])))
    cv2.line(scene, a, b, bgr(color), thickness, cv2.LINE_AA)
    return scene


def draw_arrow(
    scene: np.ndarray,
    origin: Sequence[float],
    direction: Sequence[float],
    color: Color,
    length: float,
    thickness: int = 2,
    tip_ratio: float = 0.35,
) -> np.ndarray:
    """Panah sepanjang `length` piksel dari `origin` searah vektor `direction`."""
    start = np.asarray(origin, dtype=np.float64)
    tip = start + np.asarray(direction, dtype=np.float64) * length
    cv2.arrowedLine(
        scene, (int(start[0]), int(start[1])), (int(tip[0]), int(tip[1])), bgr(color),
        thickness, cv2.LINE_AA, tipLength=tip_ratio,
    )  # fmt: skip
    return scene


def draw_point(
    scene: np.ndarray, point: Sequence[float], color: Color, radius: int = 4
) -> np.ndarray:
    """Titik penuh, misalnya titik jangkar yang dipakai uji zona."""
    cv2.circle(
        scene, (int(round(point[0])), int(round(point[1]))), radius, bgr(color), -1
    )
    return scene


def draw_link(
    scene: np.ndarray,
    start: Sequence[float],
    end: Sequence[float],
    color: Color,
    label: str = "",
    thickness: int = 2,
    scale: float = 0.45,
) -> np.ndarray:
    """Garis antara dua titik, berketerangan di tengah, misalnya jarak dalam meter."""
    draw_line(scene, start, end, color, thickness)
    if label:
        middle = (int((start[0] + end[0]) / 2), int((start[1] + end[1]) / 2))
        cv2.putText(scene, label, middle, FONT, scale, bgr(color), 1, cv2.LINE_AA)
    return scene


def draw_skeleton(
    scene: np.ndarray,
    keypoints_xy: np.ndarray | None,
    keypoints_conf: np.ndarray | None = None,
    min_confidence: float = 0.35,
    color: Color = "#E0E0E0",
    vertex_color: Color = "#FFFFFF",
    thickness: int = 1,
    radius: int = 3,
) -> np.ndarray:
    """Kerangka pose COCO-17, hanya keypoint dengan confidence cukup.

    Keypoint yang tidak terdeteksi bernilai (0, 0). Tanpa saringan ini,
    garis anggota badan tertarik ke sudut kiri atas frame.
    """
    if keypoints_xy is None:
        return scene
    for row in range(len(keypoints_xy)):
        xy = keypoints_xy[row]
        conf = keypoints_conf[row] if keypoints_conf is not None else np.ones(len(xy))
        visible = [bool(conf[i] >= min_confidence) for i in range(len(xy))]
        for a, b in SKELETON_EDGES:
            if a < len(xy) and b < len(xy) and visible[a] and visible[b]:
                draw_line(scene, xy[a], xy[b], color, thickness)
        for index, point in enumerate(xy):
            if visible[index]:
                draw_point(scene, point, vertex_color, radius)
    return scene


# --------------------------------------------------------------------------
# Masker Area
# --------------------------------------------------------------------------
#
# Area yang diabaikan dihitamkan sebelum frame masuk ke model,
# jadi deteksi yang tidak diinginkan tidak pernah ada dan
# tidak bisa dihitung dua kali. Masker digambar sekali
# di awal, lalu setiap frame cukup satu bitwise_and.
#


def polygon_mask(
    polygons: Sequence[Sequence], width: int, height: int, keep_inside: bool = False
) -> np.ndarray | None:
    """Masker seukuran frame: hitamkan poligon, atau hitamkan semua di luar poligon."""
    shapes = [
        np.asarray(p, dtype=np.int32).reshape(-1, 2)
        for p in (polygons or [])
        if len(p) >= 3
    ]
    if not shapes:
        return None
    fill = 255 if keep_inside else 0
    mask = np.full((height, width, 3), 255 - fill, dtype=np.uint8)
    cv2.fillPoly(mask, shapes, (fill, fill, fill))
    return mask


def combine_masks(*masks: np.ndarray | None) -> np.ndarray | None:
    """Gabungkan beberapa masker menjadi satu, agar setiap frame cukup satu operasi."""
    present = [mask for mask in masks if mask is not None]
    if not present:
        return None
    combined = present[0]
    for mask in present[1:]:
        combined = cv2.bitwise_and(combined, mask)
    return combined


def apply_mask(image: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    """Salinan frame dengan area masker dihitamkan; frame asli jika tidak ada masker."""
    return image if mask is None else cv2.bitwise_and(image, mask)
