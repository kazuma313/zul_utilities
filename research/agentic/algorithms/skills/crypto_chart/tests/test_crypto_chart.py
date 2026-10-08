"""Tests without network access or a model for scripts/crypto_chart.py and the get_crypto_chart tool.

    python -m pytest research/agentic/algorithms/skills/crypto_chart/tests -q -p no:cacheprovider
"""

import importlib.util
import logging
import math
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import crypto_chart as cc  # noqa: E402
from skills.crypto_chart import crypto_chart_skill as skill  # noqa: E402

# The snapshot skill's script, loaded by path: the picture must show the same numbers as the snapshot file.
_spec = importlib.util.spec_from_file_location("snapshot_for_chart_tests",
                                               SKILL.parent / "crypto_snapshot" / "scripts" / "crypto_snapshot.py")
snapshot = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = snapshot      # dataclasses look the module up while the class is built
_spec.loader.exec_module(snapshot)

START_MS = 1_790_000_000_000
HOUR_MS = 3_600_000


def klines(n=200):
    """A wavy market: closes follow a sine with a slow rise; volume cycles 10..14."""
    rows, previous = [], 100.0
    for i in range(n):
        close = 100 + 10 * math.sin(i / 7) + i * 0.1
        high, low = max(previous, close) + 1, min(previous, close) - 1
        rows.append([START_MS + i * HOUR_MS, str(previous), str(high), str(low), str(close), str(10 + i % 5),
                     START_MS + (i + 1) * HOUR_MS - 1, str(close * 10), 50, "5", "500", "0"])
        previous = close
    return rows


TICKER = {"lastPrice": "118.20", "priceChangePercent": "-0.75", "volume": "300", "quoteVolume": "35460"}


def fake_api(path, params):
    if params["symbol"] == "NOPEUSDT":
        raise cc.ChartError('HTTP 400 dari https://api.binance.com: {"code":-1121,"msg":"Invalid symbol."}')
    return klines() if path.endswith("/klines") else dict(TICKER)


def snapshot_fake_api(path, params):
    return klines() if path.endswith("/klines") else dict(TICKER)


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(cc, "fetch_json", fake_api)
    monkeypatch.setattr(skill._cc, "fetch_json", fake_api)


