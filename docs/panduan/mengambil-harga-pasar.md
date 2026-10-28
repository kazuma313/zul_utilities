# Mengambil harga pasar: emas, indeks, dan saham

Utility `market_price` mengambil dua hal dari data chart publik Yahoo Finance: harga terkini beserta pergerakannya (perubahan, rata-rata bergerak, RSI, dan rentang 52 minggu), dan harga historis dalam bentuk CSV. Contoh di halaman ini memakai emas dalam dolar dan rupiah, S&P 500, IHSG, BBCA, dan BMRI.

Utility ini tidak memakai model AI. Semua angka dan pembacaannya dihitung oleh kode, jadi utility ini bisa dipakai langsung dari terminal atau dari kode Python tanpa agent.

> [!NOTE]
> Pembacaan seperti `overbought` atau `harga di bawah SMA 200` hanya menggambarkan posisi harga, bukan saran beli atau jual.

**Sebelum mulai:** `uv` ter-install, kamu berada di root repository Zul, dan komputermu bisa membuka `query1.finance.yahoo.com`. Utility ini ada di `framework/agentic/utilities/market_price/` dan tidak ikut paket yang di-install lewat `pip install zul`. Tidak ada package yang perlu di-install, karena skripnya hanya memakai standard library Python.

## Nama instrumen

Setiap perintah menerima satu atau beberapa nama. Nama yang dikenali:

| Input | Instrumen | Satuan |
|---|---|---|
| `gold/usd` | Emas futures COMEX bulan terdekat (`GC=F`), bukan harga spot | USD per troy ounce |
| `gold/idr` | Emas dalam rupiah: `GC=F` × `USDIDR=X` ÷ 31,1035 | IDR per gram |
| `gold/idr-oz` | Sama dengan `gold/idr`, tanpa pembagian gram | IDR per troy ounce |
| `spx` | S&P 500 (`^GSPC`) | poin indeks |
| `ihsg` | IHSG, Indeks Harga Saham Gabungan (`^JKSE`) | poin indeks |
| `usd/idr` | Kurs dolar terhadap rupiah (`USDIDR=X`) | IDR per USD |
| `idx:BBCA`, `idx:BMRI` | Saham di Bursa Efek Indonesia: `idx:` ditambah kodenya menjadi `BBCA.JK` | IDR per saham |
| `AAPL`, `^GSPC`, `BBCA.JK` | Simbol Yahoo Finance apa adanya | mata uang simbol itu |

Dengan opsi `--market idx`, nama tanpa tanda baca seperti `bbca` dibaca sebagai saham BEI. Singkatan lain yang dikenali: `gold`, `xauusd`, dan `xau/usd` untuk `gold/usd`, `xauidr` dan `xau/idr` untuk `gold/idr`, `sp500` untuk `spx`, `jkse` untuk `ihsg`, dan `usdidr` untuk `usd/idr`.

> [!WARNING]
> `gold/idr` adalah harga internasional yang dikonversi dengan kurs dolar, bukan harga jual toko emas atau Antam. Selisihnya mencakup spread, premi, dan pajak. Jangan membandingkan angkanya langsung dengan harga di toko.

## Mengambil harga terkini dan pergerakannya

1. Pindah ke folder utility:

    ```shell
    cd framework/agentic/utilities/market_price
    ```

