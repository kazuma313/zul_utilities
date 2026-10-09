#!/usr/bin/env python3
"""crypto_snapshot.py - token / URL list -> file .txt ber-frontmatter (format skill agent).

Untuk setiap token atau URL token (Binance / TradingView), script mengambil data candle
dari public API Binance lalu menulis satu file .txt berisi harga saat ini, EMA 12 & 21,
Stochastic (5, 3, 3), dan volume. Tidak ada model bahasa yang dipakai: semua angka dan
pembacaannya dihitung di sini, dan log mencetak satu baris ringkasan per token.

Pemakaian:
    python crypto_snapshot.py BTC ETH SOL
    python crypto_snapshot.py BTC/USDC ETHBTC -i 4h -o output
    python crypto_snapshot.py urls.txt
    python crypto_snapshot.py "https://www.binance.com/en/trade/BTC_USDT"

Input yang dikenali:
    nama token     BTC, eth (quote default USDT, ubah dengan -q USDC)
    pair           BTC/USDT, BTC_USDT, btc-usdt, BTCUSDT, ETHBTC
    URL            https://www.binance.com/en/trade/BTC_USDT
                   https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=4h
                   https://www.tradingview.com/symbols/SOLUSDT/
                   https://www.tradingview.com/chart/?symbol=BINANCE%3ABNBUSDT
    file           satu token atau URL per baris; baris kosong dan baris '#' diabaikan

Hanya butuh Python 3.9+ (tanpa dependency eksternal).
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

DEFAULT_INTERVAL = "1h"
DEFAULT_QUOTE = "USDT"  # quote untuk input berupa nama token saja, mis. "BTC" -> BTCUSDT
# Quote yang dikenali di ujung pair tanpa pemisah, mis. "ETHBTC" -> ETH / BTC.
KNOWN_QUOTES = ("FDUSD", "USDT", "USDC", "TUSD", "BUSD", "BTC", "ETH", "BNB", "EUR", "TRY", "BRL", "JPY")
VALID_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M",
}
CANDLE_LIMIT = 200  # cukup banyak agar EMA sudah konvergen

# Host dicoba berurutan; host kedua adalah mirror resmi data publik Binance.
API_HOSTS = ("https://api.binance.com", "https://data-api.binance.vision")
HTTP_TIMEOUT_SECONDS = 10
HTTP_MAX_ATTEMPTS = 3
HTTP_BACKOFF_SECONDS = 1.5
RETRYABLE_STATUS = {418, 429, 500, 502, 503, 504}

log = logging.getLogger("crypto_snapshot")


class SnapshotError(Exception):
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
    volume: float        # dalam base asset (mis. BTC)
    quote_volume: float  # dalam quote asset (mis. USDT)


@dataclass(frozen=True)
class Ticker24h:
    last_price: float
    change_percent: float
    volume: float
    quote_volume: float


@dataclass(frozen=True)
class Snapshot:
    target: Target
    fetched_at: datetime
    last_candle: Candle
    ticker: Ticker24h
    ema_fast: float
    ema_slow: float
    stoch_k: float
    stoch_d: float
    volume_avg: float


# --------------------------------------------------------------------------- #
# Indikator (fungsi murni, mudah di-test)
# --------------------------------------------------------------------------- #
def sma(values: Sequence[float], period: int) -> list[float]:
    """Simple moving average; panjang hasil = len(values) - period + 1."""
    if len(values) < period:
        raise SnapshotError(f"Data kurang untuk SMA({period}): {len(values)} nilai")
    window_sum = sum(values[:period])
    result = [window_sum / period]
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        result.append(window_sum / period)
    return result


def ema(values: Sequence[float], period: int) -> float:
    """EMA terakhir; di-seed dengan SMA dari `period` nilai pertama."""
    if len(values) < period:
        raise SnapshotError(f"Data kurang untuk EMA({period}): {len(values)} nilai")
    multiplier = 2 / (period + 1)
    current = sum(values[:period]) / period
    for value in values[period:]:
        current = (value - current) * multiplier + current
    return current


def stochastic(
    candles: Sequence[Candle], k_period: int, k_smooth: int, d_period: int
) -> tuple[float, float]:
    """Stochastic (k_period, k_smooth, d_period) -> (%K, %D) terakhir."""
    raw_k = []
    for i in range(k_period - 1, len(candles)):
        window = candles[i - k_period + 1 : i + 1]
        highest = max(c.high for c in window)
        lowest = min(c.low for c in window)
        price_range = highest - lowest
        # Range nol (harga flat) -> pakai titik tengah agar tidak divide-by-zero.
        raw_k.append(50.0 if price_range == 0 else (candles[i].close - lowest) / price_range * 100)
    k_line = sma(raw_k, k_smooth)
    d_line = sma(k_line, d_period)
    return k_line[-1], d_line[-1]


# --------------------------------------------------------------------------- #
# Parsing URL -> Target
# --------------------------------------------------------------------------- #
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


def _normalize_symbol(raw: str) -> Optional[str]:
    candidate = raw.split(":")[-1]  # buang prefix exchange, mis. "BINANCE:BTCUSDT"
    candidate = re.sub(r"[_\-/]", "", candidate).upper()
    return candidate if _SYMBOL_PATTERN.match(candidate) else None


def parse_target(url: str, default_interval: str) -> Target:
    """Ambil symbol (dan interval bila ada) dari URL."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise SnapshotError(f"Bukan URL http(s) yang valid: {url}")

    query = urllib.parse.parse_qs(parsed.query)
    path_segments = [s for s in parsed.path.split("/") if s]
    candidates = query.get("symbol", []) + path_segments[-1:]
    symbol = next((s for s in map(_normalize_symbol, candidates) if s), None)
    if symbol is None:
        raise SnapshotError(f"Symbol tidak ditemukan di URL: {url}")

    interval = query.get("interval", [default_interval])[0]
    if interval not in VALID_INTERVALS:
        raise SnapshotError(f"Interval '{interval}' tidak didukung ({url})")
    return Target(source_url=url, symbol=symbol, interval=interval)


