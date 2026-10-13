"""
Latensi pemanggilan fungsi: p50, p95, p99, dan QPS, termasuk saat paralel.

Gunanya:
    `measure_latency` memanggil sebuah fungsi untuk setiap input, berulang
    dan dengan beberapa thread, lalu meringkas durasinya. QPS dihitung dari
    waktu dinding, jadi mencerminkan throughput sungguhan saat paralel.
    `summarize_times` meringkas durasi yang dicatat dengan cara lain,
    misalnya oleh `TimerDecorator` di
    `zul.utilities.script_helper.eval_performance`. Hanya butuh library
    standar.

Cara pakai:
    from zul.evaluation.latency import measure_latency, save_times_csv

    stats = measure_latency(lambda q: retriever.retrieve(q, 5), questions,
                            repeats=10, workers=8, label="redis-rrf")
    print(stats.qps, stats.p95)
    save_times_csv({"recursive": durations}, "outputs/latency.csv")
"""

from __future__ import annotations

import csv
import statistics
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LatencyStats:
    """Ringkasan latensi dalam detik, dan QPS dari waktu dinding."""

    label: str
    calls: int
    wall_seconds: float
    qps: float
    mean: float
    p50: float
    p95: float
    p99: float
    min: float
    max: float

    def as_dict(self) -> dict[str, Any]:
        """Semua nilai sebagai dict, misalnya untuk satu baris CSV."""
        return asdict(self)


def _percentile(sorted_values: list[float], percent: float) -> float:
    if not sorted_values:
        return 0.0
    position = round(percent / 100 * (len(sorted_values) - 1))
    return sorted_values[min(len(sorted_values) - 1, max(0, position))]


def summarize_times(
    times: Iterable[float], label: str = "", wall_seconds: float | None = None
) -> LatencyStats:
    """Ringkas daftar durasi. Tanpa `wall_seconds`, QPS dihitung dari total durasi."""
    values = sorted(float(t) for t in times)
    wall = sum(values) if wall_seconds is None else wall_seconds
    return LatencyStats(
        label=label,
        calls=len(values),
        wall_seconds=round(wall, 4),
        qps=round(len(values) / wall, 2) if wall > 0 else 0.0,
        mean=round(statistics.fmean(values), 4) if values else 0.0,
        p50=round(_percentile(values, 50), 4),
        p95=round(_percentile(values, 95), 4),
        p99=round(_percentile(values, 99), 4),
        min=round(values[0], 4) if values else 0.0,
        max=round(values[-1], 4) if values else 0.0,
    )


def measure_latency(
    fn: Callable[[Any], Any],
    inputs: Iterable[Any],
    *,
    repeats: int = 1,
    workers: int = 1,
    label: str = "",
) -> LatencyStats:
    """
    Panggil `fn(x)` untuk setiap input sebanyak `repeats` kali, lalu ringkas latensinya.

    Args:
        fn: Fungsi yang diukur, dengan satu argumen.
        inputs: Input untuk `fn`, misalnya daftar pertanyaan.
        repeats: Berapa kali seluruh input diulang.
        workers: Jumlah thread yang memanggil `fn` bersamaan; 1 berarti
            berurutan.
        label: Nama di ringkasan; bawaannya nama fungsi.
    """
    items = list(inputs)
    tasks = [item for _ in range(repeats) for item in items]

    def timed(item: Any) -> float:
        start = time.perf_counter()
        fn(item)
        return time.perf_counter() - start

    wall_start = time.perf_counter()
    if workers <= 1:
        times = [timed(item) for item in tasks]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            times = list(pool.map(timed, tasks))
    wall = time.perf_counter() - wall_start
    name = label or getattr(fn, "__name__", "fn")
    return summarize_times(times, label=name, wall_seconds=wall)


def save_times_csv(series: dict[str, list[float]], path: str | Path) -> Path:
    """Simpan beberapa deret durasi ke satu CSV, satu kolom per deret.

    Panjang deret boleh berbeda; sel yang tidak terisi dibiarkan kosong.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(series.keys())
        writer.writerows(zip_longest(*series.values(), fillvalue=""))
    return path
