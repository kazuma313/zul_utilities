"""Market price skill: historical candles and current price action for gold, indices, stocks and FX.

No language model is involved anywhere: candles come from Yahoo Finance's public chart endpoint, every
number is computed by scripts/market_price.py, and the readings (above or below an average, overbought,
oversold) are fixed thresholds in that script.  The same input at the same moment gives the same numbers.

    from utilities.market_price.market_price_skill import get_price_action, get_history
    now = get_price_action("gold/idr")          # also "gold/usd", "spx", "ihsg", "idx:BBCA", "AAPL"
    now["price"], now["session_change_percent"], now["rsi"], now["summary"], now["document"]
    past = get_history("idx:BBCA", range="1y", interval="1d")
    past["summary"], past["candles"][-1], past["csv"]

`get_market_price` and `get_price_history` are the same thing as LangChain tools for an agent; they are
None when langchain-core is not installed, and the plain functions work without it.  For many instruments
at once, or to keep the results as files, run scripts/market_price.py (see SKILL.md).
"""

import importlib
import sys
from pathlib import Path
from typing import Optional

_SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _load(required, optional=()):
    """Import this folder's scripts without leaving their names behind (other folders share module names)."""
    own = {p.stem for p in _SCRIPTS.glob("*.py")}
    aside = {name: sys.modules.pop(name) for name in own if name in sys.modules}
    sys.path.insert(0, str(_SCRIPTS))
    loaded = {}
    try:
        for name in required:
            loaded[name] = importlib.import_module(name)
        for name in optional:
            try:
                loaded[name] = importlib.import_module(name)
            except ImportError:
                loaded[name] = None
    finally:
        for name in own:
            sys.modules.pop(name, None)
        sys.modules.update(aside)
        while str(_SCRIPTS) in sys.path:
            sys.path.remove(str(_SCRIPTS))
    return loaded


_mp = _load(["market_price"])["market_price"]
MarketPriceError = _mp.MarketPriceError
INSTRUMENTS = tuple(_mp.ALIASES)
HISTORY_TEXT_ROWS = 20


# ---------------------------------------------------------------------------
# Plain functions: no model, no LangChain
# ---------------------------------------------------------------------------

def get_price_action(instrument: str, market: Optional[str] = None) -> dict:
    """Current price and recent price action of one instrument, as a plain dict.

    `instrument` is an alias ("gold/usd", "gold/idr", "gold/idr-oz", "spx", "ihsg", "usd/idr"), an IDX stock
    ("idx:BBCA", or "BBCA" with market="idx"), or a Yahoo Finance symbol ("AAPL", "^GSPC", "BBCA.JK").
    Returns {"instrument", "symbol", "name", "currency", "unit", "source", "fetched_at", "price_updated",
    "price", "previous_close", "previous_close_date", "session_change_percent", "changes_percent", "sma",
    "rsi", "rsi_reading", "high_52w", "low_52w", "range_position_percent", "volume_ratio", "summary",
    "name_slug", "document"}; "document" is the text of the .txt file the script writes.
    Raises MarketPriceError with a readable reason (unknown symbol, network blocked, too few candles).
    """
    return _mp.snapshot_dict(_mp.build_snapshot(_mp.resolve_instrument(instrument, market)))


def get_history(
    instrument: str,
    range: str = _mp.DEFAULT_RANGE,
    interval: str = _mp.DEFAULT_INTERVAL,
    start: Optional[str] = None,
    end: Optional[str] = None,
    market: Optional[str] = None,
) -> dict:
    """Historical candles of one instrument, as a plain dict.

    `range` is 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max; `interval` is 1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk
    1mo 3mo (Yahoo keeps only a few days of 1m and about 60 days of the other intraday intervals).
    `start` and `end` (YYYY-MM-DD, the end day included) replace `range`.
    Returns {"instrument", "symbol", "name", "currency", "unit", "source", "interval", "range", "count",
    "candles", "summary", "name_slug", "csv"}; each candle is {"time", "open", "high", "low", "close",
    "volume"}.  Raises MarketPriceError with a readable reason.
    """
    series = _mp.fetch_series(_mp.resolve_instrument(instrument, market), interval, range, start, end)
    label = f"{start or 'awal'}_{end or 'kini'}" if start or end else range
    return _mp.history_dict(series, label)


def price_action_text(instrument: str) -> str:
    """The price action document of one instrument, or the reason it failed as a plain sentence."""
    try:
        return get_price_action(instrument)["document"]
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return (f"No price for {instrument!r}: {error}. Do not estimate prices or indicators yourself; "
                "report the reason to the user.")


def history_text(
    instrument: str, range: str = _mp.DEFAULT_RANGE, interval: str = _mp.DEFAULT_INTERVAL, rows: int = HISTORY_TEXT_ROWS
) -> str:
    """The summary line and the last `rows` candles of one instrument as CSV, or the reason it failed."""
    try:
        record = get_history(instrument, range, interval)
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return (f"No history for {instrument!r}: {error}. Do not estimate prices yourself; "
                "report the reason to the user.")
    lines = record["csv"].splitlines()
    shown = lines[:1] + lines[1:][-rows:]
    text = [record["summary"]]
    if record["count"] > rows:
        text.append(f"(last {rows} of {record['count']} candles)")
    return "\n".join(text + shown)


# ---------------------------------------------------------------------------
# Optional: the same as LangChain tools, for an agent
# ---------------------------------------------------------------------------

def _get_market_price(instrument: str) -> str:
    """Get the current price and recent price action of gold, an index, a stock or an exchange rate.

    Use it whenever the user asks for the current price, the trend or recent movement of gold in USD or
    rupiah (gold/usd, gold/idr), the S&P 500 (spx), the IHSG (ihsg), the dollar rate (usd/idr), an
    Indonesian stock (idx:BBCA, idx:BMRI) or any Yahoo Finance symbol (AAPL, ^GSPC, BBCA.JK).
    The numbers come from Yahoo Finance and are computed by code; never compute or guess them yourself.
    Readings describe where the price is, not advice to buy or sell.

    Args:
        instrument: gold/usd, gold/idr, gold/idr-oz, spx, ihsg, usd/idr, idx:KODE, or a Yahoo symbol.
    """
    return price_action_text(instrument)


def _get_price_history(instrument: str, range: str = "1y", interval: str = "1d") -> str:
    """Get historical candles (time, open, high, low, close, volume) of gold, an index, a stock or a rate.

    Use it when the user asks how the price moved over a period. The reply is a summary line and the
    last 20 candles as CSV; for the whole history ask the user to run scripts/market_price.py history.

    Args:
        instrument: gold/usd, gold/idr, gold/idr-oz, spx, ihsg, usd/idr, idx:KODE, or a Yahoo symbol.
        range: 1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max. Default 1y.
        interval: 1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk 1mo 3mo. Default 1d.
    """
    return history_text(instrument, range, interval)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    get_market_price = None
    get_price_history = None
else:
    get_market_price = StructuredTool.from_function(_get_market_price, name="get_market_price")
    get_price_history = StructuredTool.from_function(_get_price_history, name="get_price_history")


__all__ = [
    "get_price_action",
    "get_history",
    "price_action_text",
    "history_text",
    "get_market_price",
    "get_price_history",
    "MarketPriceError",
    "INSTRUMENTS",
]
