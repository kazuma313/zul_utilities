---
name: market-price
description: Gold (USD or rupiah), indices (S&P 500, IHSG), IDX stocks (BBCA, BMRI), exchange rates (USD/IDR) or any Yahoo Finance symbol -> the current price with recent price action (changes over 1 week to 1 year, SMA 20/50/200, RSI 14, 52-week range), or historical candles as CSV. Every number is computed by code from Yahoo Finance's public chart data. Use when the user asks for the current price, the trend, how the price moved over a period, or historical prices of gold, "harga emas", "emas per gram", gold/idr, gold/usd, spx, ihsg, usd/idr, a stock such as BBCA or BMRI, or says "cek harga", "price action", "data historis" - even with only a name. Not for news, fundamentals or price predictions, and not investment advice. Needs network access to query1.finance.yahoo.com; standard library only.
---

# market-price

Turns an instrument name into two things: the current price with its recent price action, or the historical candles as a CSV file.

No language model is used anywhere in this skill. The candles come from Yahoo Finance's public chart endpoint, the figures and the readings (above or below an average, overbought, oversold) are computed by `scripts/market_price.py` with fixed thresholds, and the script also prints the one-line summary per instrument. A person can run it from a terminal; an agent only passes the instrument.

Never compute the figures yourself or take prices from memory or web search: run the skill. Prices go stale in minutes.

## Names the skill understands

| Input | Instrument | Unit |
|---|---|---|
| `gold/usd` | gold futures, nearest COMEX month (`GC=F`), not the spot price | USD per troy ounce |
| `gold/idr` | gold in rupiah: `GC=F` x `USDIDR=X` / 31.1035 | IDR per gram |
| `gold/idr-oz` | the same without the division by grams | IDR per troy ounce |
| `spx` | S&P 500 (`^GSPC`) | index points |
| `ihsg` | IHSG, the Jakarta Composite (`^JKSE`) | index points |
| `usd/idr` | dollar rate (`USDIDR=X`) | IDR per USD |
| `idx:BBCA`, `idx:BMRI` | an IDX stock: `idx:` plus the code becomes `BBCA.JK` | IDR per share |
| `AAPL`, `^GSPC`, `BBCA.JK` | any Yahoo Finance symbol as it is | the symbol's currency |

Synonyms: `gold`, `xauusd`, `xau/usd` (gold/usd), `xauidr`, `xau/idr` (gold/idr), `sp500` (spx), `jkse` (ihsg), `usdidr` (usd/idr). With `--market idx`, a bare name such as `bbca` is read as an IDX stock.

Gold in rupiah is the international price converted at the dollar rate, not the retail price of a gold dealer (no spread, premium or tax). Say so when the user compares it with a shop price.

## Current price and price action: `now`

```
python scripts/market_price.py now gold/idr gold/usd spx ihsg idx:BBCA idx:BMRI
python scripts/market_price.py now bbca bmri --market idx -o snapshots
```

The log has an `OK` line and a summary line per instrument, then `Selesai: N sukses, N gagal`:

```
INFO OK    gold/idr
INFO       GOLD/IDR: 2,359,446 IDR per gram (+0.50% sesi terakhir) | 1 bulan -3.28% | 1 tahun +10.00% | harga di bawah SMA 50 dan 200 | RSI 14 41.6 netral | posisi 52 minggu 34%
```

With `-o DIR` it also writes one `<name>-snapshot.txt` per instrument (a `name`/`description` header, then Harga, Perubahan, Tren, Rentang 52 minggu, Volume and the last 5 candles).

## Historical candles: `history`

```
python scripts/market_price.py history gold/idr spx -r 5y -i 1wk -o prices
python scripts/market_price.py history idx:BBCA --start 2026-01-01 --end 2026-10-27
```

Writes `<name>-<interval>-<range>.csv` (or `...-<start>-<end>.csv`) with the columns `time,open,high,low,close,volume`: `time` is a date for daily and longer intervals, and a date-time with the exchange's offset for intraday ones.

| Option | Values |
|---|---|
| `-r` / `--range` | `1d 5d 1mo 3mo 6mo 1y 2y 5y 10y ytd max` (default `1y`) |
| `-i` / `--interval` | `1m 2m 5m 15m 30m 60m 90m 1h 1d 5d 1wk 1mo 3mo` (default `1d`) |
| `--start`, `--end` | `YYYY-MM-DD`, the end day included; they replace `--range` |

Yahoo limits intraday data: `1m` only about 8 days per request, `2m 5m 15m 30m 90m` the last 60 days, `60m` and `1h` up to 2 years. A request beyond the limit fails with Yahoo's own message.

Exit code 0 all succeeded, 1 something failed (the others still ran), 2 invalid input. Report every `GAGAL` line with its reason.

## One instrument, from Python: the functions

```python
from utilities.market_price.market_price_skill import get_price_action, get_history

now = get_price_action("gold/idr")       # or "spx", "idx:BBCA", "bbca" with market="idx", "AAPL"
now["price"], now["session_change_percent"], now["rsi"], now["range_position_percent"]
now["summary"]                           # the same line the script logs
now["document"]                          # the same .txt text the script writes

past = get_history("idx:BBCA", range="1y", interval="1d")   # or start="2026-01-01", end="2026-10-27"
past["summary"], past["candles"][-1], past["csv"]
```

Both raise `MarketPriceError` with a readable reason. The folder `framework/agentic/` must be on `sys.path`.

## One instrument, inside a conversation: the tools

```
get_market_price(instrument="gold/idr")
get_price_history(instrument="spx", range="6mo", interval="1d")
```

`get_market_price` replies with the price action document, and `get_price_history` with a summary line and the last 20 candles as CSV. A failure comes back as one sentence with the reason. Give the user the price, the change, the trend reading and the RSI, and name the time of the data (`Harga terakhir diperbarui`).

## Reading the result

- Changes compare the last close with the close on or before the date that many days earlier (7, 30, 91 and 365 days; year to date uses the last close of the previous year). A figure is `n/a` when the history is too short.
- The last candle includes the session that is still running, so figures move until the market closes. After the close, Yahoo sometimes sends today's candle without a close; the script then uses the latest price.
- Prices can be delayed from the exchange. For `gold/idr` the time shown is the older of the gold price and the rate.
- RSI 14 (Wilder): overbought at 70 or more, oversold at 30 or less. The 52-week position is 0 at the lowest and 100 at the highest price of the last 365 days.
- `close` is as Yahoo sends it, not adjusted for dividends. Long-term returns of a stock that pays dividends are therefore lower than its total return.
- In `gold/idr` candles only the close is exact. Open, high and low use the rate of the close, so they are estimates.
- Readings describe where the price is. They are not advice to buy or sell.

## When it fails

- **"HTTP 404 ... No data found, symbol may be delisted"** - the symbol does not exist at Yahoo. For an Indonesian stock write `idx:CODE`.
- **"HTTP 422 ... data not available"** - the interval is not allowed for that range (see the limits above). Use a longer interval or a shorter range.
- **"HTTP 429" or "Gagal menghubungi"** - Yahoo is limiting requests or the network is blocked. The script retries three times on both hosts first. Say so; do not replace the numbers with estimates.
- **"Bukan instrumen yang dikenali"** - the name is not an alias, `idx:CODE` or a Yahoo symbol.
- **"tidak ada tanggal yang cocok antara harga dan kurs"** - gold and the rate share no date in the period asked.
- **"hanya N candle"** - a new listing; use `history` instead of `now`.

The Yahoo endpoint is public but unofficial: it can change or limit requests without notice.
