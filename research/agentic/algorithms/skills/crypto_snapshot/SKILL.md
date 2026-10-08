---
name: crypto-snapshot
description: Crypto token or pair -> the current price with EMA 12 and 21, Stochastic (5, 3, 3) and volume, computed from Binance's public candles, as one .txt file per token with a name/description header. Use when the user asks for the current price, a market snapshot, trend, momentum, EMA, stochastic or volume of a crypto token or pair (BTC, ETH, SOL, BTCUSDT, ...), gives Binance or TradingView links, or says "cek harga", "update market", "snapshot", "analisa teknikal singkat" - even with only a token name. Not for news, fundamentals or price predictions, and not investment advice. Needs network access to api.binance.com or data-api.binance.vision; standard library only.
---

# crypto-snapshot

Turns crypto tokens into a short market snapshot: the current price and 24-hour change, EMA 12 and 21, Stochastic (5, 3, 3) and volume, computed from Binance's public candle data.

No language model is used anywhere in this skill. The candles come from Binance, the indicators and the readings (bullish / bearish, overbought / oversold) are computed by `scripts/crypto_snapshot.py` with fixed thresholds, and the script also prints the one-line summary per token. A person can run it from a terminal; an agent only passes the token.

Never compute the indicators yourself or take numbers from memory or web search: run the skill. Prices go stale in minutes.

## Many tokens, or files to keep: the script

```
python scripts/crypto_snapshot.py BTC ETH SOL -o snapshots
python scripts/crypto_snapshot.py BTC/USDC ETHBTC -i 4h
python scripts/crypto_snapshot.py tokens.txt -o snapshots
python scripts/crypto_snapshot.py "https://www.tradingview.com/symbols/SOLUSDT/"
```

Inputs, mixed freely:

| Input | Becomes |
|---|---|
| `BTC`, `eth` | `BTCUSDT`, `ETHUSDT` (`-q USDC` changes the default quote) |
| `BTC/USDC`, `BTC_USDT`, `btc-usdt` | that pair |
| `BTCUSDT`, `ETHBTC` | that pair (a known quote at the end: USDT, USDC, FDUSD, BTC, ETH, BNB, ...) |
| `WBTC`, `BETH` | `WBTCUSDT`, `BETHUSDT`: a name that ends in a quote is split only when 3+ letters remain |
| Binance trade / API and TradingView symbol / chart URLs | the symbol in the URL; an `interval=` in the URL wins over `-i` |
| a file | one input per line; blank lines and `#` lines are ignored |

Timeframes for `-i`: `1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M` (default `1h`).

The log has an `OK` line and a summary line per token, then `Selesai: N sukses, N gagal`:

```
INFO OK    BTC -> snapshots\btcusdt-1h-snapshot.txt
INFO       BTCUSDT 1h: harga 82,980.01 (-1.47% 24 jam) | EMA 12/21 bearish | Stoch %K 34.42 %D 27.24 netral | volume 0.62x rata-rata
```

Exit code 0 all succeeded, 1 something failed (the others still ran), 2 no valid input. Report every `GAGAL` line with its reason.

## One token, from Python: the function

```python
from skills.crypto_snapshot.crypto_snapshot_skill import get_snapshot

record = get_snapshot("BTC")            # or get_snapshot("ETH/USDT", "4h"), or a URL
record["price"], record["ema_reading"], record["stoch_reading"], record["volume_ratio"]
record["summary"]                       # the same line the script logs
record["document"]                      # the same .txt text the script writes
```

Raises `SnapshotError` with a readable reason. The folder `research/agentic/algorithms/` must be on `sys.path`.

## One token, inside a conversation: the tool

```
get_crypto_snapshot(token="BTC")
get_crypto_snapshot(token="ETH/USDT", interval="4h")
```

The reply is the snapshot document; a failure comes back as one sentence with the reason. Give the user the price, the EMA reading, %K/%D and the volume ratio, and name the time of the data (`Waktu ambil data`).

## Output

One file per token, `<symbol>-<interval>-snapshot.txt` (`1mo` for the monthly `1M`):

```
---
name: btcusdt-1h-snapshot
description: Snapshot pasar BTCUSDT timeframe 1h berisi harga saat ini, EMA 12 dan 21, Stochastic (5, 3, 3), dan volume. Use when asked about the current price, trend, momentum, or volume of BTCUSDT.
---

# BTCUSDT - Snapshot Pasar (1h)

- Sumber URL / Sumber data / Waktu ambil data (UTC) / Candle terakhir dibuka (UTC)

## Harga                        current price, 24-hour change
## EMA (1h)                     EMA 12, EMA 21, reading (bullish / bearish / netral)
## Stochastic (5, 3, 3) (1h)    %K, %D, reading (overbought %K >= 80 / oversold %K <= 20 / netral)
## Volume                       last candle, 20-candle average, ratio, 24-hour volume
```

To change the format, change `render()` in the script, so the output stays repeatable.

## When it fails

- **HTTP 403 or "Gagal menghubungi"** - neither `api.binance.com` nor `data-api.binance.vision` is reachable from here. Say so; do not replace the numbers with estimates.
- **HTTP 400 "Invalid symbol"** - the pair is not on Binance spot. Try another quote (`USDC`) only when the user did not name one.
- **"Symbol tidak ditemukan di URL"** - not a supported URL (for example CoinGecko). Pass the token name instead.
- **"hanya N candle"** - a new listing; use a smaller timeframe.

## Reading the result

- The indicators include the candle that is still open, so they move until it closes, as on a live chart.
- Stochastic (5, 3, 3): %K over 5 candles smoothed by SMA 3, %D = SMA 3 of %K.
- "bullish", "overbought" and the rest describe where the indicators are, not advice to buy or sell.

## Changing parameters

Indicator periods, candle count, overbought/oversold levels, the default quote, API hosts and retries are constants at the top of `scripts/crypto_snapshot.py`.

Tests without network or model: `python -m pytest research/agentic/algorithms/skills/crypto_snapshot/tests -q -p no:cacheprovider`.
