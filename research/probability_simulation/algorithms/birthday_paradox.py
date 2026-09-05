"""
-> dalam grup k orang, berapa probabilitas minimal dua orang punya hari ulang
tahun sama? Jalankan simulasi untuk berbagai k dan bandingkan dengan rumus
analitisnya.

Input:
    k (int) - jumlah orang dalam grup.
    trials (int) - jumlah simulasi yang dijalankan, default 10000.
    seed (int | None) - random seed untuk hasil yang reproducible, default None.
Output: (float) - estimasi probabilitas (0.0 - 1.0) minimal dua orang berbagi
    hari ulang tahun yang sama.
"""


def simulate_birthday_paradox(k: int, trials: int = 10000, seed: int | None = None) -> float:
    """
    Estimate the probability that at least two people in a group of k share a
    birthday, via Monte Carlo simulation.

    Args:
        k (int): Number of people in the group.
        trials (int): Number of simulation trials. Defaults to 10000.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated probability in [0.0, 1.0].

    Raises:
        ValueError: If k is negative or trials is not positive.
    """
    raise NotImplementedError("TODO: implement simulate_birthday_paradox")


if __name__ == "__main__":
    print(simulate_birthday_paradox(k=23, trials=10000, seed=42))
