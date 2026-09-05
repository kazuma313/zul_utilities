"""
this module for testing group anagrams algorithm
"""

import unittest
from research.string_algorithms.algorithms.group_anagram import group_anagrams


def _as_sorted_groups(groups):
    return sorted(sorted(group) for group in groups)


class TestGroupAnagramCorrectness(unittest.TestCase):
    """Verifies the algorithm groups anagrams correctly."""

    def test_groups_anagrams_together(self):
        result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
        expected = [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]

        self.assertEqual(_as_sorted_groups(result), _as_sorted_groups(expected))

    def test_no_anagrams_in_common(self):
        result = group_anagrams(["abc", "def", "ghi"])

        self.assertEqual(_as_sorted_groups(result), [["abc"], ["def"], ["ghi"]])


class TestGroupAnagramSoftwareEngineering(unittest.TestCase):
    """Checks edge cases, robustness and side effects."""

    def test_empty_input(self):
        self.assertEqual(group_anagrams([]), [])

    def test_single_word(self):
        self.assertEqual(_as_sorted_groups(group_anagrams(["abc"])), [["abc"]])

    def test_does_not_mutate_input_list(self):
        words = ["eat", "tea", "bat"]
        original = list(words)

        group_anagrams(words)

        self.assertEqual(words, original)


if __name__ == "__main__":
    unittest.main()
