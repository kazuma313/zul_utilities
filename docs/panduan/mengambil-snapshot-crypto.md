# Mengambil snapshot harga crypto

Utility `crypto_snapshot` mengambil harga token crypto saat ini beserta EMA 12 dan 21, Stochastic (5, 3, 3), dan volume dari API publik Binance. Hasilnya satu file `.txt` per token dan satu baris ringkasan per token di terminal.

Utility ini tidak memakai model AI. Semua angka dan pembacaannya dihitung oleh kode, jadi utility ini bisa dipakai langsung dari terminal atau dari kode Python tanpa agent.

> [!NOTE]
> Pembacaan seperti `bullish` atau `overbought` hanya menggambarkan posisi indikator, bukan saran beli atau jual.

**Sebelum mulai:** `uv` ter-install, kamu berada di root repository Zul, dan komputermu bisa membuka `api.binance.com` atau `data-api.binance.vision`. Utility ini ada di `research/agentic/algorithms/utilities/crypto_snapshot/`. Tidak ada package yang perlu di-install, karena skripnya hanya memakai standard library Python.

## Mengambil snapshot dari terminal

1. Pindah ke folder utility:

    ```shell
    cd research/agentic/algorithms/utilities/crypto_snapshot
    ```

2. Jalankan skripnya dengan nama token:

    ```shell
    uv run python scripts/crypto_snapshot.py BTC ETH SOL -o snapshots
    ```

    Setiap token mendapat dua baris log: lokasi file hasilnya, lalu ringkasannya. Contoh keluaran pada 8 Oktober 2026 pukul 05.43 UTC:

    ```text
    INFO OK    BTC -> snapshots/btcusdt-1h-snapshot.txt
    INFO       BTCUSDT 1h: harga 82,932.00 (-1.54% 24 jam) | EMA 12/21 bearish | Stoch %K 33.18 %D 26.83 netral | volume 0.64x rata-rata
    INFO OK    ETH -> snapshots/ethusdt-1h-snapshot.txt
    INFO       ETHUSDT 1h: harga 2,571.27 (-1.74% 24 jam) | EMA 12/21 bearish | Stoch %K 35.52 %D 39.07 netral | volume 0.55x rata-rata
    INFO OK    SOL -> snapshots/solusdt-1h-snapshot.txt
    INFO       SOLUSDT 1h: harga 115.44 (-2.71% 24 jam) | EMA 12/21 bearish | Stoch %K 26.25 %D 35.34 netral | volume 0.74x rata-rata
    INFO Selesai: 3 sukses, 0 gagal
    ```

3. Buka file di folder `snapshots`. Satu token menjadi satu file `.txt`.

Menjalankan perintah yang sama lagi menimpa file lama dengan data terbaru.

## Membaca baris ringkasan

Setiap bagian baris ringkasan berarti:

| Bagian | Arti |
|---|---|
| `harga 82,932.00 (-1.54% 24 jam)` | Harga terakhir, dan perubahannya dalam 24 jam. |
| `EMA 12/21 bearish` | EMA 12 di bawah EMA 21. `bullish` jika di atas, `netral` jika sama. |
| `Stoch %K 33.18 %D 26.83 netral` | `overbought` jika %K 80 atau lebih, `oversold` jika %K 20 atau kurang, selain itu `netral`. |
| `volume 0.64x rata-rata` | Volume candle terakhir dibanding rata-rata 20 candle. Di bawah 1 berarti lebih sepi dari biasanya. |

## Membaca file hasilnya

Setiap file dimulai dengan header `name` dan `description`, lalu empat bagian: harga, EMA, Stochastic, dan volume.

