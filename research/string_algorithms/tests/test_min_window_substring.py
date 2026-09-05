"""
this module for testing minimum window substring algorithm
"""

import time
import unittest
from research.string_algorithms.algorithms.min_window_substring import min_window_substring


class TestMinWindowSubstringCorrectness(unittest.TestCase):
    """Verifies the algorithm finds the correct shortest window."""

    def test_classic_example(self):
        self.assertEqual(min_window_substring("ADOBECODEBANC", "ABC"), "BANC")

    def test_whole_string_required(self):
        self.assertEqual(min_window_substring("aa", "aa"), "aa")


class TestMinWindowSubstringSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and algorithmic efficiency."""

    def test_no_valid_window(self):
        self.assertEqual(min_window_substring("a", "aa"), "")

    def test_source_equals_target(self):
        self.assertEqual(min_window_substring("a", "a"), "a")

    def test_target_is_empty(self):
        self.assertEqual(min_window_substring("abc", ""), "")

    def test_handles_large_input_efficiently(self):
        # a brute-force O(n^2)/O(n^3) scan over all substrings would be
        # noticeably slow here; a sliding-window O(n) solution stays fast.
        s = "x" * 200000 + "ABC"

        start = time.perf_counter()
        result = min_window_substring(s, "ABC")
        elapsed = time.perf_counter() - start

        self.assertEqual(result, "ABC")
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
