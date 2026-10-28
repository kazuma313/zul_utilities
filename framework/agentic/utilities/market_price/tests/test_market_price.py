"""Tests without network access or a model for scripts/market_price.py and the market price tools.

    python -m pytest framework/agentic/utilities/market_price/tests -q -p no:cacheprovider
"""

import io
import json
import logging
import sys
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

import pytest
import yaml

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(SKILL.parent.parent))
import market_price as mp  # noqa: E402
from utilities.market_price import market_price_skill as skill  # noqa: E402

REPO = SKILL.parent.parent.parent.parent
DAY = 86_400
UTC = timezone.utc
START = int(datetime(2025, 1, 1, tzinfo=UTC).timestamp())


def payload(symbol, closes, *, start=START, step=DAY, offset=0, price=None, updated=None,
            currency="USD", kind="INDEX", volume=1000, long_name=None, short_name=None):
    """A Yahoo chart response: one candle per close, None where the close is None."""
    stamps = [start + i * step for i in range(len(closes))]
    unfinished = [c is None for c in closes]
    quote = {
        "open": [10.0 if u else c - 1 for c, u in zip(closes, unfinished)],
        "high": [12.0 if u else c + 1 for c, u in zip(closes, unfinished)],
        "low": [9.0 if u else c - 2 for c, u in zip(closes, unfinished)],
        "close": list(closes),
        "volume": [volume] * len(closes),
    }
    meta = {
        "currency": currency,
        "instrumentType": kind,
        "gmtoffset": offset,
        "regularMarketPrice": price if price is not None else closes[-1],
        "regularMarketTime": updated if updated is not None else stamps[-1] + 8 * 3600,
        "fullExchangeName": "Test Exchange",
    }
    if long_name:
        meta["longName"] = long_name
    if short_name:
        meta["shortName"] = short_name
    return {"chart": {"result": [{"meta": meta, "timestamp": stamps, "indicators": {"quote": [quote]}}], "error": None}}


def rising(n, first=100.0):
    return [first + i for i in range(n)]


def http_error(code, body="{}"):
    return urllib.error.HTTPError("https://example.test", code, "x", {}, io.BytesIO(body.encode()))


# One fake market: gold futures 2000 + i dollars, a flat 16,000 rupiah per dollar, an index, and a stock.
MARKET = {
    "GC=F": lambda: payload("GC=F", rising(300, 2000.0), kind="FUTURE", short_name="Gold Dec 26"),
    "USDIDR=X": lambda: payload("USDIDR=X", [16000.0] * 300, currency="IDR", kind="CURRENCY", volume=0),
    "^GSPC": lambda: payload("^GSPC", rising(300, 5000.0), long_name="S&P 500", volume=2_000_000),
    "BBCA.JK": lambda: payload(
        "BBCA.JK", rising(300, 8000.0), offset=25200, currency="IDR", kind="EQUITY", volume=5_000_000
    ),
}


def fake_api(failing=(), calls=None):
    def fetch_json(path, params):
        symbol = unquote(path.rsplit("/", 1)[-1])
        if calls is not None:
            calls.append((symbol, dict(params)))
        if symbol in failing:
            raise mp.MarketPriceError("HTTP 404 dari https://query1.finance.yahoo.com: No data found, symbol may be delisted")
        return MARKET[symbol]()
    return fetch_json


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api(failing={"NOPE.JK"}))
    monkeypatch.setattr(skill._mp, "fetch_json", fake_api(failing={"NOPE.JK"}))


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------

def test_sma_last_uses_the_latest_window_and_none_when_data_is_short():
    assert mp.sma_last([1, 2, 3, 4], 2) == 3.5
    assert mp.sma_last([1, 2], 3) is None


def test_rsi_follows_wilder_smoothing():
    # Period 2: changes +1, -1 give 0.5/0.5; then +1 gives gain 0.75 and loss 0.25, so RS 3 and RSI 75.
    assert mp.rsi([1, 2, 1, 2], 2) == pytest.approx(75.0)


def test_rsi_of_a_steady_rise_a_flat_market_and_too_little_data():
    assert mp.rsi(list(range(30))) == 100.0
    assert mp.rsi([5.0] * 30) == 50.0
    assert mp.rsi([1, 2, 3], 14) is None


