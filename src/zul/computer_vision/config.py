"""
Config scene dari YAML: pengaturan bersama, pengaturan per kamera, dan geometri.

Gunanya:
    Satu file dasar memuat nilai setiap pengaturan, lalu file per kamera
    menimpa yang berbeda dan menambahkan geometri scene: zona, garis, dan
    area yang diabaikan. Pengaturan divalidasi terhadap dataclass, jadi
    salah ketik dan tipe yang salah ketahuan sebelum model dimuat.

Cara pakai:
    from dataclasses import dataclass
    from zul.computer_vision.config import load_scene, validate_settings

    @dataclass(frozen=True)
    class Rules:
        CONFIDENCE: float
        FACING_CONE_DEG: float

    scene = load_scene("configs/base.yaml", "configs/interior.yaml")
    values = validate_settings(scene["settings"], Rules)   # dict nama -> nilai
    scene["overrides"]          # pengaturan dasar yang ditimpa file kamera

Contoh isi YAML:
    settings:
      CONFIDENCE: 0.20
      FACING_CONE_DEG: 90.0
    POLYGON:
      - [[12, 222], [200, 261], [446, 719], [25, 719]]
    POLYGON_LABELS: [rak_a]
"""

from __future__ import annotations

import dataclasses
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Config yang tidak bisa dipakai; pesannya menyebut file, kunci, dan solusinya."""


# --------------------------------------------------------------------------
# Membaca Dan Menggabungkan
# --------------------------------------------------------------------------
#
# Kunci di luar `settings:` adalah geometri scene. File kamera menimpa file
# dasar per kunci, sedangkan blok settings digabung per nama, supaya file
# kamera hanya perlu menulis nilai yang berbeda dengan file dasarnya.
#


def read_yaml(path: str | Path) -> dict:
    """Isi satu file YAML sebagai dict; file yang tidak ada menjadi dict kosong."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f" di baris {mark.line + 1}" if mark is not None else ""
        raise ConfigError(
            f"{path} bukan YAML yang valid{where}: {getattr(error, 'problem', error)}. "
            "Setiap entri butuh `KUNCI:` dan item list butuh `- ` di depannya."
        ) from error
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(
            f"{path} harus berisi mapping `KUNCI: nilai`, bukan {type(data).__name__}"
        )
    return data


def merge_scene(base: dict, scene: dict) -> dict:
    """Gabungan config dasar dan config kamera, dengan daftar nilai yang ditimpa."""
    base_settings = base.get("settings") or {}
    scene_settings = scene.get("settings") or {}
    merged = {**base, **scene}
    merged["settings"] = {**base_settings, **scene_settings}
    merged["overrides"] = sorted(key for key in scene_settings if key in base_settings)
    return merged


def load_scene(base_path: str | Path, scene_path: str | Path | None = None) -> dict:
    """`read_yaml` untuk file dasar dan file kamera, lalu `merge_scene`."""
    base = read_yaml(base_path)
    scene = read_yaml(scene_path) if scene_path is not None else {}
    return merge_scene(base, scene)


def first_present(config: dict, *keys: str) -> Any:
    """Nilai kunci pertama yang terisi, untuk kunci yang punya lebih dari satu ejaan."""
    for key in keys:
        if config.get(key):
            return config[key]
    return None


# --------------------------------------------------------------------------
# Validasi Pengaturan
# --------------------------------------------------------------------------
#
# Dataclass hanya menyebut nama dan tipe setiap pengaturan, tanpa nilainya.
# Nilainya datang dari YAML, jadi kunci yang hilang menghentikan program
# alih-alih diam-diam memakai nilai bawaan yang mungkin tidak sesuai.
#


def _type_name(annotation: Any) -> str:
    return (
        annotation
        if isinstance(annotation, str)
        else getattr(annotation, "__name__", str(annotation))
    )


def _fits(value: Any, declared: str) -> tuple[bool, Any]:
    if declared == "float" and isinstance(value, int) and not isinstance(value, bool):
        return True, float(value)
    if declared in {"Any", ""}:
        return True, value
    base = declared.split("[")[0].lower()
    return type(value).__name__ == base, value


def validate_settings(settings: dict, *groups: type) -> dict[str, Any]:
    """Nilai setiap pengaturan yang dideklarasikan `groups`, setelah diperiksa.

    Raises:
        ConfigError: ada kunci yang tidak dikenal, kunci yang hilang, atau
            nilai yang tipenya tidak sesuai deklarasi.
    """
    declared: dict[str, tuple[str, str]] = {}
    for group in groups:
        for item in dataclasses.fields(group):
            declared[item.name] = (_type_name(item.type), group.__name__)

    unknown = sorted(set(settings) - set(declared))
    if unknown:
        hints = []
        for name in unknown:
            near = get_close_matches(name, declared, n=1)
            hints.append(f"{name} (maksudnya {near[0]}?)" if near else name)
        raise ConfigError(f"settings: kunci tidak dikenal: {', '.join(hints)}")

    missing = [name for name in declared if name not in settings]
    if missing:
        raise ConfigError(
            f"settings: {len(missing)} pengaturan belum diisi: "
            + ", ".join(f"{name} ({declared[name][1]})" for name in missing)
        )

    values: dict[str, Any] = {}
    for name, (type_name, group) in declared.items():
        ok, value = _fits(settings[name], type_name)
        if not ok:
            raise ConfigError(
                f"settings: {name} ({group}) harus {type_name}, "
                f"bukan {type(settings[name]).__name__} ({settings[name]!r})"
            )
        values[name] = value
    return values


def changed_settings(base: dict, current: dict) -> list[str]:
    """Baris `NAMA: lama -> baru` untuk pengaturan yang berbeda dari config dasar."""
    return [
        f"{name}: {base.get(name)!r} -> {value!r}"
        for name, value in current.items()
        if name in base and base[name] != value
    ]
