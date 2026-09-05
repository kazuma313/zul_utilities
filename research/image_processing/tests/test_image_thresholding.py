"""
this module for testing image thresholding algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.image_thresholding import threshold_image


class TestImageThresholdingCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right binary values."""

    def test_mixed_values(self):
        image = np.array([[10, 200], [128, 50]], dtype=np.uint8)
        expected = np.array([[0, 255], [255, 0]], dtype=np.uint8)

        np.testing.assert_array_equal(threshold_image(image, 127), expected)

    def test_all_below_threshold(self):
        image = np.array([[1, 2], [3, 4]], dtype=np.uint8)
        expected = np.zeros((2, 2), dtype=np.uint8)

        np.testing.assert_array_equal(threshold_image(image, 200), expected)

    def test_all_above_threshold(self):
        image = np.array([[250, 251], [252, 253]], dtype=np.uint8)
        expected = np.full((2, 2), 255, dtype=np.uint8)

        np.testing.assert_array_equal(threshold_image(image, 10), expected)

    def test_value_equal_to_threshold_is_black(self):
        image = np.array([[127]], dtype=np.uint8)
        expected = np.array([[0]], dtype=np.uint8)

        np.testing.assert_array_equal(threshold_image(image, 127), expected)


class TestImageThresholdingSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_does_not_mutate_input_image(self):
        image = np.array([[10, 200], [128, 50]], dtype=np.uint8)
        original = image.copy()

        threshold_image(image, 127)

        np.testing.assert_array_equal(image, original)

    def test_output_dtype_is_uint8(self):
        image = np.array([[10, 200]], dtype=np.uint8)

        result = threshold_image(image, 127)

        self.assertEqual(result.dtype, np.uint8)

    def test_threshold_out_of_range_raises_value_error(self):
        image = np.array([[10, 200]], dtype=np.uint8)

        with self.assertRaises(ValueError):
            threshold_image(image, 300)


if __name__ == "__main__":
    unittest.main()