```text title="snapshots/btcusdt-1h-snapshot.txt"
---
name: btcusdt-1h-snapshot
description: Snapshot pasar BTCUSDT timeframe 1h berisi harga saat ini, EMA 12 dan 21, Stochastic (5, 3, 3), dan volume. Use when asked about the current price, trend, momentum, or volume of BTCUSDT.
---

# BTCUSDT - Snapshot Pasar (1h)

- Sumber URL: https://www.binance.com/en/trade/BTC_USDT
- Sumber data: Binance public API
- Waktu ambil data (UTC): 2026-10-08 05:43:56
- Candle terakhir dibuka (UTC): 2026-10-08 05:00 (masih berjalan)

## Harga
- Harga saat ini: 82,932.00
- Perubahan 24 jam: -1.54%

## EMA (1h)
- EMA 12: 83,122.98
- EMA 21: 83,391.23
- Pembacaan: EMA 12 di bawah EMA 21 (bearish)

## Stochastic (5, 3, 3) (1h)
- %K: 33.18
- %D: 26.83
- Pembacaan: netral

## Volume
- Volume candle terakhir: 462.25 (base) / 38,289,565.24 (quote)
- Rata-rata volume 20 candle: 721.20 (base)
- Rasio terhadap rata-rata: 0.64x
- Volume 24 jam: 20,489.69 (base) / 1,710,057,296.99 (quote)

Catatan: indikator dihitung termasuk candle yang masih berjalan, sehingga
nilainya dapat berubah sampai candle tersebut ditutup.
```

Beberapa hal tentang isinya:

- **Base dan quote.** Volume `base` dihitung dalam token-nya, di sini BTC. Volume `quote` dihitung dalam mata uang pasangannya, di sini USDT.
- **Candle terakhir masih berjalan.** Indikator ikut menghitung candle itu, jadi nilainya masih bisa bergeser sampai candle ditutup, sama seperti chart live.
- **Stochastic (5, 3, 3)** berarti %K dihitung dari 5 candle lalu dihaluskan dengan rata-rata 3 nilai, dan %D adalah rata-rata 3 nilai %K.

## Memilih token, pair, dan timeframe

Nama token, pair, dan URL bisa dicampur dalam satu perintah:

| Input | Dibaca sebagai |
|---|---|
| `BTC`, `eth` | `BTCUSDT`, `ETHUSDT`. Quote bawaannya USDT. |
| `BTC/USDC`, `BTC_USDT`, `btc-usdt` | Pair itu. |
| `BTCUSDT`, `ETHBTC` | Pair itu, karena diakhiri quote yang dikenal: USDT, USDC, FDUSD, BTC, ETH, BNB, dan lainnya. |
| `https://www.binance.com/en/trade/BTC_USDT` | Symbol di URL. |
| `https://www.tradingview.com/symbols/SOLUSDT/` | Symbol di URL. |
| `https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=4h` | Symbol dan timeframe di URL. Timeframe di URL mengalahkan `-i`. |

Contohnya, pair dengan USDC dan BTC pada timeframe 4 jam:

```shell
uv run python scripts/crypto_snapshot.py BTC/USDC ETHBTC -i 4h -o snapshots
```

Timeframe yang bisa dipakai di `-i`: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, dan `1M` (bulanan). Bawaannya `1h`. Untuk mengganti quote bawaan dari nama token saja, tambahkan `-q`, misalnya `-q USDC` membuat `BTC` dibaca sebagai `BTCUSDC`.

Untuk daftar yang dipakai berulang, tulis satu input per baris di file teks. Baris kosong dan baris yang diawali `#` diabaikan:

```text title="tokens.txt"
# daftar pagi
BTC
ETH/USDT
https://www.tradingview.com/symbols/SOLUSDT/
```

```shell
uv run python scripts/crypto_snapshot.py tokens.txt -o snapshots
```

> [!NOTE]
> Nama token yang diakhiri nama quote, seperti `WBTC` atau `BETH`, tetap dibaca sebagai token (`WBTCUSDT`, `BETHUSDT`) jika sisa namanya kurang dari tiga huruf. Untuk token lain yang namanya mirip pair, tulis pair lengkapnya dengan garis miring, misalnya `WBTC/USDT`.