2. Jalankan perintah `now` dengan nama instrumen dan folder untuk file hasilnya:

    ```shell
    uv run python scripts/market_price.py now gold/idr gold/usd spx ihsg idx:BBCA idx:BMRI -o snapshots
    ```

    Setiap instrumen mendapat dua baris log: lokasi file hasilnya, lalu ringkasannya. Contoh keluaran pada 27 Oktober 2026 pukul 18.33 UTC:

    ```text
    INFO OK    gold/idr -> snapshots/gold-idr-snapshot.txt
    INFO       GOLD/IDR: 2,358,171 IDR per gram (+0.45% sesi terakhir) | 1 bulan -3.34% | 1 tahun +9.94% | harga di bawah SMA 50 dan 200 | RSI 14 41.3 netral | posisi 52 minggu 34%
    INFO OK    gold/usd -> snapshots/gold-usd-snapshot.txt
    INFO       GOLD/USD: 4,069.20 USD per troy ounce (+0.76% sesi terakhir) | 1 bulan -5.83% | 1 tahun +1.23% | harga di bawah SMA 50 dan 200 | RSI 14 38.6 netral | posisi 52 minggu 10%
    INFO OK    spx -> snapshots/spx-snapshot.txt
    INFO       SPX: 7,716.95 poin indeks (+0.52% sesi terakhir) | 1 bulan -0.34% | 1 tahun +12.24% | harga di atas SMA 50 dan 200 | RSI 14 50.8 netral | posisi 52 minggu 92%
    INFO OK    ihsg -> snapshots/ihsg-snapshot.txt
    INFO       IHSG: 5,266.13 poin indeks (-1.99% sesi terakhir) | 1 bulan -15.63% | 1 tahun -35.12% | harga di bawah SMA 50 dan 200 | RSI 14 31.6 netral | posisi 52 minggu 8%
    INFO OK    idx:BBCA -> snapshots/idx-bbca-snapshot.txt
    INFO       IDX:BBCA: 4,900 IDR per saham (-0.81% sesi terakhir) | 1 bulan -21.60% | 1 tahun -41.32% | harga di bawah SMA 50 dan 200 | RSI 14 28.9 oversold | posisi 52 minggu 4%
    INFO OK    idx:BMRI -> snapshots/idx-bmri-snapshot.txt
    INFO       IDX:BMRI: 3,870 IDR per saham (-1.02% sesi terakhir) | 1 bulan -5.15% | 1 tahun -13.42% | harga di bawah SMA 50 dan 200 | RSI 14 46.6 netral | posisi 52 minggu 31%
    INFO Selesai: 6 sukses, 0 gagal
    ```

3. Buka file di folder `snapshots`. Satu instrumen menjadi satu file `.txt`.

Tanpa `-o`, perintah hanya mencetak ringkasan dan tidak menulis file. Menjalankan perintah yang sama lagi menimpa file lama dengan data terbaru.

## Membaca baris ringkasan

Setiap bagian baris ringkasan berarti:

| Bagian | Arti |
|---|---|
| `2,358,171 IDR per gram` | Harga terakhir dan satuannya. |
| `+0.45% sesi terakhir` | Perubahan penutupan terakhir terhadap penutupan sesi sebelumnya. |
| `1 bulan -3.34%`, `1 tahun +9.94%` | Perubahan terhadap penutupan 30 dan 365 hari sebelumnya. |
| `harga di bawah SMA 50 dan 200` | Harga terhadap rata-rata penutupan 50 dan 200 sesi. Bila keduanya berbeda arah, tertulis `di atas SMA 50, di bawah SMA 200`. |
| `RSI 14 41.3 netral` | RSI 14 sesi (Wilder). `overbought` jika 70 atau lebih, `oversold` jika 30 atau kurang, selain itu `netral`. |
| `posisi 52 minggu 34%` | Posisi harga di antara terendah (0) dan tertinggi (100) dalam 365 hari terakhir. |

## Membaca file hasilnya

Setiap file dimulai dengan header `name` dan `description`, lalu bagian harga, perubahan, tren, rentang 52 minggu, volume, dan lima candle terakhir. Contohnya untuk BBCA:

```text title="snapshots/idx-bbca-snapshot.txt"
---
name: idx-bbca-snapshot
description: "Pergerakan harga PT Bank Central Asia Tbk (idx:BBCA): harga terakhir, perubahan 1 minggu sampai 1 tahun, SMA 20/50/200, RSI 14, dan rentang 52 minggu. Use when asked about the current price, recent price action, or trend of PT Bank Central Asia Tbk."
---

# PT Bank Central Asia Tbk - Pergerakan Harga

- Instrumen: BBCA.JK di Jakarta
- Satuan: IDR per saham
- Sumber data: Yahoo Finance
- Waktu ambil data (UTC): 2026-10-27 18:33
- Harga terakhir diperbarui (UTC): 2026-10-27 09:14 (bisa tertunda dari bursa)

## Harga
- Harga terakhir: 4,900
- Penutupan sebelumnya (2026-10-26): 4,940
- Perubahan sesi terakhir (2026-10-27): -0.81%

## Perubahan

| Periode | Perubahan | Dibanding penutupan |
|---|---|---|
| 1 minggu | -5.77% | 2026-10-20 (5,200) |
| 1 bulan | -21.60% | 2026-09-25 (6,250) |
| 3 bulan | -21.29% | 2026-07-28 (6,225) |
| 1 tahun | -41.32% | 2025-10-27 (8,350) |
| Sejak awal tahun | -39.32% | 2025-12-30 (8,075) |

## Tren
- SMA 20: 5,658 (harga di bawah, -13.40%)
- SMA 50: 6,110 (harga di bawah, -19.80%)
- SMA 200: 6,531 (harga di bawah, -24.98%)
- RSI 14: 28.9 (oversold; overbought >= 70, oversold <= 30)

## Rentang 52 minggu
- Tertinggi: 8,750
- Terendah: 4,740
- Posisi harga di rentang: 4% (0 = terendah, 100 = tertinggi)
- Jarak dari tertinggi: -44.00%
- Dihitung dari 240 sesi

## Volume
- Volume sesi terakhir: 366,846,200
- Rasio terhadap rata-rata 20 sesi sebelumnya: 1.21x

## 5 candle terakhir (1d)

| Tanggal | Buka | Tertinggi | Terendah | Tutup | Perubahan |
|---|---|---|---|---|---|
| 2026-10-21 | 5,300 | 5,350 | 5,125 | 5,275 | +1.44% |
| 2026-10-22 | 5,125 | 5,275 | 5,100 | 5,175 | -1.90% |
| 2026-10-23 | 5,175 | 5,225 | 5,000 | 5,025 | -2.90% |
| 2026-10-26 | 5,025 | 5,075 | 4,940 | 4,940 | -1.69% |
| 2026-10-27 | 4,940 | 4,980 | 4,800 | 4,900 | -0.81% |

Catatan: candle terakhir dihitung termasuk sesi yang masih berjalan, sehingga nilainya
dapat berubah sampai bursa tutup. Pembacaan menggambarkan posisi harga, bukan saran
beli atau jual.
```

Bagian volume hanya ada untuk instrumen yang punya volume. Kurs, `gold/idr`, dan IHSG tidak punya, jadi bagian itu tidak muncul di file mereka. Baris "Sejak awal tahun" membandingkan dengan penutupan terakhir tahun sebelumnya. Untuk BBCA itu 30 Desember 2025, karena data tidak punya candle 31 Desember.

## Mengambil harga historis

1. Jalankan perintah `history` dengan nama instrumen, rentang, interval, dan folder untuk file CSV-nya:

    ```shell
    uv run python scripts/market_price.py history gold/idr gold/usd spx ihsg idx:BBCA idx:BMRI -r 1y -i 1d -o prices
    ```

    Setiap instrumen mendapat dua baris log: lokasi file CSV-nya, lalu ringkasan periodenya. Contoh keluaran pada waktu yang sama:

    ```text
    INFO OK    gold/idr -> prices/gold-idr-1d-1y.csv
    INFO       GOLD/IDR 1d: 252 candle, 2025-10-27 sampai 2026-10-27, penutupan 2,145,039 -> 2,358,171 (+9.94%) IDR per gram
    INFO OK    gold/usd -> prices/gold-usd-1d-1y.csv
    INFO       GOLD/USD 1d: 252 candle, 2025-10-27 sampai 2026-10-27, penutupan 4,019.70 -> 4,069.20 (+1.23%) USD per troy ounce
    INFO OK    spx -> prices/spx-1d-1y.csv
    INFO       SPX 1d: 252 candle, 2025-10-27 sampai 2026-10-27, penutupan 6,875.16 -> 7,716.98 (+12.24%) poin indeks
    INFO OK    ihsg -> prices/ihsg-1d-1y.csv
    INFO       IHSG 1d: 240 candle, 2025-10-27 sampai 2026-10-27, penutupan 8,117.15 -> 5,266.13 (-35.12%) poin indeks
    INFO OK    idx:BBCA -> prices/idx-bbca-1d-1y.csv
    INFO       IDX:BBCA 1d: 240 candle, 2025-10-27 sampai 2026-10-27, penutupan 8,350 -> 4,900 (-41.32%) IDR per saham
    INFO OK    idx:BMRI -> prices/idx-bmri-1d-1y.csv
    INFO       IDX:BMRI 1d: 240 candle, 2025-10-27 sampai 2026-10-27, penutupan 4,470 -> 3,870 (-13.42%) IDR per saham
    INFO Selesai: 6 sukses, 0 gagal
    ```