def test_pct_change_and_a_zero_base():
    assert mp.pct_change(110, 100) == pytest.approx(10.0)
    assert mp.pct_change(5, 0) is None


def test_close_on_or_before_picks_the_last_candle_not_after_the_date():
    zone = timezone.utc
    candles = [mp.Candle(datetime(2026, 1, d, tzinfo=zone), 1, 1, 1, float(d), 0) for d in (2, 5, 9)]

    assert mp.close_on_or_before(candles, datetime(2026, 1, 6, tzinfo=zone)).close == 5.0
    assert mp.close_on_or_before(candles, datetime(2026, 1, 9, tzinfo=zone)).close == 9.0
    assert mp.close_on_or_before(candles, datetime(2026, 1, 1, tzinfo=zone)) is None


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, symbol, rate",
    [
        ("gold/usd", "GC=F", None),
        ("Gold/IDR", "GC=F", "USDIDR=X"),
        ("xau/usd", "GC=F", None),
        ("spx", "^GSPC", None),
        ("IHSG", "^JKSE", None),
        ("usdidr", "USDIDR=X", None),
    ],
)
def test_aliases_and_synonyms_resolve_to_yahoo_symbols(text, symbol, rate):
    instrument = mp.resolve_instrument(text)

    assert (instrument.symbol, instrument.rate_symbol) == (symbol, rate)


def test_gold_in_rupiah_is_priced_per_gram_or_per_ounce():
    assert mp.resolve_instrument("gold/idr").divisor == mp.GRAMS_PER_TROY_OUNCE
    assert mp.resolve_instrument("gold/idr").unit == "IDR per gram"
    assert mp.resolve_instrument("gold/idr-oz").divisor == 1.0
    assert mp.resolve_instrument("gold/idr-oz").unit == "IDR per troy ounce"


def test_idx_prefix_and_market_option_make_a_jakarta_stock():
    by_prefix = mp.resolve_instrument("idx:bbca")
    by_market = mp.resolve_instrument("bmri", market="idx")

    assert (by_prefix.symbol, by_prefix.key, by_prefix.decimals) == ("BBCA.JK", "idx:BBCA", 0)
    assert by_market.symbol == "BMRI.JK"


def test_aliases_win_over_the_market_option_and_symbols_with_marks_stay_as_they_are():
    assert mp.resolve_instrument("ihsg", market="idx").symbol == "^JKSE"
    assert mp.resolve_instrument("^GSPC", market="idx").symbol == "^GSPC"
    assert mp.resolve_instrument("BBCA.JK").symbol == "BBCA.JK"
    assert mp.resolve_instrument("aapl").symbol == "AAPL"


@pytest.mark.parametrize("text", ["bad input!", "idx:", "idx:BA CA", "", "a" * 30])
def test_text_that_is_no_instrument_is_refused_with_the_ways_to_name_one(text):
    with pytest.raises(mp.MarketPriceError) as error:
        mp.resolve_instrument(text)

    assert "alias" in str(error.value) or "kode saham" in str(error.value).lower()


def test_slug_makes_a_safe_file_name():
    assert mp.slug("gold/idr") == "gold-idr"
    assert mp.slug("^GSPC") == "gspc"
    assert mp.slug("idx:BBCA") == "idx-bbca"


# ---------------------------------------------------------------------------
# Reading Yahoo's response
# ---------------------------------------------------------------------------

def test_candles_without_a_close_are_dropped_and_dates_follow_the_exchange_zone():
    data = payload("X", [1.0, None, 3.0], start=int(datetime(2026, 1, 5, 2, tzinfo=UTC).timestamp()), offset=25200)

    series = mp.parse_chart(data, "X", "1d")

    assert [c.close for c in series.candles] == [1.0, 3.0]
    assert series.candles[0].time.isoformat() == "2026-01-05T09:00:00+07:00"


def test_an_unfinished_last_candle_takes_the_latest_price_when_it_is_the_same_day():
    start = int(datetime(2026, 10, 26, 2, tzinfo=UTC).timestamp())
    updated = int(datetime(2026, 10, 27, 9, 14, tzinfo=UTC).timestamp())  # 16:14 in Jakarta, same day
    data = payload("BBCA.JK", [4940.0, None], start=start, offset=25200, price=4900.0, updated=updated)

    series = mp.parse_chart(data, "BBCA.JK", "1d")

    assert [c.close for c in series.candles] == [4940.0, 4900.0]
    assert (series.last.open, series.last.high, series.last.low) == (10.0, 12.0, 9.0)


