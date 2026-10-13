# Latihan

Soal latihan yang dikerjakan manual untuk mengasah kemampuan coding. Setiap soal punya test; fungsinya sengaja dibiarkan kosong (`NotImplementedError`) sampai dikerjakan, jadi test yang gagal berarti soal yang belum selesai.

| Folder | Isi |
|---|---|
| `sorting_algorithm/` | Bubble sort dan selection sort. |
| `string_algorithms/` | Anagram, palindrome, edit distance, kompresi string, substring, dan tanda kurung. |
| `probability_simulation/` | Simulasi Monte Carlo, paradoks ulang tahun, dadu, deret koin, random walk, dan antrean. |
| `image_processing/` | Filter, threshold, deteksi tepi, konvolusi, dan bounding box. Petunjuknya ada di [README](image_processing/README.md). |
| `benchmarking/` | Notebook benchmark GPU, CPU, dan load test. |
| `stress_test/` | Benchmark beban konkuren. |
| `deep_research.ipynb`, `pptx_to_pdf.ipynb` | Percobaan kecil. |

## Menjalankan test

Dari root repository:

```bash
uv run pytest research/latihan -q
```

Untuk satu soal saja:

```bash
uv run pytest research/latihan/string_algorithms/tests/test_palindrome.py -v
```

Kode latihan mengimpor dirinya lewat paket `research.latihan`, misalnya `from research.latihan.sorting_algorithm.algorithms.bubble_sort import bubble_sort`.
