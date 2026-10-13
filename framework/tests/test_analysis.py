import os

import numpy as np
import pytest

# Backend Agg menggambar ke memori saja, jadi test tidak membuka jendela.
os.environ["MPLBACKEND"] = "Agg"
pytest.importorskip("matplotlib").use("Agg")
pytest.importorskip("pandas")
pytest.importorskip("scipy")

from zul.utilities.analysis import (  # noqa: E402
    ChartGenerator,
    batch_create_charts,
    create_chart_from_csv,
)
from zul.utilities.script_helper.save_file import (  # noqa: E402
    save_latency_to_csv,
    save_text_to_md,
)

TWO = {
    "Milvus": [12.1, 11.8, 12.4, 12.0, 11.9],
    "Redis": [9.7, 10.2, 9.9, 10.1, 9.8],
}
THREE = {
    "A": [1.0, 2.0, 3.0, 4.0],
    "B": [2.0, 3.0, 4.0, 5.0],
    "C": [6.0, 7.0, 8.0, 9.5],
}

TWO_SAMPLE_TESTS = {
    "t_test": ("statistic", 15.15544456622767, 3.5573362074326657e-07),
    "mann_whitney": ("statistic", 25.0, 0.007936507936507936),
    "kolmogorov_smirnov": ("statistic", 1.0, 0.007936507936507936),
}
MULTI_SAMPLE_TESTS = {
    "anova": ("f_statistic", 15.921348314606748, 0.0011068186132174548),
    "kruskal_wallis": ("h_statistic", 7.939045936395763, 0.018882438510726615),
}


@pytest.fixture
def chart():
    """ChartGenerator yang figure-nya selalu ditutup sesudah test."""
    generator = ChartGenerator({"figsize": [4, 3]})
    yield generator
    generator.clear()


def assert_tests(results, expected):
    assert set(results) == set(expected)
    for name, (statistic_key, statistic, p_value) in expected.items():
        result = results[name]
        assert set(result) == {statistic_key, "p_value", "significant"}
        assert result[statistic_key] == pytest.approx(statistic)
        assert result["p_value"] == pytest.approx(p_value)
        assert result["significant"] == (p_value < 0.05)


# --------------------------------------------------------------------------
# Tipe Chart
# --------------------------------------------------------------------------


def test_bar_chart_summarises_each_dataset_and_runs_two_sample_tests(chart):
    stats = chart.create_comparison_chart({"chart_type": "bar", "data": TWO})

    assert list(stats) == ["Milvus", "Redis", "statistical_tests"]
    assert set(stats["Milvus"]) == {"mean", "median", "std", "min", "max"}
    assert stats["Milvus"]["mean"] == pytest.approx(np.mean(TWO["Milvus"]))
    assert stats["Redis"]["std"] == pytest.approx(np.std(TWO["Redis"]))
    assert stats["Redis"]["min"] == pytest.approx(9.7)
    assert_tests(stats["statistical_tests"], TWO_SAMPLE_TESTS)
    assert chart.current_fig is not None


def test_three_datasets_use_anova_and_kruskal_wallis(chart):
    stats = chart.create_comparison_chart({"chart_type": "box", "data": THREE})

    assert set(stats["C"]) == {
        "mean",
        "median",
        "std",
        "q25",
        "q75",
        "iqr",
        "min",
        "max",
    }
    assert stats["C"]["iqr"] == pytest.approx(1.625)
    assert_tests(stats["statistical_tests"], MULTI_SAMPLE_TESTS)


def test_line_chart_reports_the_trend_of_each_dataset(chart):
    stats = chart.create_comparison_chart(
        {"chart_type": "line", "data": THREE, "labels": ["q1", "q2", "q3", "q4"]}
    )

    assert set(stats["C"]) == {"mean", "median", "std", "trend"}
    assert stats["C"]["trend"] == pytest.approx(1.15)
    assert_tests(stats["statistical_tests"], MULTI_SAMPLE_TESTS)


@pytest.mark.parametrize("overlay", [True, False])
def test_histogram_reports_skewness_and_kurtosis(chart, overlay):
    stats = chart.create_comparison_chart(
        {
            "chart_type": "histogram",
            "data": TWO,
            "additional_options": {"bins": 5, "overlay": overlay},
        }
    )

    assert set(stats["Milvus"]) == {"mean", "median", "std", "skewness", "kurtosis"}
    assert stats["Milvus"]["skewness"] == pytest.approx(0.6927284074925594)
    assert stats["Redis"]["kurtosis"] == pytest.approx(-1.4908058409951348)
    assert_tests(stats["statistical_tests"], TWO_SAMPLE_TESTS)


