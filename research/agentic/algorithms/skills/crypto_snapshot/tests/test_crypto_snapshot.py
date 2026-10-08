"""Tests without network access or a model for scripts/crypto_snapshot.py and the get_crypto_snapshot tool.

    python -m pytest research/agentic/algorithms/skills/crypto_snapshot/tests -q -p no:cacheprovider
"""

import logging
import sys
from pathlib import Path

import pytest
import yaml

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import crypto_snapshot as cs  # noqa: E402
from skills.crypto_snapshot import crypto_snapshot_skill as skill  # noqa: E402

START_MS = 1_790_000_000_000
HOUR_MS = 3_600_000


def klines(n=200):
    """Rising market: close 100, 101, ...; high/low one above/below; volume 10 per candle."""
    rows = []
    for i in range(n):
        close = 100.0 + i
        rows.append([START_MS + i * HOUR_MS, str(close - 0.5), str(close + 1), str(close - 1), str(close),
                     "10", START_MS + (i + 1) * HOUR_MS - 1, str(close * 10), 50, "5", "500", "0"])
    return rows


TICKER = {"lastPrice": "299.00", "priceChangePercent": "1.50", "volume": "240.5", "quoteVolume": "71910.25"}


def fake_api(failing=()):
    def fetch_json(path, params):
        if params["symbol"] in failing:
            raise cs.SnapshotError('HTTP 400 dari https://api.binance.com: {"code":-1121,"msg":"Invalid symbol."}')
        return klines() if path.endswith("/klines") else dict(TICKER)
    return fetch_json


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(cs, "fetch_json", fake_api(failing={"NOPEUSDT"}))
    monkeypatch.setattr(skill._cs, "fetch_json", fake_api(failing={"NOPEUSDT"}))


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def test_sma_slides_over_the_window():
    assert cs.sma([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]


def test_ema_is_seeded_with_the_sma_and_follows_new_values():
    assert cs.ema([1, 2, 3], 3) == 2.0
    assert cs.ema([1, 2, 3, 4], 3) == 3.0          # (4 - 2) * 2/(3+1) + 2
    assert cs.ema([7.0] * 50, 12) == pytest.approx(7.0)


def test_stochastic_of_a_steady_rise_and_of_a_flat_market():
    rising = [cs.Candle(None, 0, c + 1, c - 1, c, 1, 1) for c in range(100, 140)]
    flat = [cs.Candle(None, 0, 5, 5, 5, 1, 1) for _ in range(40)]

    assert cs.stochastic(rising, 5, 3, 3) == pytest.approx((500 / 6, 500 / 6))
    assert cs.stochastic(flat, 5, 3, 3) == (50.0, 50.0)


def test_too_few_values_is_a_readable_error():
    with pytest.raises(cs.SnapshotError, match="Data kurang"):
        cs.ema([1, 2], 12)


# ---------------------------------------------------------------------------
# Inputs: token names, pairs, URLs, files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text, quote, symbol, url", [
    ("BTC", "USDT", "BTCUSDT", "https://www.binance.com/en/trade/BTC_USDT"),
    ("eth", "USDT", "ETHUSDT", "https://www.binance.com/en/trade/ETH_USDT"),
    ("SOL", "USDC", "SOLUSDC", "https://www.binance.com/en/trade/SOL_USDC"),
    ("eth/usdc", "USDT", "ETHUSDC", "https://www.binance.com/en/trade/ETH_USDC"),
    ("btc-usdt", "USDT", "BTCUSDT", "https://www.binance.com/en/trade/BTC_USDT"),
    ("BNB_FDUSD", "USDT", "BNBFDUSD", "https://www.binance.com/en/trade/BNB_FDUSD"),
    ("BTCUSDT", "USDT", "BTCUSDT", "https://www.binance.com/en/trade/BTC_USDT"),
    ("ETHBTC", "USDT", "ETHBTC", "https://www.binance.com/en/trade/ETH_BTC"),
    ("WBTC", "USDT", "WBTCUSDT", "https://www.binance.com/en/trade/WBTC_USDT"),
    ("BETH", "USDT", "BETHUSDT", "https://www.binance.com/en/trade/BETH_USDT"),
])
def test_token_names_and_pairs_need_no_url(text, quote, symbol, url):
    target = cs.parse_input(text, "1h", quote)

    assert (target.symbol, target.source_url, target.interval) == (symbol, url, "1h")


@pytest.mark.parametrize("url, symbol, interval", [
    ("https://www.binance.com/en/trade/BTC_USDT", "BTCUSDT", "1h"),
    ("https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=4h", "ETHUSDT", "4h"),
    ("https://www.tradingview.com/symbols/SOLUSDT/", "SOLUSDT", "1h"),
    ("https://www.tradingview.com/chart/?symbol=BINANCE%3ABNBUSDT", "BNBUSDT", "1h"),
])
def test_binance_and_tradingview_urls(url, symbol, interval):
    target = cs.parse_input(url, "1h")

    assert (target.symbol, target.interval, target.source_url) == (symbol, interval, url)


