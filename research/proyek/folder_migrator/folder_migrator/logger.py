"""Logging configuration.

:class:`LoggerFactory` centralises logger creation so every module shares the
same handlers and format, and so the file-vs-console policy lives in one place.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

_LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB per log file
_BACKUP_COUNT: Final[int] = 5


class LoggerFactory:
    """Create loggers that write both to a rotating file and to the console."""

    @staticmethod
    def create(
        log_path: Path,
        name: str = "folder_migrator",
        level: int = logging.INFO,
    ) -> logging.Logger:
        """Build (or return an already-configured) logger.

        Args:
            log_path: Destination log file; parent directories are created.
            name: Logger name.
            level: Minimum log level.

        Returns:
            A configured :class:`logging.Logger` instance.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        LoggerFactory._reset_handlers(logger)  # Release any previously-open log file.
        logger.addHandler(LoggerFactory._file_handler(log_path, level))
        logger.addHandler(LoggerFactory._console_handler(level))
        logger.propagate = False
        return logger

    @staticmethod
    def _reset_handlers(logger: logging.Logger) -> None:
        """Remove and close existing handlers so re-init never duplicates or locks files."""
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    @staticmethod
    def _file_handler(log_path: Path, level: int) -> logging.Handler:
        """Create a size-based rotating file handler."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        handler.setLevel(level)
        return handler

    @staticmethod
    def _console_handler(level: int) -> logging.Handler:
        """Create a stream handler for console output."""
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        handler.setLevel(level)
        return handler
