"""Crypto chart skill: a candlestick chart image of a crypto pair, with EMA 12/21, volume and Stochastic (5, 3, 3).

No language model is involved anywhere: candles come from Binance's public API, the indicators are computed
by scripts/crypto_chart.py with the same formulas and candle count as the crypto_snapshot skill (so the
numbers in the picture match the snapshot), and matplotlib draws the image.

    from utilities.crypto_chart.crypto_chart_skill import draw_chart
    result = draw_chart("BTC")                                  # charts/btcusdt-1h-chart.png
    result = draw_chart("ETH/USDT", "4h", indicators="none")    # candles only
    result["path"], result["ema_fast"], result["stoch_k"], result["summary"]

`get_crypto_chart` is the same thing as a LangChain tool for an agent; it is None when langchain-core is
not installed, and the plain function works without it.  For many tokens at once, run the script.
"""

import importlib
import os
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent / "scripts"
OUTPUT_DIR_ENV = "CRYPTO_CHART_DIR"     # where the tool saves images; default ./charts


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


_cc = _load(["crypto_chart"])["crypto_chart"]
ChartError = _cc.ChartError


# ---------------------------------------------------------------------------
# Plain function: no model, no LangChain
# ---------------------------------------------------------------------------

def draw_chart(token: str, interval: str = _cc.DEFAULT_INTERVAL, indicators="all",
               candles: int = _cc.DEFAULT_CANDLES_SHOWN, theme: str = "light", image_format: str = "png",
               output_dir=None, quote: str = _cc.DEFAULT_QUOTE) -> dict:
    """Draw and save the candlestick chart of one pair; return where it is and what it shows.

    `token` is a token name ("BTC"), a pair ("ETH/USDT", "ETHBTC") or a Binance / TradingView URL.
    `indicators` is "all" (EMA 12/21, volume, Stochastic), "none" (candles only), or a list or comma string
    of "ema", "volume", "stoch".  The image goes to `output_dir` (default: $CRYPTO_CHART_DIR or ./charts)
    as <symbol>-<interval>-chart.png (or .svg).
    Returns {"path", "symbol", "interval", "source_url", "fetched_at", "candles_shown", "indicators", "price",
    "change_24h_percent", "last_close", "ema_fast", "ema_slow", "stoch_k", "stoch_d", "volume_ratio",
    "summary"}; an indicator that is not drawn has None.  Raises ChartError with a readable reason.
    """
    target = _cc.parse_input(token, interval, quote)
    chosen = _cc.parse_indicators(indicators)
    folder = Path(output_dir or os.environ.get(OUTPUT_DIR_ENV) or "charts")
    result = _cc.make_chart(target, folder, chosen, candles, theme, image_format)
    result["summary"] = _cc.describe(result)
    return result


def chart_text(token: str, interval: str = _cc.DEFAULT_INTERVAL, indicators="all") -> str:
    """Where the chart image was saved and what it shows, or the reason it failed, as plain sentences."""
    try:
        result = draw_chart(token, interval, indicators)
    except Exception as error:  # noqa: BLE001 - the reason goes back to the caller as text
        return f"No chart for {token!r}: {error}. Do not draw or describe a chart yourself; report the reason."
    path = Path(result["path"]).resolve()
    return (f"Chart image saved: {path}\n{result['summary']}\n"
            f"Data time (UTC): {result['fetched_at']}. Show this image file to the user. The indicators describe "
            "where the price is, not advice to buy or sell.")


# ---------------------------------------------------------------------------
# Optional: the same as a LangChain tool, for an agent
# ---------------------------------------------------------------------------

def _get_crypto_chart(token: str, interval: str = "1h", indicators: str = "all") -> str:
    """Draw a candlestick chart image of a crypto token, with EMA 12/21, volume and Stochastic (5, 3, 3).

    Use it whenever the user wants to see the chart, a picture, a candlestick or a graph of a crypto token
    or pair (BTC, ETH, SOL, BTCUSDT, ...). The reply gives the path of the saved PNG and the last value of
    each indicator in the picture; show that file to the user. Never describe a chart you have not drawn.

    Args:
        token: Token name such as "BTC", a pair such as "ETH/USDT", or a Binance / TradingView URL.
        interval: Candle timeframe: 1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M. Default 1h.
        indicators: "all" (default), "none" for candles only, or a comma list of ema, volume, stoch.
    """
    return chart_text(token, interval, indicators)


try:
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - the plain function above works without LangChain
    get_crypto_chart = None
else:
    get_crypto_chart = StructuredTool.from_function(_get_crypto_chart, name="get_crypto_chart")


__all__ = ["draw_chart", "chart_text", "get_crypto_chart", "ChartError"]
