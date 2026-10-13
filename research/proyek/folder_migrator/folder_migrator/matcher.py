"""Regex-based include/exclude matching.

The :class:`RegexMatcher` isolates the single responsibility of deciding
whether a given name should be processed, keeping this policy out of the
traversal and move logic.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Pattern

from .exceptions import ConfigurationError


class RegexMatcher:
    """Decide whether files/directories are eligible based on regex rules.

    A file is *eligible* when it matches at least one include pattern and no
    exclude pattern. A directory is *pruned* (not descended into) when it
    matches any exclude pattern.
    """

    def __init__(self, include: Sequence[str], exclude: Sequence[str]) -> None:
        """Compile the include and exclude patterns.

        Args:
            include: Include regex patterns. Empty means "include everything".
            exclude: Exclude regex patterns.

        Raises:
            ConfigurationError: If any pattern is not a valid regular expression.
        """
        self._include: list[Pattern[str]] = self._compile(include, "include")
        self._exclude: list[Pattern[str]] = self._compile(exclude, "exclude")

    @staticmethod
    def _compile(patterns: Iterable[str], label: str) -> list[Pattern[str]]:
        """Compile a list of patterns, wrapping failures in ConfigurationError."""
        compiled: list[Pattern[str]] = []
        for pattern in patterns:
            try:
                compiled.append(re.compile(pattern))
            except re.error as error:
                raise ConfigurationError(
                    f"Invalid {label} regex '{pattern}': {error}"
                ) from error
        return compiled

    def is_excluded(self, name: str) -> bool:
        """Return True if ``name`` matches any exclude pattern."""
        return any(pattern.search(name) for pattern in self._exclude)

    def is_included(self, name: str) -> bool:
        """Return True if ``name`` matches any include pattern (or no rule set)."""
        if not self._include:
            return True
        return any(pattern.search(name) for pattern in self._include)

    def should_move_file(self, name: str) -> bool:
        """Return True if a file named ``name`` is eligible to be moved."""
        return self.is_included(name) and not self.is_excluded(name)

    def should_enter_directory(self, name: str) -> bool:
        """Return True if a directory named ``name`` should be descended into."""
        return not self.is_excluded(name)
