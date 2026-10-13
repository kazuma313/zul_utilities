"""Shared pytest fixtures for the folder_migrator test suite."""
from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Callable

import pytest

from folder_migrator.models import MigrationConfig


@pytest.fixture(autouse=True)
def _reset_logger() -> Iterator[None]:
    """Close the shared logger's handlers after each test.

    Prevents an open rotating-file handle from blocking temp-dir cleanup
    (notably on Windows) between tests.
    """
    yield
    logger = logging.getLogger("folder_migrator")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


@pytest.fixture
def make_config(tmp_path: Path) -> Callable[..., MigrationConfig]:
    """Return a factory that builds a MigrationConfig with sensible test defaults."""

    def _make(source: Path, destination: Path, **overrides: object) -> MigrationConfig:
        defaults: dict[str, object] = {
            "include": (r".*",),
            "exclude": (),
            "follow_symlink": False,
            "overwrite": False,
            "workers": 2,
            "checkpoint_path": tmp_path / "checkpoint.json",
            "log_path": tmp_path / "logs" / "move.log",
            "checkpoint_every": 10,
        }
        defaults.update(overrides)
        return MigrationConfig(source=source, destination=destination, **defaults)  # type: ignore[arg-type]

    return _make


@pytest.fixture
def source_tree(tmp_path: Path) -> Path:
    """Create a small nested source tree and return its root.

    Layout::

        src/
          root.txt
          keep/a.txt
          move/b.txt
          move/nested/c.txt
          skip.log
          __pycache__/cache.pyc
    """
    src = tmp_path / "src"
    (src / "keep").mkdir(parents=True)
    (src / "move" / "nested").mkdir(parents=True)
    (src / "__pycache__").mkdir(parents=True)
    (src / "root.txt").write_text("root", encoding="utf-8")
    (src / "keep" / "a.txt").write_text("a", encoding="utf-8")
    (src / "move" / "b.txt").write_text("b", encoding="utf-8")
    (src / "move" / "nested" / "c.txt").write_text("c", encoding="utf-8")
    (src / "skip.log").write_text("log", encoding="utf-8")
    (src / "__pycache__" / "cache.pyc").write_text("x", encoding="utf-8")
    return src