2. Buka file di folder `prices`. Satu instrumen menjadi satu file `.csv` dengan kolom `time`, `open`, `high`, `low`, `close`, dan `volume`:

    ```text title="prices/spx-1d-1y.csv"
    time,open,high,low,close,volume
    2025-10-27,6845.459961,6877.279785,6843.939941,6875.160156,5290650000
    2025-10-28,6897.740234,6911.299805,6870.72998,6890.890137,5695930000
    2025-10-29,6910.950195,6920.339844,6851.910156,6890.589844,6280130000
    ```

Kolom `time` berisi tanggal untuk interval harian atau lebih panjang, dan tanggal beserta jam dan zona waktu bursa untuk interval intraday, misalnya `2026-10-27T09:30-04:00`. Instrumen yang tidak diperdagangkan, seperti kurs dan `gold/idr`, mendapat `volume` 0.

### Memilih periode dan interval

Opsi yang menentukan data yang diambil:

| Opsi | Nilai |
|---|---|
| `-r`, `--range` | `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`. Bawaan: `1y`. |
| `-i`, `--interval` | `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`. Bawaan: `1d`. |
| `--start`, `--end` | Tanggal `YYYY-MM-DD`. `--end` ikut dihitung. Keduanya menggantikan `--range`. |

Untuk periode tertentu, pakai tanggal. Perintah ini mengambil candle harian BBCA dari 20 sampai 27 Oktober 2026:

```shell
uv run python scripts/market_price.py history idx:BBCA --start 2026-10-20 --end 2026-10-27 -o prices
```

```text
INFO OK    idx:BBCA -> prices/idx-bbca-1d-2026-10-20-2026-10-27.csv
INFO       IDX:BBCA 1d: 6 candle, 2026-10-20 sampai 2026-10-27, penutupan 5,200 -> 4,900 (-5.77%) IDR per saham
INFO Selesai: 1 sukses, 0 gagal
```