## Mengambil snapshot dari kode Python

Fungsi `get_snapshot` mengembalikan snapshot satu token sebagai `dict` biasa. Fungsi ini tidak memakai model AI maupun LangChain:

```python title="contoh pemakaian di kode"
import json

from utilities.crypto_snapshot.crypto_snapshot_skill import get_snapshot

record = get_snapshot("BTC")          # juga "ETH/USDT", get_snapshot("SOL", "4h"), atau URL
record.pop("document")                # teks file .txt, sama dengan hasil skrip
print(json.dumps(record, indent=2))
```

Contoh keluarannya pada 8 Oktober 2026 pukul 05.43 UTC:

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "source_url": "https://www.binance.com/en/trade/BTC_USDT",
  "fetched_at": "2026-10-08T05:43:58Z",
  "last_candle_open": "2026-10-08T05:00:00Z",
  "price": 82928.01,
  "change_24h_percent": -1.525,
  "ema_fast": 83122.67312567,
  "ema_slow": 83391.04438094,
  "ema_reading": "EMA 12 di bawah EMA 21 (bearish)",
  "stoch_k": 33.13,
  "stoch_d": 26.81,
  "stoch_reading": "netral",
  "volume_last": 462.32798,
  "volume_avg": 721.208699,
  "volume_ratio": 0.64,
  "volume_24h": 20487.45828,
  "quote_volume_24h": 1709869066.3114681,
  "summary": "BTCUSDT 1h: harga 82,928.01 (-1.52% 24 jam) | EMA 12/21 bearish | Stoch %K 33.13 %D 26.81 netral | volume 0.64x rata-rata",
  "name": "btcusdt-1h-snapshot"
}
```

`summary` sama dengan baris ringkasan di log skrip. `document` berisi teks file `.txt` yang sama dengan hasil skrip. Folder `research/agentic/algorithms/` harus ada di `sys.path` supaya `utilities` bisa diimpor. Jika gagal, fungsi ini melempar `SnapshotError` dengan alasannya, misalnya symbol yang tidak ada di Binance.

## Memakai utility di agent

Utility ini menyediakan tool LangChain bernama `get_crypto_snapshot`. Tool ini hanya ada jika `langchain-core` ter-install; tanpa itu nilainya `None`, dan fungsi `get_snapshot` tetap bisa dipakai.

```python title="contoh pemakaian di agent"
from utilities.crypto_snapshot.crypto_snapshot_skill import get_crypto_snapshot

tools = [get_crypto_snapshot]
```

Model cukup mengisi `token`, dan `interval` jika pengguna menyebut timeframe. Contoh panggilan `get_crypto_snapshot(token="ETH/USDT", interval="4h")` membalas dengan isi file snapshot:

```text
---
name: ethusdt-4h-snapshot
description: Snapshot pasar ETHUSDT timeframe 4h berisi harga saat ini, EMA 12 dan 21, Stochastic (5, 3, 3), dan volume. Use when asked about the current price, trend, momentum, or volume of ETHUSDT.
---

# ETHUSDT - Snapshot Pasar (4h)

- Sumber URL: https://www.binance.com/en/trade/ETH_USDT
- Sumber data: Binance public API
- Waktu ambil data (UTC): 2026-10-08 05:43:59
- Candle terakhir dibuka (UTC): 2026-10-08 04:00 (masih berjalan)

## Harga
- Harga saat ini: 2,570.86
- Perubahan 24 jam: -1.75%

## EMA (4h)
- EMA 12: 2,610.23
- EMA 21: 2,636.73
- Pembacaan: EMA 12 di bawah EMA 21 (bearish)

## Stochastic (5, 3, 3) (4h)
- %K: 46.97
- %D: 34.50
- Pembacaan: netral