def candles():
    return [cc.Candle(cc.datetime.fromtimestamp(r[0] / 1000, tz=cc.timezone.utc),
                      float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in klines()]


# ---------------------------------------------------------------------------
# Indicator series
# ---------------------------------------------------------------------------

def test_series_start_with_none_until_the_indicator_exists():
    assert cc.sma_series([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]
    assert cc.ema_series([1, 2, 3, 4], 3) == [None, None, 2.0, 3.0]
    k, d = cc.stochastic_series(candles(), 5, 3, 3)
    assert k[:6] == [None] * 6 and k[6] is not None      # 5 candles, then 3 values to smooth
    assert d[:8] == [None] * 8 and d[8] is not None


def test_last_values_match_the_snapshot_skill():
    data = candles()
    series = cc.build_series(data)
    closes = [c.close for c in data]
    snap_k, snap_d = snapshot.stochastic(
        [snapshot.Candle(None, c.open, c.high, c.low, c.close, c.volume, 0) for c in data], 5, 3, 3)
    pairs = [
        (series.ema_fast[-1], snapshot.ema(closes, 12)),
        (series.ema_slow[-1], snapshot.ema(closes, 21)),
        (series.stoch_k[-1], snap_k),
        (series.stoch_d[-1], snap_d),
        (series.volume_avg[-1], snapshot.sma([c.volume for c in data], 20)[-1]),
    ]

    # The snapshot sums its windows by rolling, the chart sums each window: the last digits may differ,
    # the numbers written in the picture and in the snapshot file may not.
    for chart_value, snapshot_value in pairs:
        assert chart_value == pytest.approx(snapshot_value, rel=1e-12)
        assert f"{chart_value:.2f}" == f"{snapshot_value:.2f}"


@pytest.mark.parametrize("text, chosen", [
    ("all", ("ema", "volume", "stoch")),
    ("none", ()),
    ("", ()),
    ("stoch,ema", ("ema", "stoch")),            # panels keep their order
    ("Volume", ("volume",)),
    (["ema", "volume"], ("ema", "volume")),
])
def test_indicator_choices(text, chosen):
    assert cc.parse_indicators(text) == chosen


def test_unknown_indicator_is_a_readable_error():
    with pytest.raises(cc.ChartError, match="Indikator tidak dikenal: rsi"):
        cc.parse_indicators("ema,rsi")


@pytest.mark.parametrize("text, symbol", [("BTC", "BTCUSDT"), ("eth/usdc", "ETHUSDC"), ("ETHBTC", "ETHBTC"),
                                          ("https://www.tradingview.com/symbols/SOLUSDT/", "SOLUSDT")])
def test_inputs_are_read_like_the_snapshot_skill(text, symbol):
    assert cc.parse_input(text, "1h").symbol == symbol == snapshot.parse_input(text, "1h").symbol


# ---------------------------------------------------------------------------
# The picture: panels follow the indicators
# ---------------------------------------------------------------------------

def figure(indicators, theme="light"):
    data = candles()
    target = cc.Target("https://www.binance.com/en/trade/BTC_USDT", "BTCUSDT", "1h")
    return cc.build_figure(target, cc.build_series(data), cc.Ticker24h(118.2, -0.75),
                           cc.datetime(2026, 10, 8, 6, 0, tzinfo=cc.timezone.utc), indicators, 80, theme)


def legend_texts(fig):
    return [t.get_text() for ax in fig.axes if ax.get_legend() for t in ax.get_legend().get_texts()]


@pytest.mark.parametrize("indicators, panels", [((), 1), (("ema",), 1), (("volume",), 2), (("stoch",), 2),
                                                (("ema", "volume", "stoch"), 3)])
def test_one_panel_for_price_plus_one_per_lower_indicator(indicators, panels):
    fig = figure(indicators)

    assert len(fig.axes) == panels


def test_drawn_indicators_carry_their_last_value_in_the_legend():
    texts = legend_texts(figure(("ema", "volume", "stoch")))

    assert any(t.startswith("EMA 12  ") for t in texts) and any(t.startswith("EMA 21  ") for t in texts)
    assert any(t.startswith("%K  ") for t in texts) and "Stochastic (5, 3, 3)" in texts


def test_candles_only_has_no_indicator_lines():
    fig = figure(())

    assert legend_texts(fig) == []
    assert len(fig.axes[0].get_lines()) == 1          # only the dashed last-price line


def test_unknown_theme_is_refused():
    with pytest.raises(cc.ChartError, match="Tema"):
        figure((), theme="neon")


# ---------------------------------------------------------------------------
# Files, CLI and skill, with a fake API
# ---------------------------------------------------------------------------

def test_png_and_svg_files_are_written(offline, tmp_path):
    target = cc.parse_input("BTC", "1h")
    png = cc.make_chart(target, tmp_path, ("ema",), 60, "dark", "png")
    svg = cc.make_chart(target, tmp_path, (), 60, "light", "svg")

    assert Path(png["path"]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert "<svg" in Path(svg["path"]).read_text(encoding="utf-8")[:500]
    assert png["stoch_k"] is None and png["ema_fast"] is not None
    assert sorted(p.name for p in tmp_path.iterdir()) == ["btcusdt-1h-chart.png", "btcusdt-1h-chart.svg"]


def test_cli_draws_each_token_and_logs_what_is_in_the_picture(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="crypto_chart")

    code = cc.main(["BTC", "ETH/USDT", "-i", "4h", "-n", "50", "-o", str(tmp_path)])

    assert code == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["btcusdt-4h-chart.png", "ethusdt-4h-chart.png"]
    assert "BTCUSDT 4h: 50 candle, harga" in caplog.text and "Stoch %K" in caplog.text


def test_cli_without_indicators_says_so(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="crypto_chart")

    assert cc.main(["SOL", "--indicators", "none", "-o", str(tmp_path)]) == 0
    assert "tanpa indikator" in caplog.text


def test_cli_keeps_going_after_a_failure_and_rejects_bad_options(offline, tmp_path, caplog):
    assert cc.main(["NOPE", "BTC", "-o", str(tmp_path)]) == 1
    assert "GAGAL NOPE" in caplog.text and (tmp_path / "btcusdt-1h-chart.png").is_file()
    assert cc.main(["BTC", "--indicators", "rsi", "-o", str(tmp_path)]) == 2


def test_draw_chart_returns_the_path_and_the_numbers(offline, tmp_path):
    result = skill.draw_chart("SOL", "4h", indicators="ema,stoch", output_dir=tmp_path)

    assert Path(result["path"]).is_file() and result["symbol"] == "SOLUSDT"
    assert result["volume_ratio"] is None and result["stoch_k"] is not None
    assert result["summary"].startswith("SOLUSDT 4h: 80 candle")


def test_tool_text_points_to_the_image_or_gives_the_reason(offline, tmp_path, monkeypatch):
    monkeypatch.setenv(skill.OUTPUT_DIR_ENV, str(tmp_path))

    assert skill.chart_text("BTC").startswith("Chart image saved: ")
    assert skill.chart_text("NOPE").startswith("No chart for 'NOPE'")


@pytest.mark.skipif(skill.get_crypto_chart is None, reason="langchain-core not installed")
def test_langchain_tool_saves_the_image(offline, tmp_path, monkeypatch):
    monkeypatch.setenv(skill.OUTPUT_DIR_ENV, str(tmp_path))

    reply = skill.get_crypto_chart.invoke({"token": "ETH", "interval": "1d", "indicators": "none"})

    assert "ethusdt-1d-chart.png" in reply and (tmp_path / "ethusdt-1d-chart.png").is_file()