Yahoo membatasi data intraday. Interval `1m` hanya sekitar 8 hari per permintaan, `2m`, `5m`, `15m`, `30m`, dan `90m` hanya 60 hari terakhir, dan `60m` serta `1h` sampai 2 tahun. Permintaan di luar batas gagal dengan pesan dari Yahoo, seperti yang ada di [Memperbaiki pesan GAGAL](#memperbaiki-pesan-gagal).

## Memakai dari Python

Dua fungsi mengembalikan dict biasa dan tidak memakai model. Folder `framework/agentic` harus ada di `sys.path`, seperti di [skill pool](https://github.com/kazuma313/zul_utilities/tree/main/framework/agentic):

```python
import sys

sys.path.insert(0, "framework/agentic")

from utilities.market_price.market_price_skill import get_history, get_price_action

now = get_price_action("gold/idr")
print(now["price"], now["session_change_percent"], now["rsi"], now["range_position_percent"])
print(now["summary"])

past = get_history("idx:BBCA", range="1mo", interval="1d")
print(past["summary"])
print(past["candles"][-1])
```

Contoh keluarannya:

```text
2358171.390019 0.4506 41.35 33.9
GOLD/IDR: 2,358,171 IDR per gram (+0.45% sesi terakhir) | 1 bulan -3.34% | 1 tahun +9.94% | harga di bawah SMA 50 dan 200 | RSI 14 41.3 netral | posisi 52 minggu 34%
IDX:BBCA 1d: 22 candle, 2026-09-28 sampai 2026-10-27, penutupan 6,225 -> 4,900 (-21.29%) IDR per saham
{'time': '2026-10-27', 'open': 4940.0, 'high': 4980.0, 'low': 4800.0, 'close': 4900.0, 'volume': 366846200.0}
```

`get_price_action` mengembalikan harga, penutupan sebelumnya, perubahan per periode (`changes_percent`), SMA (`sma`), `rsi`, rentang 52 minggu, `summary`, dan `document`, yaitu teks yang sama dengan file `.txt`. `get_history` mengembalikan `candles`, `summary`, dan `csv`. Untuk nama saham BEI tanpa awalan, tambahkan `market="idx"`, misalnya `get_price_action("bbca", market="idx")`. Kedua fungsi melempar `MarketPriceError` dengan alasan yang bisa dibaca, misalnya simbol yang tidak ada atau jaringan yang tertutup.

## Memakai dari agent

Dua tool LangChain membungkus fungsi yang sama dan tersedia jika `langchain-core` ter-install. Tanpa itu, nilainya `None` dan fungsi biasa tetap bisa dipakai:

```python
from utilities.market_price.market_price_skill import get_market_price, get_price_history

tools = [get_market_price, get_price_history]
```

`get_market_price` membalas dengan dokumen pergerakan harga, dan `get_price_history` dengan baris ringkasan dan 20 candle terakhir dalam CSV. Jika gagal, tool membalas dengan satu kalimat berisi alasannya dan meminta model tidak memperkirakan harga sendiri. `SKILL.md` dan `METADATA.md` di folder utility memuat petunjuk dan kebutuhan untuk agent yang membaca skill.

## Memperbaiki pesan GAGAL

Setiap instrumen diproses sendiri-sendiri. Satu yang gagal tidak menghentikan yang lain, dan kode keluarannya 1. Kode 2 berarti input tidak valid dan tidak ada permintaan yang dikirim.

| Pesan | Perbaikan |
|---|---|
| `HTTP 404 ... No data found, symbol may be delisted` | Simbol tidak ada di Yahoo. Untuk saham BEI, tulis `idx:KODE`. |
| `HTTP 422 ... 1m data not available ... Only 8 days` | Interval itu tidak boleh untuk rentang yang diminta. Pakai rentang yang lebih pendek atau interval yang lebih panjang. |
| `HTTP 422 ... 5m data not available ... within the last 60 days` | Sama, untuk `2m`, `5m`, `15m`, `30m`, dan `90m`. Pakai rentang paling lama 60 hari. |
| `HTTP 429` atau `Gagal menghubungi` | Yahoo membatasi permintaan atau jaringanmu menutupnya. Skrip mencoba tiga kali di dua host dulu. Tunggu beberapa menit, lalu coba lagi. |
| `Bukan instrumen yang dikenali` | Nama bukan alias, `idx:KODE`, atau simbol Yahoo. Pesannya mencetak daftar alias. |
| `Tanggal harus berbentuk YYYY-MM-DD` | Tulis `--start` dan `--end` dengan tahun, bulan, lalu hari, misalnya `2026-10-20`. |
| `tidak ada tanggal yang cocok antara harga dan kurs` | Emas dan kurs tidak punya tanggal yang sama pada periode itu. Perlebar periodenya. |
| `hanya N candle` | Instrumen baru terdaftar dan datanya kurang untuk `now`. Pakai `history`. |

## Batas

- **Sumbernya tidak resmi.** Endpoint chart Yahoo Finance terbuka dan tanpa API key, tetapi bukan API yang dijamin. Bentuknya bisa berubah dan permintaan bisa dibatasi tanpa pemberitahuan. Periksa ketentuan Yahoo sebelum memakai datanya di luar keperluan pribadi.
- **Harga bisa tertunda.** Setiap dokumen menyebut waktu harga terakhir diperbarui. Untuk `gold/idr`, waktu itu adalah yang lebih lama antara harga emas dan kurs.
- **Emas adalah futures.** `gold/usd` memakai kontrak COMEX bulan terdekat (di Yahoo bernama `Gold Dec 26` saat halaman ini ditulis), bukan harga spot. Harga bisa sedikit berbeda dari harga spot.
- **Hanya penutupan `gold/idr` yang tepat.** Harga buka, tertinggi, dan terendah dikalikan kurs penutupan pada hari yang sama, jadi nilainya perkiraan.
- **Harga `close` tidak disesuaikan dividen.** Untuk BBCA, penutupan paling awal dalam dua tahun adalah 10.600 sedangkan `adjclose` Yahoo 9.670. Imbal hasil jangka panjang saham berdividen dari file ini lebih rendah daripada imbal hasil totalnya.
- **Candle terakhir bisa belum selesai.** Setelah bursa tutup, Yahoo kadang mengirim candle hari itu tanpa harga penutupan. Skrip lalu memakai harga terakhir untuk candle itu, bila tanggalnya sama.
- **Bukan analisis.** Utility ini tidak membaca berita, laporan keuangan, atau memperkirakan harga.

## Langkah berikutnya

- [Mengambil snapshot harga crypto](mengambil-snapshot-crypto.md) dan [Membuat candlestick chart crypto](membuat-chart-crypto.md) untuk utility sejenis yang membaca token crypto dari Binance.
- [Membuat grafik](membuat-grafik.md) untuk menggambar perbandingan data, misalnya dari file CSV hasil `history`.
