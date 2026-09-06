# Image Processing Practice

Daftar 8 soal latihan (dengan estimasi waktu ala interview) dan file yang bersesuaian.
Semua fungsi masih berupa stub (`raise NotImplementedError`) — isi implementasinya lalu
jalankan test yang cocok untuk memverifikasi.

| # | Soal | Waktu | File algoritma | File test |
|---|------|-------|-----------------|-----------|
| 1 | Grayscale Conversion & Thresholding (manual vs Otsu) | Easy, 10m | [algorithms/grayscale_thresholding.py](algorithms/grayscale_thresholding.py) | [tests/test_grayscale_thresholding.py](tests/test_grayscale_thresholding.py) |
| 2 | Basic Filtering (Gaussian blur vs median blur) | Easy, 15m | [algorithms/basic_filtering.py](algorithms/basic_filtering.py) | [tests/test_basic_filtering.py](tests/test_basic_filtering.py) |
| 3 | Edge Detection (Canny vs Sobel) | Medium, 20m | [algorithms/edge_detection.py](algorithms/edge_detection.py) | [tests/test_edge_detection.py](tests/test_edge_detection.py) |
| 4 | Histogram & Contrast Enhancement | Medium, 20m | [algorithms/histogram_equalization.py](algorithms/histogram_equalization.py) | [tests/test_histogram_equalization.py](tests/test_histogram_equalization.py) |
| 5 | Deteksi & Hitung Objek Berdasarkan Warna | Medium, 25m | [algorithms/color_object_detection.py](algorithms/color_object_detection.py) | [tests/test_color_object_detection.py](tests/test_color_object_detection.py) |
| 6 | Custom Convolution dengan `filter2D` | Medium, 20m | [algorithms/custom_convolution.py](algorithms/custom_convolution.py) | [tests/test_custom_convolution.py](tests/test_custom_convolution.py) |
| 7 | Bonus: Bounding Box + urutkan berdasarkan area | Hard, 25m | [algorithms/object_bounding_boxes.py](algorithms/object_bounding_boxes.py) | [tests/test_object_bounding_boxes.py](tests/test_object_bounding_boxes.py) |
| 8 | Bonus: Baca kode CV orang lain, jelaskan dalam 2 menit | - | *(tidak ada kode — latihan verbal)* | - |

## Soal #8: latihan verbal, bukan kode

Ambil satu soal (#1-#7) yang sudah kamu selesaikan, lalu coba jelaskan solusimu
seolah-olah ke orang lain dalam 2 menit: apa masalahnya, kenapa pendekatan itu
yang dipilih, dan di bagian mana implementasimu bisa gagal. Ini melatih bagian
"explain your solution" yang eksplisit disebut di brief interview — tidak ada
test case untuk soal ini.

## Menjalankan test

```bash
uv run pytest research/image_processing -q          # semua soal
uv run pytest research/image_processing/tests/test_edge_detection.py -v   # satu soal
```
