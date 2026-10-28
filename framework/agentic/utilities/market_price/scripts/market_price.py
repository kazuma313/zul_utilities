#!/usr/bin/env python3
"""market_price.py - harga historis dan pergerakan harga terkini: emas, indeks, saham, dan kurs.

Data diambil dari endpoint chart publik Yahoo Finance, tanpa API key. Tidak ada model
bahasa yang dipakai: semua angka dan pembacaannya dihitung di sini, dan log mencetak satu
baris ringkasan per instrumen.

Dua perintah:
    now       harga terakhir dan pergerakannya: perubahan, SMA 20/50/200, RSI 14, rentang 52 minggu
    history   candle historis, disimpan sebagai CSV

Pemakaian:
    python market_price.py now gold/idr gold/usd spx ihsg idx:BBCA idx:BMRI
    python market_price.py now bbca bmri --market idx -o snapshots
    python market_price.py history gold/idr spx -r 5y -i 1wk -o prices
    python market_price.py history idx:BBCA --start 2026-01-01 --end 2026-10-27

Input yang dikenali:
    alias          gold/usd, gold/idr, gold/idr-oz, spx, ihsg, usd/idr
    saham BEI      idx:BBCA (menjadi BBCA.JK); atau bbca dengan --market idx
    simbol Yahoo   AAPL, ^GSPC, BBCA.JK, GC=F, USDIDR=X

Emas diambil dari futures COMEX bulan terdekat (GC=F), bukan harga spot. Harga emas rupiah
dihitung: harga emas (USD per troy ounce) x kurs USD/IDR, lalu dibagi 31,1035 gram per
ounce untuk satuan gram.

Hanya butuh Python 3.9+ (tanpa dependency eksternal).
Exit code: 0 = semua sukses, 1 = ada yang gagal, 2 = input tidak valid.
"""

from __future__ import annotations

import argparse
import bisect
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Sequence

# --------------------------------------------------------------------------- #
# Konfigurasi - ubah di sini, bukan di dalam fungsi
# --------------------------------------------------------------------------- #
SMA_PERIODS = (20, 50, 200)
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
VOLUME_AVG_PERIOD = 20
# Perubahan dihitung terhadap penutupan pada atau sebelum tanggal (hari terakhir - N hari).
CHANGE_PERIODS = (("1 minggu", 7), ("1 bulan", 30), ("3 bulan", 91), ("1 tahun", 365))
WEEKS_52_DAYS = 365
SNAPSHOT_RANGE = "2y"  # cukup panjang agar SMA 200 dan RSI sudah konvergen
SNAPSHOT_INTERVAL = "1d"
LAST_CANDLES = 5

DEFAULT_RANGE = "1y"
DEFAULT_INTERVAL = "1d"
VALID_RANGES = ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
VALID_INTERVALS = ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")
INTRADAY_INTERVALS = frozenset(("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"))
GRAMS_PER_TROY_OUNCE = 31.1034768

# Host dicoba berurutan; keduanya melayani data chart yang sama.
API_HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
USER_AGENT = "Mozilla/5.0 (compatible; zul-market-price/1.0)"
HTTP_TIMEOUT_SECONDS = 15
HTTP_MAX_ATTEMPTS = 3
HTTP_BACKOFF_SECONDS = 2.0
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
SOURCE_NAME = "Yahoo Finance"

log = logging.getLogger("market_price")


class MarketPriceError(Exception):
    """Error yang pesannya aman ditampilkan ke pengguna."""


# --------------------------------------------------------------------------- #
# Model data
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Instrument:
    """Yang diminta pengguna: satu simbol Yahoo, atau hasil kali dua simbol (harga x kurs)."""

    key: str
    symbol: str
    name: str = ""
    unit: str = ""
    rate_symbol: Optional[str] = None  # bila ada: harga dikalikan kurs ini
    divisor: float = 1.0  # lalu dibagi angka ini, mis. gram per troy ounce
    decimals: Optional[int] = None  # None = ditentukan dari jenis instrumen


@dataclass(frozen=True)
class Candle:
    time: datetime  # zona waktu bursa
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Series:
    instrument: Instrument
    symbol: str
    name: str
    currency: str
    unit: str
    exchange: str
    kind: str  # jenis menurut Yahoo: EQUITY, INDEX, FUTURE, CURRENCY, ...
    decimals: int
    interval: str
    candles: list
    updated: datetime  # kapan harga terakhir diperbarui di bursa
    detail: str  # simbol dan kontrak sumber, mis. "GC=F (Gold Dec 26)"

    @property
    def last(self) -> Candle:
        return self.candles[-1]


