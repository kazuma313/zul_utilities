"""Core migration orchestration.

Two collaborating classes keep responsibilities separated:

* :class:`FileMover` — moves a single filesystem entry and reports the outcome.
* :class:`FolderMover` — traverses the tree, schedules moves across worker
  threads, records progress, and drives the resume/checkpoint logic.

Traversal is an explicit stack over :func:`os.scandir` (never recursion and
never a full in-memory file list), so arbitrarily deep and wide trees with
millions of files are handled with bounded memory.
"""
from __future__ import annotations

import concurrent.futures as cf
import logging
import os
import shutil
import signal
import threading
from collections.abc import Iterable
from pathlib import Path

from .checkpoint import CheckpointManager
from .config import ConfigLoader
from .logger import LoggerFactory
from .matcher import RegexMatcher
from .models import MigrationConfig, MoveOutcome, MoveResult
from .utils import ProgressReporter, scan_directory, to_relative


class FileMover:
    """Move a single file/entry from source to destination."""

    def __init__(self, config: MigrationConfig, matcher: RegexMatcher) -> None:
        """Store collaborators.

        Args:
            config: Validated migration configuration.
            matcher: Include/exclude policy.
        """
        self._config = config
        self._matcher = matcher

    def move(self, source: Path, relative_path: str) -> MoveResult:
        """Move ``source`` to its destination, never raising on failure.

        Args:
            source: Absolute path of the entry to move.
            relative_path: Path of the entry relative to the source root.

        Returns:
            A :class:`MoveResult` describing the outcome (moved/skipped/failed).
        """
        name = source.name
        if source.is_symlink() and not self._config.follow_symlink:
            return MoveResult(relative_path, MoveOutcome.SKIPPED, "symlink")
        if not self._matcher.should_move_file(name):
            return MoveResult(relative_path, MoveOutcome.SKIPPED, "excluded by regex")

        destination = self._config.destination / relative_path
        if destination.exists() and not self._config.overwrite:
            return MoveResult(relative_path, MoveOutcome.SKIPPED, "destination exists")
        return self._safe_move(source, destination, relative_path)

    def _safe_move(self, source: Path, destination: Path, relative_path: str) -> MoveResult:
        """Perform the move, converting expected errors into a FAILED result."""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and self._config.overwrite:
                self._remove_existing(destination)
            shutil.move(str(source), str(destination))
            return MoveResult(relative_path, MoveOutcome.MOVED)
        except (PermissionError, FileNotFoundError, InterruptedError, OSError) as error:
            return MoveResult(relative_path, MoveOutcome.FAILED, str(error))

    @staticmethod
    def _remove_existing(destination: Path) -> None:
        """Delete an existing destination before overwriting it."""
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()


