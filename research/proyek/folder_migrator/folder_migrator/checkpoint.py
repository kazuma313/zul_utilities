"""Checkpoint persistence and progress tracking.

:class:`CheckpointManager` owns all reads/writes of the checkpoint file and all
mutations of the in-memory :class:`Checkpoint`. It is thread-safe so worker
threads can record results concurrently. Writes are atomic (temp file +
``os.replace``) so a crash mid-write never corrupts the checkpoint.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from .exceptions import CheckpointError
from .models import Checkpoint, MoveOutcome, MoveResult


class CheckpointManager:
    """Load, mutate, and atomically persist migration progress."""

    def __init__(self, checkpoint_path: Path) -> None:
        """Initialise the manager.

        Args:
            checkpoint_path: File where the checkpoint is stored.
        """
        self._path = checkpoint_path
        self._lock = threading.Lock()
        self._checkpoint = Checkpoint()

    @property
    def checkpoint(self) -> Checkpoint:
        """Return the current in-memory checkpoint."""
        return self._checkpoint

    def load(self) -> Checkpoint:
        """Load the checkpoint from disk, or start a fresh one if absent.

        Returns:
            The loaded (or newly created) checkpoint.

        Raises:
            CheckpointError: If an existing checkpoint file cannot be parsed.
        """
        if not self._path.is_file():
            self._checkpoint = Checkpoint()
            return self._checkpoint
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._checkpoint = self._deserialize(data)
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as error:
            raise CheckpointError(f"Cannot read checkpoint '{self._path}': {error}") from error
        return self._checkpoint

    def is_directory_completed(self, relative_dir: str) -> bool:
        """Return True if the given directory was already fully processed."""
        with self._lock:
            return relative_dir in self._checkpoint.completed_directories

    def mark_directory_completed(self, relative_dir: str) -> None:
        """Record that a directory has been fully processed."""
        with self._lock:
            self._checkpoint.completed_directories.add(relative_dir)

    def record(self, result: MoveResult) -> None:
        """Update aggregate counters for a single move result (thread-safe)."""
        with self._lock:
            if result.outcome is MoveOutcome.MOVED:
                self._checkpoint.moved_count += 1
            elif result.outcome is MoveOutcome.SKIPPED:
                self._checkpoint.skipped_count += 1
            else:
                self._checkpoint.failed_count += 1
            self._checkpoint.last_processed = result.relative_path

    def flush(self) -> None:
        """Atomically persist the current checkpoint to disk.

        Raises:
            CheckpointError: If the checkpoint cannot be written.
        """
        with self._lock:
            self._checkpoint.updated_at = time.time()
            payload = self._serialize(self._checkpoint)
        try:
            self._atomic_write(payload)
        except OSError as error:
            raise CheckpointError(f"Cannot write checkpoint '{self._path}': {error}") from error

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        """Write JSON to a temp file then atomically replace the target."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp_path, self._path)

    @staticmethod
    def _serialize(checkpoint: Checkpoint) -> dict[str, Any]:
        """Convert a checkpoint into a JSON-serialisable dict."""
        return {
            "completed_directories": sorted(checkpoint.completed_directories),
            "moved_count": checkpoint.moved_count,
            "skipped_count": checkpoint.skipped_count,
            "failed_count": checkpoint.failed_count,
            "last_processed": checkpoint.last_processed,
            "started_at": checkpoint.started_at,
            "updated_at": checkpoint.updated_at,
        }

    @staticmethod
    def _deserialize(data: dict[str, Any]) -> Checkpoint:
        """Rebuild a checkpoint from a parsed JSON dict."""
        return Checkpoint(
            completed_directories=set(data.get("completed_directories", [])),
            moved_count=int(data.get("moved_count", 0)),
            skipped_count=int(data.get("skipped_count", 0)),
            failed_count=int(data.get("failed_count", 0)),
            last_processed=data.get("last_processed"),
            started_at=float(data.get("started_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
        )
