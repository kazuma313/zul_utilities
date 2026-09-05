"""
this module for testing coin flip streak simulation
"""

import unittest
from research.probability_simulation.algorithms.coin_streak import simulate_coin_streak


class TestCoinStreakCorrectness(unittest.TestCase):
    """Verifies the simulation matches known/expected probabilities."""

    def test_streak_longer_than_flips_is_impossible(self):
        result = simulate_coin_streak(n=5, k=10, trials=1000, seed=42)

        self.assertEqual(result, 0.0)

    def test_streak_of_1_is_certain(self):
        # any sequence of at least one flip has a streak of >= 1 head,
        # as long as at least one head appears somewhere across trials it's high;
        # use enough flips to make P(at least one head) ~1
        result = simulate_coin_streak(n=20, k=1, trials=2000, seed=42)

        self.assertGreater(result, 0.99)

    def test_longer_streak_is_less_likely(self):
        short_streak = simulate_coin_streak(n=20, k=2, trials=5000, seed=42)
        long_streak = simulate_coin_streak(n=20, k=10, trials=5000, seed=42)

        self.assertGreater(short_streak, long_streak)


class TestCoinStreakSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and determinism."""

    def test_result_is_a_probability(self):
        result = simulate_coin_streak(n=20, k=5, trials=5000, seed=42)

        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_same_seed_is_reproducible(self):
        first = simulate_coin_streak(n=20, k=5, trials=2000, seed=42)
        second = simulate_coin_streak(n=20, k=5, trials=2000, seed=42)

        self.assertEqual(first, second)

    def test_non_positive_n_raises_value_error(self):
        with self.assertRaises(ValueError):
            simulate_coin_streak(n=0, k=1, trials=100, seed=42)

    def test_non_positive_k_raises_value_error(self):
        with self.assertRaises(ValueError):
            simulate_coin_streak(n=10, k=0, trials=100, seed=42)


if __name__ == "__main__":
    unittest.main()