def test_an_unfinished_candle_from_another_day_is_not_filled():
    start = int(datetime(2026, 10, 26, 2, tzinfo=UTC).timestamp())
    updated = int(datetime(2026, 10, 28, 9, tzinfo=UTC).timestamp())
    data = payload("X", [4940.0, None], start=start, offset=25200, price=4900.0, updated=updated)

    assert [c.close for c in mp.parse_chart(data, "X", "1d").candles] == [4940.0]


def test_series_carries_the_name_unit_and_contract_from_the_meta():
    series = mp.parse_chart(MARKET["GC=F"](), "GC=F", "1d")
    stock = mp.parse_chart(MARKET["BBCA.JK"](), "BBCA.JK", "1d")

    assert (series.currency, series.detail, series.decimals) == ("USD", "GC=F (Gold Dec 26)", 2)
    assert (stock.currency, stock.decimals) == ("IDR", 0)


@pytest.mark.parametrize(
    "data, reason",
    [
        ({"chart": {"result": None, "error": {"code": "Not Found", "description": "No data found"}}}, "No data found"),
        ({"chart": {"result": [], "error": None}}, "tidak ada data"),
        (payload("X", [None]), "tidak ada candle dengan harga penutupan"),
    ],
)
def test_a_response_without_usable_data_raises_a_readable_reason(data, reason):
    with pytest.raises(mp.MarketPriceError) as error:
        mp.parse_chart(data, "X", "1d")

    assert reason in str(error.value)


# ---------------------------------------------------------------------------
# Network: retry, host fallback, request parameters
# ---------------------------------------------------------------------------

@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(mp.time, "sleep", lambda seconds: None)


def test_a_rate_limit_is_retried_and_then_succeeds(monkeypatch, no_sleep):
    answers = [http_error(429), http_error(429), {"ok": True}]

    def get(url):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(mp, "_get_json", get)

    assert mp.fetch_json("/v8/finance/chart/X", {"interval": "1d"}) == {"ok": True}
    assert answers == []


def test_a_missing_symbol_is_not_retried_and_shows_the_reason_from_yahoo(monkeypatch, no_sleep):
    calls = []
    body = json.dumps({"chart": {"result": None, "error": {"code": "Not Found", "description": "No data found"}}})

    def get(url):
        calls.append(url)
        raise http_error(404, body)

    monkeypatch.setattr(mp, "_get_json", get)

    with pytest.raises(mp.MarketPriceError) as error:
        mp.fetch_json("/v8/finance/chart/NOPE", {})

    assert "HTTP 404" in str(error.value) and "No data found" in str(error.value)
    assert len(calls) == 1


def test_the_second_host_is_tried_after_the_first_keeps_failing(monkeypatch, no_sleep):
    hosts = []

    def get(url):
        hosts.append(url.split("/v8")[0])
        if "query1" in url:
            raise urllib.error.URLError("unreachable")
        return {"ok": True}

    monkeypatch.setattr(mp, "_get_json", get)

    assert mp.fetch_json("/v8/finance/chart/X", {}) == {"ok": True}
    assert hosts == ["https://query1.finance.yahoo.com"] * mp.HTTP_MAX_ATTEMPTS + ["https://query2.finance.yahoo.com"]


def test_when_every_host_fails_the_last_reason_is_raised(monkeypatch, no_sleep):
    monkeypatch.setattr(mp, "_get_json", lambda url: (_ for _ in ()).throw(urllib.error.URLError("unreachable")))

    with pytest.raises(mp.MarketPriceError) as error:
        mp.fetch_json("/v8/finance/chart/X", {})

    assert "Gagal menghubungi" in str(error.value)


def test_a_range_or_a_pair_of_dates_becomes_the_request_parameters(monkeypatch):
    calls = []
    monkeypatch.setattr(mp, "fetch_json", fake_api(calls=calls))

    mp.fetch_symbol("^GSPC", "1wk", "6mo")
    mp.fetch_symbol("^GSPC", "1d", None, "2026-01-01", "2026-02-01")

    by_range, by_dates = calls[0][1], calls[1][1]
    assert (by_range["interval"], by_range["range"]) == ("1wk", "6mo")
    assert "period1" not in by_range
    assert by_dates["period1"] == int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    assert by_dates["period2"] == int(datetime(2026, 2, 2, tzinfo=UTC).timestamp())  # the end day is included
    assert "range" not in by_dates


