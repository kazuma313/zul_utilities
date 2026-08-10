"""Tests for include/exclude regex matching."""
from __future__ import annotations

import pytest

from folder_migrator.exceptions import ConfigurationError
from folder_migrator.matcher import RegexMatcher


def test_include_all_by_default() -> None:
    matcher = RegexMatcher([r".*"], [])
    assert matcher.should_move_file("anything.txt")


def test_include_specific_extension() -> None:
    matcher = RegexMatcher([r"\.png$"], [])
    assert matcher.should_move_file("photo.png")
    assert not matcher.should_move_file("notes.txt")


def test_exclude_takes_precedence_over_include() -> None:
    matcher = RegexMatcher([r".*"], [r"\.DS_Store", r"__pycache__"])
    assert not matcher.should_move_file(".DS_Store")
    assert matcher.should_move_file("main.py")


def test_directory_pruning() -> None:
    matcher = RegexMatcher([r".*"], [r"^\.git$", r"node_modules"])
    assert not matcher.should_enter_directory(".git")
    assert not matcher.should_enter_directory("node_modules")
    assert matcher.should_enter_directory("src")


def test_invalid_regex_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        RegexMatcher([r"([unclosed"], [])