class FolderMover:
    """Traverse a source tree and move its contents with resume support."""

    def __init__(
        self,
        config: MigrationConfig,
        matcher: RegexMatcher,
        checkpoint_manager: CheckpointManager,
        file_mover: FileMover,
        logger: logging.Logger,
        progress: ProgressReporter,
    ) -> None:
        """Wire the injected collaborators (dependency injection)."""
        self._config = config
        self._matcher = matcher
        self._checkpoint = checkpoint_manager
        self._file_mover = file_mover
        self._logger = logger
        self._progress = progress
        self._stop = threading.Event()

    @classmethod
    def from_config(cls, config: MigrationConfig) -> "FolderMover":
        """Build a fully-wired mover from a configuration object.

        Args:
            config: Validated migration configuration.

        Returns:
            A ready-to-run :class:`FolderMover`.
        """
        matcher = RegexMatcher(config.include, config.exclude)
        return cls(
            config=config,
            matcher=matcher,
            checkpoint_manager=CheckpointManager(config.checkpoint_path),
            file_mover=FileMover(config, matcher),
            logger=LoggerFactory.create(config.log_path),
            progress=ProgressReporter(),
        )

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> "FolderMover":
        """Build a mover directly from a YAML/JSON config file path."""
        return cls.from_config(ConfigLoader.load(config_path))

    def run(self) -> None:
        """Execute the migration, resuming from any existing checkpoint.

        The checkpoint is always flushed on exit — whether the run finishes,
        is interrupted (CTRL+C / SIGTERM), or hits an unexpected error — so the
        next invocation can resume cleanly.
        """
        self._install_signal_handlers()
        checkpoint = self._checkpoint.load()
        if checkpoint.moved_count or checkpoint.completed_directories:
            self._logger.info(
                "Resuming from checkpoint: %d moved, %d directories done",
                checkpoint.moved_count,
                len(checkpoint.completed_directories),
            )
        self._logger.info("Starting migration: %s -> %s", self._config.source, self._config.destination)
        try:
            self._process_tree()
        except KeyboardInterrupt:  # pragma: no cover - defensive
            self._logger.warning("Interrupted by user; progress has been checkpointed.")
        finally:
            self._finalize()

    def _process_tree(self) -> None:
        """Walk the source tree directory-by-directory using an explicit stack."""
        with cf.ThreadPoolExecutor(max_workers=self._config.workers) as executor:
            stack: list[Path] = [self._config.source]
            while stack and not self._stop.is_set():
                current = stack.pop()
                self._process_one_directory(current, stack, executor)

    def _process_one_directory(
        self, current: Path, stack: list[Path], executor: cf.ThreadPoolExecutor
    ) -> None:
        """Process a single directory: enqueue subdirs, then move its files."""
        relative_dir = to_relative(current, self._config.source)
        try:
            files, subdirs = scan_directory(current, self._config.follow_symlink)
        except OSError as error:
            self._logger.error("Cannot scan directory '%s': %s", relative_dir, error)
            return

        self._enqueue_subdirectories(subdirs, stack)
        if self._checkpoint.is_directory_completed(relative_dir):
            self._logger.debug("Skipping already-completed directory: %s", relative_dir)
            return

        self._logger.info("Processing directory: %s (%d files)", relative_dir, len(files))
        self._move_directory_files(files, relative_dir, executor)
        self._checkpoint.mark_directory_completed(relative_dir)
        self._checkpoint.flush()

    def _enqueue_subdirectories(
        self, subdirs: list[os.DirEntry[str]], stack: list[Path]
    ) -> None:
        """Push eligible subdirectories onto the traversal stack."""
        for entry in subdirs:
            if self._matcher.should_enter_directory(entry.name):
                stack.append(Path(entry.path))
            else:
                self._logger.warning("Excluded directory: %s", entry.path)

    def _move_directory_files(
        self, files: list[os.DirEntry[str]], relative_dir: str, executor: cf.ThreadPoolExecutor
    ) -> None:
        """Move every file in a directory with a bounded number of in-flight tasks."""
        max_inflight = self._config.workers * 4
        pending: set[cf.Future[MoveResult]] = set()
        for entry in files:
            if self._stop.is_set():
                break
            relative_path = entry.name if relative_dir == "." else f"{relative_dir}/{entry.name}"
            pending.add(executor.submit(self._file_mover.move, Path(entry.path), relative_path))
            if len(pending) >= max_inflight:
                done, pending = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
                self._drain(done)
        self._drain(cf.as_completed(pending))

    def _drain(self, futures: Iterable[cf.Future[MoveResult]]) -> None:
        """Record and log the results of completed move futures."""
        for future in futures:
            try:
                result = future.result()
            except Exception as error:  # pragma: no cover - FileMover already guards
                self._logger.error("Unexpected worker error: %s", error)
                continue
            self._checkpoint.record(result)
            self._report(result)

    def _report(self, result: MoveResult) -> None:
        """Log a single result at the appropriate level and update progress."""
        if result.outcome is MoveOutcome.MOVED:
            self._logger.debug("Moved: %s", result.relative_path)
        elif result.outcome is MoveOutcome.SKIPPED:
            self._logger.warning("Skipped %s (%s)", result.relative_path, result.detail)
        else:
            self._logger.error("Failed %s: %s", result.relative_path, result.detail)
        state = self._checkpoint.checkpoint
        processed = state.moved_count + state.skipped_count + state.failed_count
        self._progress.update(processed, state.moved_count, result.relative_path)

    def _finalize(self) -> None:
        """Flush the checkpoint and log the final summary."""
        self._checkpoint.flush()
        self._progress.finish()
        state = self._checkpoint.checkpoint
        self._logger.info(
            "Migration finished: %d moved, %d skipped, %d failed",
            state.moved_count,
            state.skipped_count,
            state.failed_count,
        )

    def _install_signal_handlers(self) -> None:
        """Install SIGINT/SIGTERM handlers that request a graceful stop."""
        def _handler(signum: int, _frame: object) -> None:
            self._logger.warning("Received signal %d; finishing in-flight moves...", signum)
            self._stop.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except (ValueError, OSError):  # Not in main thread (e.g. under pytest).
                pass
