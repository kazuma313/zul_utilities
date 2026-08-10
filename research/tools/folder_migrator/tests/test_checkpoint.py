"""Tests for checkpoint persistence and resume state."""
from __future__ import annotations

from pathlib import Path

import pytest

from folder_migrator.checkpoint import CheckpointManager
from folder_migrator.exceptions import CheckpointError
from folder_migrator.models import MoveOutcome, MoveResult


def test_load_missing_returns_fresh_checkpoint(tmp_path: Path) -> None:
    manager = CheckpointManager(tmp_path / "checkpoint.json")
    checkpoint = manager.load()
    assert checkpoint.moved_count == 0
    assert checkpoint.completed_directories == set()


def test_record_counts_by_outcome(tmp_path: Path) -> None:
    manager = CheckpointManager(tmp_path / "checkpoint.json")
    manager.load()
    manager.record(MoveResult("a.txt", MoveOutcome.MOVED))
    manager.record(MoveResult("b.txt", MoveOutcome.SKIPPED, "exists"))
    manager.record(MoveResult("c.txt", MoveOutcome.FAILED, "denied"))
    state = manager.checkpoint
    assert (state.moved_count, state.skipped_count, state.failed_count) == (1, 1, 1)
    assert state.last_processed == "c.txt"


def test_flush_and_reload_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    manager = CheckpointManager(path)
    manager.load()
    manager.record(MoveResult("a.txt", MoveOutcome.MOVED))
    manager.mark_directory_completed("images")
    manager.flush()

    resumed = CheckpointManager(path)
    checkpoint = resumed.load()
    assert checkpoint.moved_count == 1
    assert resumed.is_directory_completed("images")


def test_corrupt_checkpoint_raises(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    path.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(CheckpointError):
        CheckpointManager(path).load()
