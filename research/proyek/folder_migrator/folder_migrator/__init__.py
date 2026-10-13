"""folder_migrator — resumable, production-grade bulk folder mover.

Public API:
    >>> from folder_migrator import FolderMover
    >>> FolderMover.from_config_file("config.yaml").run()
"""
from __future__ import annotations

from .checkpoint import CheckpointManager
from .config import ConfigLoader
from .exceptions import (
    CheckpointError,
    ConfigurationError,
    FolderMigratorError,
    MoveFileError,
)
from .matcher import RegexMatcher
from .models import Checkpoint, MigrationConfig, MoveOutcome, MoveResult
from .mover import FileMover, FolderMover

__all__ = [
    "CheckpointError",
    "CheckpointManager",
    "Checkpoint",
    "ConfigLoader",
    "ConfigurationError",
    "FileMover",
    "FolderMigratorError",
    "FolderMover",
    "MigrationConfig",
    "MoveFileError",
    "MoveOutcome",
    "MoveResult",
    "RegexMatcher",
]

__version__ = "1.0.0"
