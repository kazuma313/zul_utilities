"""
Adapter PyYAML: membaca dan menulis teks YAML.

Gunanya:
    Semua YAML di Zul, misalnya file config, dibaca dan ditulis lewat dua
    fungsi ini. Hanya bentuk aman yang dipakai: safe_load dan safe_dump,
    jadi file YAML tidak bisa menjalankan kode Python.

Cara pakai:
    from zul.adapters import yaml as yaml_adapter

    data = yaml_adapter.loads("settings:\\n  CONFIDENCE: 0.2\\n")
    text = yaml_adapter.dumps({"settings": {"CONFIDENCE": 0.2}})
"""

from __future__ import annotations

from typing import Any

import yaml


class YamlError(ValueError):
    """YAML yang tidak bisa dibaca atau ditulis, beserta baris dan masalahnya."""

    def __init__(
        self, problem: str, line: int | None = None, reading: bool = True
    ) -> None:
        where = f" di baris {line}" if line is not None else ""
        action = (
            "YAML tidak valid" if reading else "data tidak bisa ditulis sebagai YAML"
        )
        super().__init__(f"{action}{where}: {problem}")
        self.problem = problem
        self.line = line


def loads(text: str) -> Any:
    """Isi teks YAML sebagai objek Python; teks kosong menjadi None.

    Raises:
        YamlError: teks bukan YAML yang valid. `line` dihitung mulai dari 1.
    """
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        line = mark.line + 1 if mark is not None else None
        raise YamlError(str(getattr(error, "problem", error)), line) from error


def dumps(data: Any, sort_keys: bool = False) -> str:
    """Objek Python sebagai teks YAML blok, dengan urutan kunci dipertahankan.

    Raises:
        YamlError: `data` berisi objek yang tidak bisa ditulis sebagai YAML,
            misalnya objek kelas buatan sendiri.
    """
    try:
        return yaml.safe_dump(
            data, sort_keys=sort_keys, allow_unicode=True, default_flow_style=False
        )
    except yaml.YAMLError as error:
        problem = error.args[0] if error.args else str(error)
        raise YamlError(str(problem), reading=False) from error
