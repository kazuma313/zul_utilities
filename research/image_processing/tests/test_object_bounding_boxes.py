"""
this module for testing bounding box detection & drawing (problem #7, bonus)
"""

import unittest
import numpy as np
from research.image_processing.algorithms.object_bounding_boxes import (
    find_bounding_boxes,
    draw_bounding_boxes,
)


class TestObjectBoundingBoxesCorrectness(unittest.TestCase):
    """Verifies bounding boxes are found and ordered correctly."""

    def test_finds_single_bounding_box(self):
        mask = np.zeros((10, 10), dtype=np.uint8)
        mask[2:5, 3:7] = 255  # a 3-tall, 4-wide rectangle at (x=3, y=2)

        boxes = find_bounding_boxes(mask)

        self.assertEqual(boxes, [(3, 2, 4, 3)])

    def test_boxes_sorted_by_area_descending(self):
        mask = np.zeros((12, 12), dtype=np.uint8)
        mask[1:3, 1:3] = 255  # small 2x2 box, area 4
        mask[6:11, 6:11] = 255  # large 5x5 box, area 25

        boxes = find_bounding_boxes(mask)

        areas = [w * h for (_, _, w, h) in boxes]
        self.assertEqual(areas, sorted(areas, reverse=True))
        self.assertEqual(areas[0], 25)


class TestObjectBoundingBoxesSoftwareEngineering(unittest.TestCase):
    """Checks the implementations' contracts, robustness and side effects."""

    def test_empty_mask_returns_no_boxes(self):
        mask = np.zeros((10, 10), dtype=np.uint8)

        self.assertEqual(find_bounding_boxes(mask), [])

    def test_draw_bounding_boxes_output_shape_matches_input(self):
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        boxes = [(1, 1, 3, 3)]

        result = draw_bounding_boxes(image, boxes)

        self.assertEqual(result.shape, image.shape)

    def test_draw_bounding_boxes_does_not_mutate_input_image(self):
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        original = image.copy()
        boxes = [(1, 1, 3, 3)]

        draw_bounding_boxes(image, boxes)

        np.testing.assert_array_equal(image, original)

    def test_draw_bounding_boxes_with_no_boxes_is_a_no_op(self):
        image = np.zeros((10, 10, 3), dtype=np.uint8)

        result = draw_bounding_boxes(image, [])

        np.testing.assert_array_equal(result, image)


if __name__ == "__main__":
    unittest.main()
