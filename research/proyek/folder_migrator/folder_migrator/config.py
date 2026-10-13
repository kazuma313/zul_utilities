"""Configuration loading and validation.

:class:`ConfigLoader` reads a YAML or JSON file, validates it, and returns an
immutable :class:`MigrationConfig`. Keeping parsing and validation here means
the rest of the system can trust the config object unconditionally.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

from .exceptions import ConfigurationError
from .models import (
    DEFAULT_CHECKPOINT_NAME,
    DEFAULT_INCLUDE,
    DEFAULT_LOG_PATH,
    MigrationConfig,
)

_YAML_SUFFIXES: Final[frozenset[str]] = frozenset({".yaml", ".yml"})
_JSON_SUFFIXES: Final[frozenset[str]] = frozenset({".json"})


class ConfigLoader:
    """Load and validate a migration configuration file."""

    @staticmethod
    def load(config_path: str | Path) -> MigrationConfig:
        """Load configuration from a YAML or JSON file.

        Args:
            config_path: Path to the ``.yaml``, ``.yml`` or ``.json`` file.

        Returns:
            A validated :class:`MigrationConfig`.

        Raises:
            ConfigurationError: If the file is missing, unparseable, or invalid.
        """
        path = Path(config_path)
        raw = ConfigLoader._read_raw(path)
        return ConfigLoader._build_config(raw)

    @staticmethod
    def _read_raw(path: Path) -> dict[str, Any]:
        """Read and parse the config file into a plain dictionary."""
        if not path.is_file():
            raise ConfigurationError(f"Config file not found: {path}")
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        try:
            if suffix in _YAML_SUFFIXES:
                data = ConfigLoader._parse_yaml(text)
            elif suffix in _JSON_SUFFIXES:
                data = json.loads(text)
            else:
                raise ConfigurationError(f"Unsupported config format: '{suffix}'")
        except (json.JSONDecodeError, ValueError) as error:
            raise ConfigurationError(f"Cannot parse config '{path}': {error}") from error
        if not isinstance(data, dict):
            raise ConfigurationError("Config root must be a mapping/object.")
        return data

    @staticmethod
    def _parse_yaml(text: str) -> Any:
        """Parse YAML text, giving a clear error if PyYAML is unavailable."""
        try:
            import yaml  # Imported lazily so JSON-only users need no dependency.
        except ImportError as error:  # pragma: no cover - environment specific
            raise ConfigurationError(
                "PyYAML is required for YAML configs. Install it or use JSON."
            ) from error
        return yaml.safe_load(text)

    @staticmethod
    def _build_config(raw: dict[str, Any]) -> MigrationConfig:
        """Validate raw values and construct an immutable config object."""
        source = ConfigLoader._require_path(raw, "source", must_exist=True)
        destination = ConfigLoader._require_path(raw, "destination", must_exist=False)
        ConfigLoader._assert_disjoint(source, destination)

        workers = int(raw.get("workers", 4))
        if workers < 1:
            raise ConfigurationError("'workers' must be >= 1.")

        checkpoint_every = int(raw.get("checkpoint_every", 500))
        if checkpoint_every < 1:
            raise ConfigurationError("'checkpoint_every' must be >= 1.")

        return MigrationConfig(
            source=source,
            destination=destination,
            include=tuple(raw.get("include", DEFAULT_INCLUDE)),
            exclude=tuple(raw.get("exclude", ())),
            follow_symlink=bool(raw.get("follow_symlink", False)),
            overwrite=bool(raw.get("overwrite", False)),
            workers=workers,
            checkpoint_path=Path(raw.get("checkpoint_path", DEFAULT_CHECKPOINT_NAME)),
            log_path=Path(raw.get("log_path", DEFAULT_LOG_PATH)),
            checkpoint_every=checkpoint_every,
        )

    @staticmethod
    def _assert_disjoint(source: Path, destination: Path) -> None:
        """Ensure destination is not the same as, or nested inside, source.

        Raises:
            ConfigurationError: If destination equals or lives under source,
                which would make the traversal re-scan already-moved files.
        """
        src = source.resolve()
        dst = destination.resolve()
        if src == dst or src in dst.parents:
            raise ConfigurationError(
                "'destination' must not be equal to or located inside 'source'."
            )

    @staticmethod
    def _require_path(raw: dict[str, Any], key: str, *, must_exist: bool) -> Path:
        """Extract a required path value and optionally assert it exists."""
        value = raw.get(key)
        if not value or not isinstance(value, str):
            raise ConfigurationError(f"'{key}' is required and must be a string.")
        path = Path(value).expanduser()
        if must_exist and not path.is_dir():
            raise ConfigurationError(f"'{key}' directory does not exist: {path}")
        return path
