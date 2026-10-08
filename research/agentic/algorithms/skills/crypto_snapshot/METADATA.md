---
name: crypto-snapshot
description: Crypto token or pair -> the current price with EMA 12 and 21, Stochastic (5, 3, 3) and volume, computed from Binance's public candles, as one .txt file per token with a name/description header. Use when the user asks for the current price, a market snapshot, trend, momentum, EMA, stochastic or volume of a crypto token or pair (BTC, ETH, SOL, BTCUSDT, ...), gives Binance or TradingView links, or says "cek harga", "update market", "snapshot", "analisa teknikal singkat" - even with only a token name. Not for news, fundamentals or price predictions, and not investment advice. Needs network access to api.binance.com or data-api.binance.vision; standard library only.
version: 1.1.0
requires:
  python: ">=3.9"
  pip: []                      # standard library only
  optional:
    - langchain-core (only for the tool get_crypto_snapshot; get_snapshot works without it)
  model: none                  # no language model anywhere; every number and reading is computed by code
  network: api.binance.com, data-api.binance.vision (mirror, tried second)
entry: crypto_snapshot_skill.py
functions:
  - get_snapshot(token, interval, quote) -> {symbol, price, change_24h_percent, ema_fast, ema_slow, ema_reading, stoch_k, stoch_d, stoch_reading, volume_ratio, ..., summary, document}
tools:
  - get_crypto_snapshot (crypto_snapshot_skill.py; None without langchain-core)
scripts:
  - scripts/crypto_snapshot.py (tokens, pairs, URLs or a list file -> one .txt per token, one summary line per token in the log)
outputs: [txt]
verified: 2026-10-08 against the live Binance API from a home connection in Indonesia - BTC, ETH and SOL at 1h, BTC through get_snapshot, ETH at 4h through the tool; tests/ cover indicators, inputs, files and exit codes without network or model
---
