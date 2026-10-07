---
date:
  created: 2026-10-07
categories:
  - RAG
  - Model lokal
authors:
  - kurnia
draft: true
---

# Memilih model lokal untuk menulis konteks chunk

Saya menguji tiga model lokal untuk menulis konteks chunk dengan metode contextual retrieval. Kualitas kalimatnya mirip, tetapi kecepatannya berbeda jauh, dan pemeriksaan otomatis tidak menangkap semua kalimat yang salah.

<!-- more -->

## Yang saya uji

Skill `contextual_retrieval` di Zul memotong dokumen menjadi chunk, lalu meminta model lokal menulis satu atau dua kalimat konteks di depan setiap chunk sebelum chunk itu masuk ke vector database. Caranya mengikuti [Contextual Retrieval dari Anthropic](https://www.anthropic.com/engineering/contextual-retrieval).

Saya menjalankan `qwen3:8b`, `gemma3:4b`, dan `qwen3:4b` lewat Ollama pada 102 chunk dari lima dokumen: tiga transcript YouTube berbahasa Indonesia dan dua halaman dokumentasi Zul. Laptopnya memakai GPU RTX 3060 6 GB. Claude Opus 5.5 menilai 34 chunk tanpa tahu model mana yang menulis setiap kalimat.

![Grafik batang: detik per chunk dan nilai judge untuk tiga model](../resources/2026-10-07-memilih-model-lokal/kecepatan-dan-nilai-terang.svg#only-light)
![Grafik batang: detik per chunk dan nilai judge untuk tiga model](../resources/2026-10-07-memilih-model-lokal/kecepatan-dan-nilai-gelap.svg#only-dark)

| Model | Detik per chunk | Nilai judge (1–5) | Kalimat dengan fakta salah |
|---|---|---|---|
| `qwen3:8b` | 12,7 | 4,49 | 2 dari 34 |
| `gemma3:4b` | 4,9 | 4,22 | 0 dari 34 |
| `qwen3:4b` | 7,2 | 4,32 | 4 dari 33 |

## Yang saya pelajari

### Selisih kualitasnya kecil, selisih kecepatannya besar

Nilai ketiga model hanya berbeda kurang dari 0,3 poin dari skala 5. Kecepatannya berbeda jauh: per chunk, `qwen3:8b` sekitar 2,6 kali lebih lambat dari `gemma3:4b`. Penyebabnya, `qwen3:8b` berukuran 6,3 GB dan tidak muat penuh di GPU 6 GB, jadi Ollama menjalankan sekitar sepertiganya di CPU.

### Pemeriksaan otomatis tidak menangkap semua kesalahan

Setiap kalimat dari model diperiksa kode: kalimat yang memuat nama atau angka yang tidak ada di dokumen ditolak. Pemeriksaan itu berhasil menolak "Musk", karena transcript hanya menyebut "si Elon". Tetapi kalimat salah yang semua katanya ada di dokumen tetap lolos. Contohnya, `qwen3:8b` menulis "crash 2021", padahal pembicaranya menjadi trader saat crash Terra Luna. `qwen3:4b` menulis "Rp1.000" untuk akun yang nilainya 1.000 dolar.

Karena itu, AI yang membaca hasilnya sebaiknya memakai `context` hanya untuk mencari, dan mengutip dari teks chunk aslinya.

### Konteks tidak selalu membuat pencarian lebih baik

Di lima dokumen ini, BM25 sudah menemukan 95% jawaban di lima hasil teratas tanpa konteks apa pun, karena topik dokumennya sangat berbeda. Konteks paling berguna saat banyak chunk mirip satu sama lain, misalnya puluhan podcast dengan topik yang sama. Manfaatnya perlu diukur di koleksi sendiri.

### Model embedding juga perlu dipilih

`nomic-embed-text` hanya menemukan 67% jawaban di lima hasil teratas, jauh di bawah BM25. Model ini lemah untuk bahasa Indonesia. Model embedding multibahasa seperti `bge-m3` layak dicoba berikutnya.

## Yang saya pakai sekarang

- `qwen3:8b` sebagai model bawaan skill ini.
- `gemma3:4b` saat dokumennya banyak dan waktunya terbatas.
- Header dari kode (judul, sumber, bagian) selalu dipasang, dengan atau tanpa model.

## Sumber

- [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval), Anthropic.
- [Laporan lengkap penilaian model](https://github.com/kazuma313/zul_utilities/tree/main/research/contextual_retrieval_assessment), berisi data, skor, dan catatan judge.
- [Menyiapkan dokumen untuk RAG](../../panduan/menyiapkan-dokumen-untuk-rag.md), cara memakai skill-nya.
