"""
this module for testing queue (Poisson process) simulation
"""

import unittest
from research.probability_simulation.algorithms.queue_simulation import simulate_queue


class TestQueueSimulationCorrectness(unittest.TestCase):
    """Verifies the simulation's queueing behavior matches expectations."""

    def test_busier_system_has_longer_wait(self):
        light_load = simulate_queue(arrival_rate=2, service_rate=10, duration=200, seed=42)
        heavy_load = simulate_queue(arrival_rate=9, service_rate=10, duration=200, seed=42)

        self.assertGreater(heavy_load["avg_wait_time"], light_load["avg_wait_time"])


class TestQueueSimulationSoftwareEngineering(unittest.TestCase):
    """Checks the implementation's contracts, robustness and determinism."""

    def test_result_has_expected_keys(self):
        result = simulate_queue(arrival_rate=5, service_rate=8, duration=100, seed=42)

        self.assertIn("avg_wait_time", result)
        self.assertIn("avg_queue_length", result)

    def test_metrics_are_non_negative(self):
        result = simulate_queue(arrival_rate=5, service_rate=8, duration=100, seed=42)

        self.assertGreaterEqual(result["avg_wait_time"], 0.0)
        self.assertGreaterEqual(result["avg_queue_length"], 0.0)

    def test_same_seed_is_reproducible(self):
        first = simulate_queue(arrival_rate=5, service_rate=8, duration=50, seed=42)
        second = simulate_queue(arrival_rate=5, service_rate=8, duration=50, seed=42)

        self.assertEqual(first, second)

    def test_non_positive_rates_raise_value_error(self):
        with self.assertRaises(ValueError):
            simulate_queue(arrival_rate=0, service_rate=8, duration=50, seed=42)


if __name__ == "__main__":
    unittest.main()