def test_the_same_symbol_is_fetched_once_per_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(mp, "fetch_json", fake_api(calls=calls))
    cache = {}

    mp.fetch_series(mp.resolve_instrument("gold/idr"), "1d", "1y", cache=cache)
    mp.fetch_series(mp.resolve_instrument("gold/usd"), "1d", "1y", cache=cache)
    mp.fetch_series(mp.resolve_instrument("usd/idr"), "1d", "1y", cache=cache)

    assert sorted(symbol for symbol, _ in calls) == ["GC=F", "USDIDR=X"]


@pytest.mark.parametrize("interval, range_, reason", [("2d", "1y", "Interval"), ("1d", "3y", "Rentang")])
def test_options_outside_the_list_are_refused_before_any_request(interval, range_, reason):
    with pytest.raises(mp.MarketPriceError) as error:
        mp.fetch_symbol("^GSPC", interval, range_)

    assert reason in str(error.value)


def test_a_date_that_is_not_a_date_is_refused():
    with pytest.raises(mp.MarketPriceError):
        mp.parse_day("2026-13-40")


# ---------------------------------------------------------------------------
# Cross rate: gold in rupiah
# ---------------------------------------------------------------------------

def test_gold_in_rupiah_is_gold_times_the_rate_over_grams_per_ounce(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    series = mp.fetch_series(mp.resolve_instrument("gold/idr"), "1d", "1y")

    gold_last = 2000.0 + 299
    assert series.last.close == pytest.approx(gold_last * 16000 / mp.GRAMS_PER_TROY_OUNCE)
    assert (series.unit, series.decimals, series.last.volume) == ("IDR per gram", 0, 0.0)
    assert series.detail == "GC=F (Gold Dec 26) x USDIDR=X / 31.1035"


def test_each_day_uses_the_rate_of_the_same_day_or_the_latest_earlier_one():
    zone = timezone.utc
    day = lambda d: datetime(2026, 3, d, tzinfo=zone)  # noqa: E731
    base = mp.Series(mp.Instrument("g", "G"), "G", "G", "USD", "USD", "", "FUTURE", 2, "1d",
                     [mp.Candle(day(d), 100, 100, 100, 100, 0) for d in (1, 2, 3, 4)], day(4), "G")
    rate = mp.Series(mp.Instrument("r", "R"), "R", "R", "IDR", "IDR", "", "CURRENCY", 2, "1d",
                     [mp.Candle(day(2), 1, 1, 1, 10, 0), mp.Candle(day(4), 1, 1, 1, 20, 0)], day(4), "R")

    converted = mp.convert_series(base, rate, 1.0)

    # March 1 has no rate yet and is dropped; March 3 reuses the rate of March 2.
    assert [(c.time.day, c.close) for c in converted.candles] == [(2, 1000.0), (3, 1000.0), (4, 2000.0)]


def test_intraday_candles_use_the_latest_rate_at_or_before_their_own_time():
    zone = timezone.utc
    at = lambda h, m: datetime(2026, 3, 2, h, m, tzinfo=zone)  # noqa: E731
    make = lambda times, close: [mp.Candle(t, 1, 1, 1, close(i), 0) for i, t in enumerate(times)]  # noqa: E731
    base = mp.Series(mp.Instrument("g", "G"), "G", "G", "USD", "USD", "", "FUTURE", 2, "5m",
                     make([at(9, 0), at(9, 5), at(9, 10)], lambda i: 1.0), at(9, 10), "G")
    rate = mp.Series(mp.Instrument("r", "R"), "R", "R", "IDR", "IDR", "", "CURRENCY", 2, "5m",
                     make([at(9, 0), at(9, 8)], lambda i: [5.0, 7.0][i]), at(9, 8), "R")

    converted = mp.convert_series(base, rate, 1.0)

    assert [c.close for c in converted.candles] == [5.0, 5.0, 7.0]
    assert converted.updated == at(9, 8)  # the older of the two: the number is only as fresh as its rate


def test_prices_and_rates_that_never_overlap_are_refused():
    zone = timezone.utc
    base = mp.Series(mp.Instrument("g", "G"), "G", "G", "USD", "USD", "", "FUTURE", 2, "1d",
                     [mp.Candle(datetime(2026, 1, 1, tzinfo=zone), 1, 1, 1, 1, 0)], datetime(2026, 1, 1, tzinfo=zone), "G")
    rate = mp.Series(mp.Instrument("r", "R"), "R", "R", "IDR", "IDR", "", "CURRENCY", 2, "1d",
                     [mp.Candle(datetime(2026, 2, 1, tzinfo=zone), 1, 1, 1, 1, 0)], datetime(2026, 2, 1, tzinfo=zone), "R")

    with pytest.raises(mp.MarketPriceError):
        mp.convert_series(base, rate, 1.0)


# ---------------------------------------------------------------------------
# Current price action
# ---------------------------------------------------------------------------

def test_the_snapshot_measures_changes_against_earlier_closes(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    snapshot = mp.build_snapshot(mp.resolve_instrument("spx"))

    last = 5000.0 + 299
    assert snapshot.series.last.close == last
    assert snapshot.previous.close == last - 1
    assert snapshot.session_change == pytest.approx(1 / (last - 1) * 100)
    by_label = {label: percent for label, percent, _ in snapshot.changes}
    assert by_label["1 minggu"] == pytest.approx(7 / (last - 7) * 100)
    assert by_label["1 bulan"] == pytest.approx(30 / (last - 30) * 100)
    assert by_label["1 tahun"] is None  # 300 sessions starting 2025-01-01 reach back only 299 days
    assert snapshot.sma[20] == pytest.approx(last - 9.5)
    assert snapshot.sma[200] == pytest.approx(last - 99.5)
    assert snapshot.rsi == 100.0
    assert (snapshot.high_52w, snapshot.low_52w) == (last + 1, 5000.0 - 2)
    assert snapshot.sessions_52w == 300


def test_year_to_date_compares_with_the_last_close_of_the_year_before(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    snapshot = mp.build_snapshot(mp.resolve_instrument("spx"))

    label, percent, base = snapshot.changes[-1]
    assert (label, percent, base) == ("Sejak awal tahun", None, None)  # every fake candle is in 2025


def test_volume_is_compared_with_the_twenty_sessions_before_the_last(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    assert mp.build_snapshot(mp.resolve_instrument("spx")).volume_ratio == pytest.approx(1.0)
    assert mp.build_snapshot(mp.resolve_instrument("gold/idr")).volume_ratio is None  # converted prices have no volume


def test_a_short_history_leaves_the_long_averages_empty_instead_of_failing(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", lambda path, params: payload("^GSPC", rising(30)))

    snapshot = mp.build_snapshot(mp.resolve_instrument("spx"))

    assert snapshot.sma[20] is not None and snapshot.sma[50] is None and snapshot.sma[200] is None
    assert "SMA 50: n/a" in mp.render(snapshot)
    assert "SMA n/a (data kurang)" in mp.summary_line(snapshot)


def test_a_single_candle_is_not_enough(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", lambda path, params: payload("^GSPC", [100.0]))

    with pytest.raises(mp.MarketPriceError):
        mp.build_snapshot(mp.resolve_instrument("spx"))


def test_the_summary_line_has_price_changes_trend_rsi_and_range_position(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    line = mp.summary_line(mp.build_snapshot(mp.resolve_instrument("gold/idr")))

    assert line.startswith("GOLD/IDR: ")
    assert " IDR per gram (+0.0" in line
    assert "harga di atas SMA 50 dan 200" in line
    assert "RSI 14 100.0 overbought" in line
    assert line.endswith("posisi 52 minggu 100%")  # 99.7% of the range, rounded to a whole number


def test_the_document_has_valid_front_matter_and_the_sections_of_a_snapshot(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    document = mp.render(mp.build_snapshot(mp.resolve_instrument("idx:BBCA")))

    _, front, body = document.split("---\n", 2)
    meta = yaml.safe_load(front)
    assert meta["name"] == "idx-bbca-snapshot"
    assert "BBCA" in meta["description"] and "price action" in meta["description"]
    for section in ("## Harga", "## Perubahan", "## Tren", "## Rentang 52 minggu", "## Volume", "## 5 candle terakhir (1d)"):
        assert section in body
    assert "Satuan: IDR per saham" in body
    assert "Harga terakhir: 8,299" in body
    assert "bukan saran" in body


def test_the_snapshot_dict_can_be_dumped_as_json_and_names_its_figures(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    record = mp.snapshot_dict(mp.build_snapshot(mp.resolve_instrument("gold/usd")))

    json.dumps(record)
    assert record["price"] == 2299.0 and record["previous_close"] == 2298.0
    assert record["unit"] == "USD per troy ounce" and record["rsi_reading"].startswith("overbought")
    assert set(record["changes_percent"]) == {"1 minggu", "1 bulan", "3 bulan", "1 tahun", "Sejak awal tahun"}
    assert record["document"].startswith("---\nname: gold-usd-snapshot")


@pytest.mark.parametrize("value, reading", [(70.0, "overbought"), (30.0, "oversold"), (50.0, "netral"), (None, "n/a")])
def test_rsi_readings_use_fixed_thresholds(value, reading):
    assert mp.rsi_reading(value) == reading


# ---------------------------------------------------------------------------
# Historical candles
# ---------------------------------------------------------------------------

def test_daily_candles_are_written_with_dates_and_intraday_ones_with_zone(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())
    daily = mp.fetch_series(mp.resolve_instrument("spx"), "1d", "1y")
    intraday = mp.replace(daily, interval="5m")

    assert mp.render_csv(daily).splitlines()[:2] == [
        "time,open,high,low,close,volume",
        "2025-01-01,4999,5001,4998,5000,2000000",
    ]
    assert mp.render_csv(intraday).splitlines()[1].startswith("2025-01-01T00:00+00:00,")


def test_the_history_summary_names_the_period_and_the_move(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    series = mp.fetch_series(mp.resolve_instrument("spx"), "1d", "1y")

    assert mp.history_summary(series) == (
        "SPX 1d: 300 candle, 2025-01-01 sampai 2025-10-27, penutupan 5,000.00 -> 5,299.00 (+5.98%) poin indeks"
    )


def test_the_history_dict_has_the_candles_and_the_csv_text(monkeypatch):
    monkeypatch.setattr(mp, "fetch_json", fake_api())

    record = mp.history_dict(mp.fetch_series(mp.resolve_instrument("idx:BBCA"), "1d", "6mo"), "6mo")

    assert (record["count"], record["interval"], record["range"]) == (300, "1d", "6mo")
    assert record["candles"][0] == {"time": "2025-01-01", "open": 7999.0, "high": 8001.0, "low": 7998.0, "close": 8000.0, "volume": 5000000.0}
    assert record["name_slug"] == "idx-bbca-1d-6mo"
    assert record["csv"].startswith("time,open,high,low,close,volume\n")


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def test_now_logs_one_summary_per_instrument_and_writes_files_only_with_an_output_folder(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="market_price")

    code = mp.main(["now", "spx", "gold/idr", "idx:BBCA"])

    assert code == 0
    text = caplog.text
    assert "SPX: 5,299.00 poin indeks" in text and "GOLD/IDR:" in text and "IDX:BBCA:" in text
    assert "Selesai: 3 sukses, 0 gagal" in text
    assert list(tmp_path.iterdir()) == []

    assert mp.main(["now", "spx", "-o", str(tmp_path)]) == 0
    assert (tmp_path / "spx-snapshot.txt").read_text(encoding="utf-8").startswith("---\nname: spx-snapshot")


def test_one_failing_instrument_does_not_stop_the_others_and_exits_with_one(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="market_price")

    code = mp.main(["now", "nope.jk", "spx", "-o", str(tmp_path)])

    assert code == 1
    assert "GAGAL nope.jk -> HTTP 404" in caplog.text and "Selesai: 1 sukses, 1 gagal" in caplog.text
    assert [p.name for p in tmp_path.iterdir()] == ["spx-snapshot.txt"]


@pytest.mark.parametrize(
    "argv",
    [["now", "spx", "bad input!"], ["history", "spx", "--start", "2026-13-40"], ["history", "spx", "--end", "tomorrow"]],
)
def test_input_that_is_invalid_exits_with_two_before_any_request(monkeypatch, tmp_path, argv):
    monkeypatch.setattr(mp, "fetch_json", lambda path, params: pytest.fail("no request should be made"))

    assert mp.main([*argv, "-o", str(tmp_path)]) == 2


def test_market_option_reads_bare_names_as_jakarta_stocks(offline, tmp_path):
    assert mp.main(["now", "bbca", "--market", "idx", "-o", str(tmp_path)]) == 0
    assert (tmp_path / "idx-bbca-snapshot.txt").is_file()


def test_history_writes_one_csv_per_instrument_named_by_interval_and_range(offline, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="market_price")

    code = mp.main(["history", "spx", "gold/idr", "-r", "6mo", "-i", "1wk", "-o", str(tmp_path)])

    assert code == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == ["gold-idr-1wk-6mo.csv", "spx-1wk-6mo.csv"]
    assert "SPX 1wk: 300 candle" in caplog.text


def test_history_with_dates_names_the_file_by_the_dates(offline, tmp_path):
    assert mp.main(["history", "idx:BBCA", "--start", "2026-01-01", "--end", "2026-02-01", "-o", str(tmp_path)]) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["idx-bbca-1d-2026-01-01-2026-02-01.csv"]


def test_files_are_written_whole_or_not_at_all(tmp_path):
    target = tmp_path / "deep" / "file.txt"

    mp.write_atomic(target, "isi")

    assert target.read_text(encoding="utf-8") == "isi"
    assert not (tmp_path / "deep" / "file.txt.tmp").exists()


# ---------------------------------------------------------------------------
# Python functions and tools
# ---------------------------------------------------------------------------

def test_get_price_action_returns_the_dict_with_the_document(offline):
    record = skill.get_price_action("spx")

    assert record["instrument"] == "spx" and record["price"] == 5299.0
    assert record["document"].startswith("---\nname: spx-snapshot")
    assert skill.get_price_action("bbca", market="idx")["symbol"] == "BBCA.JK"


def test_get_history_returns_candles_summary_and_csv(offline):
    record = skill.get_history("gold/usd", range="1y", interval="1d")

    assert record["count"] == 300 and record["candles"][-1]["close"] == 2299.0
    assert record["summary"].startswith("GOLD/USD 1d: 300 candle")
    assert skill.get_history("spx", start="2026-01-01", end="2026-02-01")["range"] == "2026-01-01_2026-02-01"


def test_a_failure_comes_back_as_text_that_tells_the_model_not_to_guess(offline):
    for text in (skill.price_action_text("nope.jk"), skill.history_text("nope.jk")):
        assert "Do not estimate" in text and "HTTP 404" in text


def test_the_history_text_keeps_the_header_and_only_the_last_rows(offline):
    lines = skill.history_text("spx", "1y", "1d", rows=5).splitlines()

    assert lines[0].startswith("SPX 1d: 300 candle") and lines[1] == "(last 5 of 300 candles)"
    assert lines[2] == "time,open,high,low,close,volume" and len(lines) == 8
    assert lines[-1].startswith("2025-10-27,")
    assert "(last" not in skill.history_text("spx", "1y", "1d", rows=300)


def test_unknown_instrument_is_an_error_not_a_guess():
    with pytest.raises(skill.MarketPriceError):
        skill.get_price_action("bad input!")


def test_tools_exist_when_langchain_is_installed_and_wrap_the_text_functions(offline):
    if skill.get_market_price is None:
        pytest.skip("langchain-core is not installed")

    assert skill.get_market_price.name == "get_market_price"
    assert skill.get_market_price.invoke({"instrument": "spx"}).startswith("---\nname: spx-snapshot")
    assert skill.get_price_history.invoke({"instrument": "spx", "range": "1y"}).startswith("SPX 1d:")


# ---------------------------------------------------------------------------
# Documentation stays in step with the code
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [SKILL / "SKILL.md", REPO / "docs" / "panduan" / "mengambil-harga-pasar.md"],
    ids=["SKILL.md", "docs page"],
)
def test_every_alias_is_mentioned_where_users_look_for_it(path):
    text = path.read_text(encoding="utf-8")

    assert [key for key in skill.INSTRUMENTS if f"`{key}`" not in text] == []
