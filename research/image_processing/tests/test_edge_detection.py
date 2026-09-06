"""
this module for testing Sobel & Canny edge detection (problem #3)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.edge_detection import (
    sobel_edge_detection,
    canny_edge_detection,
)


class TestEdgeDetectionCorrectness(unittest.TestCase):
    """Verifies both detectors produce the right response on known inputs."""

    def test_sobel_flat_image_has_no_edges(self):
        image = np.full((5, 5), 100, dtype=np.uint8)

        result = sobel_edge_detection(image)

        np.testing.assert_array_equal(result, np.zeros((5, 5), dtype=result.dtype))

    def test_sobel_vertical_edge_is_detected(self):
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 3:] = 255

        result = sobel_edge_detection(image)

        self.assertTrue(np.any(result[:, 2:4] > 0))

    def test_canny_flat_image_has_no_edges(self):
        image = np.full((10, 10), 100, dtype=np.uint8)

        result = canny_edge_detection(image)

        np.testing.assert_array_equal(result, np.zeros((10, 10), dtype=result.dtype))

    def test_canny_vertical_edge_is_detected(self):
        image = np.zeros((10, 10), dtype=np.uint8)
        image[:, 5:] = 255

        result = canny_edge_detection(image, threshold1=50, threshold2=150)

        self.assertTrue(np.any(result[:, 3:7] == 255))


class TestEdgeDetectionSoftwareEngineering(unittest.TestCase):
    """Checks the implementations' contracts, robustness and side effects."""

    def test_output_shape_and_dtype(self):
        image = np.zeros((5, 5), dtype=np.uint8)

        sobel_result = sobel_edge_detection(image)
        canny_result = canny_edge_detection(image)

        self.assertEqual(sobel_result.shape, image.shape)
        self.assertEqual(sobel_result.dtype, np.uint8)
        self.assertEqual(canny_result.shape, image.shape)
        self.assertEqual(canny_result.dtype, np.uint8)

    def test_canny_output_is_binary(self):
        image = np.zeros((10, 10), dtype=np.uint8)
        image[:, 5:] = 255

        result = canny_edge_detection(image)

        self.assertTrue(set(np.unique(result)).issubset({0, 255}))

    def test_does_not_mutate_input_image(self):
        image = np.zeros((5, 5), dtype=np.uint8)
        image[:, 3:] = 255
        original = image.copy()

        sobel_edge_detection(image)
        canny_edge_detection(image)

        np.testing.assert_array_equal(image, original)

    def test_color_image_raises_value_error(self):
        color_image = np.zeros((5, 5, 3), dtype=np.uint8)

        with self.assertRaises(ValueError):
            sobel_edge_detection(color_image)
        with self.assertRaises(ValueError):
            canny_edge_detection(color_image)

    def test_canny_invalid_threshold_order_raises_value_error(self):
        image = np.zeros((5, 5), dtype=np.uint8)

        with self.assertRaises(ValueError):
            canny_edge_detection(image, threshold1=200, threshold2=100)


if __name__ == "__main__":
    unittest.main()