_TOKEN_PATTERN = re.compile(r"^([A-Za-z0-9]{2,15})(?:[/_\-]([A-Za-z0-9]{2,10}))?$")


def token_to_target(text: str, default_interval: str, quote: str = DEFAULT_QUOTE) -> Target:
    """Nama token atau pair -> Target, tanpa perlu menyusun URL.

    "BTC" -> BTCUSDT, "BTC/USDC" -> BTCUSDC, "ETHBTC" -> ETHBTC. Source URL-nya adalah
    halaman trade Binance untuk pair itu, supaya file hasil tetap menyebut sumbernya.
    """
    match = _TOKEN_PATTERN.match(text.strip())
    if not match:
        raise SnapshotError(f"Bukan nama token, pair, atau URL yang dikenali: {text}")
    if default_interval not in VALID_INTERVALS:
        raise SnapshotError(f"Interval '{default_interval}' tidak didukung ({text})")
    base, pair_quote = match.group(1).upper(), (match.group(2) or "").upper()
    if not pair_quote:
        # Sisa minimal 3 huruf, supaya WBTC atau BETH tetap dibaca sebagai token, bukan W/BTC.
        known = next((q for q in KNOWN_QUOTES if base.endswith(q) and len(base) - len(q) >= 3), None)
        base, pair_quote = (base[: -len(known)], known) if known else (base, quote.upper())
    symbol = f"{base}{pair_quote}"
    if not _SYMBOL_PATTERN.match(symbol):
        raise SnapshotError(f"Symbol tidak valid: {symbol} (dari {text})")
    return Target(
        source_url=f"https://www.binance.com/en/trade/{base}_{pair_quote}",
        symbol=symbol,
        interval=default_interval,
    )


def parse_input(item: str, default_interval: str, quote: str = DEFAULT_QUOTE) -> Target:
    """URL -> parse_target, selain itu dibaca sebagai nama token atau pair."""
    if re.match(r"^https?://", item.strip()):
        return parse_target(item.strip(), default_interval)
    return token_to_target(item, default_interval, quote)


