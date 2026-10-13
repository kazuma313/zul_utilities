"""
Hook MkDocs: menaruh versi Zul dari pyproject.toml ke config situs.

Gunanya:
    Header situs dokumentasi menampilkan versi Zul di samping namanya.
    Versinya dibaca dari pyproject.toml setiap kali situs dibangun, jadi
    header selalu sama dengan versi package tanpa perlu ditulis ulang.

Cara pakai:
    Hook ini didaftarkan di mkdocs.yml (`hooks:`) dan berjalan sendiri
    saat `mkdocs build` atau `mkdocs serve`. Template header di
    overrides/partials/header.html membaca nilainya dari
    `config.extra.zul_version`.
"""

import tomllib
from pathlib import Path


def read_version(pyproject: Path) -> str:
    """Versi package di bagian [project] milik pyproject.toml."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data["project"]["version"]


def on_config(config):
    pyproject = Path(config.config_file_path).parent / "pyproject.toml"
    config.extra["zul_version"] = read_version(pyproject)
    return config
