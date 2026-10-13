# Studi pembaca gambar untuk skill belajar

Model mana yang paling baik mengubah gambar menjadi teks untuk skill `silabus_belajar` dan `materi_belajar`? Empat gambar yang sama dibaca oleh setiap pembaca, lalu hasilnya dinilai terhadap isi yang seharusnya ada.

| Gambar | Isi | Cara menilai |
|---|---|---|
| `mediawiki.webp` | Tangkapan layar mediawiki.org | Jumlah frasa penting yang ditemukan |
| `slide.png` | Slide survei | Jumlah frasa penting yang ditemukan |
| `halaman-pdf.png` | Halaman 5 PDF di `research/arsip/catatan_docs/`, dijadikan gambar seperti hasil scan | Recall dan precision kata |
| `tabel.png` | Tabel yang digambar oleh script | Jumlah sel yang ditemukan dan baris yang utuh |

Isi yang seharusnya ada tersimpan di `inputs/truth.json`.

## Hasil

| Pembaca | Gambar | Waktu | Skor |
|---|---|---|---|
| gemma3:4b | mediawiki.webp | 58,5 detik | 22 dari 25 frasa |
| gemma3:4b | slide.png | 37,8 detik | 9 dari 9 frasa |
| gemma3:4b | halaman-pdf.png | 94,8 detik | recall 0,773, precision 0,799 |
| gemma3:4b | tabel.png | 36,3 detik | 25 dari 25 sel, 4 baris utuh |
| qwen3-vl:4b | mediawiki.webp | 314,3 detik | 0 dari 25 frasa |

Hanya gemma3:4b yang selesai membaca keempat gambar. qwen3-vl:4b lebih dari lima kali lebih lambat dan tidak menemukan satu frasa pun di gambar pertama, jadi tidak dilanjutkan. glm-ocr dan Docling belum dijalankan. Semua angka diukur di RTX 3060 Laptop 6 GB dengan Ollama.

## Menjalankan ulang

Dari root repository:

```bash
uv run python framework/studies/file_reader_comparison/run_reader_comparison.py --prepare
uv run python framework/studies/file_reader_comparison/run_reader_comparison.py
uv run python framework/studies/file_reader_comparison/run_reader_comparison.py --score
```

`--prepare` membuat ulang `inputs/`, perintah tanpa opsi menjalankan setiap pembaca, dan `--score` menilai ulang hasil di `outputs/`. Waktu dan skor ditulis ke `results.json`.
