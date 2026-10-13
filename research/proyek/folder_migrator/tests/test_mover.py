"""Tests for FileMover (single move) and FolderMover (full migration/resume)."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

import pytest

from folder_migrator.checkpoint import CheckpointManager
from folder_migrator.matcher import RegexMatcher
from folder_migrator.models import MigrationConfig, MoveOutcome
from folder_migrator.mover import FileMover, FolderMover


def _file_mover(config: MigrationConfig) -> FileMover:
    return FileMover(config, RegexMatcher(config.include, config.exclude))


# --------------------------- FileMover unit tests ---------------------------

def test_move_file_success(tmp_path: Path, make_config: Callable[..., MigrationConfig]) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    (src / "a.txt").write_text("hi", encoding="utf-8")
    config = make_config(src, dst)

    result = _file_mover(config).move(src / "a.txt", "a.txt")

    assert result.outcome is MoveOutcome.MOVED
    assert (dst / "a.txt").read_text(encoding="utf-8") == "hi"
    assert not (src / "a.txt").exists()


def test_skip_when_destination_exists(tmp_path: Path, make_config: Callable[..., MigrationConfig]) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (src / "a.txt").write_text("new", encoding="utf-8")
    (dst / "a.txt").write_text("old", encoding="utf-8")
    config = make_config(src, dst, overwrite=False)

    result = _file_mover(config).move(src / "a.txt", "a.txt")

    assert result.outcome is MoveOutcome.SKIPPED
    assert (dst / "a.txt").read_text(encoding="utf-8") == "old"
    assert (src / "a.txt").exists()  # untouched


def test_overwrite_replaces_destination(tmp_path: Path, make_config: Callable[..., MigrationConfig]) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (src / "a.txt").write_text("new", encoding="utf-8")
    (dst / "a.txt").write_text("old", encoding="utf-8")
    config = make_config(src, dst, overwrite=True)

    result = _file_mover(config).move(src / "a.txt", "a.txt")

    assert result.outcome is MoveOutcome.MOVED
    assert (dst / "a.txt").read_text(encoding="utf-8") == "new"


def test_skip_excluded_file(tmp_path: Path, make_config: Callable[..., MigrationConfig]) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    (src / "debug.log").write_text("x", encoding="utf-8")
    config = make_config(src, dst, exclude=(r"\.log$",))

    result = _file_mover(config).move(src / "debug.log", "debug.log")

    assert result.outcome is MoveOutcome.SKIPPED
    assert (src / "debug.log").exists()


# ------------------------ FolderMover integration ---------------------------

def test_full_migration_moves_tree(
    source_tree: Path, tmp_path: Path, make_config: Callable[..., MigrationConfig]
) -> None:
    dst = tmp_path / "dst"
    config = make_config(source_tree, dst, exclude=(r"__pycache__", r"\.log$"))

    FolderMover.from_config(config).run()

    # Included files moved, structure preserved.
    assert (dst / "root.txt").exists()
    assert (dst / "keep" / "a.txt").exists()
    assert (dst / "move" / "nested" / "c.txt").exists()
    # Excluded file and pruned directory are left in the source.
    assert (source_tree / "skip.log").exists()
    assert (source_tree / "__pycache__" / "cache.pyc").exists()
    # Checkpoint written.
    assert config.checkpoint_path.is_file()


def test_resume_skips_completed_directory(
    tmp_path: Path, make_config: Callable[..., MigrationConfig]
) -> None:
    src, dst = tmp_path / "src", tmp_path / "dst"
    (src / "keep").mkdir(parents=True)
    (src / "move").mkdir(parents=True)
    (src / "keep" / "a.txt").write_text("a", encoding="utf-8")
    (src / "move" / "b.txt").write_text("b", encoding="utf-8")
    config = make_config(src, dst)

    # Pre-seed the checkpoint: "keep" is already done.
    seed = CheckpointManager(config.checkpoint_path)
    seed.load()
    seed.mark_directory_completed("keep")
    seed.flush()

    FolderMover.from_config(config).run()

    # "keep" was skipped (files remain in source), "move" was processed.
    assert (src / "keep" / "a.txt").exists()
    assert not (dst / "keep" / "a.txt").exists()
    assert (dst / "move" / "b.txt").exists()


def test_directory_with_failure_is_not_marked_completed(
    tmp_path: Path,
    make_config: Callable[..., MigrationConfig],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed file must not silently prevent that directory from ever being retried.

    Regression test: previously, ``mark_directory_completed`` ran unconditionally
    after processing a directory, so a resumed run would skip it forever even
    though one of its files never actually moved.
    """
    src, dst = tmp_path / "src", tmp_path / "dst"
    (src / "docs").mkdir(parents=True)
    (src / "docs" / "ok.txt").write_text("ok", encoding="utf-8")
    (src / "docs" / "bad.txt").write_text("bad", encoding="utf-8")
    config = make_config(src, dst)

    real_move = shutil.move

    def _flaky_move(source: str, destination: str) -> object:
        if "bad.txt" in str(source):
            raise OSError("simulated failure (e.g. path too long)")
        return real_move(source, destination)

    monkeypatch.setattr("folder_migrator.mover.shutil.move", _flaky_move)

    FolderMover.from_config(config).run()

    checkpoint = CheckpointManager(config.checkpoint_path).load()
    assert "docs" not in checkpoint.completed_directories
    assert checkpoint.failed_count == 1
    assert (dst / "docs" / "ok.txt").exists()
    assert (src / "docs" / "bad.txt").exists()  # left in place, safe to retry

    # Resume after the transient failure is fixed: the directory is revisited
    # (not skipped), the already-moved file is left alone, and the previously
    # failed file is retried and succeeds.
    monkeypatch.undo()
    FolderMover.from_config(config).run()

    assert (dst / "docs" / "bad.txt").exists()
    assert not (src / "docs" / "bad.txt").exists()
    final_checkpoint = CheckpointManager(config.checkpoint_path).load()
    assert "docs" in final_checkpoint.completed_directories
