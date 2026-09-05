"""
this module for testing 2D convolution algorithm
"""

import unittest
import numpy as np
from research.image_processing.algorithms.convolution_2d import convolve2d


class TestConvolution2DCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right values for known kernels."""

    def test_identity_kernel_returns_same_image(self):
        image = np.arange(9, dtype=float).reshape(3, 3)
        kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=float)

        result = convolve2d(image, kernel)

        np.testing.assert_allclose(result, image)

    def test_box_blur_center_pixel(self):
        image = np.array(
            [
                [1, 1, 1],
                [1, 9, 1],
                [1, 1, 1],
            ],
            dtype=float,
        )
        kernel = np.ones((3, 3)) / 9

        result = convolve2d(image, kernel)

        # center pixel = average of all 9 values = (8*1 + 9) / 9
        self.assertAlmostEqual(result[1, 1], 17 / 9)


class TestConvolution2DSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_output_shape_matches_input(self):
        image = np.arange(16, dtype=float).reshape(4, 4)
        kernel = np.ones((3, 3)) / 9

        result = convolve2d(image, kernel)

        self.assertEqual(result.shape, image.shape)

    def test_does_not_mutate_input_image_or_kernel(self):
        image = np.arange(9, dtype=float).reshape(3, 3)
        kernel = np.ones((3, 3)) / 9
        image_copy, kernel_copy = image.copy(), kernel.copy()

        convolve2d(image, kernel)

        np.testing.assert_array_equal(image, image_copy)
        np.testing.assert_array_equal(kernel, kernel_copy)

    def test_even_sized_kernel_raises_value_error(self):
        image = np.arange(9, dtype=float).reshape(3, 3)
        kernel = np.ones((2, 2))

        with self.assertRaises(ValueError):
            convolve2d(image, kernel)


if __name__ == "__main__":
    unittest.main()
