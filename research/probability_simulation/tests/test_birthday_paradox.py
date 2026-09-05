"""
this module for testing birthday paradox simulation
"""

import unittest
from research.probability_simulation.algorithms.birthday_paradox import (
    simulate_birthday_paradox,
)


class TestBirthdayParadoxCorrectness(unittest.TestCase):
    """Verifies the simulation matches known/analytic probabilities."""

    def test_k_equals_1_has_zero_probability(self):
        result = simulate_birthday_paradox(k=1, trials=1000, seed=42)

        self.assertEqual(result, 0.0)

    def test_matches_analytic_value_for_k_23(self):
        # analytic probability for k=23 is approximately 0.5073
        result = simulate_birthday_paradox(k=23, trials=20000, seed=42)

        self.assertAlmostEqual(result, 0.5073, delta=0.05)

    def test_larger_group_has_higher_probability(self):
        small_group = simulate_birthday_paradox(k=5, trials=5000, seed=42)
        large_group = simulate_birthday_paradox(k=40, trials=5000, seed=42)

        self.assertGreater(large_group, small_group)


class TestBirthdayParadoxSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and determinism."""

    def test_result_is_a_probability(self):
        result = simulate_birthday_paradox(k=23, trials=5000, seed=42)

        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_same_seed_is_reproducible(self):
        first = simulate_birthday_paradox(k=23, trials=2000, seed=42)
        second = simulate_birthday_paradox(k=23, trials=2000, seed=42)

        self.assertEqual(first, second)

    def test_negative_group_size_raises_value_error(self):
        with self.assertRaises(ValueError):
            simulate_birthday_paradox(k=-1, trials=100, seed=42)

    def test_non_positive_trials_raises_value_error(self):
        with self.assertRaises(ValueError):
            simulate_birthday_paradox(k=23, trials=0, seed=42)


if __name__ == "__main__":
    unittest.main()
