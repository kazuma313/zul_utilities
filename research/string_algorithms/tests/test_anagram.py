"""
this module for testing anagram detection algorithm
"""

import time
import unittest
from research.string_algorithms.algorithms.anagram import is_anagram


class TestAnagramCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right true/false answer."""

    def test_valid_anagram(self):
        self.assertTrue(is_anagram("listen", "silent"))

    def test_not_an_anagram(self):
        self.assertFalse(is_anagram("hello", "world"))

    def test_different_lengths(self):
        self.assertFalse(is_anagram("ab", "abc"))

    def test_case_sensitive(self):
        self.assertFalse(is_anagram("Listen", "silent"))


class TestAnagramSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and algorithmic efficiency."""

    def test_empty_strings(self):
        self.assertTrue(is_anagram("", ""))

    def test_same_string(self):
        self.assertTrue(is_anagram("abc", "abc"))

    def test_handles_large_input_efficiently(self):
        # a naive O(n^2) comparison would noticeably slow down here;
        # an O(n log n) sort or O(n) counting solution stays fast.
        s = "ab" * 100000
        t = "ba" * 100000

        start = time.perf_counter()
        result = is_anagram(s, t)
        elapsed = time.perf_counter() - start

        self.assertTrue(result)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
