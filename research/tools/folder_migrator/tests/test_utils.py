"""Tests for :mod:`folder_migrator.utils` — long-path handling and progress output."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

from folder_migrator.utils import ProgressReporter, to_long_path


class TestToLongPath:
    def test_noop_on_non_windows(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "name", "posix")
        target = tmp_path / "file.txt"
        assert to_long_path(target) == target

    def test_adds_extended_prefix_on_windows(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "name", "nt")
        target = tmp_path / "file.txt"
        result = to_long_path(target)
        assert str(result).startswith("\\\\?\\")
        assert str(target) in str(result)

    def test_idempotent_when_already_prefixed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "name", "nt")
        once = to_long_path(tmp_path / "file.txt")
        twice = to_long_path(once)
        assert twice == once

    def test_relative_path_resolved_against_cwd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "name", "nt")
        result = to_long_path(Path("relative.txt"))
        assert str(result).startswith("\\\\?\\")
        assert str(Path.cwd()) in str(result)


class TestProgressReporter:
    def test_update_never_raises_on_unencodable_characters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A console codepage that cannot encode a filename must not crash the run."""

        class _Cp1252Stdout(io.TextIOBase):
            encoding = "cp1252"

            def write(self, text: str) -> int:  # noqa: D102
                text.encode("cp1252")  # raises UnicodeEncodeError, like a real console
                return len(text)

            def flush(self) -> None:  # noqa: D102
                pass

        monkeypatch.setattr(sys, "stdout", _Cp1252Stdout())
        reporter = ProgressReporter(interval_seconds=0.0)
        # U+2060 WORD JOINER cannot be represented in cp1252 and previously crashed the migration.
        reporter.update(1, 1, "weird⁠name.txt", force=True)  # must not raise

    def test_update_writes_normal_progress_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        reporter = ProgressReporter(interval_seconds=0.0)
        reporter.update(5, 3, "ok.txt", force=True)
        out = capsys.readouterr().out
        assert "Processed: 5" in out
        assert "moved: 3" in out
        assert "ok.txt" in out
