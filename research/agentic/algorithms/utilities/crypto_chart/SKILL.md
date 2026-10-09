---
name: crypto-chart
description: Crypto token or pair -> a candlestick chart image (PNG or SVG) from Binance's public candles, with the indicators drawn in it - EMA 12 and 21 over the candles, volume with its 20-candle average, and Stochastic (5, 3, 3) - or candles only. Use when the user wants to see the chart, a picture, a candlestick or a graph of a crypto token or pair (BTC, ETH, SOL, BTCUSDT, ...), says "lihat chart", "gambar candle", "kirim grafiknya", or gives Binance or TradingView links and wants an image. For the numbers only, use crypto-snapshot. Not investment advice. Needs network access to api.binance.com or data-api.binance.vision and pip install matplotlib.
---

# crypto-chart

Draws a candlestick chart of a crypto pair from Binance's public candles. The indicators you choose are drawn in the picture:

| Indicator | Where |
|---|---|
| `ema` | EMA 12 and EMA 21 as lines over the candles, last values in the legend |
| `volume` | a second panel: volume bars in the candle's colour and the 20-candle average |
| `stoch` | a third panel: Stochastic (5, 3, 3) %K and %D with the 20 and 80 levels |

All three by default; `none` draws the candles only. The price panel always has the last price as a dashed line with its value on the right.

No language model is used anywhere. The indicators use the same formulas and the same 200 candles as `crypto_snapshot`, so the values in the picture are the values in the snapshot file taken at the same moment. matplotlib draws the image.

## Many tokens: the script

```
pip install matplotlib
python scripts/crypto_chart.py BTC -o charts
python scripts/crypto_chart.py BTC ETH/USDT -i 4h -n 120
python scripts/crypto_chart.py SOL --indicators ema,volume
python scripts/crypto_chart.py SOL --indicators none --theme dark --format svg
```

Inputs are read like `crypto_snapshot`: token names (`BTC`, quote `-q USDT`), pairs (`ETH/USDT`, `ETHBTC`), Binance and TradingView URLs, or a file with one per line.

| Option | Use |
|---|---|
| `-i 4h` | Timeframe: `1m 3m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d 3d 1w 1M` (default `1h`; an `interval=` in a URL wins). |
| `-n 120` | Candles in the picture, 10 to 200 (default 80). The rest are used to warm the indicators up. |
| `--indicators` | `all` (default), `none`, or a comma list of `ema`, `volume`, `stoch`. |
| `--theme dark` | Dark background; `light` is the default. |
| `--format svg` | SVG instead of PNG. |

One file per token, `<symbol>-<interval>-chart.png` (`1mo` for `1M`). The log has an `OK` line and a line with what the picture shows:

```
INFO OK    BTC -> charts/btcusdt-1h-chart.png
INFO       BTCUSDT 1h: 80 candle, harga 82,683.99 | EMA 12 83,084.83 / EMA 21 83,368.68 | volume 0.79x rata-rata | Stoch %K 26.79 %D 24.70
```

Exit code 0 all succeeded, 1 something failed (the others still ran), 2 no valid input or an unknown indicator.

## One token, from Python: the function

```python
from utilities.crypto_chart.crypto_chart_skill import draw_chart

result = draw_chart("BTC")                                  # charts/btcusdt-1h-chart.png
result = draw_chart("ETH/USDT", "4h", indicators="none")    # candles only
result["path"], result["ema_fast"], result["stoch_k"], result["summary"]
```

An indicator that is not drawn has `None`. Images go to `output_dir`, else `$CRYPTO_CHART_DIR`, else `./charts`. Raises `ChartError` with a readable reason. The folder `research/agentic/algorithms/` must be on `sys.path`.

## One token, inside a conversation: the tool

```
get_crypto_chart(token="BTC")
get_crypto_chart(token="ETH/USDT", interval="4h", indicators="none")
```

The reply gives the path of the saved image and the line of what it shows; send that file to the user. A failure comes back as one sentence with the reason: never describe a chart you did not draw.

## When it fails

- **"matplotlib belum ter-install"** - `pip install matplotlib`.
- **HTTP 400 "Invalid symbol"**, **HTTP 403 / "Gagal menghubungi"**, **"Symbol tidak ditemukan di URL"**, **"hanya N candle"** - the same causes as in `crypto_snapshot` (unknown pair, Binance not reachable, unsupported URL, new listing).
- **"Indikator tidak dikenal"** - only `ema`, `volume`, `stoch`, `all` and `none` exist.

## Changing the picture

Indicator periods, the candle count, the overbought/oversold levels, image size and DPI, and the colours of both themes are constants at the top of `scripts/crypto_chart.py`. Keep `CANDLE_LIMIT` equal to the one in `crypto_snapshot`, so both skills show the same numbers.

Tests without network or model: `python -m pytest research/agentic/algorithms/utilities/crypto_chart/tests -q -p no:cacheprovider`.
