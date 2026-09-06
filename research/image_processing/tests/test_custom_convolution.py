"""
this module for testing custom kernel convolution via filter2D (problem #6)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.custom_convolution import (
    apply_kernel,
    SHARPEN_KERNEL,
)


class TestCustomConvolutionCorrectness(unittest.TestCase):
    """Verifies the algorithm applies kernels with the right math."""

    def test_identity_kernel_returns_same_image(self):
        image = np.arange(9, dtype=np.uint8).reshape(3, 3)
        identity_kernel = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=float)

        result = apply_kernel(image, identity_kernel)

        np.testing.assert_array_equal(result, image)

    def test_sharpen_kernel_increases_center_pixel(self):
        image = np.array(
            [
                [100, 100, 100],
                [100, 120, 100],
                [100, 100, 100],
            ],
            dtype=np.uint8,
        )

        result = apply_kernel(image, SHARPEN_KERNEL)

        # center = 5*120 - (100+100+100+100) = 200
        self.assertEqual(int(result[1, 1]), 200)


class TestCustomConvolutionSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_output_shape_matches_input(self):
        image = np.arange(16, dtype=np.uint8).reshape(4, 4)

        result = apply_kernel(image, SHARPEN_KERNEL)

        self.assertEqual(result.shape, image.shape)

    def test_output_dtype_is_uint8(self):
        image = np.arange(16, dtype=np.uint8).reshape(4, 4)

        result = apply_kernel(image, SHARPEN_KERNEL)

        self.assertEqual(result.dtype, np.uint8)

    def test_does_not_mutate_input_image_or_kernel(self):
        image = np.arange(9, dtype=np.uint8).reshape(3, 3)
        kernel = SHARPEN_KERNEL.copy()
        image_copy, kernel_copy = image.copy(), kernel.copy()

        apply_kernel(image, kernel)

        np.testing.assert_array_equal(image, image_copy)
        np.testing.assert_array_equal(kernel, kernel_copy)

    def test_even_sized_kernel_raises_value_error(self):
        image = np.arange(9, dtype=np.uint8).reshape(3, 3)
        even_kernel = np.ones((2, 2))

        with self.assertRaises(ValueError):
            apply_kernel(image, even_kernel)


if __name__ == "__main__":
    unittest.main()
