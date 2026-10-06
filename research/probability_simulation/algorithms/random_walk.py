"""
-> Random Walk 1D/2D
Simulasikan random walk sepanjang n langkah (tiap langkah +-1 dengan
probabilitas sama). Hitung posisi akhir rata-rata dan jarak rata-rata dari
titik asal setelah banyak simulasi. Bonus: visualisasikan salah satu lintasan.

Input (random_walk):
    n_steps (int) - jumlah langkah.
    dimensions (int) - 1 untuk 1D, 2 untuk 2D, default 1.
    seed (int | None) - random seed, default None.
Output (random_walk): (list[tuple]) - lintasan posisi, panjang n_steps + 1
    (termasuk titik awal di origin), tiap elemen tuple sepanjang `dimensions`.

Input (average_distance_from_origin):
    n_steps (int) - jumlah langkah per simulasi.
    dimensions (int) - 1 atau 2, default 1.
    trials (int) - jumlah simulasi, default 1000.
    seed (int | None) - random seed, default None.
Output (average_distance_from_origin): (float) - rata-rata jarak Euclidean
    dari origin setelah n_steps, dirata-rata dari `trials` simulasi.
    
pesudocode:
set random seed

each_step = 1

distance_list = []

random_step = rand.chouce([-1, 1])

for _ in range (trials):

    random_steps =  ranint(1, n_steps)
    distance_list.append(random_steps*each_step)
    

average_distance = sum(distance_list)/trials

return average_distance
"""


def random_walk(n_steps: int, dimensions: int = 1, seed: int | None = None) -> list:
    """
    Simulate a single random walk path of n_steps in 1D or 2D.

    Args:
        n_steps (int): Number of steps.
        dimensions (int): 1 for 1D, 2 for 2D. Defaults to 1.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        list[tuple]: Path positions, length n_steps + 1 (including the
            starting point at the origin), each entry a tuple of length
            `dimensions`.

    Raises:
        ValueError: If dimensions is not 1 or 2, or n_steps is negative.
    """
    raise NotImplementedError("TODO: implement random_walk")


def average_distance_from_origin(
    n_steps: int,
    dimensions: int = 1,
    trials: int = 1000,
    seed: int | None = None,
) -> float:
    """
    Estimate the average Euclidean distance from the origin after n_steps,
    averaged over many random-walk trials.

    Args:
        n_steps (int): Number of steps per trial.
        dimensions (int): 1 or 2. Defaults to 1.
        trials (int): Number of simulation trials. Defaults to 1000.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        float: Average distance from the origin.
    """
    raise NotImplementedError("TODO: implement average_distance_from_origin")


if __name__ == "__main__":
    print(random_walk(n_steps=10, dimensions=1, seed=42))
    print(average_distance_from_origin(n_steps=10, dimensions=1, trials=1000, seed=42))
