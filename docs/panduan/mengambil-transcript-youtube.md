# Mengambil transcript YouTube

Skill `youtube_transcript` mengambil transcript video YouTube beserta metadatanya: dari terminal untuk banyak video sekaligus, dari kode Python, atau sebagai tool di agent. Skill ini tidak memakai model AI. Caption diambil dari YouTube, metadata dari yt-dlp, dan semua format dibuat oleh kode.

Skill ini hanya mengambil caption yang sudah ada di YouTube. Video tanpa caption tidak punya transcript, karena skill ini tidak mengubah suara menjadi teks.

**Sebelum mulai:** `uv` ter-install, kamu berada di root repository Zul, dan komputermu bisa membuka youtube.com. Skill ini ada di `research/agentic/algorithms/skills/youtube_transcript/`.

## Instalasi kebutuhannya

Install dua paket yang dipakai skill ini ke environment proyek:

```shell
uv pip install "youtube-transcript-api>=1.2" yt-dlp
```

`youtube-transcript-api` mengambil caption. `yt-dlp` mengambil metadata: durasi, kategori, tag, dan bab video. Tanpa `yt-dlp`, metadata yang didapat hanya judul dan channel.

## Mengambil transcript beberapa video

1. Pindah ke folder skill:

    ```shell
    cd research/agentic/algorithms/skills/youtube_transcript
    ```

2. Tulis URL video di file teks, satu URL per baris. Baris kosong dan baris yang diawali `#` diabaikan:

    ```text title="urls.txt"
    # podcast trading
    https://youtu.be/Qft-J2LG0NM?si=4BZhF60S3gUFPZ77
    https://www.youtube.com/live/56HmqxOTK0U?si=nIQaoKYTBU8MUGAt
    ```

    Semua bentuk URL video bisa dipakai: `youtube.com/watch`, `youtu.be`, `shorts`, `live`, dan `embed`. URL playlist dan channel tidak bisa.

3. Jalankan skripnya:

    ```shell
    uv run python scripts/yt_transcripts.py -i urls.txt -o transcripts
    ```

    Skrip menulis satu baris log per video, lalu ringkasannya:

    ```text
    19:15:01 INFO    [1/2] OK      https://youtu.be/Qft-J2LG0NM?si=4BZhF60S3gUFPZ77 -> trader-sejati-berani-cutloss-cintain-cuannya-bukan-coin-nya-Qft-J2LG0NM.txt
    19:15:07 INFO    [2/2] OK      https://www.youtube.com/live/56HmqxOTK0U?si=nIQaoKYTBU8MUGAt -> timothy-ronald-show-2026-10-05-56HmqxOTK0U.txt
    19:15:07 INFO    Selesai: 2 sukses, 0 dilewati, 0 gagal
    ```

4. Buka file di folder `transcripts`. Satu video menjadi satu file `.txt`.

Video yang file-nya sudah ada dilewati saat skrip dijalankan lagi, jadi perintah yang sama aman diulang. Tambahkan `--overwrite` untuk mengambil ulang semuanya.

## Membaca file hasilnya

Setiap file dimulai dengan header berisi metadata video, lalu deskripsi video dari pengunggah, lalu transcript-nya:

```text title="trader-sejati-berani-cutloss-cintain-cuannya-bukan-coin-nya-Qft-J2LG0NM.txt"
---
name: trader-sejati-berani-cutloss-cintain-cuannya-bukan-coin-nya
description: "Transcript of the YouTube video \"Trader Sejati = ...\" by Theresa Learns (44:10; language id, auto-generated captions; uploaded 2026-10-04). Video summary: ..."
title: "Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInnerCircle KJo"
channel: "Theresa Learns"
url: "https://www.youtube.com/watch?v=Qft-J2LG0NM"
upload_date: "2026-10-04"
duration: "44:10"
category: "People & Blogs"
tags: ["theresa learns", "crypto", "cryptocurrency", ...]
transcript_language: "id"
captions: "auto-generated"
caption_coverage: 1.0
words: 7051
chapters: ["00:00:00 Intro dan Teaser", "00:01:30 Awal Mula Masuk Crypto", ...]
---

## Video description

Kali ini di Unscripted, kita ngobrol bareng KJo, ...

## Transcript

### 00:01:30 Awal Mula Masuk Crypto

biasa gitu kan. Tapi kalau ditanya kejo start mungkin aku basicnya dari profesional di programmer. ...
```

Beberapa kolom perlu diperhatikan:

| Kolom | Arti |
|---|---|
| `captions` | `auto-generated` berarti caption dibuat otomatis oleh YouTube, jadi ada kata dan nama yang salah dengar. `manual` berarti ditulis manusia. |
| `caption_coverage` | Bagian video yang tercakup caption, dari 0 sampai 1. Di bawah 0,9 transcript-nya tidak lengkap, dan skrip memberi peringatan. |
| `chapters` | Bab video. Setiap bab juga menjadi subjudul `###` di dalam transcript. |
| `live_recording` | `true` untuk rekaman siaran langsung. Nama file-nya ikut memuat tanggal, karena judul siaran sering sama setiap minggu. |

Penanda suara seperti `[musik]` dan `[tertawa]` dibuang dari transcript. Tambahkan `--keep-sound-tags` untuk mempertahankannya.

## Melewati video game dan film

