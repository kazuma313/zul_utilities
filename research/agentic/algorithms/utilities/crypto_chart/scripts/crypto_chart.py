#!/usr/bin/env python3
"""crypto_chart.py - token / URL -> gambar candlestick chart (PNG atau SVG) beserta indikatornya.

Untuk setiap token atau URL token (Binance / TradingView), script mengambil candle dari
public API Binance lalu menggambar candlestick chart. Indikator yang dipilih ikut digambar:
EMA 12 & 21 di atas candle, volume beserta rata-ratanya di panel kedua, dan Stochastic
(5, 3, 3) di panel ketiga. Tanpa indikator, gambarnya hanya candle.

Tidak ada model bahasa yang dipakai. Rumus dan jumlah candle sama dengan skill
crypto_snapshot, jadi angka di gambar sama dengan angka di file snapshot.

Pemakaian:
    python crypto_chart.py BTC
    python crypto_chart.py BTC ETH/USDT -i 4h -o charts
    python crypto_chart.py SOL --indicators ema            # hanya EMA
    python crypto_chart.py SOL --indicators none           # candle saja
    python crypto_chart.py BTC --theme dark --format svg -n 120

Input yang dikenali sama dengan crypto_snapshot: nama token (BTC), pair (ETH/USDT, ETHBTC),
URL Binance / TradingView, atau file berisi satu input per baris.

Butuh Python 3.9+ dan matplotlib (pip install matplotlib).
Exit code: 0 = semua sukses, 1 = ada yang gagal, 2 = input tidak valid.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

# --------------------------------------------------------------------------- #
# Konfigurasi - ubah di sini, bukan di dalam fungsi
# --------------------------------------------------------------------------- #
EMA_FAST = 12
EMA_SLOW = 21
STOCH_K_PERIOD = 5
STOCH_K_SMOOTH = 3
STOCH_D_PERIOD = 3
STOCH_OVERBOUGHT = 80.0
STOCH_OVERSOLD = 20.0
VOLUME_AVG_PERIOD = 20

INDICATORS = ("ema", "volume", "stoch")  # urutan panel: harga + EMA, volume, stochastic
DEFAULT_INDICATORS = INDICATORS
DEFAULT_INTERVAL = "1h"
DEFAULT_QUOTE = "USDT"
KNOWN_QUOTES = ("FDUSD", "USDT", "USDC", "TUSD", "BUSD", "BTC", "ETH", "BNB", "EUR", "TRY", "BRL", "JPY")
VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}
CANDLE_LIMIT = 200          # sama dengan crypto_snapshot, supaya nilai EMA identik
DEFAULT_CANDLES_SHOWN = 80  # candle yang tampil; sisanya untuk pemanasan indikator
DPI = 130
FIGURE_WIDTH = 12.0         # inci; 12 x 130 dpi = 1560 piksel

API_HOSTS = ("https://api.binance.com", "https://data-api.binance.vision")
HTTP_TIMEOUT_SECONDS = 10
HTTP_MAX_ATTEMPTS = 3
HTTP_BACKOFF_SECONDS = 1.5
RETRYABLE_STATUS = {418, 429, 500, 502, 503, 504}

# Hijau dan merah candle mengikuti kebiasaan chart trading; EMA dan Stochastic memakai
# pasangan biru-oranye yang tetap bisa dibedakan oleh pembaca buta warna.
THEMES = {
    "light": {
        "background": "#ffffff", "ink": "#111827", "muted": "#6b7280", "grid": "#e5e7eb",
        "up": "#26a69a", "down": "#ef5350", "fast": "#f59e0b", "slow": "#2563eb",
        "band": "#f3f4f6",
    },
    "dark": {
        "background": "#0f172a", "ink": "#e5e7eb", "muted": "#94a3b8", "grid": "#1e293b",
        "up": "#26a69a", "down": "#ef5350", "fast": "#fbbf24", "slow": "#60a5fa",
        "band": "#162033",
    },
}

log = logging.getLogger("crypto_chart")


class ChartError(Exception):
    """Error yang pesannya aman ditampilkan ke pengguna."""


# --------------------------------------------------------------------------- #
# Model data
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Target:
    source_url: str
    symbol: str
    interval: str


@dataclass(frozen=True)
class Candle:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Ticker24h:
    last_price: float
    change_percent: float


@dataclass(frozen=True)
class Series:
    """Candle dan deret indikatornya, sejajar per indeks; None sebelum indikator terbentuk."""

    candles: list[Candle]
    ema_fast: list[Optional[float]]
    ema_slow: list[Optional[float]]
    stoch_k: list[Optional[float]]
    stoch_d: list[Optional[float]]
    volume_avg: list[Optional[float]]


# --------------------------------------------------------------------------- #
# Indikator sebagai deret (fungsi murni, mudah di-test)
# --------------------------------------------------------------------------- #
def sma_series(values: Sequence[Optional[float]], period: int) -> list[Optional[float]]:
    """SMA per indeks; None sampai jendela berisi `period` nilai yang lengkap."""
    result: list[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        if None not in window:
            result[i] = sum(window) / period
    return result


def ema_series(values: Sequence[float], period: int) -> list[Optional[float]]:
    """EMA per indeks, di-seed dengan SMA dari `period` nilai pertama (sama dengan crypto_snapshot)."""
    result: list[Optional[float]] = [None] * len(values)
    if len(values) < period:
        return result
    multiplier = 2 / (period + 1)
    current = sum(values[:period]) / period
    result[period - 1] = current
    for i in range(period, len(values)):
        current = (values[i] - current) * multiplier + current
        result[i] = current
    return result


def stochastic_series(
    candles: Sequence[Candle], k_period: int, k_smooth: int, d_period: int
) -> tuple[list[Optional[float]], list[Optional[float]]]:
    """Stochastic (k_period, k_smooth, d_period) per indeks -> (%K, %D)."""
    raw: list[Optional[float]] = [None] * len(candles)
    for i in range(k_period - 1, len(candles)):
        window = candles[i - k_period + 1 : i + 1]
        highest = max(c.high for c in window)
        lowest = min(c.low for c in window)
        price_range = highest - lowest
        # Range nol (harga flat) -> pakai titik tengah agar tidak divide-by-zero.
        raw[i] = 50.0 if price_range == 0 else (candles[i].close - lowest) / price_range * 100
    k_line = sma_series(raw, k_smooth)
    return k_line, sma_series(k_line, d_period)


def build_series(candles: list[Candle]) -> Series:
    closes = [c.close for c in candles]
    stoch_k, stoch_d = stochastic_series(candles, STOCH_K_PERIOD, STOCH_K_SMOOTH, STOCH_D_PERIOD)
    return Series(
        candles=candles,
        ema_fast=ema_series(closes, EMA_FAST),
        ema_slow=ema_series(closes, EMA_SLOW),
        stoch_k=stoch_k,
        stoch_d=stoch_d,
        volume_avg=sma_series([c.volume for c in candles], VOLUME_AVG_PERIOD),
    )


# --------------------------------------------------------------------------- #
# Parsing input -> Target (sama dengan crypto_snapshot)
# --------------------------------------------------------------------------- #
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")
_TOKEN_PATTERN = re.compile(r"^([A-Za-z0-9]{2,15})(?:[/_\-]([A-Za-z0-9]{2,10}))?$")


def _normalize_symbol(raw: str) -> Optional[str]:
    candidate = raw.split(":")[-1]  # buang prefix exchange, mis. "BINANCE:BTCUSDT"
    candidate = re.sub(r"[_\-/]", "", candidate).upper()
    return candidate if _SYMBOL_PATTERN.match(candidate) else None


def parse_target(url: str, default_interval: str) -> Target:
    """Ambil symbol (dan interval bila ada) dari URL Binance / TradingView."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ChartError(f"Bukan URL http(s) yang valid: {url}")
    query = urllib.parse.parse_qs(parsed.query)
    path_segments = [s for s in parsed.path.split("/") if s]
    candidates = query.get("symbol", []) + path_segments[-1:]
    symbol = next((s for s in map(_normalize_symbol, candidates) if s), None)
    if symbol is None:
        raise ChartError(f"Symbol tidak ditemukan di URL: {url}")
    interval = query.get("interval", [default_interval])[0]
    if interval not in VALID_INTERVALS:
        raise ChartError(f"Interval '{interval}' tidak didukung ({url})")
    return Target(source_url=url, symbol=symbol, interval=interval)


