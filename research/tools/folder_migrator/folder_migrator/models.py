"""Immutable data models shared across the folder migrator.

All models are plain :mod:`dataclasses`. They carry data only and hold no
behaviour, keeping them trivial to test and safe to pass across module
boundaries.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Final

DEFAULT_INCLUDE: Final[tuple[str, ...]] = (r".*",)
DEFAULT_CHECKPOINT_NAME: Final[str] = "checkpoint.json"
DEFAULT_LOG_PATH: Final[str] = "logs/move_folder.log"


class MoveOutcome(str, Enum):
    """Result of attempting to move a single filesystem entry."""

    MOVED = "moved"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MigrationConfig:
    """Validated configuration for a migration run.

    Attributes:
        source: Root directory whose contents will be moved.
        destination: Root directory that will receive the contents.
        include: Regex patterns; a file is eligible only if it matches one.
        exclude: Regex patterns; any matching name is skipped (dirs are pruned).
        follow_symlink: Whether to descend into / move symbolic links.
        overwrite: Whether to replace files that already exist at destination.
        workers: Number of concurrent worker threads (>= 1).
        checkpoint_path: Where the resume checkpoint is persisted.
        log_path: Where the log file is written.
        checkpoint_every: Flush the checkpoint after this many processed files.
    """

    source: Path
    destination: Path
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = ()
    follow_symlink: bool = False
    overwrite: bool = False
    workers: int = 4
    checkpoint_path: Path = Path(DEFAULT_CHECKPOINT_NAME)
    log_path: Path = Path(DEFAULT_LOG_PATH)
    checkpoint_every: int = 500


@dataclass(slots=True)
class Checkpoint:
    """Mutable progress record used to resume an interrupted migration.

    Only directory-level state and aggregate counters are stored, so the file
    stays small even for millions of files (see the README "Resume mechanism").

    Attributes:
        completed_directories: Relative dir paths already fully processed.
        moved_count: Total files successfully moved.
        skipped_count: Total files intentionally skipped.
        failed_count: Total files that failed to move.
        last_processed: Relative path of the most recent entry processed.
        started_at: Unix timestamp when the run first started.
        updated_at: Unix timestamp of the last checkpoint flush.
    """

    completed_directories: set[str] = field(default_factory=set)
    moved_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    last_processed: str | None = None
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class MoveResult:
    """Outcome of a single move operation.

    Attributes:
        relative_path: Path of the entry relative to the source root.
        outcome: Whether the entry was moved, skipped, or failed.
        detail: Optional human-readable explanation (reason for skip/failure).
    """

    relative_path: str
    outcome: MoveOutcome
    detail: str | None = None
