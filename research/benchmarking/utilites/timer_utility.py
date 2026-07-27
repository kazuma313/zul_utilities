"""
Timer Decorator Service
=======================
Menyediakan decorator timer yang bisa digunakan sebagai:
  - @timer                    → print durasi sekali jalan
  - @TimerDecorator           → class-based, menyimpan histori & statistik
  - @timer_stats(logger=...) → functional + configurable logging
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, field
from functools import wraps
from time import perf_counter
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Simple function decorator  (paling ringan, cocok 90% kasus)
# ---------------------------------------------------------------------------

def timer(func: Callable) -> Callable:
    """Decorator sederhana: print durasi eksekusi ke stdout."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - t0
        print(f"[timer] {func.__qualname__!r} → {elapsed:.4f}s")
        return result
    return wrapper


# ---------------------------------------------------------------------------
# 2. Configurable decorator factory (support custom logger & callback)
# ---------------------------------------------------------------------------

def timer_stats(
    log_fn: Callable[[str], None] = print,
    *,
    unit: str = "s",
) -> Callable:
    """
    Decorator factory dengan logger & satuan waktu yang bisa dikonfigurasi.

    Contoh pemakaian:
        @timer_stats(log_fn=logger.info, unit="ms")
        def heavy_task(): ...
    """
    scale = {"s": 1, "ms": 1_000, "us": 1_000_000}.get(unit, 1)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = perf_counter()
            result = func(*args, **kwargs)
            elapsed = (perf_counter() - t0) * scale
            log_fn(f"[timer] {func.__qualname__!r} → {elapsed:.4f}{unit}")
            return result
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# 3. Class-based decorator  (menyimpan histori & statistik)
# ---------------------------------------------------------------------------

@dataclass
class TimingStats:
    """Value object untuk ringkasan statistik waktu eksekusi."""
    call_count: int
    total: float
    average: float
    minimum: float
    maximum: float
    median: float
    p95: float

    def __str__(self) -> str:
        return (
            f"calls={self.call_count} | "
            f"avg={self.average:.4f}s | "
            f"min={self.minimum:.4f}s | "
            f"max={self.maximum:.4f}s | "
            f"p95={self.p95:.4f}s"
        )


class TimerDecorator:
    """
    Class-based decorator yang merekam histori waktu eksekusi.

    Contoh pemakaian:
        @TimerDecorator
        def my_func(): ...

        my_func()
        print(my_func.stats())   # ringkasan statistik
        my_func.reset()          # hapus histori
    """

    _times: list[float] = field(default_factory=list)

    def __init__(self, func: Callable) -> None:
        self._func = func
        self._times: list[float] = []
        # Salin metadata fungsi asli agar __name__, __doc__, dsb. tetap benar
        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        t0 = perf_counter()
        result = self._func(*args, **kwargs)
        elapsed = perf_counter() - t0

        self._times.append(elapsed)
        print(f"[TimerDecorator] {self._func.__qualname__!r} → {elapsed:.4f}s")
        return result

    # ---- helpers ----

    @property
    def last(self) -> float | None:
        """Waktu eksekusi terakhir, atau None jika belum pernah dipanggil."""
        return self._times[-1] if self._times else None

    def stats(self) -> TimingStats | None:
        """Kembalikan ringkasan statistik; None jika belum ada data."""
        if not self._times:
            return None
        sorted_times = sorted(self._times)
        p95_idx = max(0, int(len(sorted_times) * 0.95) - 1)
        return TimingStats(
            call_count=len(self._times),
            total=sum(self._times),
            average=statistics.mean(self._times),
            minimum=sorted_times[0],
            maximum=sorted_times[-1],
            median=statistics.median(self._times),
            p95=sorted_times[p95_idx],
        )

    def reset(self) -> None:
        """Hapus semua data histori."""
        self._times.clear()


# ---------------------------------------------------------------------------
# Demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    # 1. Simple decorator
    @timer
    def add(a, b):
        time.sleep(0.05)
        return a + b

    add(1, 2)

    # 2. Decorator factory dengan unit ms
    @timer_stats(unit="ms")
    def multiply(a, b):
        time.sleep(0.03)
        return a * b

    multiply(3, 4)

    # 3. Class-based dengan statistik
    @TimerDecorator
    def slow_task(n: int) -> int:
        time.sleep(n * 0.02)
        return n * 2

    for i in range(1, 6):
        slow_task(i)

    print("\n=== Stats ===")
    print(slow_task.stats())
    print(f"Last call  : {slow_task.last:.4f}s")