"""
Adapter lap: memasangkan dua kelompok dengan biaya total terkecil.

Gunanya:
    Satu-satunya file Zul yang mengimpor lap (BSD-2-Clause). Tracker
    memakainya untuk memasangkan track dengan deteksi: matriks biaya masuk,
    pasangan baris dan kolom keluar sebagai list Python biasa. Butuh extra
    tracking: `pip install "zul[tracking]"`.

Cara pakai:
    import numpy as np
    from zul.adapters import lap as lap_adapter

    cost = np.array([[0.1, 0.9], [0.8, 0.2]])
    matches, free_rows, free_cols = lap_adapter.assign(cost, threshold=0.5)
    matches        # [(0, 0), (1, 1)]
"""

from __future__ import annotations

import lap
import numpy as np


def assign(
    cost: np.ndarray, threshold: float
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Pasangan baris-kolom berbiaya total terkecil, tiap biaya maksimal `threshold`.

    Mengembalikan pasangan `(baris, kolom)`, baris yang tidak berpasangan,
    dan kolom yang tidak berpasangan.
    """
    rows, cols = cost.shape[:2] if cost.ndim == 2 else (len(cost), 0)
    if cost.size == 0:
        return [], list(range(rows)), list(range(cols))
    _, row_to_col, col_to_row = lap.lapjv(
        np.asarray(cost, dtype=np.float64), extend_cost=True, cost_limit=threshold
    )
    matches = [(row, int(col)) for row, col in enumerate(row_to_col) if col >= 0]
    free_rows = [row for row, col in enumerate(row_to_col) if col < 0]
    free_cols = [col for col, row in enumerate(col_to_row) if row < 0]
    return matches, free_rows, free_cols
