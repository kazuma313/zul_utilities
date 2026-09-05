"""
this module for testing grayscale conversion algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.grayscale_conversion import to_grayscale


class TestGrayscaleConversionCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right values for known colors."""

    def test_pure_red(self):
        image = np.array([[[255, 0, 0]]], dtype=np.uint8)
        expected = np.array([[76]], dtype=np.uint8)  # round(0.299*255)

        result = to_grayscale(image)

        self.assertEqual(result.shape, (1, 1))
        np.testing.assert_array_equal(result, expected)

    def test_pure_white(self):
        image = np.full((2, 2, 3), 255, dtype=np.uint8)
        expected = np.full((2, 2), 255, dtype=np.uint8)

        np.testing.assert_array_equal(to_grayscale(image), expected)

    def test_pure_black(self):
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        expected = np.zeros((2, 2), dtype=np.uint8)

        np.testing.assert_array_equal(to_grayscale(image), expected)


class TestGrayscaleConversionSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_output_shape_matches_input_hw(self):
        image = np.random.randint(0, 256, size=(5, 7, 3), dtype=np.uint8)

        result = to_grayscale(image)

        self.assertEqual(result.shape, (5, 7))

    def test_output_dtype_is_uint8(self):
        image = np.full((2, 2, 3), 200, dtype=np.uint8)

        result = to_grayscale(image)

        self.assertEqual(result.dtype, np.uint8)

    def test_does_not_mutate_input_image(self):
        image = np.full((2, 2, 3), 123, dtype=np.uint8)
        original = image.copy()

        to_grayscale(image)

        np.testing.assert_array_equal(image, original)

    def test_wrong_number_of_channels_raises_value_error(self):
        already_grayscale = np.zeros((4, 4), dtype=np.uint8)

        with self.assertRaises(ValueError):
            to_grayscale(already_grayscale)


if __name__ == "__main__":
    unittest.main()
