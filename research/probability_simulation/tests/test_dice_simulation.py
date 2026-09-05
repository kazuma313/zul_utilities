"""
this module for testing two-dice sum probability simulation
"""

import unittest
from research.probability_simulation.algorithms.dice_simulation import (
    simulate_dice_sum_probability,
)


class TestDiceSimulationCorrectness(unittest.TestCase):
    """Verifies the simulation matches known/analytic probabilities."""

    def test_matches_analytic_value_for_sum_7(self):
        # analytic probability of sum == 7 on two dice is 6/36 = 1/6
        result = simulate_dice_sum_probability(target_sum=7, trials=200000, seed=42)

        self.assertAlmostEqual(result, 1 / 6, delta=0.02)

    def test_impossible_sum_has_zero_probability(self):
        result = simulate_dice_sum_probability(target_sum=1, trials=1000, seed=42)

        self.assertEqual(result, 0.0)

    def test_sum_out_of_range_has_zero_probability(self):
        result = simulate_dice_sum_probability(target_sum=13, trials=1000, seed=42)

        self.assertEqual(result, 0.0)


class TestDiceSimulationSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and determinism."""

    def test_result_is_a_probability(self):
        result = simulate_dice_sum_probability(target_sum=7, trials=20000, seed=42)

        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_same_seed_is_reproducible(self):
        first = simulate_dice_sum_probability(target_sum=7, trials=2000, seed=42)
        second = simulate_dice_sum_probability(target_sum=7, trials=2000, seed=42)

        self.assertEqual(first, second)

    def test_non_positive_trials_raises_value_error(self):
        with self.assertRaises(ValueError):
            simulate_dice_sum_probability(target_sum=7, trials=0, seed=42)


if __name__ == "__main__":
    unittest.main()
