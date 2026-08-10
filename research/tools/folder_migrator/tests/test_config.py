"""Tests for configuration loading and validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from folder_migrator.config import ConfigLoader
from folder_migrator.exceptions import ConfigurationError


def _write_json_config(tmp_path: Path, **overrides: object) -> Path:
    source = tmp_path / "src"
    source.mkdir()
    payload: dict[str, object] = {
        "source": str(source),
        "destination": str(tmp_path / "dst"),
        "include": [".*"],
        "exclude": ["__pycache__"],
        "workers": 4,
    }
    payload.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_valid_json_config(tmp_path: Path) -> None:
    config = ConfigLoader.load(_write_json_config(tmp_path))
    assert config.workers == 4
    assert config.exclude == ("__pycache__",)
    assert config.overwrite is False


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        ConfigLoader.load(tmp_path / "nope.json")


def test_missing_source_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"destination": str(tmp_path / "dst")}), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        ConfigLoader.load(path)


def test_invalid_workers_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        ConfigLoader.load(_write_json_config(tmp_path, workers=0))
