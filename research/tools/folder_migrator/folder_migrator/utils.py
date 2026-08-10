"""Small, dependency-free helpers used by the migrator.

Kept separate so the orchestration code in :mod:`mover` stays focused on policy
rather than low-level plumbing.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Final

_PROGRESS_INTERVAL_SECONDS: Final[float] = 0.5


def to_relative(child: Path, root: Path) -> str:
    """Return ``child`` expressed relative to ``root`` using POSIX separators.

    Args:
        child: A path located under ``root``.
        root: The base directory.

    Returns:
        The relative path as a string ("." for ``root`` itself).
    """
    return Path(os.path.relpath(child, root)).as_posix()


def scan_directory(
    directory: Path, follow_symlink: bool
) -> tuple[list[os.DirEntry[str]], list[os.DirEntry[str]]]:
    """Split a directory's entries into (files, subdirectories).

    Uses :func:`os.scandir` (a lazy iterator) so only one directory's entries
    are held in memory at a time. Symlinks are treated as files when
    ``follow_symlink`` is False so they are never descended into.

    Args:
        directory: Directory to scan.
        follow_symlink: Whether symlinked directories count as directories.

    Returns:
        A tuple ``(files, subdirectories)`` of :class:`os.DirEntry` objects.

    Raises:
        OSError: If the directory cannot be scanned (surfaced to the caller).
    """
    files: list[os.DirEntry[str]] = []
    subdirs: list[os.DirEntry[str]] = []
    with os.scandir(directory) as iterator:
        for entry in iterator:
            if entry.is_symlink() and not follow_symlink:
                files.append(entry)  # Handled/skipped by the mover, never descended.
            elif entry.is_dir(follow_symlinks=follow_symlink):
                subdirs.append(entry)
            else:
                files.append(entry)
    return files, subdirs


class ProgressReporter:
    """Throttled, single-line console progress indicator."""

    def __init__(self, interval_seconds: float = _PROGRESS_INTERVAL_SECONDS) -> None:
        """Initialise the reporter.

        Args:
            interval_seconds: Minimum delay between console updates.
        """
        self._interval = interval_seconds
        self._last_emit = 0.0

    def update(self, processed: int, moved: int, current: str, *, force: bool = False) -> None:
        """Print progress, throttled unless ``force`` is True.

        Args:
            processed: Total entries processed so far.
            moved: Total entries successfully moved.
            current: Path of the entry currently being processed.
            force: Emit immediately regardless of the throttle interval.
        """
        now = time.monotonic()
        if not force and (now - self._last_emit) < self._interval:
            return
        self._last_emit = now
        sys.stdout.write(f"\rProcessed: {processed} | moved: {moved} | current: {current}")
        sys.stdout.flush()

    def finish(self) -> None:
        """Terminate the progress line with a newline."""
        sys.stdout.write("\n")
        sys.stdout.flush()
