"""
this module for testing 1D/2D random walk simulation
"""

import unittest
from research.probability_simulation.algorithms.random_walk import (
    random_walk,
    average_distance_from_origin,
)


class TestRandomWalkCorrectness(unittest.TestCase):
    """Verifies the walk behaves like a true random walk statistically."""

    def test_1d_steps_move_by_one(self):
        path = random_walk(n_steps=10, dimensions=1, seed=42)

        for previous, current in zip(path, path[1:]):
            self.assertIn(current[0] - previous[0], (-1, 1))

    def test_more_steps_increases_average_distance(self):
        short_walk = average_distance_from_origin(n_steps=10, dimensions=1, trials=2000, seed=42)
        long_walk = average_distance_from_origin(n_steps=200, dimensions=1, trials=2000, seed=42)

        self.assertGreater(long_walk, short_walk)


class TestRandomWalkSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, edge cases and robustness."""

    def test_path_length_1d(self):
        path = random_walk(n_steps=10, dimensions=1, seed=42)

        self.assertEqual(len(path), 11)

    def test_path_starts_at_origin_1d(self):
        path = random_walk(n_steps=10, dimensions=1, seed=42)

        self.assertEqual(path[0], (0,))

    def test_path_starts_at_origin_2d(self):
        path = random_walk(n_steps=10, dimensions=2, seed=42)

        self.assertEqual(path[0], (0, 0))

    def test_zero_steps_returns_only_origin(self):
        path = random_walk(n_steps=0, dimensions=1, seed=42)

        self.assertEqual(path, [(0,)])

    def test_zero_steps_has_zero_distance(self):
        result = average_distance_from_origin(n_steps=0, dimensions=1, trials=100, seed=42)

        self.assertEqual(result, 0.0)

    def test_result_is_non_negative(self):
        result = average_distance_from_origin(n_steps=50, dimensions=2, trials=500, seed=42)

        self.assertGreaterEqual(result, 0.0)

    def test_unsupported_dimensions_raises_value_error(self):
        with self.assertRaises(ValueError):
            random_walk(n_steps=10, dimensions=3, seed=42)


if __name__ == "__main__":
    unittest.main()
