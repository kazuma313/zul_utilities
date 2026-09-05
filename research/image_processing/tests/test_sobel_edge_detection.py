"""
this module for testing Sobel edge detection algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.sobel_edge_detection import sobel_edge_detection


class TestSobelEdgeDetectionCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right gradient response."""

    def test_flat_image_has_no_edges(self):
        image = np.full((5, 5), 100, dtype=np.uint8)

        result = sobel_edge_detection(image)

        np.testing.assert_array_equal(result, np.zeros((5, 5), dtype=result.dtype))

    def test_vertical_edge_is_detected(self):
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 3:] = 255

        result = sobel_edge_detection(image)

        # somewhere near the boundary column, magnitude should be non-zero
        self.assertTrue(np.any(result[:, 2:4] > 0))


class TestSobelEdgeDetectionSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_output_shape_matches_input(self):
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 3:] = 255

        result = sobel_edge_detection(image)

        self.assertEqual(result.shape, image.shape)

    def test_output_dtype_is_uint8(self):
        image = np.zeros((5, 5), dtype=np.uint8)

        result = sobel_edge_detection(image)

        self.assertEqual(result.dtype, np.uint8)

    def test_does_not_mutate_input_image(self):
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 3:] = 255
        original = image.copy()

        sobel_edge_detection(image)

        np.testing.assert_array_equal(image, original)

    def test_color_image_raises_value_error(self):
        color_image = np.zeros((5, 5, 3), dtype=np.uint8)

        with self.assertRaises(ValueError):
            sobel_edge_detection(color_image)


if __name__ == "__main__":
    unittest.main()