@pytest.mark.parametrize("text", ["$$$", "B", "https://www.coingecko.com/", "BTC/USDT/EUR"])
def test_unknown_inputs_are_refused_with_a_reason(text):
    with pytest.raises(cs.SnapshotError):
        cs.parse_input(text, "1h")


def test_files_tokens_and_urls_mix_and_duplicates_go(tmp_path):
    listing = tmp_path / "tokens.txt"
    listing.write_text("# pagi\nBTC\n\nhttps://www.tradingview.com/symbols/SOLUSDT/\nBTC\n", encoding="utf-8")

    items = cs.read_inputs(["ETH", str(listing), "https://www.binance.com/en/trade/BNB_USDT"])

    assert items == ["ETH", "BTC", "https://www.tradingview.com/symbols/SOLUSDT/",
                     "https://www.binance.com/en/trade/BNB_USDT"]


def test_a_missing_file_is_not_taken_for_a_token(tmp_path):
    with pytest.raises(cs.SnapshotError, match="Bukan URL, nama token, atau file"):
        cs.read_inputs([str(tmp_path / "tidak-ada.txt")])


def test_monthly_interval_does_not_collide_with_minutes_in_file_names():
    assert cs.snapshot_name(cs.Target("x", "BTCUSDT", "1M")) == "btcusdt-1mo-snapshot"
    assert cs.snapshot_name(cs.Target("x", "BTCUSDT", "1m")) == "btcusdt-1m-snapshot"


# ---------------------------------------------------------------------------
# Snapshot, file and summary, with a fake API
# ---------------------------------------------------------------------------

def test_snapshot_file_has_a_valid_header_and_every_section(offline):
    document = cs.render(cs.build_snapshot(cs.parse_input("BTC", "1h")))
    _, header, body = document.split("---", 2)

    assert yaml.safe_load(header)["name"] == "btcusdt-1h-snapshot"
    for section in ("## Harga", "## EMA (1h)", "## Stochastic (5, 3, 3) (1h)", "## Volume"):
        assert section in body
    assert "- Harga saat ini: 299.00" in body
    assert "- Perubahan 24 jam: +1.50%" in body
    assert "(bullish)" in body and "overbought" in body
    assert "- Rasio terhadap rata-rata: 1.00x" in body


def test_summary_line_reads_like_a_report(offline):
    line = cs.summary_line(cs.build_snapshot(cs.parse_input("ETH", "4h")))

    assert line == ("ETHUSDT 4h: harga 299.00 (+1.50% 24 jam) | EMA 12/21 bullish | "
                    "Stoch %K 83.33 %D 83.33 overbought (%K >= 80) | volume 1.00x rata-rata")


def test_cli_writes_one_file_per_token_and_logs_a_summary(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="crypto_snapshot")

    code = cs.main(["BTC", "ETH/USDT", "-o", str(tmp_path)])

    assert code == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["btcusdt-1h-snapshot.txt", "ethusdt-1h-snapshot.txt"]
    assert "BTCUSDT 1h: harga 299.00" in caplog.text
    assert "Selesai: 2 sukses, 0 gagal" in caplog.text


def test_cli_keeps_going_after_a_failure_and_exits_1(offline, tmp_path, caplog):
    code = cs.main(["NOPE", "BTC", "-o", str(tmp_path)])

    assert code == 1
    assert (tmp_path / "btcusdt-1h-snapshot.txt").is_file()
    assert "GAGAL NOPE" in caplog.text and "Invalid symbol" in caplog.text


def test_cli_without_any_input_exits_2(tmp_path):
    empty = tmp_path / "kosong.txt"
    empty.write_text("# belum ada token\n", encoding="utf-8")

    assert cs.main([str(empty), "-o", str(tmp_path)]) == 2


# ---------------------------------------------------------------------------
# Skill: plain function and tool, no model
# ---------------------------------------------------------------------------

def test_get_snapshot_returns_plain_values(offline):
    record = skill.get_snapshot("SOL", "4h")

    assert record["symbol"] == "SOLUSDT" and record["interval"] == "4h"
    assert record["price"] == 299.0 and record["change_24h_percent"] == 1.5
    assert record["ema_fast"] > record["ema_slow"]
    assert record["stoch_k"] == 83.33 and record["volume_ratio"] == 1.0
    assert record["document"].startswith("---\nname: solusdt-4h-snapshot\n")


def test_tool_text_reports_failures_as_a_sentence(offline):
    reply = skill.snapshot_text("NOPE")

    assert reply.startswith("No snapshot for 'NOPE'") and "Invalid symbol" in reply


@pytest.mark.skipif(skill.get_crypto_snapshot is None, reason="langchain-core not installed")
def test_langchain_tool_returns_the_snapshot_document(offline):
    reply = skill.get_crypto_snapshot.invoke({"token": "BTC", "interval": "1d"})

    assert reply.startswith("---\nname: btcusdt-1d-snapshot\n")
