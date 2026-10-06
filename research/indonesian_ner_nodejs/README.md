# NER bahasa Indonesia di Node.js

Folder ini menjalankan model [`cahya/bert-base-indonesian-NER`](https://huggingface.co/cahya/bert-base-indonesian-NER) di Node.js dengan [transformers.js](https://huggingface.co/docs/transformers.js). Model ini mengenali 19 jenis entitas dalam teks bahasa Indonesia, misalnya orang, organisasi, tempat, tanggal, dan uang.

## Hasil

- **Berjalan di Node.js, di CPU.** Model dimuat dalam 0,7 detik. Enam kalimat selesai dalam 0,13 detik, dan transcript sepanjang 44.000 karakter selesai dalam 8 detik.
- **Hasilnya sama dengan model asli di PyTorch.** Untuk enam kalimat di `samples.txt`, token, label, dan 21 entitasnya sama persis, dengan selisih logit terbesar 0,0000088. Perbandingan ini dijalankan oleh `check.mjs`.
- **Bagus untuk teks formal, lemah untuk bahasa lisan.** Di kalimat berita hasilnya tepat (lihat contoh di bawah). Di transcript podcast, banyak kata yang salah dikenali: "lu" dianggap orang 19 kali, "AI" dianggap orang 18 kali, dan "Kopi Kenangan" dianggap lokasi. Pakai model ini untuk teks formal, atau periksa hasilnya kalau teksnya bahasa percakapan.

Contoh keluaran `node ner.mjs --file samples.txt`:

```text
- Presiden Joko Widodo meresmikan Bendungan Jatigede di Sumedang, Jawa Barat, pada 24 Juli 2025.
    PER  Joko Widodo  (0.9862, orang)
    LOC  Bendungan Jatigede  (0.7883, lokasi)
    GPE  Sumedang  (0.9964, entitas geopolitik (negara, provinsi, kota))
    GPE  Jawa Barat  (0.9898, entitas geopolitik (negara, provinsi, kota))
    DAT  24 Juli 2025  (0.9876, tanggal)
- Harga Bitcoin sempat turun ke 74.000 dolar AS setelah Donald Trump mengumumkan tarif baru.
    PRD  Bitcoin  (0.8708, produk)
    MON  74.000 dolar AS  (0.9882, uang)
    PER  Donald Trump  (0.9877, orang)
```

## Kenapa modelnya perlu dikonversi

transformers.js hanya bisa membaca model dalam format ONNX. Repository model ini hanya berisi bobot PyTorch dan Flax. Karena itu, `export_onnx.py` mengonversinya sekali dengan Python, lalu Node.js membaca hasil konversi dari folder `models/`.

## Menyiapkan

**Sebelum mulai:** Node.js (diuji dengan versi 24.19), dan `uv` dengan environment proyek Zul (torch dan transformers sudah ada di sana).

1. Pindah ke folder ini:

    ```bash
    cd research/indonesian_ner_nodejs
    ```

2. Unduh model dan konversi ke ONNX:

    ```bash
    uv run --project ../.. --with onnx --with onnxscript python export_onnx.py
    ```

    Perintah ini memasang `onnx` dan `onnxscript` hanya untuk sekali jalan, tanpa mengubah `.venv` proyek. Skrip menulis `models/cahya/bert-base-indonesian-NER/` (sekitar 420 MB) dan `reference.json`. Bobot asli tersimpan di cache Hugging Face, `~/.cache/huggingface/hub/models--cahya--bert-base-indonesian-NER` (sekitar 845 MB). Transformers mengunduh `pytorch_model.bin` dan juga salinan `model.safetensors` dari bot konversi Hugging Face; isi keduanya sama.

3. Pasang transformers.js:

    ```bash
    npm install
    ```

    npm akan memperingatkan bahwa skrip `postinstall` milik `onnxruntime-node` dan `protobufjs` tidak dijalankan. Di Windows dengan CPU, keduanya tidak diperlukan.

4. Pastikan hasilnya sama dengan PyTorch:

    ```bash
    node check.mjs
    ```

    Keluaran yang benar diakhiri dengan `OK: token ids, logits and entities match the PyTorch model`.

## Menjalankan

Untuk satu teks:

```bash
node ner.mjs "Bank Indonesia menaikkan suku bunga acuan menjadi 6,25 persen."
```

Untuk satu file, dengan satu teks per baris:

```bash
node ner.mjs --file samples.txt
```

Tambahkan `--json` untuk mendapat entitas dalam format JSON.

Untuk memakainya dari kode:

```js
import { loadNer } from './ner.mjs';

const ner = await loadNer();
const { entities } = await ner('Universitas Gadjah Mada di Yogyakarta menerima 9.000 mahasiswa baru.');
// [{ type: 'ORG', text: 'Universitas Gadjah Mada', start: 0, end: 23, score: 0.99 }, ...]
```

`start` dan `end` adalah posisi karakter di teks asli, jadi `text.slice(start, end)` selalu sama dengan `text` entitas itu. Teks sepanjang apa pun bisa diproses. BERT hanya membaca 512 token sekaligus, jadi teks yang lebih panjang dipotong menjadi beberapa bagian di akhir kalimat, dan posisinya disesuaikan kembali ke teks asli.

## Kenapa tidak memakai pipeline bawaan transformers.js

transformers.js punya pipeline `token-classification`. Mode `aggregation_strategy: 'simple'`-nya punya tiga kekurangan untuk model ini:

- Ia menggabungkan potongan kata (subword), bukan kata utuh.
- Ia tidak memberi posisi karakter.
- Ia mengembalikan teks dalam huruf kecil (`joko widodo`), karena model ini memakai tokenizer huruf kecil.

`ner.mjs` memakai cara `aggregation_strategy="first"` di Python. Sebuah kata mengambil label potongan pertamanya, lalu kata-kata digabung menjadi entitas menurut tag B- dan I-. Teks entitas diambil dari teks asli.

## Jenis entitas

Kartu model tidak menyebut data latihnya. Tetapi 39 labelnya sama, dengan urutan yang sama, dengan korpus [NERGrit](https://huggingface.co/datasets/grit-id/id_nergrit_corpus), jadi artinya diambil dari sana:

| Kode | Arti | Kode | Arti |
|---|---|---|---|
| `PER` | orang | `DAT` | tanggal |
| `ORG` | organisasi | `TIM` | waktu |
| `NOR` | organisasi politik | `MON` | uang |
| `GPE` | entitas geopolitik (negara, provinsi, kota) | `PRC` | persentase |
| `LOC` | lokasi | `QTY` | kuantitas |
| `FAC` | fasilitas | `CRD` | bilangan |
| `EVT` | peristiwa | `ORD` | urutan |
| `PRD` | produk | `LAW` | hukum, seperti undang-undang |
| `WOA` | karya seni | `REG` | agama |
| `LAN` | bahasa | | |

## Isi folder

| File | Isi |
|---|---|
| `export_onnx.py` | Mengunduh model, mengonversinya ke ONNX, dan menulis `reference.json` |
| `ner.mjs` | NER di Node.js: `loadNer()` untuk kode, dan perintah `node ner.mjs` |
| `check.mjs` | Membandingkan hasil Node.js dengan PyTorch |
| `samples.txt` | Enam kalimat contoh |
| `reference.json` | Jawaban model PyTorch untuk `samples.txt`: token, logit, label, dan entitas |
| `package.json`, `package-lock.json` | `@huggingface/transformers` 4.3.1 |
| `models/`, `node_modules/` | Model ONNX dan paket npm. Keduanya tidak masuk git (lihat `.gitignore`). |
