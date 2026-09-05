"""
this module for testing Monte Carlo expected value estimation
"""

import random
import unittest
from research.probability_simulation.algorithms.monte_carlo_integral import (
    monte_carlo_expected_value,
)


class TestMonteCarloIntegralCorrectness(unittest.TestCase):
    """Verifies the estimator converges to the right mean and shrinking error."""

    def test_constant_sampler_returns_exact_mean_and_zero_error(self):
        mean, standard_error = monte_carlo_expected_value(lambda: 5.0, n_samples=1000, seed=42)

        self.assertAlmostEqual(mean, 5.0)
        self.assertAlmostEqual(standard_error, 0.0)

    def test_uniform_sampler_mean_close_to_half(self):
        rng = random.Random(42)
        mean, _ = monte_carlo_expected_value(lambda: rng.uniform(0, 1), n_samples=50000, seed=42)

        self.assertAlmostEqual(mean, 0.5, delta=0.05)

    def test_standard_error_shrinks_with_more_samples(self):
        rng = random.Random(1)
        _, se_small = monte_carlo_expected_value(lambda: rng.uniform(0, 1), n_samples=100, seed=1)
        _, se_large = monte_carlo_expected_value(
            lambda: rng.uniform(0, 1), n_samples=50000, seed=1
        )

        self.assertLess(se_large, se_small)


class TestMonteCarloIntegralSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts and robustness."""

    def test_return_type_is_tuple_of_two_floats(self):
        result = monte_carlo_expected_value(lambda: 1.0, n_samples=10, seed=42)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], float)

    def test_non_positive_sample_count_raises_value_error(self):
        with self.assertRaises(ValueError):
            monte_carlo_expected_value(lambda: 1.0, n_samples=0, seed=42)


if __name__ == "__main__":
    unittest.main()