def token_to_target(text: str, default_interval: str, quote: str = DEFAULT_QUOTE) -> Target:
    """Nama token atau pair -> Target: "BTC" -> BTCUSDT, "BTC/USDC" -> BTCUSDC, "ETHBTC" -> ETHBTC."""
    match = _TOKEN_PATTERN.match(text.strip())
    if not match:
        raise ChartError(f"Bukan nama token, pair, atau URL yang dikenali: {text}")
    if default_interval not in VALID_INTERVALS:
        raise ChartError(f"Interval '{default_interval}' tidak didukung ({text})")
    base, pair_quote = match.group(1).upper(), (match.group(2) or "").upper()
    if not pair_quote:
        # Sisa minimal 3 huruf, supaya WBTC atau BETH tetap dibaca sebagai token, bukan W/BTC.
        known = next((q for q in KNOWN_QUOTES if base.endswith(q) and len(base) - len(q) >= 3), None)
        base, pair_quote = (base[: -len(known)], known) if known else (base, quote.upper())
    symbol = f"{base}{pair_quote}"
    if not _SYMBOL_PATTERN.match(symbol):
        raise ChartError(f"Symbol tidak valid: {symbol} (dari {text})")
    return Target(f"https://www.binance.com/en/trade/{base}_{pair_quote}", symbol, default_interval)


