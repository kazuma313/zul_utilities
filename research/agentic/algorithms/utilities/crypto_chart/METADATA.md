---
name: crypto-chart
description: Crypto token or pair -> a candlestick chart image (PNG or SVG) from Binance's public candles, with the indicators drawn in it - EMA 12 and 21 over the candles, volume with its 20-candle average, and Stochastic (5, 3, 3) - or candles only. Use when the user wants to see the chart, a picture, a candlestick or a graph of a crypto token or pair (BTC, ETH, SOL, BTCUSDT, ...), says "lihat chart", "gambar candle", "kirim grafiknya", or gives Binance or TradingView links and wants an image. For the numbers only, use crypto-snapshot. Not investment advice. Needs network access to api.binance.com or data-api.binance.vision and pip install matplotlib.
version: 1.0.0
requires:
  python: ">=3.9"
  pip: ["matplotlib"]
  optional:
    - langchain-core (only for the tool get_crypto_chart; draw_chart works without it)
  model: none                  # no language model anywhere; candles, indicators and drawing are code
  network: api.binance.com, data-api.binance.vision (mirror, tried second)
entry: crypto_chart_skill.py
functions:
  - draw_chart(token, interval, indicators, candles, theme, image_format, output_dir) -> {path, symbol, ema_fast, ema_slow, stoch_k, stoch_d, volume_ratio, ..., summary}
tools:
  - get_crypto_chart (crypto_chart_skill.py; None without langchain-core)
scripts:
  - scripts/crypto_chart.py (tokens, pairs, URLs or a list file -> one image per token, one line per image in the log)
env:
  CRYPTO_CHART_DIR: folder where draw_chart and the tool save images (default ./charts)
outputs: [png, svg]
related: crypto_snapshot (same inputs, same formulas and candle count, so the picture shows the snapshot's numbers)
verified: 2026-10-08 against the live Binance API - BTC 1h with all indicators and ETH 4h candles only, light and dark; tests/ cover the indicator series, the panels per indicator choice, PNG and SVG files and exit codes without network or model
---
