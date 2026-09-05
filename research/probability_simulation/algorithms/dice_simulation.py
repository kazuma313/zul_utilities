"""
-> Simulasi Lempar Dadu
Simulasikan melempar dua dadu 6-sisi sebanyak n kali. Estimasi probabilitas
jumlah keduanya = 7. Bandingkan dengan nilai analitis (1/6).

Input:
    target_sum (int) - jumlah target dari dua dadu (misal 7).
    trials (int) - jumlah lemparan yang disimulasikan, default 100000.
    seed (int | None) - random seed, default None.
Output: (float) - estimasi probabilitas (0.0 - 1.0) jumlah dua dadu == target_sum.
"""


def simulate_dice_sum_probability(
    target_sum: int,
    trials: int = 100000,
    seed: int | None = None,
) -> float:
    """
    Estimate the probability that the sum of two 6-sided dice equals
    target_sum, via Monte Carlo simulation.

    Args:
        target_sum (int): Target sum of the two dice (e.g. 7).
        trials (int): Number of simulated rolls. Defaults to 100000.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Estimated probability in [0.0, 1.0].

    Raises:
        ValueError: If trials is not positive.
    """
    raise NotImplementedError("TODO: implement simulate_dice_sum_probability")


if __name__ == "__main__":
    print(simulate_dice_sum_probability(target_sum=7, trials=100000, seed=42))