# --------------------------------------------------------------------------- #
# Akses API (retry + fallback host)
# --------------------------------------------------------------------------- #
def _get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "crypto-snapshot/1.0"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_json(path: str, params: dict):
    """GET ke API dengan retry + backoff, lalu pindah ke host cadangan."""
    query = urllib.parse.urlencode(params)
    last_error: Exception = SnapshotError("Tidak ada host API yang dikonfigurasi")
    for host in API_HOSTS:
        url = f"{host}{path}?{query}"
        for attempt in range(1, HTTP_MAX_ATTEMPTS + 1):
            try:
                return _get_json(url)
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", "replace")[:200]
                last_error = SnapshotError(f"HTTP {error.code} dari {host}: {detail}")
                if error.code == 400:  # symbol/parameter salah: host lain pun sama
                    raise last_error from error
                if error.code not in RETRYABLE_STATUS:
                    break  # mis. 403/451 (geo-block): langsung coba host berikutnya
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = SnapshotError(f"Gagal menghubungi {host}: {error}")
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
            quote_volume=float(row[7]),
        )
        for row in rows
    ]


def fetch_ticker(target: Target) -> Ticker24h:
    data = fetch_json("/api/v3/ticker/24hr", {"symbol": target.symbol})
    return Ticker24h(
        last_price=float(data["lastPrice"]),
        change_percent=float(data["priceChangePercent"]),
        volume=float(data["volume"]),
        quote_volume=float(data["quoteVolume"]),
    )


# --------------------------------------------------------------------------- #
# Use case: Target -> Snapshot
# --------------------------------------------------------------------------- #
def build_snapshot(target: Target) -> Snapshot:
    candles = fetch_candles(target)
    minimum = EMA_SLOW + STOCH_K_PERIOD + STOCH_K_SMOOTH + STOCH_D_PERIOD
    if len(candles) < minimum:
        raise SnapshotError(
            f"{target.symbol}: hanya {len(candles)} candle, butuh minimal {minimum}"
        )
    closes = [c.close for c in candles]
    stoch_k, stoch_d = stochastic(candles, STOCH_K_PERIOD, STOCH_K_SMOOTH, STOCH_D_PERIOD)
    return Snapshot(
        target=target,
        fetched_at=datetime.now(timezone.utc),
        last_candle=candles[-1],
        ticker=fetch_ticker(target),
        ema_fast=ema(closes, EMA_FAST),
        ema_slow=ema(closes, EMA_SLOW),
        stoch_k=stoch_k,
        stoch_d=stoch_d,
        volume_avg=sma([c.volume for c in candles], VOLUME_AVG_PERIOD)[-1],
    )


# --------------------------------------------------------------------------- #
# Rendering: Snapshot -> teks ber-frontmatter
# --------------------------------------------------------------------------- #
def fmt(value: float) -> str:
    """Format angka: 2 desimal untuk nilai besar, lebih presisi untuk nilai kecil."""
    if abs(value) >= 100:
        return f"{value:,.2f}"
    if abs(value) >= 1:
        return f"{value:,.4f}"
    return f"{value:.10f}".rstrip("0").rstrip(".") or "0"


def _yaml_scalar(text: str) -> str:
    """Satu baris, di-quote hanya bila perlu (string JSON adalah YAML yang valid)."""
    text = " ".join(text.split())
    needs_quote = ": " in text or " #" in text or text[:1] in "\"'[]{}>|*&!%@`#-?:,"
    return json.dumps(text, ensure_ascii=False) if needs_quote else text


def _ema_reading(snapshot: Snapshot) -> str:
    if snapshot.ema_fast > snapshot.ema_slow:
        return f"EMA {EMA_FAST} di atas EMA {EMA_SLOW} (bullish)"
    if snapshot.ema_fast < snapshot.ema_slow:
        return f"EMA {EMA_FAST} di bawah EMA {EMA_SLOW} (bearish)"
    return f"EMA {EMA_FAST} sama dengan EMA {EMA_SLOW} (netral)"


