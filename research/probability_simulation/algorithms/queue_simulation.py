"""
-> Simulasi Antrian (Queueing / Poisson Process)
Simulasikan kedatangan pelanggan ke sebuah toko mengikuti proses Poisson
dengan rate lambda per jam, dan waktu layanan mengikuti distribusi tertentu
(misal exponential). Hitung rata-rata waktu tunggu pelanggan atau rata-rata
jumlah pelanggan dalam antrian pada satu waktu.

Input:
    arrival_rate (float) - rate kedatangan pelanggan (lambda), per jam.
    service_rate (float) - rate layanan (mu), pelanggan per jam.
    duration (float) - lama simulasi, dalam jam.
    seed (int | None) - random seed, default None.
Output: (dict) - berisi minimal:
    "avg_wait_time" (float) - rata-rata waktu tunggu pelanggan (jam).
    "avg_queue_length" (float) - rata-rata jumlah pelanggan dalam antrian.
"""


def simulate_queue(
    arrival_rate: float,
    service_rate: float,
    duration: float,
    seed: int | None = None,
) -> dict:
    """
    Simulate an M/M/1-style queue (Poisson arrivals, exponential service).

    Args:
        arrival_rate (float): Customer arrival rate (lambda), per hour.
        service_rate (float): Service rate (mu), customers per hour.
        duration (float): Simulation duration, in hours.
        seed (int | None): Random seed for reproducibility. Defaults to None.

    Returns:
        dict: {"avg_wait_time": float, "avg_queue_length": float}.

    Raises:
        ValueError: If arrival_rate, service_rate, or duration is not positive.
    """
    raise NotImplementedError("TODO: implement simulate_queue")


if __name__ == "__main__":
    print(simulate_queue(arrival_rate=5, service_rate=8, duration=100, seed=42))
