"""
Shared reader for YAML / JSON configuration files

Gunanya:
    Satu tempat untuk membaca file config dan memvalidasinya dengan model
    Pydantic. Format dipilih dari ekstensi file (.yaml, .yml, .json).
    YAML dibaca dan ditulis lewat `zul.adapters.yaml`, dalam bentuk aman
    yang tidak bisa menjalankan kode Python.

Cara pakai:
    from zul.utilities.vector_DB.config.config_file import load_config, read_config_file

    raw = read_config_file("milvus_config.json")          # dict mentah
    config = load_config(MilvusConfig, "milvus_config.json")  # tervalidasi

Error yang dilempar:
    FileNotFoundError   file tidak ada
    ValueError          format tidak didukung, YAML tidak valid, file kosong,
                        atau isi tidak lolos validasi (pesan menyebut nama
                        file dan field)
"""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from zul.adapters import yaml as yaml_adapter

# --------------------------------------------------------------------------
# Format File yang Didukung
# --------------------------------------------------------------------------
#
# Format sebuah file config ditentukan dari ekstensinya, bukan dari
# isinya. Jadi file yang berekstensi lain langsung ditolak lewat
# pesan yang menyebutkan pilihan ekstensi yang boleh dipakai.
#


YAML_SUFFIXES = (".yaml", ".yml")
JSON_SUFFIXES = (".json",)

ConfigModel = TypeVar("ConfigModel", bound=BaseModel)

# --------------------------------------------------------------------------
# Membaca dan Memvalidasi
# --------------------------------------------------------------------------


def read_config_file(config_path: str | Path) -> dict[str, Any]:
    """
    Read a .yaml, .yml or .json file into a plain dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If the format is unsupported, the YAML is invalid, or the file
            is empty / not a mapping
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    suffix = config_path.suffix.lower()
    with open(config_path, encoding="utf-8") as f:
        if suffix in YAML_SUFFIXES:
            config_dict = _parse_yaml(f.read(), config_path)
        elif suffix in JSON_SUFFIXES:
            config_dict = json.load(f)
        else:
            raise ValueError(
                f"Unsupported file format: {config_path.suffix}. "
                "Use .yaml, .yml, or .json"
            )

    if config_dict is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    if not isinstance(config_dict, dict):
        raise ValueError(f"Configuration root must be a mapping: {config_path}")

    return config_dict


def _parse_yaml(text: str, config_path: Path) -> Any:
    """Isi teks YAML; YAML yang rusak menjadi ValueError dengan nama file."""
    try:
        return yaml_adapter.loads(text)
    except yaml_adapter.YamlError as error:
        where = f" at line {error.line}" if error.line is not None else ""
        raise ValueError(
            f"Invalid YAML in {config_path}{where}: {error.problem}"
        ) from error


def load_config(model: type[ConfigModel], config_path: str | Path) -> ConfigModel:
    """
    Read a configuration file and validate it against a Pydantic model

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file format is unsupported or validation fails
    """
    config_dict = read_config_file(config_path)

    # Pesan validasi dari Pydantic tidak menyebutkan file asalnya. Error
    # dibungkus ulang di sini agar nama file ikut tampil, karena satu
    # aplikasi dapat memuat lebih dari satu file config sekaligus.
    try:
        return model(**config_dict)
    except ValidationError as e:
        raise ValueError(
            f"Configuration validation failed for '{config_path}': {e}"
        ) from e


# --------------------------------------------------------------------------
# Menulis
# --------------------------------------------------------------------------


def write_config_file(
    config_dict: dict[str, Any], output_path: str | Path, format: str = "yaml"
) -> None:
    """Write a dictionary to a YAML or JSON file ('yaml' / 'yml' / 'json')"""
    output_path = Path(output_path)
    format = format.lower()

    if format in ("yaml", "yml"):
        text = yaml_adapter.dumps(config_dict, sort_keys=False)
    elif format == "json":
        text = json.dumps(config_dict, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