## Volume
- Volume candle terakhir: 26,117.43 (base) / 66,962,703.76 (quote)
- Rata-rata volume 20 candle: 50,090.93 (base)
- Rasio terhadap rata-rata: 0.52x
- Volume 24 jam: 352,727.64 (base) / 909,843,615.29 (quote)

Catatan: indikator dihitung termasuk candle yang masih berjalan, sehingga
nilainya dapat berubah sampai candle tersebut ditutup.
```

Jika gagal, tool membalas dengan satu kalimat berisi alasannya, supaya model melaporkannya dan tidak mengarang angka. Contoh untuk token yang tidak ada di Binance:

```text
No snapshot for 'NOPE': HTTP 400 dari https://api.binance.com: {"code":-1121,"msg":"Invalid symbol."}. Do not estimate prices or indicators yourself; report the reason to the user.
```

## Jika skrip gagal

Token yang gagal tidak menghentikan token lain. Kode keluar skrip menunjukkan hasil keseluruhan:

| Kode keluar | Arti |
|---|---|
| `0` | Semua token berhasil. |
| `1` | Sebagian gagal. Token lain tetap diproses. |
| `2` | Tidak ada input yang valid, misalnya file daftar kosong. |

Token yang gagal tampil sebagai baris `GAGAL` beserta alasannya:

```text
ERROR GAGAL NOPE -> HTTP 400 dari https://api.binance.com: {"code":-1121,"msg":"Invalid symbol."}
INFO Selesai: 0 sukses, 1 gagal
```

| Pesan | Penyebab | Yang bisa dilakukan |
|---|---|---|
| `HTTP 400 ... Invalid symbol` | Pair tidak ada di Binance spot, atau penulisannya salah. | Periksa nama token, atau coba quote lain seperti `USDC`. |
| `HTTP 403` atau `Gagal menghubungi` | `api.binance.com` dan `data-api.binance.vision` tidak bisa dibuka dari jaringan ini. | Jalankan dari jaringan lain, atau izinkan kedua domain itu. |
| `Symbol tidak ditemukan di URL` | URL bukan dari Binance atau TradingView. | Tulis nama token-nya saja, misalnya `BTC`. |
| `hanya N candle, butuh minimal 32` | Token baru listing, datanya belum cukup. | Pakai timeframe yang lebih kecil, misalnya `-i 15m`. |

## Mengubah parameter

Periode indikator dan pengaturan lain adalah konstanta di bagian atas `scripts/crypto_snapshot.py`:

| Konstanta | Bawaan | Isi |
|---|---|---|
| `EMA_FAST`, `EMA_SLOW` | `12`, `21` | Periode kedua EMA. |
| `STOCH_K_PERIOD`, `STOCH_K_SMOOTH`, `STOCH_D_PERIOD` | `5`, `3`, `3` | Periode Stochastic. |
| `STOCH_OVERBOUGHT`, `STOCH_OVERSOLD` | `80`, `20` | Batas pembacaan Stochastic. |
| `VOLUME_AVG_PERIOD` | `20` | Jumlah candle untuk rata-rata volume. |
| `CANDLE_LIMIT` | `200` | Jumlah candle yang diambil dari Binance. |
| `DEFAULT_QUOTE` | `USDT` | Quote untuk input berupa nama token saja. |
| `API_HOSTS` | `api.binance.com`, `data-api.binance.vision` | Host yang dicoba berurutan. |

Test utility ini berjalan tanpa jaringan dan tanpa model:

```shell
uv run pytest research/agentic/algorithms/utilities/crypto_snapshot/tests -q -p no:cacheprovider
```

## Halaman terkait

- [Membuat candlestick chart crypto](membuat-chart-crypto.md) untuk melihat candle dan indikator yang sama dalam bentuk gambar.
- [Mengambil transcript YouTube](mengambil-transcript-youtube.md), utility lain yang juga berjalan tanpa model AI.
- [Menambah tool](menambah-tool.md) untuk memasukkan tool seperti `get_crypto_snapshot` ke agent di proyek hasil `zul build hexa`.
