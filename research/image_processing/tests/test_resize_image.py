"""
this module for testing manual image resize algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.resize_image import resize_image


class TestResizeImageCorrectness(unittest.TestCase):
    """Verifies the algorithm produces images of the right size/content."""

    def test_downscale_shape(self):
        image = np.arange(16, dtype=np.uint8).reshape(4, 4)

        result = resize_image(image, 2, 2, method="nearest")

        self.assertEqual(result.shape, (2, 2))

    def test_same_size_returns_equivalent_image(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)

        result = resize_image(image, 2, 2, method="nearest")

        np.testing.assert_array_equal(result, image)


class TestResizeImageSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_output_shape_nearest(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)

        result = resize_image(image, 4, 4, method="nearest")

        self.assertEqual(result.shape, (4, 4))

    def test_output_shape_bilinear(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)

        result = resize_image(image, 4, 4, method="bilinear")

        self.assertEqual(result.shape, (4, 4))

    def test_does_not_mutate_input_image(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)
        original = image.copy()

        resize_image(image, 4, 4, method="nearest")

        np.testing.assert_array_equal(image, original)

    def test_unsupported_method_raises_value_error(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)

        with self.assertRaises(ValueError):
            resize_image(image, 4, 4, method="bicubic")

    def test_non_positive_dimensions_raise_value_error(self):
        image = np.array([[10, 20], [30, 40]], dtype=np.uint8)

        with self.assertRaises(ValueError):
            resize_image(image, 0, 4, method="nearest")


if __name__ == "__main__":
    unittest.main()
