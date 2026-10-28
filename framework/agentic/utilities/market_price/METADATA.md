---
name: market-price
description: Gold (USD or rupiah), indices (S&P 500, IHSG), IDX stocks (BBCA, BMRI), exchange rates (USD/IDR) or any Yahoo Finance symbol -> the current price with recent price action (changes over 1 week to 1 year, SMA 20/50/200, RSI 14, 52-week range), or historical candles as CSV. Every number is computed by code from Yahoo Finance's public chart data. Use when the user asks for the current price, the trend, how the price moved over a period, or historical prices of gold, "harga emas", gold/idr, gold/usd, spx, ihsg, usd/idr, or a stock such as BBCA or BMRI - even with only a name. Not for news, fundamentals or price predictions, and not investment advice. Needs network access to query1.finance.yahoo.com; standard library only.
version: 1.0.0
requires:
  python: ">=3.9"
  pip: []                      # standard library only
  optional:
    - langchain-core (only for the tools get_market_price and get_price_history; the functions work without it)
  model: none                  # no language model anywhere; every number and reading is computed by code
  network: query1.finance.yahoo.com, query2.finance.yahoo.com (mirror, tried second)
entry: market_price_skill.py
functions:
  - get_price_action(instrument, market) -> {instrument, symbol, name, currency, unit, price, previous_close, session_change_percent, changes_percent, sma, rsi, rsi_reading, high_52w, low_52w, range_position_percent, volume_ratio, summary, document, ...}
  - get_history(instrument, range, interval, start, end, market) -> {instrument, symbol, name, currency, unit, interval, range, count, candles, summary, csv, ...}
  - price_action_text(instrument) -> str (the document, or the reason it failed as one sentence)
  - history_text(instrument, range, interval, rows) -> str (summary line and the last rows as CSV, or the reason)
tools:
  - get_market_price (market_price_skill.py; None without langchain-core)
  - get_price_history (market_price_skill.py; None without langchain-core)
scripts:
  - scripts/market_price.py (now: names -> summary line per instrument, optional .txt per instrument; history: names -> one .csv per instrument)
outputs: [txt, csv]
instruments: [gold/usd, gold/idr, gold/idr-oz, spx, ihsg, usd/idr, idx:CODE, any Yahoo Finance symbol]
verified: 2026-10-28 against the live Yahoo Finance chart endpoint from a home connection in Indonesia - gold/idr, gold/usd, spx, ihsg, idx:BBCA and idx:BMRI through now and history, the intraday limits (1m, 5m, 1h), and the error paths for a missing symbol, an interval beyond its limit and a bad name; tests/ cover indicators, names, the response format (including the unfinished last candle), retries, the cross rate, documents, files and exit codes without network or model
---
