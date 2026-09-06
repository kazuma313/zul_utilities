"""
this module for testing grayscale conversion & thresholding (problem #1)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.grayscale_thresholding import (
    to_grayscale,
    binary_threshold,
)


class TestGrayscaleThresholdingCorrectness(unittest.TestCase):
    """Verifies grayscale conversion and thresholding produce the right values."""

    def test_pure_red_grayscale_value(self):
        image = np.array([[[255, 0, 0]]], dtype=np.uint8)
        expected = np.array([[76]], dtype=np.uint8)  # round(0.299*255)

        result = to_grayscale(image)

        np.testing.assert_array_equal(result, expected)

    def test_manual_threshold_splits_correctly(self):
        gray = np.array([[10, 200], [128, 50]], dtype=np.uint8)
        expected = np.array([[0, 255], [255, 0]], dtype=np.uint8)

        result = binary_threshold(gray, threshold=127, method="manual")

        np.testing.assert_array_equal(result, expected)

    def test_otsu_finds_a_clean_split_on_bimodal_histogram(self):
        # two clearly separated intensity clusters: Otsu should threshold
        # between them regardless of the exact value it picks.
        gray = np.array([[10, 12], [240, 245]], dtype=np.uint8)

        result = binary_threshold(gray, method="otsu")

        self.assertTrue(np.all(result[0, :] == 0))
        self.assertTrue(np.all(result[1, :] == 255))


class TestGrayscaleThresholdingSoftwareEngineering(unittest.TestCase):
    """Checks the implementations' contracts, robustness and side effects."""

    def test_grayscale_output_shape_and_dtype(self):
        image = np.random.randint(0, 256, size=(5, 7, 3), dtype=np.uint8)

        result = to_grayscale(image)

        self.assertEqual(result.shape, (5, 7))
        self.assertEqual(result.dtype, np.uint8)

    def test_does_not_mutate_input_image(self):
        image = np.full((2, 2, 3), 123, dtype=np.uint8)
        original = image.copy()

        to_grayscale(image)

        np.testing.assert_array_equal(image, original)

    def test_threshold_output_is_binary(self):
        gray = np.array([[10, 200], [128, 50]], dtype=np.uint8)

        result = binary_threshold(gray, threshold=127, method="manual")

        self.assertTrue(set(np.unique(result)).issubset({0, 255}))

    def test_invalid_method_raises_value_error(self):
        gray = np.array([[10, 200]], dtype=np.uint8)

        with self.assertRaises(ValueError):
            binary_threshold(gray, method="adaptive")

    def test_threshold_out_of_range_raises_value_error(self):
        gray = np.array([[10, 200]], dtype=np.uint8)

        with self.assertRaises(ValueError):
            binary_threshold(gray, threshold=300, method="manual")


if __name__ == "__main__":
    unittest.main()
