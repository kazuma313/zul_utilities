"""
this module for testing Monte Carlo pi estimation
"""

import math
import unittest
from research.probability_simulation.algorithms.monte_carlo_pi import estimate_pi


class TestMonteCarloPiCorrectness(unittest.TestCase):
    """Verifies the estimate converges to the true value of pi."""

    def test_result_is_close_to_pi(self):
        result = estimate_pi(n_samples=200000, seed=42)

        self.assertAlmostEqual(result, math.pi, delta=0.05)

    def test_more_samples_gives_smaller_error(self):
        few_samples_error = abs(estimate_pi(n_samples=100, seed=1) - math.pi)
        many_samples_error = abs(estimate_pi(n_samples=200000, seed=1) - math.pi)

        self.assertLess(many_samples_error, few_samples_error)


class TestMonteCarloPiSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and determinism."""

    def test_result_is_positive(self):
        result = estimate_pi(n_samples=1000, seed=42)

        self.assertGreater(result, 0)

    def test_same_seed_is_reproducible(self):
        first = estimate_pi(n_samples=5000, seed=42)
        second = estimate_pi(n_samples=5000, seed=42)

        self.assertEqual(first, second)

    def test_non_positive_sample_count_raises_value_error(self):
        with self.assertRaises(ValueError):
            estimate_pi(n_samples=0, seed=42)


if __name__ == "__main__":
    unittest.main()