def test_dashboard_adds_performance_comparisons(chart):
    stats = chart.create_comparison_chart(
        {"chart_type": "dashboard", "data": TWO, "metric_name": "Latency"}
    )

    assert list(stats) == [
        "Milvus",
        "Redis",
        "statistical_tests",
        "performance_comparisons",
    ]
    assert stats["Milvus"]["count"] == 5
    assert stats["Milvus"]["q25"] == pytest.approx(11.9)
    assert_tests(stats["statistical_tests"], TWO_SAMPLE_TESTS)
    comparison = stats["performance_comparisons"]["Milvus_vs_Redis"]
    assert comparison["baseline_mean"] == pytest.approx(12.04)
    assert comparison["comparison_mean"] == pytest.approx(9.94)
    assert comparison["improvement_percentage"] == pytest.approx(17.441860465116264)
    assert comparison["is_better"]


def test_dashboard_with_four_datasets_uses_the_taller_grid(chart):
    data = {**THREE, "D": [3.0, 3.5, 4.0, 4.5]}

    stats = chart.create_comparison_chart({"chart_type": "dashboard", "data": data})

    assert set(stats["statistical_tests"]) == {"anova", "kruskal_wallis"}
    assert list(stats["performance_comparisons"]) == ["A_vs_B", "A_vs_C", "A_vs_D"]


def test_unknown_chart_type_raises_value_error(chart):
    with pytest.raises(ValueError, match="Unsupported chart type: pie"):
        chart.create_comparison_chart({"chart_type": "pie", "data": TWO})


# --------------------------------------------------------------------------
# Menyimpan Dan Menutup Chart
# --------------------------------------------------------------------------


def test_save_writes_a_png_file(chart, tmp_path):
    chart.create_comparison_chart({"chart_type": "dashboard", "data": TWO})
    target = tmp_path / "dashboard.png"

    chart.save(str(target), dpi=50)

    assert target.read_bytes().startswith(b"\x89PNG")


def test_clear_forgets_the_figure_and_save_then_does_nothing(chart, tmp_path):
    chart.create_comparison_chart({"chart_type": "bar", "data": TWO})

    chart.clear()
    chart.save(str(tmp_path / "kosong.png"))

    assert chart.current_fig is None
    assert chart.current_ax is None
    assert not (tmp_path / "kosong.png").exists()


# --------------------------------------------------------------------------
# Chart Dari CSV Dan Batch
# --------------------------------------------------------------------------


def test_create_chart_from_csv_reads_the_listed_columns(chart, tmp_path):
    csv_file = tmp_path / "hasil.csv"
    csv_file.write_text(
        "query,milvus_ms,redis_ms\n"
        "q1,12.1,9.7\nq2,11.8,10.2\nq3,12.4,9.9\nq4,12.0,10.1\nq5,11.9,9.8\n",
        encoding="utf-8",
    )

    stats = create_chart_from_csv(
        chart,
        str(csv_file),
        {
            "chart_type": "bar",
            "data_columns": ["milvus_ms", "redis_ms", "tidak_ada"],
            "label_column": "query",
        },
    )

    assert list(stats) == ["milvus_ms", "redis_ms", "statistical_tests"]
    assert stats["milvus_ms"]["mean"] == pytest.approx(12.04)
    assert_tests(stats["statistical_tests"], TWO_SAMPLE_TESTS)


def test_batch_create_charts_saves_each_chart_and_clears_it(tmp_path, capsys):
    chart = ChartGenerator({"figsize": [4, 3]})
    configs = [
        {
            "chart_type": "bar",
            "data": TWO,
            "title": "Latency",
            "save_filename": str(tmp_path / "bar.png"),
            "show": False,
        },
        {"chart_type": "line", "data": THREE, "show": False},
    ]

    results = batch_create_charts(chart, configs)

    assert len(results) == 2
    assert "t_test" in results[0]["statistical_tests"]
    assert "anova" in results[1]["statistical_tests"]
    assert (tmp_path / "bar.png").read_bytes().startswith(b"\x89PNG")
    assert chart.current_fig is None
    assert "Creating chart 1/2: Latency" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Menyimpan Ke Folder data
# --------------------------------------------------------------------------


def test_save_text_to_md_writes_into_the_data_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    save_text_to_md("# Hasil OCR\n\nteks é", "hasil_ocr")

    saved = tmp_path / "data" / "hasil_ocr.md"
    assert saved.read_text(encoding="utf-8") == "# Hasil OCR\n\nteks é"


def test_save_latency_to_csv_writes_one_column_per_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    save_latency_to_csv(
        {"short": [0.11, 0.12], "long": [0.31, 0.29]}, file_name="latency_milvus"
    )

    saved = tmp_path / "data" / "latency_milvus.csv"
    assert saved.read_text(encoding="utf-8").splitlines() == [
        "short,long",
        "0.11,0.31",
        "0.12,0.29",
    ]


def test_save_latency_to_csv_rejects_columns_of_different_length(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        save_latency_to_csv({"short": [0.11, 0.12], "long": [0.31]})

    assert not (tmp_path / "data" / "query_latency_recursive_results.csv").exists()
