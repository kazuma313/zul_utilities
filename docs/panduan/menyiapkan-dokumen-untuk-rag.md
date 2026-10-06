# Menyiapkan dokumen untuk RAG

Halaman ini menunjukkan cara memotong dokumen menjadi chunk dan memberi setiap chunk konteks dengan skill `contextual_retrieval`, supaya hasilnya siap dimasukkan ke vector database dan dicari oleh AI. Metodenya mengikuti [Contextual Retrieval dari Anthropic](https://www.anthropic.com/engineering/contextual-retrieval), dengan model lokal di laptop.

Sebuah chunk sering tidak bisa dipahami sendirian. Kalimat "Kenapa sih orang-orang masih mengharapkan harganya akan turun lagi?" tidak menyebut siapa yang bicara, di acara apa, dan tentang harga apa. Contextual retrieval menaruh keterangan itu di depan chunk sebelum chunk di-embed dan diindeks, sehingga pertanyaan seperti "apa kata KJo soal harga Bitcoin" bisa menemukannya.

**Sebelum mulai:** `uv` terpasang, kamu berada di root repository Zul, dan Ollama berjalan dengan model yang disarankan di bagian [Memilih model](#memilih-model). Skill ini ada di `research/agentic/algorithms/skills/contextual_retrieval/` dan tidak membutuhkan paket tambahan.

## Cara skill ini menjaga hasilnya tetap bisa dipercaya

Hasil skill ini dibaca oleh AI lain, jadi konteks yang salah lebih berbahaya daripada konteks yang kosong. Karena itu tugasnya dibagi:

| Bagian | Dibuat oleh | Isi |
|---|---|---|
| Chunk | kode | Potongan sekitar 1.000 karakter yang tidak melewati batas bagian atau bab. Blok kode tidak pernah terbelah. |
| `header` | kode | Judul dokumen, sumber, dan bagian. Selalu benar, juga tanpa model. |
| `context` | model lokal | Satu atau dua kalimat yang menjelaskan chunk itu di dalam dokumennya. |

Kalimat dari model diperiksa kode sebelum dipakai. Kalimat yang memuat angka atau nama yang tidak ada di dokumen, menyalin chunk, atau ditulis dalam bahasa yang salah ditolak, lalu model diminta sekali lagi. Jika masih gagal, chunk itu hanya memakai `header`. Dengan begitu chunk di index punya konteks yang sudah diperiksa atau tidak punya konteks sama sekali, tidak pernah konteks karangan.

## Memproses dokumen

1. Pindah ke folder skill:

    ```shell
    cd research/agentic/algorithms/skills/contextual_retrieval
    ```

2. Jalankan skrip pada satu atau beberapa file:

    ```shell
    uv run python scripts/contextualize.py NAMA_FILE -o chunks.jsonl
    ```

    Ganti `NAMA_FILE` dengan path file Markdown, file teks, atau file transcript dari skill `youtube_transcript`. Header YAML di file transcript menjadi metadata, dan bab videonya menjadi bagian.

3. Baca ringkasan yang dicetak skrip:

    ```text
    model: qwen3:8b (recommended for chunk contexts; --model or SKILL_MODEL chooses another)
    OK: 102 chunks from 5 documents in 1296 s; 101 with a model context, 1 with the header only
    - 1 rejected: names not in the document
    written: chunks.jsonl
    ```

    Baris `rejected` menyebut alasan kalimat model ditolak. Chunk-chunk itu tetap ada di file, hanya tanpa kalimat konteks.

Tambahkan `--no-llm` untuk membuat chunk dengan `header` saja, tanpa model. Cara ini selesai dalam hitungan detik untuk dokumen berapa pun.

## Membaca file hasilnya

Setiap baris `chunks.jsonl` adalah satu chunk dalam format JSON:

```json title="satu baris chunks.jsonl (dipendekkan)"
{
  "id": "Qft-J2LG0NM#13",
  "section": ["Transcript", "00:08:30 Conviction Bitcoin"],
  "text": "Pas BTC turun ke 74.000 sampai 76.000 last year karena masalah tarif. ...",
  "header": "Dokumen: Trader Sejati = Berani CUTLOSS, ... Sumber: video YouTube Theresa Learns, 2026-10-04, 44:10. Bagian: 00:08:30 Conviction Bitcoin.",
  "context": "...",
  "context_source": "model",
  "contextualized_text": "Dokumen: ... \n...\n\nPas BTC turun ke 74.000 ...",
  "metadata": {"url": "https://www.youtube.com/watch?v=Qft-J2LG0NM", "channel": "Theresa Learns", "upload_date": "2026-10-04"}
}
```

Saat memasukkan ke vector database:

- Embed `contextualized_text`, dan pakai teks yang sama untuk index BM25.
- Simpan `text` untuk ditampilkan atau dikirim ke AI sebagai potongan sumber.
- Simpan `id`, `section`, `metadata`, dan `context_source` sebagai metadata, supaya AI yang membaca bisa menyebut sumbernya.

Untuk sekalian menyimpan embedding, tambahkan `--embed nomic-embed-text`. Setiap record lalu mendapat kolom `embedding`.

## Memakai skill dari kode Python

```python title="contoh pemakaian di kode"
from skills.contextual_retrieval.contextual_retrieval_skill import contextualize_file, write_jsonl

records = contextualize_file("catatan.md")                    # model dipilih otomatis
write_jsonl(records, "chunks.jsonl")

records = contextualize_file("catatan.md", use_model=False)   # header saja, tanpa model
```

Folder `research/agentic/algorithms/` harus ada di `sys.path` supaya `skills` bisa diimpor. Untuk agent, skill ini juga menyediakan tool LangChain bernama `contextualize_document`.

## Memilih model

Tanpa opsi `--model`, skrip memakai model pertama dari daftar berikut yang sudah ada di Ollama. Urutannya diambil dari pengujian pada 102 chunk (tiga transcript YouTube berbahasa Indonesia dan dua halaman dokumentasi ini), di laptop dengan GPU RTX 3060 6 GB. Claude Opus 5.5 menilai 34 chunk tanpa tahu model mana yang menulis setiap kalimat.

| Model | Detik per chunk | Nilai rata-rata (1-5) | Kalimat dengan fakta salah | Kapan dipakai |
|---|---|---|---|---|
| `qwen3:8b` | 12,7 | 4,49 | 2 dari 34 | Pilihan bawaan. Kalimatnya paling setia pada dokumen, paling rapi, dan paling pendek. |
| `gemma3:4b` | 4,9 | 4,22 | 0 dari 34 | Untuk dokumen dalam jumlah besar. Hampir dua kali lebih cepat, tetapi kalimatnya lebih sering umum dan tidak menyebut isi chunk. |
| `qwen3:4b` | 7,2 | 4,32 | 4 dari 33 | Tidak disarankan sebagai pilihan bawaan. Kalimatnya paling spesifik, tetapi paling sering salah fakta. |

Untuk memakai model lain, tambahkan `--model NAMA_MODEL`. Ganti `NAMA_MODEL` dengan nama model di Ollama, misalnya `gemma3:4b`.

Dua hal yang perlu kamu ketahui dari pengujian itu:

- Pemeriksaan kode menolak nama dan angka yang tidak ada di dokumen, tetapi tidak menolak kalimat yang salah dari kata-kata yang ada di dokumen. Contohnya tahun yang ditempel ke peristiwa yang salah, atau "Rp" di depan angka yang sebenarnya dolar. Karena itu, minta AI yang membaca hasilnya memakai `context` hanya untuk mencari, dan mengutip dari `text`.
- Pada lima dokumen ini, konteks dari model tidak membuat pencarian lebih baik secara terukur, karena BM25 sudah menemukan 95% jawaban di lima hasil teratas. Konteks paling berguna untuk koleksi besar yang banyak chunk-nya mirip. Ukur koleksimu sendiri dengan `evals/retrieval_eval.py` di folder skill.

`nomic-embed-text` lemah untuk teks berbahasa Indonesia. Pada pengujian ini, embedding hanya menemukan 67% jawaban di lima hasil teratas, sedangkan BM25 menemukan 95%. Untuk koleksi berbahasa Indonesia, bandingkan dengan model embedding multibahasa seperti `bge-m3` memakai skrip yang sama.

## Lihat juga

- `SKILL.md` di folder skill untuk semua kolom record dan opsi skrip.
- `research/contextual_retrieval_assessment/README.md` untuk laporan lengkap penilaian model, beserta dokumen, hasil, dan catatan penilaiannya.
- [Mengambil transcript YouTube](mengambil-transcript-youtube.md) untuk menyiapkan transcript video sebagai bahan.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) untuk memasukkan hasilnya ke Milvus.
