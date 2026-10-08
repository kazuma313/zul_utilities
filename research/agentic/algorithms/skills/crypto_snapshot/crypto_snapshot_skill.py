"""Crypto snapshot skill: current price of a crypto pair with EMA 12/21, Stochastic (5, 3, 3) and volume.

No language model is involved anywhere: candles and the 24-hour ticker come from Binance's public API,
every number is computed by scripts/crypto_snapshot.py, and the readings (bullish, overbought, ...) are
fixed thresholds in that script.  The same input at the same moment gives the same numbers.

    from skills.crypto_snapshot.crypto_snapshot_skill import get_snapshot
    record = get_snapshot("BTC")                  # also "ETH/USDT", "SOLUSDT" or a Binance / TradingView URL
    record["price"], record["ema_reading"], record["stoch_reading"], record["summary"], record["document"]

`get_crypto_snapshot` is the same thing as a LangChain tool for an agent; it is None when langchain-core
is not installed, and the plain functions work without it.  For many tokens at once, or to keep the
snapshots as files, run scripts/crypto_snapshot.py (see SKILL.md).
"""

import importlib
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"


def _load(required, optional=()):
    """Import this skill's scripts without leaving their names behind (the other skills share module names)."""
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


_cs = _load(["crypto_snapshot"])["crypto_snapshot"]
SnapshotError = _cs.SnapshotError


# ---------------------------------------------------------------------------
# Plain functions: no model, no LangChain
# ---------------------------------------------------------------------------

def get_snapshot(token: str, interval: str = _cs.DEFAULT_INTERVAL, quote: str = _cs.DEFAULT_QUOTE) -> dict:
    """Price, EMA, Stochastic and volume of one pair, as a plain dict.

    `token` is a token name ("BTC", quote `quote`), a pair ("ETH/USDT", "SOLUSDT", "ETHBTC") or a Binance /
    TradingView URL; an `interval` inside the URL wins over the argument.
    Returns {"symbol", "interval", "source_url", "fetched_at", "last_candle_open", "price",
    "change_24h_percent", "ema_fast", "ema_slow", "ema_reading", "stoch_k", "stoch_d", "stoch_reading",
    "volume_last", "volume_avg", "volume_ratio", "volume_24h", "quote_volume_24h", "summary", "name",
    "document"}; "document" is the text of the .txt file the script writes.
    Raises SnapshotError with a readable reason (unknown symbol, network blocked, too few candles).
    """
    target = _cs.parse_input(token, interval, quote)
    return _cs.snapshot_dict(_cs.build_snapshot(target))


def snapshot_text(token: str, interval: str = _cs.DEFAULT_INTERVAL) -> str:
    """The snapshot document of one pair, or the reason it failed as a plain sentence."""
    try:
        return get_snapshot(token, interval)["document"]
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return (f"No snapshot for {token!r}: {error}. Do not estimate prices or indicators yourself; "
                "report the reason to the user.")


# ---------------------------------------------------------------------------
# Optional: the same as a LangChain tool, for an agent
# ---------------------------------------------------------------------------

def _get_crypto_snapshot(token: str, interval: str = "1h") -> str:
    """Get the current price of a crypto token with EMA 12 and 21, Stochastic (5, 3, 3) and volume.

    Use it whenever the user asks for the current price, a market snapshot, trend, momentum, EMA,
    stochastic or volume of a crypto token or pair (BTC, ETH, SOL, BTCUSDT, ...), even without a URL.
    The numbers come from Binance's public API and are computed by code; never compute or guess them
    yourself. Readings such as "bullish" or "overbought" describe the indicators, not advice to buy or sell.

    Args:
        token: Token name such as "BTC", a pair such as "ETH/USDT", or a Binance / TradingView URL.
        interval: Candle timeframe: 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M. Default 1h.
    """
    return snapshot_text(token, interval)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain functions above work without LangChain
    get_crypto_snapshot = None
else:
    get_crypto_snapshot = StructuredTool.from_function(_get_crypto_snapshot, name="get_crypto_snapshot")


__all__ = ["get_snapshot", "snapshot_text", "get_crypto_snapshot", "SnapshotError"]
