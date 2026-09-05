"""
this module for testing valid palindrome algorithm
"""

import unittest
from research.string_algorithms.algorithms.palindrome import is_valid_palindrome


class TestPalindromeCorrectness(unittest.TestCase):
    """Verifies the algorithm handles punctuation and case correctly."""

    def test_valid_palindrome_with_punctuation(self):
        self.assertTrue(is_valid_palindrome("A man, a plan, a canal: Panama"))

    def test_not_a_palindrome(self):
        self.assertFalse(is_valid_palindrome("race a car"))


class TestPalindromeSoftwareEngineering(unittest.TestCase):
    """Checks edge cases and robustness."""

    def test_empty_string_is_palindrome(self):
        self.assertTrue(is_valid_palindrome(""))

    def test_only_non_alphanumeric_is_palindrome(self):
        self.assertTrue(is_valid_palindrome(".,"))

    def test_single_character(self):
        self.assertTrue(is_valid_palindrome("a"))


if __name__ == "__main__":
    unittest.main()
