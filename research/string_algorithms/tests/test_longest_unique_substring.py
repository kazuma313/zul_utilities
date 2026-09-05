"""
this module for testing longest substring without repeating characters algorithm
"""

import time
import unittest
from research.string_algorithms.algorithms.longest_unique_substring import (
    longest_substring_without_repeating,
)


class TestLongestUniqueSubstringCorrectness(unittest.TestCase):
    """Verifies the algorithm finds the correct longest length."""

    def test_classic_example(self):
        self.assertEqual(longest_substring_without_repeating("abcabcbb"), 3)

    def test_mixed_example(self):
        self.assertEqual(longest_substring_without_repeating("pwwkew"), 3)


class TestLongestUniqueSubstringSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and algorithmic efficiency."""

    def test_all_same_character(self):
        self.assertEqual(longest_substring_without_repeating("bbbbb"), 1)

    def test_empty_string(self):
        self.assertEqual(longest_substring_without_repeating(""), 0)

    def test_no_repeats(self):
        self.assertEqual(longest_substring_without_repeating("abcdef"), 6)

    def test_handles_large_input_efficiently(self):
        # a brute-force O(n^2)/O(n^3) scan over all substrings would be
        # noticeably slow here; a sliding-window O(n) solution stays fast.
        import string

        s = (string.ascii_lowercase * 10000)

        start = time.perf_counter()
        result = longest_substring_without_repeating(s)
        elapsed = time.perf_counter() - start

        self.assertEqual(result, 26)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
