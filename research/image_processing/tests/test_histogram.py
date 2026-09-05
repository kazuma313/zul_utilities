"""
this module for testing histogram & histogram equalization algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.histogram import (
    compute_histogram,
    histogram_equalization,
)


class TestHistogramCorrectness(unittest.TestCase):
    """Verifies the histogram and equalization produce the right values."""

    def test_counts_are_correct(self):
        image = np.array([[0, 0], [128, 255]], dtype=np.uint8)

        result = compute_histogram(image)

        self.assertEqual(result[0], 2)
        self.assertEqual(result[128], 1)
        self.assertEqual(result[255], 1)
        self.assertEqual(result.sum(), image.size)

    def test_constant_image_stays_uniform(self):
        image = np.full((3, 3), 100, dtype=np.uint8)

        result = histogram_equalization(image)

        self.assertEqual(len(np.unique(result)), 1)


class TestHistogramSoftwareEngineering(unittest.TestCase):
    """Checks the implementations' contracts, robustness and side effects."""

    def test_histogram_shape_is_256(self):
        image = np.array([[0, 64], [128, 255]], dtype=np.uint8)

        result = compute_histogram(image)

        self.assertEqual(result.shape, (256,))

    def test_equalization_output_shape_matches_input(self):
        image = np.array([[0, 64], [128, 255]], dtype=np.uint8)

        result = histogram_equalization(image)

        self.assertEqual(result.shape, image.shape)

    def test_equalization_output_dtype_is_uint8(self):
        image = np.array([[0, 64], [128, 255]], dtype=np.uint8)

        result = histogram_equalization(image)

        self.assertEqual(result.dtype, np.uint8)

    def test_does_not_mutate_input_image(self):
        image = np.array([[0, 64], [128, 255]], dtype=np.uint8)
        original = image.copy()

        compute_histogram(image)
        histogram_equalization(image)

        np.testing.assert_array_equal(image, original)


if __name__ == "__main__":
    unittest.main()
