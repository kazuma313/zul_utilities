"""Command-line entry point for the folder migrator.

Usage:
    python main.py --config config.yaml

The CLI is intentionally thin: it parses arguments, builds a fully-wired
:class:`FolderMover`, and delegates. All real work lives in the package so it
stays independently testable.
"""
from __future__ import annotations

import argparse
import sys

from folder_migrator.exceptions import ConfigurationError, FolderMigratorError
from folder_migrator.mover import FolderMover

_EXIT_OK = 0
_EXIT_CONFIG_ERROR = 2
_EXIT_RUNTIME_ERROR = 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Resumable, production-grade bulk folder mover.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to the YAML or JSON configuration file (default: config.yaml).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the migration and return a process exit code.

    Args:
        argv: Optional argument list for testing.

    Returns:
        ``0`` on success, ``2`` on configuration error, ``1`` on runtime error.
    """
    args = parse_args(argv)
    try:
        mover = FolderMover.from_config_file(args.config)
        mover.run()
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return _EXIT_CONFIG_ERROR
    except FolderMigratorError as error:
        print(f"Migration error: {error}", file=sys.stderr)
        return _EXIT_RUNTIME_ERROR
    return _EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
