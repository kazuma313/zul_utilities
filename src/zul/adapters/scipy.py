"""
Adapter SciPy: uji statistik dan bentuk distribusi untuk membandingkan dataset.

Gunanya:
    Satu-satunya file Zul yang mengimpor scipy. Setiap uji menerima list
    angka dan mengembalikan tuple (statistik, p-value) berupa float Python,
    jadi modul lain tidak perlu tahu bentuk objek hasil scipy.stats.
    Butuh extra analysis: `pip install "zul[analysis]"`.

Cara pakai:
    from zul.adapters import scipy as scipy_adapter

    statistic, p_value = scipy_adapter.t_test([12.1, 11.8, 12.4], [9.7, 10.2, 9.9])
    statistic, p_value = scipy_adapter.anova([1, 2, 3], [2, 3, 4], [6, 7, 9])
    print(scipy_adapter.skewness([1.0, 2.0, 5.0]))

Semua uji dua arah (two-sided). Nilai yang tidak bisa dihitung, misalnya
t-test pada dua dataset yang semua angkanya sama, menjadi float nan.
"""

from __future__ import annotations

from collections.abc import Sequence

from scipy import stats

Values = Sequence[float]

# --------------------------------------------------------------------------
# Uji Dua Dataset
# --------------------------------------------------------------------------


def t_test(first: Values, second: Values) -> tuple[float, float]:
    """t-test dua sampel independen, varians keduanya dianggap sama."""
    result = stats.ttest_ind(first, second)
    return float(result.statistic), float(result.pvalue)


def mann_whitney(first: Values, second: Values) -> tuple[float, float]:
    """Uji Mann-Whitney U; tidak menganggap datanya berdistribusi normal."""
    result = stats.mannwhitneyu(first, second, alternative="two-sided")
    return float(result.statistic), float(result.pvalue)


def kolmogorov_smirnov(first: Values, second: Values) -> tuple[float, float]:
    """Uji Kolmogorov-Smirnov: apakah dua dataset berasal dari distribusi sama."""
    result = stats.ks_2samp(first, second)
    return float(result.statistic), float(result.pvalue)


# --------------------------------------------------------------------------
# Uji Tiga Dataset Atau Lebih
# --------------------------------------------------------------------------


def anova(*groups: Values) -> tuple[float, float]:
    """One-way ANOVA; statistiknya adalah nilai F."""
    result = stats.f_oneway(*groups)
    return float(result.statistic), float(result.pvalue)


def kruskal_wallis(*groups: Values) -> tuple[float, float]:
    """Uji Kruskal-Wallis; statistiknya adalah nilai H."""
    result = stats.kruskal(*groups)
    return float(result.statistic), float(result.pvalue)


# --------------------------------------------------------------------------
# Bentuk Distribusi
# --------------------------------------------------------------------------


def skewness(values: Values) -> float:
    """Kemiringan distribusi; positif berarti ekor kanannya lebih panjang."""
    return float(stats.skew(values))


def kurtosis(values: Values) -> float:
    """Kurtosis Fisher: distribusi normal bernilai 0."""
    return float(stats.kurtosis(values))
