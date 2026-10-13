"""
-> Monte Carlo untuk Estimasi Integral / Expected Value
Diberi sebuah fungsi matematika (misal payoff acak), estimasi expected
value-nya lewat sampling, lalu diskusikan bagaimana variance dari estimator
berkurang seiring n bertambah (Central Limit Theorem secara intuitif).

Input:
    sampler (Callable[[], float]) - fungsi tanpa argumen yang mengembalikan
        satu sample acak dari payoff/fungsi yang ingin diestimasi.
    n_samples (int) - jumlah sample yang diambil.
    seed (int | None) - random seed, default None.
Output: tuple(mean, standard_error)
    mean (float) - estimasi expected value.
    standard_error (float) - standard error dari estimator (std / sqrt(n)).
"""

from typing import Callable


def monte_carlo_expected_value(
    sampler: Callable[[], float],
    n_samples: int,
    seed: int | None = None,
) -> tuple:
    """
    Estimate the expected value of a random payoff via Monte Carlo sampling.

    Args:
        sampler (Callable[[], float]): No-argument function returning one
            random sample of the payoff/quantity to estimate.
        n_samples (int): Number of samples to draw.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        tuple[float, float]: (estimated mean, standard error of the estimator).

    Raises:
        ValueError: If n_samples is not positive.
    """
    raise NotImplementedError("TODO: implement monte_carlo_expected_value")


if __name__ == "__main__":
    import random

    random.seed(42)
    mean, se = monte_carlo_expected_value(lambda: random.uniform(0, 1), n_samples=10000, seed=42)
    print(mean, se)
