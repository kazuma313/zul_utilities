"""
Pengaturan aplikasi: config dasar, config kamera, dan geometri scene.

Gunanya:
    configs/base.yaml berisi pengaturan yang sama untuk semua kamera, lalu
    configs/<kamera>.yaml menimpa yang berbeda dan menambahkan geometri:
    video sumber, zona, garis penghitung, dan area yang diabaikan.
    Pengaturan diperiksa terhadap dataclass di file ini, jadi salah ketik
    dan tipe yang salah ketahuan sebelum model dimuat.

Cara pakai:
    from cctv.settings import load_scene_config

    scene = load_scene_config("configs/base.yaml", "configs/entrance.yaml")
    scene.settings.CONFIDENCE       # 0.2
    scene.zones[0].name             # "depan_toko"
    scene.lines[0].start            # (1257.0, 497.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zul.computer_vision.config import ConfigError, load_scene, validate_settings

# --------------------------------------------------------------------------
# Kelompok Pengaturan
# --------------------------------------------------------------------------
#
# Setiap kelompok di bawah hanya menyebut nama dan tipe pengaturan. Nilainya
# datang dari YAML, jadi kunci yang hilang menghentikan program, alih-alih
# diam-diam memakai nilai bawaan yang belum tentu cocok untuk kamera ini.
#


@dataclass(frozen=True)
class ModelSettings:
    MODEL: str
    WEIGHTS: str
    PERSON_CLASS_ID: int
    CONFIDENCE: float
    DETECT_SIZE: int
    HALF: bool
    DEVICE: str


@dataclass(frozen=True)
class TrackingSettings:
    TRACK_HIGH_THRESHOLD: float
    TRACK_NEW_THRESHOLD: float
    LOST_TRACK_BUFFER: int


@dataclass(frozen=True)
class RuleSettings:
    ANCHOR_RATIO: float
    MIN_CROSSING_FRAMES: int
    ZONE_GRACE_S: float
    DWELL_THRESHOLD_S: float
    FACING_CONE_DEG: float
    ATTENTION_MINIMUM_S: float
    PROXIMITY_METRES: float
    CONTACT_MINIMUM_S: float
    PERSON_HEIGHT_METRES: float


@dataclass(frozen=True)
class DrawSettings:
    TRACE_LENGTH: int
    SHOW_SKELETON: bool
    ZONE_COLOR: str
    LINE_COLOR: str
    IGNORE_COLOR: str
    ATTENTION_COLOR: str
    CONTACT_COLOR: str


SETTING_GROUPS = (ModelSettings, TrackingSettings, RuleSettings, DrawSettings)


@dataclass(frozen=True)
class Settings(DrawSettings, RuleSettings, TrackingSettings, ModelSettings):
    """Semua pengaturan dalam satu objek, misalnya `settings.CONFIDENCE`."""


# --------------------------------------------------------------------------
# Geometri Scene
# --------------------------------------------------------------------------

Point = tuple[float, float]


@dataclass(frozen=True)
class Zone:
    """Poligon bernama. `anchor` adalah titik yang harus dihadapi orang di zona ini."""

    name: str
    polygon: tuple[Point, ...]
    anchor: Point | None = None


@dataclass(frozen=True)
class Line:
    """Garis penghitung bernama; sisi kiri dari `start` ke `end` adalah sisi masuk."""

    name: str
    start: Point
    end: Point


@dataclass(frozen=True)
class SceneConfig:
    """Satu kamera: video sumber, pengaturan, dan geometrinya."""

    name: str
    source: Path
    settings: Settings
    zones: tuple[Zone, ...] = ()
    lines: tuple[Line, ...] = ()
    ignore_polygons: tuple[tuple[Point, ...], ...] = ()
    overrides: tuple[str, ...] = field(default=())


def load_scene_config(
    base_path: str | Path, scene_path: str | Path, source: str | Path | None = None
) -> SceneConfig:
    """Gabungkan config dasar dan config kamera, lalu periksa semuanya.

    `source` menggantikan `SOURCE_VIDEO_PATH` di config kamera, misalnya
    dari opsi `--source` di CLI.

    Raises:
        ConfigError: pengaturan tidak lengkap atau salah tipe, geometri
            tidak valid, atau video sumber tidak disebutkan.
    """
    where = Path(scene_path).name
    raw = load_scene(base_path, scene_path)
    values = validate_settings(raw.get("settings") or {}, *SETTING_GROUPS)
    video = source or raw.get("SOURCE_VIDEO_PATH")
    if not video:
        raise ConfigError(f"{where}: SOURCE_VIDEO_PATH belum diisi")

    zones = tuple(
        _zone(item, f"{where}: ZONES[{i}]")
        for i, item in enumerate(raw.get("ZONES") or [])
    )
    lines = tuple(
        _line(item, f"{where}: LINES[{i}]")
        for i, item in enumerate(raw.get("LINES") or [])
    )
    _require_unique([zone.name for zone in zones], f"{where}: ZONES")
    _require_unique([line.name for line in lines], f"{where}: LINES")
    ignored = tuple(
        _points(polygon, f"{where}: IGNORE_POLYGONS[{i}]", minimum=3)
        for i, polygon in enumerate(raw.get("IGNORE_POLYGONS") or [])
    )
    return SceneConfig(
        name=Path(scene_path).stem,
        source=Path(video),
        settings=Settings(**values),
        zones=zones,
        lines=lines,
        ignore_polygons=ignored,
        overrides=tuple(raw.get("overrides") or ()),
    )


def _zone(item: Any, where: str) -> Zone:
    if not isinstance(item, dict) or "name" not in item or "polygon" not in item:
        raise ConfigError(f"{where} harus berisi `name` dan `polygon`")
    anchor = item.get("anchor")
    return Zone(
        name=str(item["name"]),
        polygon=_points(item["polygon"], f"{where}.polygon", minimum=3),
        anchor=_point(anchor, f"{where}.anchor") if anchor is not None else None,
    )


def _line(item: Any, where: str) -> Line:
    if not isinstance(item, dict) or not {"name", "start", "end"} <= set(item):
        raise ConfigError(f"{where} harus berisi `name`, `start`, dan `end`")
    return Line(
        name=str(item["name"]),
        start=_point(item["start"], f"{where}.start"),
        end=_point(item["end"], f"{where}.end"),
    )


def _points(value: Any, where: str, minimum: int) -> tuple[Point, ...]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ConfigError(f"{where} butuh minimal {minimum} titik [x, y]")
    return tuple(_point(point, f"{where}[{i}]") for i, point in enumerate(value))


def _point(value: Any, where: str) -> Point:
    numbers = (int, float)
    if (
        not isinstance(value, list | tuple)
        or len(value) != 2
        or not all(isinstance(v, numbers) and not isinstance(v, bool) for v in value)
    ):
        raise ConfigError(f"{where} harus titik [x, y], bukan {value!r}")
    return float(value[0]), float(value[1])


def _require_unique(names: list[str], where: str) -> None:
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ConfigError(
            f"{where}: nama dipakai lebih dari sekali: {', '.join(duplicates)}"
        )