def parse_input(item: str, default_interval: str, quote: str = DEFAULT_QUOTE) -> Target:
    """URL -> parse_target, selain itu dibaca sebagai nama token atau pair."""
    if re.match(r"^https?://", item.strip()):
        return parse_target(item.strip(), default_interval)
    return token_to_target(item, default_interval, quote)


def parse_indicators(text: str | Sequence[str]) -> tuple[str, ...]:
    """"ema,volume" -> ("ema", "volume"); "all" -> semua; "none" atau "" -> tanpa indikator."""
    words = text.replace(",", " ").split() if isinstance(text, str) else list(text)
    words = [w.strip().lower() for w in words if w.strip()]
    if not words or words == ["none"]:
        return ()
    if words == ["all"]:
        return INDICATORS
    unknown = [w for w in words if w not in INDICATORS]
    if unknown:
        raise ChartError(f"Indikator tidak dikenal: {', '.join(unknown)} (pilih dari {', '.join(INDICATORS)}, all, none)")
    return tuple(i for i in INDICATORS if i in words)  # urutan panel tetap


# --------------------------------------------------------------------------- #
# Akses API (retry + fallback host)
# --------------------------------------------------------------------------- #
def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "crypto-chart/1.0"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_json(path: str, params: dict):
    """GET ke API dengan retry + backoff, lalu pindah ke host cadangan."""
    query = urllib.parse.urlencode(params)
    last_error: Exception = ChartError("Tidak ada host API yang dikonfigurasi")
    for host in API_HOSTS:
        url = f"{host}{path}?{query}"
        for attempt in range(1, HTTP_MAX_ATTEMPTS + 1):
            try:
                return _get_json(url)
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", "replace")[:200]
                last_error = ChartError(f"HTTP {error.code} dari {host}: {detail}")
                if error.code == 400:  # symbol/parameter salah: host lain pun sama
                    raise last_error from error
                if error.code not in RETRYABLE_STATUS:
                    break  # mis. 403/451 (geo-block): langsung coba host berikutnya
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = ChartError(f"Gagal menghubungi {host}: {error}")
            log.warning("Percobaan %d/%d gagal: %s", attempt, HTTP_MAX_ATTEMPTS, last_error)
            if attempt < HTTP_MAX_ATTEMPTS:
                time.sleep(HTTP_BACKOFF_SECONDS * attempt)
    raise last_error


