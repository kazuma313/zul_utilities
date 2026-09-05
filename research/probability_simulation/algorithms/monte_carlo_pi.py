"""
-> Monte Carlo Estimasi Pi
Estimasi nilai pi dengan random sampling titik dalam persegi dan hitung
proporsi yang jatuh dalam lingkaran seperempat.

Input:
    n_samples (int) - jumlah titik random yang di-sample.
    seed (int | None) - random seed, default None.
Output: (float) - estimasi nilai pi.
"""


def estimate_pi(n_samples: int, seed: int | None = None) -> float:
    """
    Estimate the value of pi using Monte Carlo sampling of points in a unit
    square, based on the proportion that fall inside the quarter circle.

    Args:
        n_samples (int): Number of random points to sample.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated value of pi.

    Raises:
        ValueError: If n_samples is not positive.
    """
    raise NotImplementedError("TODO: implement estimate_pi")


if __name__ == "__main__":
    print(estimate_pi(n_samples=100000, seed=42))
