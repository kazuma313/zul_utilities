# Studi model lokal untuk skill belajar

Model Ollama mana yang dipakai skill `silabus_belajar` dan `materi_belajar`? Studi ini membandingkan `gemma3:4b`, `qwen3:4b`, dan `qwen3:8b` pada empat tugas yang sama, dengan jawaban Claude sebagai pembanding.

Hasil singkatnya:

- Untuk silabus, skill memakai `gemma3:4b`: selesai dalam 30 sampai 40 detik, dan model yang lebih besar tidak menulis silabus yang lebih lengkap.
- Untuk materi, skill memakai `qwen3:8b`: hanya model ini yang menulis semua angka dengan benar, tetapi butuh 3,5 sampai 5,5 menit per materi.
- Semua model menulis fakta yang salah atau istilah karangan, jadi isi halaman tetap harus dibaca sebelum dipakai belajar.

Laporan lengkapnya, termasuk cara membandingkan, angka per tugas, dan batasannya, ada di [Model lokal untuk skill belajar](https://zulkit.my.id/konsep/model-lokal-untuk-skill-belajar/). Sumbernya di [`docs/konsep/model-lokal-untuk-skill-belajar.md`](../../../docs/konsep/model-lokal-untuk-skill-belajar.md).

| File | Isi |
|---|---|
| `claude/` | Jawaban pembanding yang ditulis Claude. |
| `gemma3-4b/`, `qwen3-4b/`, `qwen3-8b/` | Jawaban setiap model di putaran kedua, beserta halaman HTML-nya. |
| `run1/` | Jawaban dan halaman putaran pertama. |
| `results.json` | Waktu, token, percobaan, dan peringatan setiap tugas. |
| `metrics.json` | Ukuran yang dihitung script, seperti jumlah bab, soal hafalan, dan jam modul. |
| `review.json` | Catatan hasil membaca setiap jawaban. |

Path di `results.json` masih menunjuk ke lokasi lama, `research/learning_skills_comparison/`, karena file itu ditulis sebelum folder dipindah.

## Menjalankan ulang

Dari root repository, dengan Ollama berjalan dan ketiga model sudah di-pull:

```bash
uv run python framework/studies/learning_skills_comparison/run_comparison.py
uv run python framework/studies/learning_skills_comparison/score_outputs.py
```

Perintah pertama memanggil ketiga model, dan perintah kedua menghitung ulang `metrics.json`.