def fetch_candles(target: Target) -> list[Candle]:
    rows = fetch_json(
        "/api/v3/klines",
        {"symbol": target.symbol, "interval": target.interval, "limit": CANDLE_LIMIT},
    )
    return [
        Candle(
            open_time=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
        )
        for row in rows
    ]


def fetch_ticker(target: Target) -> Ticker24h:
    data = fetch_json("/api/v3/ticker/24hr", {"symbol": target.symbol})
    return Ticker24h(last_price=float(data["lastPrice"]), change_percent=float(data["priceChangePercent"]))


# --------------------------------------------------------------------------- #
# Menggambar: Series -> figure matplotlib
# --------------------------------------------------------------------------- #
def fmt(value: float) -> str:
    """Format angka: 2 desimal untuk nilai besar, lebih presisi untuk nilai kecil."""
    if abs(value) >= 100:
        return f"{value:,.2f}"
    if abs(value) >= 1:
        return f"{value:,.4f}"
    return f"{value:.10f}".rstrip("0").rstrip(".") or "0"


def _compact(value: float, _position=None) -> str:
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(value) >= limit:
            return f"{value / limit:.1f}{suffix}"
    return f"{value:.0f}"


def _tick_label(moment: datetime, interval: str) -> str:
    return moment.strftime("%d %b %Y" if interval[-1] in "dwM" else "%d %b %H:%M")


def chart_name(target: Target) -> str:
    # Suffix "mo" membedakan 1M (bulan) dari 1m (menit) di filesystem case-insensitive.
    interval = "1mo" if target.interval == "1M" else target.interval
    return f"{target.symbol.lower()}-{interval}-chart"


def _last(values: Sequence[Optional[float]]) -> Optional[float]:
    return values[-1] if values else None


def _legend(ax, handles, colors, **options):
    """Legend di kiri atas dengan latar warna panel, supaya tidak menutupi candle atau garis."""
    legend = ax.legend(handles=handles, loc="upper left", fontsize=8.5, frameon=True, framealpha=0.9,
                       facecolor=colors["background"], edgecolor="none", **options)
    for text in legend.get_texts():
        text.set_color(colors["ink"])
    if legend.get_title():
        legend.get_title().set_color(colors["ink"])
    return legend


