"""
this module for testing valid parentheses / balanced brackets algorithm
"""

import time
import unittest
from research.string_algorithms.algorithms.valid_parentheses import is_valid_parentheses


class TestValidParenthesesCorrectness(unittest.TestCase):
    """Verifies the algorithm accepts/rejects bracket sequences correctly."""

    def test_simple_valid(self):
        self.assertTrue(is_valid_parentheses("()[]{}"))

    def test_nested_valid(self):
        self.assertTrue(is_valid_parentheses("{[]}"))

    def test_mismatched_order(self):
        self.assertFalse(is_valid_parentheses("(]"))


class TestValidParenthesesSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and algorithmic efficiency."""

    def test_unclosed_bracket(self):
        self.assertFalse(is_valid_parentheses("(("))

    def test_empty_string_is_valid(self):
        self.assertTrue(is_valid_parentheses(""))

    def test_extra_closing_bracket(self):
        self.assertFalse(is_valid_parentheses("())"))

    def test_handles_large_balanced_input_efficiently(self):
        # a stack-based O(n) solution stays fast even on large input.
        s = "([{}])" * 50000

        start = time.perf_counter()
        result = is_valid_parentheses(s)
        elapsed = time.perf_counter() - start

        self.assertTrue(result)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
