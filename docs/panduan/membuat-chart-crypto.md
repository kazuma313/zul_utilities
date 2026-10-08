# Membuat candlestick chart crypto

Skill `crypto_chart` menggambar candlestick chart token crypto dari candle API publik Binance, dalam bentuk PNG atau SVG. Indikator yang dipilih ikut digambar: EMA 12 dan 21 di atas candle, volume di panel kedua, dan Stochastic (5, 3, 3) di panel ketiga. Tanpa indikator, gambarnya hanya berisi candle.

Skill ini tidak memakai model AI. Rumus indikator dan jumlah candle-nya sama dengan skill `crypto_snapshot`, jadi angka di gambar sama dengan angka di [snapshot](mengambil-snapshot-crypto.md) yang diambil pada saat yang sama.

> [!NOTE]
> Chart dan indikatornya menggambarkan posisi harga, bukan saran beli atau jual.

**Sebelum mulai:** `uv` ter-install, kamu berada di root repository Zul, komputermu bisa membuka `api.binance.com` atau `data-api.binance.vision`, dan matplotlib sudah ter-install. matplotlib ikut ter-install bersama extra `analysis` atau `all` milik Zul; jika belum ada, install dengan `uv pip install matplotlib`. Skill ini ada di `research/agentic/algorithms/skills/crypto_chart/`.

## Membuat chart dari terminal

1. Pindah ke folder skill:

    ```shell
    cd research/agentic/algorithms/skills/crypto_chart
    ```

2. Jalankan skripnya dengan nama token:

    ```shell
    uv run python scripts/crypto_chart.py BTC -o charts
    ```

    Setiap token mendapat dua baris log: lokasi gambarnya, lalu isi gambar beserta nilai terakhir setiap indikator. Contoh keluaran pada 8 Oktober 2026 pukul 06.05 UTC:

    ```text
    INFO OK    BTC -> charts/btcusdt-1h-chart.png
    INFO       BTCUSDT 1h: 80 candle, harga 82,810.66 | EMA 12 83,042.65 / EMA 21 83,317.95 | volume 0.10x rata-rata | Stoch %K 40.87 %D 32.23
    INFO Selesai: 1 sukses, 0 gagal
    ```