Untuk daftar campuran, lewati kategori YouTube yang tidak kamu inginkan:

```shell
uv run python scripts/yt_transcripts.py -i urls.txt -o transcripts --skip-category Gaming "Film & Animation" Music
```

Video yang dilewati muncul sebagai `SKIPPED` di log, dan transcript-nya tidak diambil.

> [!NOTE]
> Jangan menyaring dengan memilih kategori `Education` saja. Podcast dan kelas biasanya dicatat YouTube sebagai `Entertainment`, `People & Blogs`, atau `News & Politics`. Dalam uji dengan lima video edukatif, tidak satu pun berkategori `Education`.

## Mengambil transcript dari kode Python

Fungsi `fetch_transcript` mengembalikan metadata dan transcript satu video sebagai `dict`. Fungsi ini tidak memakai model AI maupun LangChain:

```python title="contoh pemakaian di kode"
from skills.youtube_transcript.youtube_transcript_skill import fetch_transcript

record = fetch_transcript("https://youtu.be/Pc3GWaOWHLk")
print(record["metadata"]["title"])      # Cara Coach Justin Menghadapi Ketidakpastian Hidup
print(record["metadata"]["duration"])   # 9:12
print(record["transcript"][:200])
```

Isi `record`:

| Kunci | Isi |
|---|---|
| `metadata` | Judul, channel, URL, tanggal unggah, durasi, kategori, tag, bab, bahasa, jenis caption, cakupan caption, dan jumlah kata. |
| `video_description` | Deskripsi video dari pengunggah, tidak diubah. |
| `transcript` | Transcript dalam paragraf, dengan subjudul per bab. |
| `document` | Semuanya sebagai teks satu file `.txt`, sama dengan hasil skrip. |

Folder `research/agentic/algorithms/` harus ada di `sys.path` supaya `skills` bisa diimpor. Untuk link yang bukan video, fungsi ini menimbulkan `ValueError`.

## Memakai skill di agent

Skill ini menyediakan tool LangChain bernama `get_youtube_transcript`. Pasang ke agent seperti tool lain:

```python title="contoh pemakaian di agent"
from skills.youtube_transcript.youtube_transcript_skill import get_youtube_transcript

tools = [get_youtube_transcript]
```

Model cukup menulis argumen `url`. Transcript yang panjang dibagi menjadi bagian sekitar 12.000 karakter, supaya muat di konteks model kecil. Podcast satu jam menjadi lima bagian, dan setiap balasan diakhiri penanda seperti `[part 1 of 5; call again with part=2 for the rest]`.

Dalam uji pemilihan skill dengan 12 skill sekaligus, `qwen3:8b` memilih skill ini dengan benar pada 27 dari 27 permintaan, dan `gemma3:4b` pada 24 dari 27. Kesalahan `gemma3:4b` terjadi pada permintaan rekomendasi video tanpa link. Untuk kasus itu tool membalas dengan arahan memakai web search.

## Jika YouTube memblokir komputermu

YouTube membatasi seberapa sering satu alamat IP boleh meminta caption. Dalam uji di laptop dengan koneksi rumah, blokir muncul setelah sekitar 30 permintaan dalam beberapa menit, dan bertahan lebih dari setengah jam. Log-nya menunjukkan `IpBlocked`, `RequestBlocked`, atau `HTTP Error 429`.

Saat terblokir, skrip berhenti setelah dua video berturut-turut gagal dan menyimpan sisa URL di `transcripts/failed_urls.txt`. Untuk melanjutkan tanpa menunggu, pakai layanan transcript Supadata. Servernya meminta ke YouTube atas namamu, sehingga blokir di IP-mu tidak berpengaruh:

1. Daftar di supadata.ai. Paket gratisnya memberi 100 transcript per bulan, tanpa kartu kredit.

2. Tambahkan API key-mu ke file `.env` di root repository Zul:

    ```text title=".env"
    SUPADATA_API_KEY=API_KEY
    ```

    Ganti `API_KEY` dengan key dari dashboard Supadata. File `.env` sudah diabaikan git, jadi key-nya tidak ikut ter-commit.

3. Jalankan ulang URL yang gagal:

    ```shell
    uv run python scripts/yt_transcripts.py -i transcripts/failed_urls.txt -o transcripts
    ```

Skrip tetap meminta ke YouTube lebih dulu karena gratis, dan baru beralih ke Supadata setelah YouTube menolak. Setiap video lewat Supadata memakai satu kredit. Dalam uji, transcript dari Supadata sama persis kata per kata dengan transcript dari YouTube. Bedanya, kolom `captions` berisi `unknown` karena Supadata tidak memberi tahu apakah caption-nya otomatis.

Pilihan lain adalah proxy residensial berputar. Isi `WEBSHARE_PROXY_USERNAME` dan `WEBSHARE_PROXY_PASSWORD` di `.env` untuk Webshare, atau berikan proxy apa pun dengan `--proxy URL`.

## Halaman terkait

- `SKILL.md` di folder skill untuk semua opsi skrip dan arti setiap pesan kesalahan.
- `evals/check_metadata.py` di folder skill untuk memeriksa apakah setiap file punya metadata yang cukup dan transcript yang lengkap.
- `REQUIREMENTS.md` di folder `skills/` untuk kebutuhan mesin semua skill.