def _stoch_reading(snapshot: Snapshot) -> str:
    if snapshot.stoch_k >= STOCH_OVERBOUGHT:
        return f"overbought (%K >= {STOCH_OVERBOUGHT:g})"
    if snapshot.stoch_k <= STOCH_OVERSOLD:
        return f"oversold (%K <= {STOCH_OVERSOLD:g})"
    return "netral"


def snapshot_name(target: Target) -> str:
    # Suffix "mo" membedakan 1M (bulan) dari 1m (menit) di filesystem case-insensitive.
    interval = "1mo" if target.interval == "1M" else target.interval
    return f"{target.symbol.lower()}-{interval}-snapshot"


def render(snapshot: Snapshot) -> str:
    target, candle, ticker = snapshot.target, snapshot.last_candle, snapshot.ticker
    stoch_label = f"({STOCH_K_PERIOD}, {STOCH_K_SMOOTH}, {STOCH_D_PERIOD})"
    description = (
        f"Snapshot pasar {target.symbol} timeframe {target.interval} berisi harga saat ini, "
        f"EMA {EMA_FAST} dan {EMA_SLOW}, Stochastic {stoch_label}, dan volume. "
        f"Use when asked about the current price, trend, momentum, or volume of {target.symbol}."
    )
    volume_ratio = _volume_ratio(snapshot)
    lines = [
        "---",
        f"name: {snapshot_name(target)}",
        f"description: {_yaml_scalar(description)}",
        "---",
        "",
        f"# {target.symbol} - Snapshot Pasar ({target.interval})",
        "",
        f"- Sumber URL: {target.source_url}",
        f"- Sumber data: Binance public API",
        f"- Waktu ambil data (UTC): {snapshot.fetched_at:%Y-%m-%d %H:%M:%S}",
        f"- Candle terakhir dibuka (UTC): {candle.open_time:%Y-%m-%d %H:%M} (masih berjalan)",
        "",
        "## Harga",
        f"- Harga saat ini: {fmt(ticker.last_price)}",
        f"- Perubahan 24 jam: {ticker.change_percent:+.2f}%",
        "",
        f"## EMA ({target.interval})",
        f"- EMA {EMA_FAST}: {fmt(snapshot.ema_fast)}",
        f"- EMA {EMA_SLOW}: {fmt(snapshot.ema_slow)}",
        f"- Pembacaan: {_ema_reading(snapshot)}",
        "",
        f"## Stochastic {stoch_label} ({target.interval})",
        f"- %K: {snapshot.stoch_k:.2f}",
        f"- %D: {snapshot.stoch_d:.2f}",
        f"- Pembacaan: {_stoch_reading(snapshot)}",
        "",
        "## Volume",
        f"- Volume candle terakhir: {fmt(candle.volume)} (base) / {fmt(candle.quote_volume)} (quote)",
        f"- Rata-rata volume {VOLUME_AVG_PERIOD} candle: {fmt(snapshot.volume_avg)} (base)",
        f"- Rasio terhadap rata-rata: {volume_ratio:.2f}x",
        f"- Volume 24 jam: {fmt(ticker.volume)} (base) / {fmt(ticker.quote_volume)} (quote)",
        "",
        "Catatan: indikator dihitung termasuk candle yang masih berjalan, sehingga",
        "nilainya dapat berubah sampai candle tersebut ditutup.",
        "",
    ]
    return "\n".join(lines)


def _volume_ratio(snapshot: Snapshot) -> float:
    return snapshot.last_candle.volume / snapshot.volume_avg if snapshot.volume_avg else 0.0


def summary_line(snapshot: Snapshot) -> str:
    """Satu baris ringkasan per token, dicetak di log; pengganti rangkuman manual."""
    target, ticker = snapshot.target, snapshot.ticker
    ema_word = _ema_reading(snapshot).rsplit("(", 1)[-1].rstrip(")")
    return (
        f"{target.symbol} {target.interval}: harga {fmt(ticker.last_price)} "
        f"({ticker.change_percent:+.2f}% 24 jam) | EMA {EMA_FAST}/{EMA_SLOW} {ema_word} | "
        f"Stoch %K {snapshot.stoch_k:.2f} %D {snapshot.stoch_d:.2f} {_stoch_reading(snapshot)} | "
        f"volume {_volume_ratio(snapshot):.2f}x rata-rata"
    )


