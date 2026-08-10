"""Custom exceptions for the folder migration utility.

Defining a small, explicit exception hierarchy lets callers catch failures at
the granularity they care about (e.g. only configuration problems) while still
allowing a single ``except FolderMigratorError`` to trap everything raised by
this package.
"""
from __future__ import annotations


class FolderMigratorError(Exception):
    """Base class for every error raised by the folder migrator."""


class ConfigurationError(FolderMigratorError):
    """Raised when the configuration file is missing, invalid, or incomplete."""


class CheckpointError(FolderMigratorError):
    """Raised when the checkpoint file cannot be read, parsed, or written."""


class MoveFileError(FolderMigratorError):
    """Raised when a single file or directory cannot be moved.

    Attributes:
        source: Path that failed to move.
        destination: Intended destination path.
    """

    def __init__(self, source: str, destination: str, reason: str) -> None:
        self.source = source
        self.destination = destination
        self.reason = reason
        super().__init__(f"Failed to move '{source}' -> '{destination}': {reason}")