@dataclass(frozen=True)
class Snapshot:
    series: Series
    fetched_at: datetime
    previous: Candle
    session_change: float
    changes: list  # [(label, persen atau None, candle acuan atau None)]
    sma: dict  # {periode: nilai atau None}
    rsi: Optional[float]
    high_52w: float
    low_52w: float
    sessions_52w: int
    volume_ratio: Optional[float]


# --------------------------------------------------------------------------- #
# Instrumen: alias, saham BEI, dan simbol Yahoo
# --------------------------------------------------------------------------- #
ALIASES = {
    "gold/usd": Instrument("gold/usd", "GC=F", "Emas (futures COMEX)", "USD per troy ounce"),
    "gold/idr": Instrument(
        "gold/idr", "GC=F", "Emas dalam rupiah", "IDR per gram",
        rate_symbol="USDIDR=X", divisor=GRAMS_PER_TROY_OUNCE, decimals=0,
    ),
    "gold/idr-oz": Instrument(
        "gold/idr-oz", "GC=F", "Emas dalam rupiah", "IDR per troy ounce",
        rate_symbol="USDIDR=X", decimals=0,
    ),
    "spx": Instrument("spx", "^GSPC", "S&P 500", "poin indeks"),
    "ihsg": Instrument("ihsg", "^JKSE", "IHSG (Indeks Harga Saham Gabungan)", "poin indeks"),
    "usd/idr": Instrument("usd/idr", "USDIDR=X", "Kurs USD terhadap rupiah", "IDR per USD"),
}
SYNONYMS = {
    "gold": "gold/usd", "xauusd": "gold/usd", "xau/usd": "gold/usd",
    "xauidr": "gold/idr", "xau/idr": "gold/idr",
    "sp500": "spx", "jkse": "ihsg", "usdidr": "usd/idr",
}

_YAHOO_SYMBOL = re.compile(r"^[\^A-Za-z0-9.=\-]{1,20}$")
_IDX_CODE = re.compile(r"^[A-Za-z0-9]{2,8}$")
IDX_PREFIXES = ("idx:", "id:")
IDX_SUFFIX = ".JK"
MARKETS = ("idx",)


def resolve_instrument(text: str, market: Optional[str] = None) -> Instrument:
    """Teks dari pengguna -> Instrument.

    Alias (gold/idr, spx, ...) dicari lebih dulu. Lalu `idx:BBCA` menjadi BBCA.JK, dan nama
    tanpa tanda baca ikut menjadi saham BEI bila `market` adalah "idx". Selain itu teks
    dibaca sebagai simbol Yahoo apa adanya.
    """
    raw = text.strip()
    lowered = raw.lower()
    alias = SYNONYMS.get(lowered, lowered)
    if alias in ALIASES:
        return ALIASES[alias]

    prefix = next((p for p in IDX_PREFIXES if lowered.startswith(p)), None)
    code = raw[len(prefix):] if prefix else (raw if market == "idx" and re.fullmatch(r"[A-Za-z0-9]+", raw) else None)
    if code is not None:
        if not _IDX_CODE.match(code):
            raise MarketPriceError(f"Kode saham BEI tidak valid: {code} (dari {text})")
        symbol = code.upper() + IDX_SUFFIX
        return Instrument(f"idx:{code.upper()}", symbol, unit="IDR per saham", decimals=0)

    if _YAHOO_SYMBOL.match(raw):
        return Instrument(raw, raw.upper())
    raise MarketPriceError(
        f"Bukan instrumen yang dikenali: {text}. Pakai alias ({', '.join(ALIASES)}), "
        "idx:KODE untuk saham BEI (idx:BBCA), atau simbol Yahoo (AAPL, ^GSPC, BBCA.JK)."
    )


def slug(key: str) -> str:
    """Nama aman untuk file: 'gold/idr' -> 'gold-idr', '^GSPC' -> 'gspc'."""
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")