def snapshot_dict(snapshot: Snapshot) -> dict:
    """Snapshot sebagai dict biasa (bisa langsung di-json.dumps), untuk dipakai dari kode."""
    target, candle, ticker = snapshot.target, snapshot.last_candle, snapshot.ticker
    return {
        "symbol": target.symbol,
        "interval": target.interval,
        "source_url": target.source_url,
        "fetched_at": snapshot.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_candle_open": candle.open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price": ticker.last_price,
        "change_24h_percent": ticker.change_percent,
        "ema_fast": round(snapshot.ema_fast, 8),
        "ema_slow": round(snapshot.ema_slow, 8),
        "ema_reading": _ema_reading(snapshot),
        "stoch_k": round(snapshot.stoch_k, 2),
        "stoch_d": round(snapshot.stoch_d, 2),
        "stoch_reading": _stoch_reading(snapshot),
        "volume_last": candle.volume,
        "volume_avg": round(snapshot.volume_avg, 8),
        "volume_ratio": round(_volume_ratio(snapshot), 2),
        "volume_24h": ticker.volume,
        "quote_volume_24h": ticker.quote_volume,
        "summary": summary_line(snapshot),
        "name": snapshot_name(target),
        "document": render(snapshot),
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
            raise SnapshotError(f"Bukan URL, nama token, atau file: {item}")
    return list(dict.fromkeys(items))  # buang duplikat, urutan dipertahankan


read_urls = read_inputs  # nama lama, tetap bisa dipakai


def process_input(
    item: str, output_dir: Path, default_interval: str, quote: str = DEFAULT_QUOTE
) -> tuple[Path, Snapshot]:
    target = parse_input(item, default_interval, quote)
    snapshot = build_snapshot(target)
    output_path = output_dir / f"{snapshot_name(target)}.txt"
    write_atomic(output_path, render(snapshot))
    return output_path, snapshot


def process_url(url: str, output_dir: Path, default_interval: str) -> Path:
    """Nama lama: satu URL atau token -> path file hasil."""
    return process_input(url, output_dir, default_interval)[0]


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ambil harga + EMA, Stochastic, volume dari daftar token atau URL crypto."
    )
    parser.add_argument(
        "inputs", nargs="+", help="nama token (BTC), pair (ETH/USDT), URL, dan/atau file daftar"
    )
    parser.add_argument("-o", "--output-dir", default="output", type=Path)
    parser.add_argument(
        "-i", "--interval", default=DEFAULT_INTERVAL, choices=sorted(VALID_INTERVALS),
        help=f"timeframe bila URL tidak menyebut interval (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "-q", "--quote", default=DEFAULT_QUOTE,
        help=f"quote untuk nama token tanpa pair, mis. BTC -> BTC{DEFAULT_QUOTE} (default: {DEFAULT_QUOTE})",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    try:
        items = read_inputs(args.inputs)
    except SnapshotError as error:
        log.error("%s", error)
        return 2
    if not items:
        log.error("Tidak ada token atau URL untuk diproses")
        return 2

    failures = 0
    for item in items:
        try:  # satu input gagal tidak menghentikan input lainnya
            output_path, snapshot = process_input(item, args.output_dir, args.interval, args.quote)
            log.info("OK    %s -> %s", item, output_path)
            log.info("      %s", summary_line(snapshot))
        except SnapshotError as error:
            failures += 1
            log.error("GAGAL %s -> %s", item, error)
        except Exception as error:  # noqa: BLE001 - jaga batch tetap jalan
            failures += 1
            log.exception("GAGAL %s -> error tak terduga: %s", item, error)

    log.info("Selesai: %d sukses, %d gagal", len(items) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