3. Buka `charts/btcusdt-1h-chart.png`. Gambar dari perintah di atas:

    ![Candlestick chart BTCUSDT 1 jam dengan EMA 12 dan 21, panel volume, dan panel Stochastic](../assets/crypto-chart/btcusdt-1h-terang.png#only-light)
    ![Candlestick chart BTCUSDT 1 jam dengan EMA 12 dan 21, panel volume, dan panel Stochastic](../assets/crypto-chart/btcusdt-1h-gelap.png#only-dark)

Satu token menjadi satu gambar, `<symbol>-<interval>-chart.png`. Menjalankan perintah yang sama lagi menimpa gambar lama dengan data terbaru.

## Membaca gambarnya

| Bagian | Isi |
|---|---|
| Judul dan subjudul | Pair, timeframe, harga terakhir, perubahan 24 jam, dan waktu data diambil (UTC). |
| Candle | Hijau jika harga penutupan sama atau di atas harga pembukaan, merah jika di bawahnya. Badan candle adalah rentang buka sampai tutup, garis tipisnya rentang tertinggi sampai terendah. |
| Garis putus-putus dengan kotak harga di kanan | Harga terakhir. |
| Garis oranye dan biru di atas candle | EMA 12 dan EMA 21. Nilai terakhirnya tertulis di legend kiri atas. |
| Panel volume | Batang volume dengan warna candle-nya, dan garis abu-abu untuk rata-rata 20 candle. Teks kiri atas berisi volume candle terakhir, rata-ratanya, dan rasionya. |
| Panel Stochastic | %K biru dan %D oranye. Garis putus-putus di 20 dan 80 adalah batas oversold dan overbought. |

Candle paling kanan masih berjalan, jadi bentuk dan indikatornya masih berubah sampai candle itu ditutup. Pada contoh di atas, data diambil 5 menit setelah candle 1 jam dibuka, karena itu batang volume terakhirnya pendek dan rasionya hanya 0.10x.

## Memilih indikator

Opsi `--indicators` menentukan indikator yang digambar. Panel volume dan Stochastic hanya muncul jika indikatornya dipilih:

| `--indicators` | Isi gambar |
|---|---|
| `all` (bawaan) | Candle dengan EMA, panel volume, dan panel Stochastic. |
| `ema` | Candle dengan EMA, satu panel. |
| `ema,volume` | Candle dengan EMA, dan panel volume. |
| `stoch` | Candle, dan panel Stochastic. |
| `none` | Candle saja. |

Contoh chart 4 jam tanpa indikator:

```shell
uv run python scripts/crypto_chart.py ETH -i 4h --indicators none -o charts
```

```text
INFO OK    ETH -> charts/ethusdt-4h-chart.png
INFO       ETHUSDT 4h: 80 candle, harga 2,567.62 | tanpa indikator
INFO Selesai: 1 sukses, 0 gagal
```

![Candlestick chart ETHUSDT 4 jam tanpa indikator](../assets/crypto-chart/ethusdt-4h-polos-terang.png#only-light)
![Candlestick chart ETHUSDT 4 jam tanpa indikator](../assets/crypto-chart/ethusdt-4h-polos-gelap.png#only-dark)

## Opsi lain

| Opsi | Isi |
|---|---|
| `-i 4h` | Timeframe: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, atau `1M`. Bawaannya `1h`. |
| `-n 120` | Jumlah candle di gambar, 10 sampai 200. Bawaannya 80. Sisa candle dipakai untuk menghitung awal indikator. |
| `--theme dark` | Latar gelap, seperti gambar versi gelap di halaman ini. Bawaannya `light`. |
| `--format svg` | Gambar SVG, bukan PNG. |
| `-q USDC` | Quote untuk nama token tanpa pair. Bawaannya USDT. |

Bentuk input sama dengan skill snapshot: nama token (`BTC`), pair (`ETH/USDT`, `ETHBTC`), URL Binance atau TradingView, atau file berisi satu input per baris. Rinciannya ada di [Memilih token, pair, dan timeframe](mengambil-snapshot-crypto.md#memilih-token-pair-dan-timeframe).

## Membuat chart dari kode Python

Fungsi `draw_chart` menggambar dan menyimpan chart satu token, lalu mengembalikan lokasi gambar dan nilai terakhir indikatornya sebagai `dict`. Fungsi ini tidak memakai model AI maupun LangChain:

```python title="contoh pemakaian di kode"
import json

from skills.crypto_chart.crypto_chart_skill import draw_chart

result = draw_chart("SOL", "4h", indicators="ema,volume")
print(json.dumps(result, indent=2))
```

Contoh keluarannya pada 8 Oktober 2026 pukul 06.04 UTC:

```json
{
  "path": "charts/solusdt-4h-chart.png",
  "symbol": "SOLUSDT",
  "interval": "4h",
  "source_url": "https://www.binance.com/en/trade/SOL_USDT",
  "fetched_at": "2026-10-08T06:04:53Z",
  "candles_shown": 80,
  "indicators": [
    "ema",
    "volume"
  ],
  "price": 115.14,
  "change_24h_percent": -2.893,
  "last_close": 115.14,
  "ema_fast": 117.44883128,
  "ema_slow": 118.3295209,
  "stoch_k": null,
  "stoch_d": null,
  "volume_ratio": 1.02,
  "summary": "SOLUSDT 4h: 80 candle, harga 115.14 | EMA 12 117.45 / EMA 21 118.33 | volume 1.02x rata-rata"
}
```

Indikator yang tidak digambar bernilai `null` (`None` di Python), seperti Stochastic pada contoh ini. Gambar disimpan di `output_dir` jika diisi, lalu di folder dari environment variable `CRYPTO_CHART_DIR`, lalu di `./charts`. Folder `research/agentic/algorithms/` harus ada di `sys.path` supaya `skills` bisa diimpor. Jika gagal, fungsi ini melempar `ChartError` dengan alasannya.

## Memakai skill di agent

Skill ini menyediakan tool LangChain bernama `get_crypto_chart`. Tool ini hanya ada jika `langchain-core` ter-install; tanpa itu nilainya `None`, dan fungsi `draw_chart` tetap bisa dipakai.

```python title="contoh pemakaian di agent"
from skills.crypto_chart.crypto_chart_skill import get_crypto_chart

tools = [get_crypto_chart]
```

Model cukup mengisi `token`, dan jika perlu `interval` serta `indicators`. Tool menyimpan gambar, lalu membalas dengan path absolutnya dan isi gambar. Aplikasi agent-mu yang mengirim file itu ke pengguna. Contoh balasan `get_crypto_chart(token="BTC")`, dengan path yang dipendekkan:

```text
Chart image saved: .../charts/btcusdt-1h-chart.png
BTCUSDT 1h: 80 candle, harga 82,788.66 | EMA 12 83,039.26 / EMA 21 83,315.95 | volume 0.10x rata-rata | Stoch %K 40.18 %D 32.01
Data time (UTC): 2026-10-08T06:04:54Z. Show this image file to the user. The indicators describe where the price is, not advice to buy or sell.
```

Jika gagal, tool membalas dengan satu kalimat berisi alasannya, supaya model tidak mengarang isi chart:

```text
No chart for 'NOPE': HTTP 400 dari https://api.binance.com: {"code":-1121,"msg":"Invalid symbol."}. Do not draw or describe a chart yourself; report the reason.
```

## Jika skrip gagal

Kode keluar dan baris `GAGAL` sama dengan skill snapshot: `0` semua berhasil, `1` sebagian gagal tetapi token lain tetap digambar, `2` tidak ada input yang valid. Pesan yang khusus untuk skill ini:

| Pesan | Penyebab | Yang bisa dilakukan |
|---|---|---|
| `matplotlib belum ter-install` | matplotlib tidak ada di environment. | Jalankan `uv pip install matplotlib`. |
| `Indikator tidak dikenal: ...` | Nilai `--indicators` di luar daftar. | Pakai `ema`, `volume`, `stoch`, `all`, atau `none`. |

Pesan lain, seperti `Invalid symbol` atau Binance yang tidak bisa dibuka, dijelaskan di [Jika skrip gagal](mengambil-snapshot-crypto.md#jika-skrip-gagal) pada panduan snapshot.

## Mengubah tampilan

Pengaturan gambar adalah konstanta di bagian atas `scripts/crypto_chart.py`:

| Konstanta | Bawaan | Isi |
|---|---|---|
| `DEFAULT_CANDLES_SHOWN` | `80` | Jumlah candle di gambar jika `-n` tidak diisi. |
| `CANDLE_LIMIT` | `200` | Candle yang diambil dari Binance. Samakan dengan skill snapshot, supaya angkanya tetap sama. |
| `DPI`, `FIGURE_WIDTH` | `130`, `12` | Resolusi dan lebar gambar dalam inci. Bawaannya menghasilkan gambar selebar 1.560 piksel. |
| `THEMES` | `light`, `dark` | Warna latar, teks, grid, candle, dan garis indikator untuk setiap tema. |
| `EMA_FAST`, `EMA_SLOW`, `STOCH_*`, `VOLUME_AVG_PERIOD` | Sama dengan skill snapshot | Periode indikator. |

Test skill ini berjalan tanpa jaringan dan tanpa model. Salah satunya memastikan nilai indikator di gambar sama dengan nilai di skill snapshot:

```shell
uv run pytest research/agentic/algorithms/skills/crypto_chart/tests -q -p no:cacheprovider
```

## Halaman terkait

- [Mengambil snapshot harga crypto](mengambil-snapshot-crypto.md) untuk angka yang sama dalam bentuk file teks.
