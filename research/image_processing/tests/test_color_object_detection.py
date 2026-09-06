"""
this module for testing color-based object detection & counting (problem #5)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.color_object_detection import (
    detect_and_count_colored_objects,
)


class TestColorObjectDetectionCorrectness(unittest.TestCase):
    """Verifies the algorithm produces the right mask/count for known inputs."""

    def test_single_red_object(self):
        image = np.zeros((6, 6, 3), dtype=np.uint8)
        image[1:3, 1:3] = [255, 0, 0]

        mask, count = detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        self.assertEqual(mask.shape, (6, 6))
        self.assertEqual(count, 1)
        self.assertTrue(np.all(mask[1:3, 1:3] == 255))

    def test_two_separate_red_objects(self):
        # each object is a 2x2 block, large enough to survive morphological
        # noise cleanup.
        image = np.zeros((8, 8, 3), dtype=np.uint8)
        image[0:2, 0:2] = [255, 0, 0]
        image[5:7, 5:7] = [255, 0, 0]

        _, count = detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        self.assertEqual(count, 2)

    def test_no_matching_objects(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)

        mask, count = detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        self.assertEqual(count, 0)
        self.assertTrue(np.all(mask == 0))

    def test_single_pixel_noise_speckle_is_filtered_out(self):
        # a real 3x3 object plus a lone 1-pixel speck of the same color far
        # away; morphological cleanup should drop the speck so it does not
        # get counted as a second object.
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        image[2:5, 2:5] = [255, 0, 0]
        image[8, 8] = [255, 0, 0]

        _, count = detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        self.assertEqual(count, 1)


class TestColorObjectDetectionSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and side effects."""

    def test_does_not_mutate_input_image(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)
        image[0:2, 0:2] = [255, 0, 0]
        original = image.copy()

        detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        np.testing.assert_array_equal(image, original)

    def test_mask_dtype_and_value_contract(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)

        mask, _ = detect_and_count_colored_objects(image, (0, 100, 100), (10, 255, 255))

        self.assertEqual(mask.dtype, np.uint8)
        self.assertTrue(set(np.unique(mask)).issubset({0, 255}))

    def test_invalid_hsv_bounds_raise_value_error(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)

        with self.assertRaises(ValueError):
            detect_and_count_colored_objects(image, (10, 255, 255), (0, 100, 100))


if __name__ == "__main__":
    unittest.main()