# --------------------------------------------------------------------------- #
# Indikator (fungsi murni, mudah di-test)
# --------------------------------------------------------------------------- #
def sma_last(values: Sequence[float], period: int) -> Optional[float]:
    """Simple moving average terakhir; None bila datanya kurang dari `period`."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values: Sequence[float], period: int = RSI_PERIOD) -> Optional[float]:
    """RSI Wilder terakhir; None bila datanya tidak lebih dari `period`."""
    if len(values) <= period:
        return None
    gains = losses = 0.0
    for i in range(1, period + 1):
        change = values[i] - values[i - 1]
        gains += max(change, 0.0)
        losses += max(-change, 0.0)
    avg_gain, avg_loss = gains / period, losses / period
    for i in range(period + 1, len(values)):
        change = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0.0)) / period
    if avg_loss == 0:
        # Tidak pernah turun: 100. Harga datar sama sekali: 50.
        return 100.0 if avg_gain > 0 else 50.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def pct_change(new: float, old: float) -> Optional[float]:
    return None if old == 0 else (new / old - 1) * 100


def close_on_or_before(candles: Sequence[Candle], when: datetime) -> Optional[Candle]:
    """Candle terakhir yang waktunya tidak melewati `when`; None bila semuanya lebih baru."""
    for candle in reversed(candles):
        if candle.time <= when:
            return candle
    return None


# --------------------------------------------------------------------------- #
# Akses API (retry + fallback host)
# --------------------------------------------------------------------------- #
def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _error_detail(error: urllib.error.HTTPError) -> str:
    """Alasan dari badan respons Yahoo bila ada, selain itu potongan teksnya."""
    body = error.read().decode("utf-8", "replace")
    try:
        description = json.loads(body)["chart"]["error"]["description"]
    except (ValueError, KeyError, TypeError):
        description = None
    return description or body[:200] or str(error.reason)


def fetch_json(path: str, params: dict):
    """GET ke API dengan retry + backoff, lalu pindah ke host cadangan."""
    query = urllib.parse.urlencode(params)
    last_error: Exception = MarketPriceError("Tidak ada host API yang dikonfigurasi")
    for host in API_HOSTS:
        url = f"{host}{path}?{query}"
        for attempt in range(1, HTTP_MAX_ATTEMPTS + 1):
            try:
                return _get_json(url)
            except urllib.error.HTTPError as error:
                detail = _error_detail(error)
                last_error = MarketPriceError(f"HTTP {error.code} dari {host}: {detail}")
                if error.code not in RETRYABLE_STATUS:
                    # Simbol atau parameter salah: host lain pun sama.
                    raise last_error from error
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = MarketPriceError(f"Gagal menghubungi {host}: {error}")
            log.warning("Percobaan %d/%d gagal: %s", attempt, HTTP_MAX_ATTEMPTS, last_error)
            if attempt < HTTP_MAX_ATTEMPTS:
                time.sleep(HTTP_BACKOFF_SECONDS * attempt)
    raise last_error


def parse_chart(payload: dict, symbol: str, interval: str) -> Series:
    """Respons chart Yahoo -> Series. Candle tanpa harga penutupan dibuang.

    Candle hari ini bisa datang tanpa penutupan setelah bursa tutup. Bila harga terakhir
    di meta bertanggal sama, penutupan candle itu diisi dengan harga tersebut.
    """
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise MarketPriceError(f"{symbol}: {chart['error'].get('description', 'data tidak tersedia')}")
    results = chart.get("result") or []
    if not results:
        raise MarketPriceError(f"{symbol}: tidak ada data")
    result = results[0]
    meta = result.get("meta") or {}
    zone = timezone(timedelta(seconds=meta.get("gmtoffset", 0)))
    price = meta.get("regularMarketPrice")
    updated = datetime.fromtimestamp(meta["regularMarketTime"], zone) if meta.get("regularMarketTime") else None

    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    stamps = result.get("timestamp") or []
    candles = []
    for i, stamp in enumerate(stamps):
        when = datetime.fromtimestamp(stamp, zone)
        close = quote["close"][i]
        if close is None:
            unfinished = (
                i == len(stamps) - 1 and price is not None and updated is not None
                and interval not in INTRADAY_INTERVALS and when.date() == updated.date()
            )
            if not unfinished:
                continue
            close = float(price)
        high, low = quote["high"][i], quote["low"][i]
        candles.append(
            Candle(
                time=when,
                open=float(quote["open"][i] if quote["open"][i] is not None else close),
                high=float(high if high is not None else close),
                low=float(low if low is not None else close),
                close=float(close),
                volume=float(quote["volume"][i] or 0),
            )
        )
    if not candles:
        raise MarketPriceError(f"{symbol}: tidak ada candle dengan harga penutupan")

    currency = meta.get("currency") or ""
    name = meta.get("longName") or meta.get("shortName") or symbol
    contract = meta.get("shortName") if meta.get("instrumentType") == "FUTURE" else None
    return Series(
        instrument=Instrument(symbol, symbol),
        symbol=symbol,
        name=name,
        currency=currency,
        unit=currency,
        exchange=meta.get("fullExchangeName") or meta.get("exchangeName") or "",
        kind=meta.get("instrumentType") or "",
        decimals=0 if currency == "IDR" and meta.get("instrumentType") == "EQUITY" else 2,
        interval=interval,
        candles=candles,
        updated=updated or candles[-1].time,
        detail=f"{symbol} ({contract})" if contract else symbol,
    )


def check_options(interval: str, range_: Optional[str]) -> None:
    if interval not in VALID_INTERVALS:
        raise MarketPriceError(f"Interval '{interval}' tidak didukung. Pilihan: {', '.join(VALID_INTERVALS)}")
    if range_ is not None and range_ not in VALID_RANGES:
        raise MarketPriceError(f"Rentang '{range_}' tidak didukung. Pilihan: {', '.join(VALID_RANGES)}")


def parse_day(text: str, end_of_day: bool = False) -> int:
    """Tanggal YYYY-MM-DD -> detik epoch UTC; `end_of_day` memajukannya satu hari agar tanggal akhir ikut."""
    try:
        day = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise MarketPriceError(f"Tanggal harus berbentuk YYYY-MM-DD: {text}") from error
    return int((day + timedelta(days=1 if end_of_day else 0)).timestamp())


def fetch_symbol(
    symbol: str,
    interval: str,
    range_: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    cache: Optional[dict] = None,
) -> Series:
    """Satu simbol Yahoo -> Series. `cache` dipakai bersama agar simbol yang sama tidak diambil dua kali."""
    check_options(interval, range_)
    key = (symbol, interval, range_, start, end)
    if cache is not None and key in cache:
        return cache[key]
    params = {"interval": interval, "includePrePost": "false"}
    if start or end:
        params["period1"] = parse_day(start or "1970-01-01")
        params["period2"] = parse_day(end, end_of_day=True) if end else int(time.time())
    else:
        params["range"] = range_ or DEFAULT_RANGE
    payload = fetch_json(f"/v8/finance/chart/{urllib.parse.quote(symbol)}", params)
    series = parse_chart(payload, symbol, interval)
    if cache is not None:
        cache[key] = series
    return series


# --------------------------------------------------------------------------- #
# Kurs silang: harga x kurs
# --------------------------------------------------------------------------- #
def convert_series(base: Series, rate: Series, divisor: float) -> Series:
    """Harga dikalikan kurs pada hari yang sama (atau kurs terakhir sebelumnya), lalu dibagi `divisor`.

    Candle harga tanpa kurs sebelum atau pada waktunya dibuang. Buka, tertinggi, dan
    terendah memakai penutupan kurs yang sama dengan penutupannya, jadi hanya penutupan
    yang tepat; selebihnya perkiraan.
    """
    daily = base.interval not in INTRADAY_INTERVALS

    def when(candle: Candle):
        return candle.time.date() if daily else candle.time.timestamp()

    rate_times = [when(c) for c in rate.candles]
    candles = []
    for candle in base.candles:
        i = bisect.bisect_right(rate_times, when(candle)) - 1
        if i < 0:
            continue
        factor = rate.candles[i].close / divisor
        candles.append(
            Candle(candle.time, candle.open * factor, candle.high * factor, candle.low * factor, candle.close * factor, 0.0)
        )
    if not candles:
        raise MarketPriceError(f"{base.symbol} x {rate.symbol}: tidak ada tanggal yang cocok antara harga dan kurs")
    return replace(
        base,
        symbol=f"{base.symbol} x {rate.symbol}",
        currency=rate.currency,
        exchange="",
        candles=candles,
        updated=min(base.updated, rate.updated),
        detail=f"{base.detail} x {rate.symbol} / {divisor:g}" if divisor != 1 else f"{base.detail} x {rate.symbol}",
    )


def fetch_series(
    instrument: Instrument,
    interval: str = DEFAULT_INTERVAL,
    range_: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    cache: Optional[dict] = None,
) -> Series:
    """Instrument -> Series, termasuk perhitungan kurs untuk instrumen turunan seperti gold/idr."""
    series = fetch_symbol(instrument.symbol, interval, range_, start, end, cache)
    if instrument.rate_symbol:
        rate = fetch_symbol(instrument.rate_symbol, interval, range_, start, end, cache)
        series = convert_series(series, rate, instrument.divisor)
    decimals = instrument.decimals if instrument.decimals is not None else series.decimals
    return replace(
        series,
        instrument=instrument,
        name=instrument.name or series.name,
        unit=instrument.unit or series.currency,
        decimals=decimals,
    )


# --------------------------------------------------------------------------- #
# Pergerakan harga terkini: Series harian -> Snapshot
# --------------------------------------------------------------------------- #
def build_snapshot(instrument: Instrument, cache: Optional[dict] = None) -> Snapshot:
    series = fetch_series(instrument, SNAPSHOT_INTERVAL, SNAPSHOT_RANGE, cache=cache)
    candles = series.candles
    if len(candles) < 2:
        raise MarketPriceError(f"{instrument.key}: hanya {len(candles)} candle, butuh minimal 2")
    last, previous = candles[-1], candles[-2]
    closes = [c.close for c in candles]

    changes = []
    for label, days in CHANGE_PERIODS:
        base = close_on_or_before(candles, last.time - timedelta(days=days))
        changes.append((label, pct_change(last.close, base.close) if base else None, base))
    earlier_year = next((c for c in reversed(candles) if c.time.year < last.time.year), None)
    changes.append(("Sejak awal tahun", pct_change(last.close, earlier_year.close) if earlier_year else None, earlier_year))

    window = [c for c in candles if c.time >= last.time - timedelta(days=WEEKS_52_DAYS)]
    recent_volumes = [c.volume for c in candles[-VOLUME_AVG_PERIOD - 1 : -1]]
    volume_ratio = None
    if last.volume > 0 and len(recent_volumes) == VOLUME_AVG_PERIOD and sum(recent_volumes) > 0:
        volume_ratio = last.volume / (sum(recent_volumes) / VOLUME_AVG_PERIOD)

    return Snapshot(
        series=series,
        fetched_at=datetime.now(timezone.utc),
        previous=previous,
        session_change=pct_change(last.close, previous.close) or 0.0,
        changes=changes,
        sma={period: sma_last(closes, period) for period in SMA_PERIODS},
        rsi=rsi(closes),
        high_52w=max(c.high for c in window),
        low_52w=min(c.low for c in window),
        sessions_52w=len(window),
        volume_ratio=volume_ratio,
    )


# --------------------------------------------------------------------------- #
# Rendering: Snapshot -> teks ber-frontmatter
# --------------------------------------------------------------------------- #
def fmt(value: Optional[float], decimals: int = 2) -> str:
    return "n/a" if value is None else f"{value:,.{decimals}f}"


def signed(percent: Optional[float]) -> str:
    return "n/a" if percent is None else f"{percent:+.2f}%"


def _yaml_scalar(text: str) -> str:
    """Satu baris, di-quote hanya bila perlu (string JSON adalah YAML yang valid)."""
    text = " ".join(text.split())
    needs_quote = ": " in text or " #" in text or text[:1] in "\"'[]{}>|*&!%@`#-?:,"
    return json.dumps(text, ensure_ascii=False) if needs_quote else text


def _utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _side(price: float, average: Optional[float]) -> str:
    if average is None:
        return "n/a"
    return "di atas" if price > average else "di bawah" if price < average else "sama dengan"


def rsi_reading(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    if value >= RSI_OVERBOUGHT:
        return "overbought"
    if value <= RSI_OVERSOLD:
        return "oversold"
    return "netral"


def range_position(snapshot: Snapshot) -> Optional[float]:
    """Posisi harga terakhir di rentang 52 minggu: 0 = terendah, 100 = tertinggi."""
    span = snapshot.high_52w - snapshot.low_52w
    return None if span == 0 else (snapshot.series.last.close - snapshot.low_52w) / span * 100


def trend_phrase(snapshot: Snapshot) -> str:
    """Harga terhadap SMA 50 dan SMA 200, dalam satu frasa."""
    price = snapshot.series.last.close
    mid, long_ = snapshot.sma[50], snapshot.sma[200]
    if mid is None and long_ is None:
        return "SMA n/a (data kurang)"
    sides = [(period, _side(price, snapshot.sma[period])) for period in (50, 200) if snapshot.sma[period] is not None]
    if len({side for _, side in sides}) == 1:
        periods = " dan ".join(str(period) for period, _ in sides)
        return f"harga {sides[0][1]} SMA {periods}"
    return ", ".join(f"{side} SMA {period}" for period, side in sides)


def snapshot_name(snapshot: Snapshot) -> str:
    return f"{slug(snapshot.series.instrument.key)}-snapshot"


def render(snapshot: Snapshot) -> str:
    series, last = snapshot.series, snapshot.series.last
    d = series.decimals
    description = (
        f"Pergerakan harga {series.name} ({snapshot.series.instrument.key}): harga terakhir, perubahan "
        f"1 minggu sampai 1 tahun, SMA 20/50/200, RSI 14, dan rentang 52 minggu. "
        f"Use when asked about the current price, recent price action, or trend of {series.name}."
    )
    lines = [
        "---",
        f"name: {snapshot_name(snapshot)}",
        f"description: {_yaml_scalar(description)}",
        "---",
        "",
        f"# {series.name} - Pergerakan Harga",
        "",
        f"- Instrumen: {series.detail}" + (f" di {series.exchange}" if series.exchange else ""),
        f"- Satuan: {series.unit}",
        f"- Sumber data: {SOURCE_NAME}",
        f"- Waktu ambil data (UTC): {snapshot.fetched_at:%Y-%m-%d %H:%M}",
        f"- Harga terakhir diperbarui (UTC): {_utc(series.updated)} (bisa tertunda dari bursa)",
        "",
        "## Harga",
        f"- Harga terakhir: {fmt(last.close, d)}",
        f"- Penutupan sebelumnya ({snapshot.previous.time:%Y-%m-%d}): {fmt(snapshot.previous.close, d)}",
        f"- Perubahan sesi terakhir ({last.time:%Y-%m-%d}): {signed(snapshot.session_change)}",
        "",
        "## Perubahan",
        "",
        "| Periode | Perubahan | Dibanding penutupan |",
        "|---|---|---|",
    ]
    for label, percent, base in snapshot.changes:
        lines.append(f"| {label} | {signed(percent)} | {base.time:%Y-%m-%d} ({fmt(base.close, d)}) |" if base else f"| {label} | n/a | data kurang |")
    lines += ["", "## Tren"]
    for period in SMA_PERIODS:
        average = snapshot.sma[period]
        if average is None:
            lines.append(f"- SMA {period}: n/a (hanya {len(series.candles)} sesi)")
        else:
            lines.append(f"- SMA {period}: {fmt(average, d)} (harga {_side(last.close, average)}, {signed(pct_change(last.close, average))})")
    lines += [
        f"- RSI {RSI_PERIOD}: {fmt(snapshot.rsi, 1)} ({rsi_reading(snapshot.rsi)}; "
        f"overbought >= {RSI_OVERBOUGHT:g}, oversold <= {RSI_OVERSOLD:g})",
        "",
        "## Rentang 52 minggu",
        f"- Tertinggi: {fmt(snapshot.high_52w, d)}",
        f"- Terendah: {fmt(snapshot.low_52w, d)}",
        f"- Posisi harga di rentang: {fmt(range_position(snapshot), 0)}% (0 = terendah, 100 = tertinggi)",
        f"- Jarak dari tertinggi: {signed(pct_change(last.close, snapshot.high_52w))}",
        f"- Dihitung dari {snapshot.sessions_52w} sesi",
    ]
    if snapshot.volume_ratio is not None:
        lines += [
            "",
            "## Volume",
            f"- Volume sesi terakhir: {fmt(last.volume, 0)}",
            f"- Rasio terhadap rata-rata {VOLUME_AVG_PERIOD} sesi sebelumnya: {snapshot.volume_ratio:.2f}x",
        ]
    lines += ["", f"## {LAST_CANDLES} candle terakhir (1d)", "", "| Tanggal | Buka | Tertinggi | Terendah | Tutup | Perubahan |", "|---|---|---|---|---|---|"]
    recent = series.candles[-LAST_CANDLES - 1 :]
    for before, candle in zip(recent, recent[1:]):
        lines.append(
            f"| {candle.time:%Y-%m-%d} | {fmt(candle.open, d)} | {fmt(candle.high, d)} | {fmt(candle.low, d)} "
            f"| {fmt(candle.close, d)} | {signed(pct_change(candle.close, before.close))} |"
        )
    lines += [
        "",
        "Catatan: candle terakhir dihitung termasuk sesi yang masih berjalan, sehingga nilainya",
        "dapat berubah sampai bursa tutup. Pembacaan menggambarkan posisi harga, bukan saran",
        "beli atau jual.",
        "",
    ]
    return "\n".join(lines)


def summary_line(snapshot: Snapshot) -> str:
    """Satu baris ringkasan per instrumen, dicetak di log; pengganti rangkuman manual."""
    series, last = snapshot.series, snapshot.series.last
    by_label = {label: percent for label, percent, _ in snapshot.changes}
    position = range_position(snapshot)
    return (
        f"{series.instrument.key.upper()}: {fmt(last.close, series.decimals)} {series.unit} "
        f"({signed(snapshot.session_change)} sesi terakhir) | 1 bulan {signed(by_label['1 bulan'])} | "
        f"1 tahun {signed(by_label['1 tahun'])} | {trend_phrase(snapshot)} | "
        f"RSI {RSI_PERIOD} {fmt(snapshot.rsi, 1)} {rsi_reading(snapshot.rsi)} | "
        f"posisi 52 minggu {fmt(position, 0)}%"
    )


def snapshot_dict(snapshot: Snapshot) -> dict:
    """Snapshot sebagai dict biasa (bisa langsung di-json.dumps), untuk dipakai dari kode."""
    series, last = snapshot.series, snapshot.series.last
    position = range_position(snapshot)
    return {
        "instrument": series.instrument.key,
        "symbol": series.symbol,
        "name": series.name,
        "currency": series.currency,
        "unit": series.unit,
        "source": SOURCE_NAME,
        "fetched_at": snapshot.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_updated": series.updated.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price": round(last.close, 6),
        "previous_close": round(snapshot.previous.close, 6),
        "previous_close_date": f"{snapshot.previous.time:%Y-%m-%d}",
        "session_change_percent": round(snapshot.session_change, 4),
        "changes_percent": {label: None if p is None else round(p, 4) for label, p, _ in snapshot.changes},
        "sma": {str(period): None if v is None else round(v, 6) for period, v in snapshot.sma.items()},
        "rsi": None if snapshot.rsi is None else round(snapshot.rsi, 2),
        "rsi_reading": rsi_reading(snapshot.rsi),
        "high_52w": round(snapshot.high_52w, 6),
        "low_52w": round(snapshot.low_52w, 6),
        "range_position_percent": None if position is None else round(position, 1),
        "volume_ratio": None if snapshot.volume_ratio is None else round(snapshot.volume_ratio, 2),
        "summary": summary_line(snapshot),
        "name_slug": snapshot_name(snapshot),
        "document": render(snapshot),
    }


# --------------------------------------------------------------------------- #
# Histori: Series -> CSV
# --------------------------------------------------------------------------- #
CSV_HEADER = "time,open,high,low,close,volume"


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def candle_time(series: Series, candle: Candle) -> str:
    """Tanggal untuk interval harian atau lebih, tanggal dan jam (dengan zona) untuk intraday."""
    if series.interval in INTRADAY_INTERVALS:
        return candle.time.isoformat(timespec="minutes")
    return candle.time.strftime("%Y-%m-%d")


def render_csv(series: Series) -> str:
    rows = [CSV_HEADER]
    for c in series.candles:
        rows.append(",".join([candle_time(series, c), *(_number(v) for v in (c.open, c.high, c.low, c.close)), _number(c.volume)]))
    return "\n".join(rows) + "\n"


def history_name(series: Series, range_label: str) -> str:
    return f"{slug(series.instrument.key)}-{series.interval}-{slug(range_label)}"


def history_summary(series: Series) -> str:
    first, last = series.candles[0], series.last
    d = series.decimals
    return (
        f"{series.instrument.key.upper()} {series.interval}: {len(series.candles)} candle, "
        f"{candle_time(series, first)} sampai {candle_time(series, last)}, "
        f"penutupan {fmt(first.close, d)} -> {fmt(last.close, d)} ({signed(pct_change(last.close, first.close))}) {series.unit}"
    )


def history_dict(series: Series, range_label: str) -> dict:
    """Histori sebagai dict biasa: metadata, daftar candle, ringkasan, dan teks CSV-nya."""
    return {
        "instrument": series.instrument.key,
        "symbol": series.symbol,
        "name": series.name,
        "currency": series.currency,
        "unit": series.unit,
        "source": SOURCE_NAME,
        "interval": series.interval,
        "range": range_label,
        "count": len(series.candles),
        "candles": [
            {"time": candle_time(series, c), "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume}
            for c in series.candles
        ],
        "summary": history_summary(series),
        "name_slug": history_name(series, range_label),
        "csv": render_csv(series),
    }


# --------------------------------------------------------------------------- #
# I/O file & CLI
# --------------------------------------------------------------------------- #
def write_atomic(path: Path, content: str) -> None:
    """Tulis ke file sementara lalu rename, agar tidak ada file setengah jadi."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    os.replace(temp_path, path)


