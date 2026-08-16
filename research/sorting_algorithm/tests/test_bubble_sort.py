"""
this module for testing bubble sort algorithm
"""

import unittest
from research.sorting_algorithm.algorithms.bubble_sort import bubble_sort

class TestBubbleSort(unittest.TestCase):
    def test_unsorted_list(self):
        input_list = [5, 2, 8, 1, 3]
        expected_output = [1, 2, 3, 5, 8]

        self.assertEqual(
            bubble_sort(input_list),
            expected_output
        )

    def test_already_sorted_list(self):
        input_list = [1, 2, 3, 4, 5]
        expected_output = [1, 2, 3, 4, 5]

        self.assertEqual(
            bubble_sort(input_list),
            expected_output
        )

    def test_duplicate_values(self):
        input_list = [4, 2, 4, 1, 3]
        expected_output = [1, 2, 3, 4, 4]

        self.assertEqual(
            bubble_sort(input_list),
            expected_output
        )

    def test_negative_values(self):
        input_list = [-3, -1, -4, -2]
        expected_output = [-4, -3, -2, -1]

        self.assertEqual(
            bubble_sort(input_list),
            expected_output
        )
        
if __name__ == "__main__":
    unittest.main()
    