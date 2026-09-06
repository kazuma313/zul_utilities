"""
this module for testing Gaussian blur & median blur (problem #2)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.basic_filtering import (
    apply_gaussian_blur,
    apply_median_blur,
)


class TestBasicFilteringCorrectness(unittest.TestCase):
    """Verifies each filter behaves the way it is expected to."""

    def test_median_blur_removes_salt_and_pepper_noise(self):
        clean = np.full((9, 9), 100, dtype=np.uint8)
        noisy = clean.copy()
        noisy[4, 4] = 255  # a single salt-noise outlier

        result = apply_median_blur(noisy, ksize=3)

        # the outlier should be gone; the neighborhood is uniform 100 so the
        # median at (4, 4) should be back to 100.
        self.assertEqual(result[4, 4], 100)

    def test_median_blur_removes_noise_better_than_gaussian(self):
        clean = np.full((9, 9), 100, dtype=np.uint8)
        noisy = clean.copy()
        noisy[4, 4] = 255

        gaussian_result = apply_gaussian_blur(noisy, ksize=3)
        median_result = apply_median_blur(noisy, ksize=3)

        gaussian_error = abs(int(gaussian_result[4, 4]) - 100)
        median_error = abs(int(median_result[4, 4]) - 100)

        self.assertLess(median_error, gaussian_error)


class TestBasicFilteringSoftwareEngineering(unittest.TestCase):
    """Checks the implementations' contracts, robustness and side effects."""

    def test_output_shape_matches_input(self):
        image = np.full((10, 10), 100, dtype=np.uint8)

        self.assertEqual(apply_gaussian_blur(image, ksize=3).shape, image.shape)
        self.assertEqual(apply_median_blur(image, ksize=3).shape, image.shape)

    def test_does_not_mutate_input_image(self):
        image = np.full((10, 10), 100, dtype=np.uint8)
        image[5, 5] = 255
        original = image.copy()

        apply_gaussian_blur(image, ksize=3)
        apply_median_blur(image, ksize=3)

        np.testing.assert_array_equal(image, original)

    def test_even_ksize_raises_value_error(self):
        image = np.full((10, 10), 100, dtype=np.uint8)

        with self.assertRaises(ValueError):
            apply_gaussian_blur(image, ksize=4)
        with self.assertRaises(ValueError):
            apply_median_blur(image, ksize=4)


if __name__ == "__main__":
    unittest.main()
