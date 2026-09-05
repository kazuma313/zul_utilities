"""
this module for testing run-length string compression algorithm
"""

import unittest
from research.string_algorithms.algorithms.string_compression import compress_string


class TestStringCompressionCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the correct run-length encoding."""

    def test_classic_example(self):
        self.assertEqual(compress_string("aaabbc"), "a3b2c1")

    def test_no_repeats(self):
        self.assertEqual(compress_string("abc"), "a1b1c1")


class TestStringCompressionSoftwareEngineering(unittest.TestCase):
    """Checks edge cases and robustness."""

    def test_all_same_character(self):
        self.assertEqual(compress_string("aaaa"), "a4")

    def test_empty_string(self):
        self.assertEqual(compress_string(""), "")

    def test_single_character(self):
        self.assertEqual(compress_string("a"), "a1")


if __name__ == "__main__":
    unittest.main()
