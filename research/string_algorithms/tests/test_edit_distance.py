"""
this module for testing minimum edit distance algorithm
"""

import time
import unittest
from research.string_algorithms.algorithms.edit_distance import min_edit_distance


class TestEditDistanceCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right minimum edit distance."""

    def test_horse_to_ros(self):
        self.assertEqual(min_edit_distance("horse", "ros"), 3)

    def test_single_substitution(self):
        self.assertEqual(min_edit_distance("cat", "cut"), 1)


class TestEditDistanceSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and algorithmic efficiency."""

    def test_identical_strings(self):
        self.assertEqual(min_edit_distance("abc", "abc"), 0)

    def test_empty_to_nonempty(self):
        self.assertEqual(min_edit_distance("", "abc"), 3)

    def test_nonempty_to_empty(self):
        self.assertEqual(min_edit_distance("abc", ""), 3)

    def test_handles_moderate_length_input_efficiently(self):
        # plain recursion without memoization/DP is exponential and would
        # not finish here in any reasonable time; a DP table (or memoized
        # recursion) is O(n*m) and stays fast.
        s = "abcde" * 60  # length 300
        t = "abfde" * 60  # length 300

        start = time.perf_counter()
        min_edit_distance(s, t)
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
