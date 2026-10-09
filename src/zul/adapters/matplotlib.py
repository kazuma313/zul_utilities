"""
Adapter Matplotlib: style, figure baru, box plot, serta menampilkan dan menyimpan.

Gunanya:
    Satu-satunya file Zul yang mengimpor matplotlib. Bagian pyplot yang
    memakai state global ada di sini: style, figure baru, jendela tampilan,
    dan menutup figure. Butuh extra analysis: `pip install "zul[analysis]"`.

    Figure dan Axes yang dikembalikan adalah objek matplotlib asli. Modul
    chart menggambar dengan memanggil method-nya langsung, misalnya bar,
    plot, hist, dan text. Method Axes tidak dibungkus satu per satu karena
    jumlahnya ratusan.

Cara pakai:
    from zul.adapters import matplotlib as matplotlib_adapter

    figure, axes = matplotlib_adapter.new_axes([12, 8])
    axes.bar([0, 1], [3.0, 4.0])
    matplotlib_adapter.save(figure, "chart.png")
    matplotlib_adapter.close(figure)

Backend tidak diatur di sini. Di server atau test tanpa layar, set
MPLBACKEND=Agg sebelum adapter ini diimpor supaya tidak ada jendela.
"""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

Size = Sequence[float]

# --------------------------------------------------------------------------
# Style Dan Figure Baru
# --------------------------------------------------------------------------


def use_style(name: str) -> None:
    """Pakai style matplotlib bernama, misalnya "default" atau "ggplot".

    Style berlaku global untuk semua figure yang dibuat sesudahnya.
    """
    plt.style.use(name)


def new_figure(figsize: Size) -> Figure:
    """Figure kosong berukuran `figsize` inci; axes-nya ditambah sendiri."""
    return plt.figure(figsize=figsize)


def new_axes(figsize: Size) -> tuple[Figure, Axes]:
    """Figure baru dengan satu Axes, berukuran `figsize` inci."""
    return plt.subplots(figsize=figsize)


def new_stacked_axes(count: int, figsize: Size) -> tuple[Figure, list[Axes]]:
    """Figure baru dengan `count` Axes yang disusun dari atas ke bawah."""
    figure, grid = plt.subplots(count, 1, figsize=figsize, squeeze=False)
    return figure, list(grid[:, 0])


def rotate_x_labels(axes: Axes, degrees: float) -> None:
    """Putar label sumbu x yang sudah ada sebesar `degrees` derajat."""
    plt.setp(axes.get_xticklabels(), rotation=degrees)


# --------------------------------------------------------------------------
# Box Plot
# --------------------------------------------------------------------------
#
# Matplotlib 3.9 mengubah nama parameter labels jadi tick_labels.
# Nama baru dicoba dulu, kemudian nama lama dipakai jika versi
# matplotlib yang ter-install belum mengenal nama baru itu.
#


def colored_boxplot(
    axes: Axes,
    values: Sequence[Sequence[float]],
    labels: Sequence[str],
    colors: Sequence[str],
    alpha: float,
) -> None:
    """Box plot satu kotak per dataset, kotak ke-i diwarnai `colors[i]`.

    Jika warnanya lebih sedikit dari jumlah dataset, kotak sisanya memakai
    warna bawaan matplotlib.
    """
    try:
        artists = axes.boxplot(values, tick_labels=labels, patch_artist=True)
    except TypeError:
        artists = axes.boxplot(values, labels=labels, patch_artist=True)

    for box, color in zip(artists["boxes"], colors, strict=False):
        box.set_facecolor(color)
        box.set_alpha(alpha)


# --------------------------------------------------------------------------
# Menampilkan Dan Menyimpan
# --------------------------------------------------------------------------


def show() -> None:
    """Tampilkan semua figure yang masih terbuka di jendela backend."""
    plt.show()


def save(figure: Figure, path: str, dpi: int = 300, bbox_inches: str = "tight") -> None:
    """Simpan figure ke file; formatnya mengikuti ekstensi, misalnya .png."""
    figure.savefig(path, dpi=dpi, bbox_inches=bbox_inches)


def close(figure: Figure) -> None:
    """Tutup figure supaya memorinya dilepas oleh pyplot."""
    plt.close(figure)