def build_figure(
    target: Target,
    series: Series,
    ticker: Ticker24h,
    fetched_at: datetime,
    indicators: Sequence[str] = DEFAULT_INDICATORS,
    candles_shown: int = DEFAULT_CANDLES_SHOWN,
    theme: str = "light",
):
    """Figure matplotlib: panel harga, lalu volume dan stochastic bila dipilih."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.ticker import FuncFormatter
    except ImportError as error:
        raise ChartError("matplotlib belum ter-install: pip install matplotlib") from error
    if theme not in THEMES:
        raise ChartError(f"Tema '{theme}' tidak dikenal (pilih dari {', '.join(THEMES)})")
    colors = THEMES[theme]

    shown = max(10, min(candles_shown, len(series.candles)))
    start = len(series.candles) - shown
    candles = series.candles[start:]
    xs = list(range(shown))
    rising = [c.close >= c.open for c in candles]
    candle_colors = [colors["up"] if up else colors["down"] for up in rising]

    panels = ["price"] + [p for p in ("volume", "stoch") if p in indicators]
    ratios = {"price": 3.2, "volume": 1.0, "stoch": 1.2}
    height = 4.8 + 1.5 * (len(panels) - 1)
    fig, axes = plt.subplots(
        len(panels), 1, sharex=True, squeeze=False,
        figsize=(FIGURE_WIDTH, height),
        gridspec_kw={"height_ratios": [ratios[p] for p in panels], "hspace": 0.08},
    )
    axes = {name: ax for name, ax in zip(panels, axes[:, 0])}
    fig.patch.set_facecolor(colors["background"])
    for ax in axes.values():
        ax.set_facecolor(colors["background"])
        ax.grid(True, color=colors["grid"], linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(colors=colors["muted"], labelsize=8, length=0)
        ax.yaxis.tick_right()
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Panel harga: sumbu tipis untuk sumbu (wick), batang untuk badan candle.
    price = axes["price"]
    lows, highs = [c.low for c in candles], [c.high for c in candles]
    price_span = (max(highs) - min(lows)) or max(highs) or 1.0
    price.vlines(xs, lows, highs, colors=candle_colors, linewidth=0.9)
    bodies = [max(abs(c.close - c.open), price_span * 0.0015) for c in candles]
    price.bar(xs, bodies, bottom=[min(c.open, c.close) for c in candles],
              width=0.62, color=candle_colors, edgecolor=candle_colors, linewidth=0.4)

    handles = []
    if "ema" in indicators:
        for values, period, key in ((series.ema_fast, EMA_FAST, "fast"), (series.ema_slow, EMA_SLOW, "slow")):
            visible = values[start:]
            last = _last(values)
            label = f"EMA {period}  {fmt(last)}" if last is not None else f"EMA {period}"
            (line,) = price.plot(xs, [v if v is not None else float("nan") for v in visible],
                                 color=colors[key], linewidth=1.6, label=label)
            handles.append(line)

    last_close = candles[-1].close
    price.axhline(last_close, color=colors["muted"], linewidth=0.8, linestyle=(0, (3, 3)))
    price.annotate(
        fmt(last_close), xy=(1.0, last_close), xycoords=("axes fraction", "data"),
        xytext=(4, 0), textcoords="offset points", va="center", ha="left", fontsize=8,
        color="#ffffff", fontweight="bold",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": candle_colors[-1], "edgecolor": "none"},
    )
    if handles:
        _legend(price, handles, colors)
    price.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt(v)))
    price.set_xlim(-1, shown + 1)
    # Ruang kosong di atas candle untuk legend, supaya legend tidak menutupi candle.
    headroom = 0.16 if handles else 0.05
    price.set_ylim(min(lows) - price_span * 0.05, max(highs) + price_span * headroom)

    if "volume" in axes:
        volume = axes["volume"]
        volume.bar(xs, [c.volume for c in candles], width=0.62, color=candle_colors, alpha=0.55, linewidth=0)
        average = [v if v is not None else float("nan") for v in series.volume_avg[start:]]
        volume.plot(xs, average, color=colors["muted"], linewidth=1.2)
        last_avg = _last(series.volume_avg)
        ratio = candles[-1].volume / last_avg if last_avg else 0.0
        volume.text(0.005, 0.94, f"Volume  {_compact(candles[-1].volume)}   rata-rata {VOLUME_AVG_PERIOD}: "
                    f"{_compact(last_avg or 0)}   ({ratio:.2f}x)", transform=volume.transAxes,
                    va="top", fontsize=8.5, color=colors["ink"],
                    bbox={"boxstyle": "square,pad=0.3", "facecolor": colors["background"], "edgecolor": "none",
                          "alpha": 0.9})
        volume.yaxis.set_major_formatter(FuncFormatter(_compact))
        volume.set_ylim(0, max(c.volume for c in candles) * 1.25)

    if "stoch" in axes:
        stoch = axes["stoch"]
        stoch.axhspan(STOCH_OVERSOLD, STOCH_OVERBOUGHT, color=colors["band"], zorder=0)
        for level in (STOCH_OVERSOLD, STOCH_OVERBOUGHT):
            stoch.axhline(level, color=colors["muted"], linewidth=0.7, linestyle=(0, (3, 3)))
        title = Line2D([], [], linestyle="none",
                       label=f"Stochastic ({STOCH_K_PERIOD}, {STOCH_K_SMOOTH}, {STOCH_D_PERIOD})")
        stoch_handles = [title]
        for values, name, key in ((series.stoch_k, "%K", "slow"), (series.stoch_d, "%D", "fast")):
            last = _last(values)
            (line,) = stoch.plot(xs, [v if v is not None else float("nan") for v in values[start:]],
                                 color=colors[key], linewidth=1.4,
                                 label=f"{name}  {last:.2f}" if last is not None else name)
            stoch_handles.append(line)
        # Satu baris legend di atas garis 100, jadi garis %K dan %D tidak tertutup.
        _legend(stoch, stoch_handles, colors, ncol=3, handlelength=1.6, columnspacing=1.4)
        stoch.set_ylim(0, 122)
        stoch.set_yticks([STOCH_OVERSOLD, 50, STOCH_OVERBOUGHT])

    # Label waktu di sumbu bawah, sekitar 8 label.
    bottom = axes[panels[-1]]
    step = max(1, shown // 8)
    ticks = list(range(step // 2, shown, step))
    bottom.set_xticks(ticks)
    bottom.set_xticklabels([_tick_label(candles[i].open_time, target.interval) for i in ticks])

    title = f"{target.symbol}   {target.interval}   Binance spot"
    subtitle = (f"Harga {fmt(last_close)} ({ticker.change_percent:+.2f}% 24 jam)   "
                f"Data {fetched_at:%Y-%m-%d %H:%M} UTC   Candle terakhir masih berjalan")
    # Jarak teks dihitung dalam inci, supaya chart satu panel pun tidak bertumpuk.
    fig.text(0.012, 1 - 0.14 / height, title, ha="left", va="top", fontsize=13, fontweight="bold",
             color=colors["ink"])
    fig.text(0.012, 1 - 0.40 / height, subtitle, ha="left", va="top", fontsize=9, color=colors["muted"])
    fig.text(0.012, 0.08 / height, "Sumber: Binance public API. Indikator menggambarkan posisi harga, "
             "bukan saran beli atau jual.", ha="left", va="bottom", fontsize=7.5, color=colors["muted"])
    fig.subplots_adjust(left=0.025, right=0.92, top=1 - 0.68 / height, bottom=0.52 / height)
    return fig


# --------------------------------------------------------------------------- #
# Use case: input -> gambar
# --------------------------------------------------------------------------- #
def make_chart(
    target: Target,
    output_dir: Path,
    indicators: Sequence[str] = DEFAULT_INDICATORS,
    candles_shown: int = DEFAULT_CANDLES_SHOWN,
    theme: str = "light",
    image_format: str = "png",
) -> dict:
    """Ambil data, gambar chart, simpan; kembalikan path dan nilai terakhir setiap indikator."""
    if image_format not in ("png", "svg"):
        raise ChartError(f"Format '{image_format}' tidak didukung (png atau svg)")
    candles = fetch_candles(target)
    minimum = EMA_SLOW + STOCH_K_PERIOD + STOCH_K_SMOOTH + STOCH_D_PERIOD
    if len(candles) < minimum:
        raise ChartError(f"{target.symbol}: hanya {len(candles)} candle, butuh minimal {minimum}")
    series = build_series(candles)
    ticker = fetch_ticker(target)
    fetched_at = datetime.now(timezone.utc)
    figure = build_figure(target, series, ticker, fetched_at, indicators, candles_shown, theme)

    output_path = output_dir / f"{chart_name(target)}.{image_format}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f"{output_path.stem}.tmp.{image_format}")
    try:
        figure.savefig(temp_path, dpi=DPI, facecolor=figure.get_facecolor())
    finally:
        import matplotlib.pyplot as plt

        plt.close(figure)
    os.replace(temp_path, output_path)  # tidak ada gambar setengah jadi

    last_avg = _last(series.volume_avg)
    return {
        "path": str(output_path),
        "symbol": target.symbol,
        "interval": target.interval,
        "source_url": target.source_url,
        "fetched_at": fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candles_shown": min(max(10, candles_shown), len(candles)),
        "indicators": list(indicators),
        "price": candles[-1].close,
        "change_24h_percent": ticker.change_percent,
        "last_close": candles[-1].close,
        "ema_fast": round(_last(series.ema_fast), 8) if "ema" in indicators else None,
        "ema_slow": round(_last(series.ema_slow), 8) if "ema" in indicators else None,
        "stoch_k": round(_last(series.stoch_k), 2) if "stoch" in indicators else None,
        "stoch_d": round(_last(series.stoch_d), 2) if "stoch" in indicators else None,
        "volume_ratio": round(candles[-1].volume / last_avg, 2) if "volume" in indicators and last_avg else None,
    }


def describe(result: dict) -> str:
    """Satu baris: isi gambar dan nilai terakhir indikatornya."""
    parts = [f"{result['symbol']} {result['interval']}: {result['candles_shown']} candle, harga {fmt(result['price'])}"]
    if result["ema_fast"] is not None:
        parts.append(f"EMA {EMA_FAST} {fmt(result['ema_fast'])} / EMA {EMA_SLOW} {fmt(result['ema_slow'])}")
    if result["volume_ratio"] is not None:
        parts.append(f"volume {result['volume_ratio']:.2f}x rata-rata")
    if result["stoch_k"] is not None:
        parts.append(f"Stoch %K {result['stoch_k']:.2f} %D {result['stoch_d']:.2f}")
    if not result["indicators"]:
        parts.append("tanpa indikator")
    return " | ".join(parts)


# --------------------------------------------------------------------------- #
# I/O & CLI
# --------------------------------------------------------------------------- #
def read_inputs(inputs: Sequence[str]) -> list[str]:
    """Setiap input bisa berupa URL, nama token / pair, atau path file berisi daftar keduanya."""
    items: list[str] = []
    for item in inputs:
        item = item.strip()
        file_path = Path(item)
        if not re.match(r"^https?://", item) and file_path.is_file():
            for line in file_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append(line)
        elif re.match(r"^https?://", item) or _TOKEN_PATTERN.match(item):
            items.append(item)
        else:
            raise ChartError(f"Bukan URL, nama token, atau file: {item}")
    return list(dict.fromkeys(items))  # buang duplikat, urutan dipertahankan


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gambar candlestick chart token crypto beserta EMA, volume, dan Stochastic."
    )
    parser.add_argument("inputs", nargs="+", help="nama token (BTC), pair (ETH/USDT), URL, dan/atau file daftar")
    parser.add_argument("-o", "--output-dir", default="charts", type=Path)
    parser.add_argument("-i", "--interval", default=DEFAULT_INTERVAL, choices=sorted(VALID_INTERVALS),
                        help=f"timeframe bila URL tidak menyebut interval (default: {DEFAULT_INTERVAL})")
    parser.add_argument("-q", "--quote", default=DEFAULT_QUOTE,
                        help=f"quote untuk nama token tanpa pair (default: {DEFAULT_QUOTE})")
    parser.add_argument("-n", "--candles", type=int, default=DEFAULT_CANDLES_SHOWN,
                        help=f"jumlah candle yang tampil, 10 sampai {CANDLE_LIMIT} (default: {DEFAULT_CANDLES_SHOWN})")
    parser.add_argument("--indicators", default=",".join(DEFAULT_INDICATORS),
                        help="ema, volume, stoch (dipisah koma), all, atau none (default: semua)")
    parser.add_argument("--theme", default="light", choices=sorted(THEMES))
    parser.add_argument("--format", dest="image_format", default="png", choices=("png", "svg"))
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    try:
        items = read_inputs(args.inputs)
        indicators = parse_indicators(args.indicators)
    except ChartError as error:
        log.error("%s", error)
        return 2
    if not items:
        log.error("Tidak ada token atau URL untuk diproses")
        return 2

    failures = 0
    for item in items:
        try:  # satu input gagal tidak menghentikan input lainnya
            target = parse_input(item, args.interval, args.quote)
            result = make_chart(target, args.output_dir, indicators, args.candles, args.theme, args.image_format)
            log.info("OK    %s -> %s", item, result["path"])
            log.info("      %s", describe(result))
        except ChartError as error:
            failures += 1
            log.error("GAGAL %s -> %s", item, error)
        except Exception as error:  # noqa: BLE001 - jaga batch tetap jalan
            failures += 1
            log.exception("GAGAL %s -> error tak terduga: %s", item, error)

    log.info("Selesai: %d sukses, %d gagal", len(items) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