def run_now(item: str, output_dir: Optional[Path], market: Optional[str], cache: dict) -> tuple[Optional[Path], Snapshot]:
    snapshot = build_snapshot(resolve_instrument(item, market), cache)
    path = None
    if output_dir is not None:
        path = output_dir / f"{snapshot_name(snapshot)}.txt"
        write_atomic(path, render(snapshot))
    return path, snapshot


def run_history(
    item: str, output_dir: Path, market: Optional[str], interval: str,
    range_: str, start: Optional[str], end: Optional[str], cache: dict,
) -> tuple[Path, Series]:
    series = fetch_series(resolve_instrument(item, market), interval, range_, start, end, cache)
    label = f"{start or 'awal'}_{end or 'kini'}" if start or end else range_
    path = output_dir / f"{history_name(series, label)}.csv"
    write_atomic(path, render_csv(series))
    return path, series


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harga historis dan pergerakan harga terkini: emas, indeks, saham, kurs.")
    commands = parser.add_subparsers(dest="command", required=True)

    def common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("inputs", nargs="+", help="alias (gold/idr, spx), idx:KODE, atau simbol Yahoo")
        sub.add_argument("-m", "--market", choices=MARKETS, help="baca nama tanpa tanda baca sebagai saham di pasar ini (idx = BEI)")
        sub.add_argument("-v", "--verbose", action="store_true")

    now = commands.add_parser("now", help="harga terakhir dan pergerakannya")
    common(now)
    now.add_argument("-o", "--output-dir", type=Path, help="tulis satu file .txt per instrumen di folder ini")

    history = commands.add_parser("history", help="candle historis sebagai CSV")
    common(history)
    history.add_argument("-o", "--output-dir", default="output", type=Path)
    history.add_argument("-r", "--range", default=DEFAULT_RANGE, choices=VALID_RANGES, help=f"rentang (default: {DEFAULT_RANGE})")
    history.add_argument("-i", "--interval", default=DEFAULT_INTERVAL, choices=VALID_INTERVALS, help=f"interval candle (default: {DEFAULT_INTERVAL})")
    history.add_argument("--start", help="tanggal awal YYYY-MM-DD; menggantikan --range")
    history.add_argument("--end", help="tanggal akhir YYYY-MM-DD, ikut dihitung (default: sekarang)")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    items = list(dict.fromkeys(item.strip() for item in args.inputs if item.strip()))
    if not items:
        log.error("Tidak ada instrumen untuk diproses")
        return 2
    try:  # input yang salah ditolak semuanya, sebelum ada permintaan jaringan
        for item in items:
            resolve_instrument(item, args.market)
        if args.command == "history":
            for day in (args.start, args.end):
                if day:
                    parse_day(day)
    except MarketPriceError as error:
        log.error("%s", error)
        return 2

    cache: dict = {}
    failures = 0
    for item in items:
        try:  # satu input gagal tidak menghentikan input lainnya
            if args.command == "now":
                path, snapshot = run_now(item, args.output_dir, args.market, cache)
                log.info("OK    %s%s", item, f" -> {path}" if path else "")
                log.info("      %s", summary_line(snapshot))
            else:
                path, series = run_history(item, args.output_dir, args.market, args.interval, args.range, args.start, args.end, cache)
                log.info("OK    %s -> %s", item, path)
                log.info("      %s", history_summary(series))
        except MarketPriceError as error:
            failures += 1
            log.error("GAGAL %s -> %s", item, error)
        except Exception as error:  # noqa: BLE001 - jaga batch tetap jalan
            failures += 1
            log.exception("GAGAL %s -> error tak terduga: %s", item, error)

    log.info("Selesai: %d sukses, %d gagal", len(items) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
