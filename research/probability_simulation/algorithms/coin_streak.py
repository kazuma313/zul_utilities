"""
-> Coin Flip Streak
Simulasikan lempar koin n kali, cari probabilitas munculnya streak (rentetan)
minimal k kali "head" berturut-turut.

Input:
    n (int) - jumlah lemparan koin per simulasi.
    k (int) - panjang streak minimal "head" berturut-turut yang dicari.
    trials (int) - jumlah simulasi yang dijalankan, default 10000.
    seed (int | None) - random seed, default None.
Output: (float) - estimasi probabilitas (0.0 - 1.0) munculnya streak head
    dengan panjang >= k dalam n lemparan.
"""


def simulate_coin_streak(n: int, k: int, trials: int = 10000, seed: int | None = None) -> float:
    """
    Estimate the probability of getting a streak of at least k consecutive
    heads in n coin flips, via Monte Carlo simulation.

    Args:
        n (int): Number of coin flips per trial.
        k (int): Minimum streak length of consecutive heads to look for.
        trials (int): Number of simulation trials. Defaults to 10000.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated probability in [0.0, 1.0].

    Raises:
        ValueError: If n or k is not a positive integer.
    """
    raise NotImplementedError("TODO: implement simulate_coin_streak")


if __name__ == "__main__":
    print(simulate_coin_streak(n=20, k=5, trials=10000, seed=42))
