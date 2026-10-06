# ChartGenerator

`ChartGenerator` menggambar grafik perbandingan beberapa dataset dengan Matplotlib dan mengembalikan ringkasan statistik beserta uji signifikansinya. Modul yang sama menyediakan dua fungsi: satu untuk membaca data dari CSV, satu untuk membuat banyak grafik sekaligus.

Baris berikut mengimpor semuanya:

```python
from zul.utilities.analysis import (
    ChartGenerator,
    batch_create_charts,
    create_chart_from_csv,
)
```

Modul ini membutuhkan extra `analysis` (`matplotlib`, `pandas`, `scipy`, `numpy`).

## `ChartGenerator(config=None)`

Menyiapkan pembuat grafik dengan pengaturan tampilan bawaan.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config` | `dict` atau `None` | `None` | Pengaturan yang menimpa nilai bawaan. Kunci yang tidak disebut tetap memakai nilai bawaan. |

Kunci `config`:

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `style` | `str` | `"default"` | Nama style Matplotlib, diterapkan saat objek dibuat. |
| `figsize` | `list` | `[12, 8]` | Ukuran gambar dalam inci: lebar, tinggi. |
| `colors` | `list[str]` | Palet 10 warna | Warna dataset, dipakai berurutan. |
| `alpha` | `float` | `0.7` | Transparansi batang, garis, dan kotak. |
| `grid` | `bool` | `True` | Menampilkan garis bantu. |
| `grid_alpha` | `float` | `0.3` | Transparansi garis bantu. |

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `config` | `dict` | Pengaturan aktif setelah digabung dengan nilai bawaan. |
| `current_fig` | figure Matplotlib atau `None` | Grafik terakhir yang dibuat. `None` sebelum grafik dibuat dan setelah `clear()`. |
| `current_ax` | axes Matplotlib atau `None` | Axes grafik terakhir untuk tipe yang punya satu axes. |

Contoh berikut membuat pembuat grafik dengan ukuran dan transparansi sendiri:

```python
chart = ChartGenerator({"figsize": [14, 10], "alpha": 0.8})
```

## `create_comparison_chart(chart_config)`

Menggambar satu grafik perbandingan dan menghitung statistik setiap dataset.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `chart_config` | `dict` | Wajib | Konfigurasi grafik. Lihat [Kunci konfigurasi grafik](#kunci-konfigurasi-grafik). |

**Mengembalikan:** `dict` statistik. Lihat [Hasil statistik](#hasil-statistik).

**Melempar:**

- `ValueError` dengan pesan `Unsupported chart type: ...` jika `chart_type` tidak dikenal.
- `KeyError` jika kunci `data` tidak ada.

Contoh berikut menggambar grafik batang untuk dua dataset:

```python
stats = chart.create_comparison_chart({
    "chart_type": "bar",
    "data": {
        "Milvus": [12.1, 11.8, 12.4, 12.0],
        "Redis": [9.7, 10.2, 9.9, 10.1],
    },
    "title": "Latency pencarian",
    "ylabel": "Latency (ms)",
})
```

### Kunci konfigurasi grafik

| Kunci | Tipe | Default | Berlaku untuk | Keterangan |
|---|---|---|---|---|
| `chart_type` | `str` | `"bar"` | Semua | `bar`, `line`, `box`, `histogram`, atau `dashboard`. Huruf besar-kecil bebas. |
| `data` | `dict` | Wajib | Semua | Nama dataset ke daftar angka. |
| `labels` | `list` | Nomor urut | `bar`, `line` | Label kategori atau sumbu x. Bawaan `Item 1`, `Item 2`, dan seterusnya untuk `bar`; `1`, `2`, dan seterusnya untuk `line`. |
| `title` | `str` | Sesuai tipe | Semua | Judul grafik. |
| `xlabel` | `str` | Sesuai tipe | `bar`, `line`, `histogram` | Label sumbu x. |
| `ylabel` | `str` | Sesuai tipe | Semua | Label sumbu y. Pada `histogram` dengan `density` aktif, sumbu y diberi label `Density`. |
| `colors` | `list[str]` | Palet `ChartGenerator` | Semua | Satu warna per dataset. |
| `figsize` | `list` | `figsize` milik `ChartGenerator`; `[16, 12]` untuk `dashboard` | Semua | Ukuran gambar dalam inci. |
| `show_statistics` | `bool` | `True` | `line`, `box` | Pada `line`: garis rata-rata tiap dataset. Pada `box`: kotak teks ringkasan statistik, jika ada dua dataset atau lebih. |
| `show_difference` | `bool` | `True` | `bar` | Menampilkan selisih persen tiap dataset terhadap dataset pertama. |
| `metric_name` | `str` | Nilai `ylabel` | `dashboard` | Nama metrik di judul setiap panel. |
| `additional_options` | `dict` | `{}` | `line`, `histogram` | Opsi khusus tipe. Lihat tabel berikut. |

Kunci `additional_options`:

| Kunci | Tipe | Default | Berlaku untuk | Keterangan |
|---|---|---|---|---|
| `markers` | `bool` | `True` | `line` | Menampilkan penanda di setiap titik data. |
| `bins` | `int` | `20` | `histogram` | Jumlah kelas histogram. |
| `overlay` | `bool` | `True` | `histogram` | Jika `True`, semua dataset digambar di satu axes. Jika `False`, satu axes per dataset. |
| `density` | `bool` | `True` | `histogram` | Jika `True`, sumbu y menunjukkan kepadatan, bukan frekuensi. |

### Tipe grafik

| `chart_type` | Menampilkan | Judul bawaan | Label sumbu bawaan |
|---|---|---|---|
| `bar` | Batang berdampingan per kategori, dengan nilai di atas tiap batang. | `Bar Chart Comparison` | x: `Categories`, y: `Values` |
| `line` | Satu garis per dataset. | `Line Chart Comparison` | x: `X-axis`, y: `Y-axis` |
| `box` | Sebaran tiap dataset: median, kuartil, pencilan. | `Box Plot Comparison` | y: `Values` |
| `histogram` | Distribusi nilai tiap dataset. | `Histogram Comparison` | x: `Values`, y: `Frequency` |
| `dashboard` | Lima panel: batang, box plot, garis, histogram, dan ringkasan teks. | `Comparison Dashboard` | y: `Values` |

Pada `bar` dan `dashboard`, dataset pertama di `data` menjadi pembanding (baseline).

### Hasil statistik

Nilai kembalian adalah `dict`. Setiap nama dataset menjadi satu kunci yang berisi ringkasan statistik dataset itu. Kunci yang tersedia bergantung pada tipe grafik:

| `chart_type` | Kunci per dataset |
|---|---|
| `bar` | `mean`, `median`, `std`, `min`, `max` |
| `line` | `mean`, `median`, `std`, `trend` |
| `box` | `mean`, `median`, `std`, `q25`, `q75`, `iqr`, `min`, `max` |
| `histogram` | `mean`, `median`, `std`, `skewness`, `kurtosis` |
| `dashboard` | `mean`, `median`, `std`, `min`, `max`, `q25`, `q75`, `count` |

`trend` adalah kemiringan garis lurus yang dicocokkan ke data. `q25` dan `q75` adalah kuartil pertama dan ketiga, dan `iqr` selisih keduanya. `count` adalah jumlah nilai di dataset. Selain `count`, nilai statistik bertipe angka NumPy seperti `numpy.float64`.

Jika ada dua dataset atau lebih, kunci `statistical_tests` berisi hasil uji signifikansi:

| Jumlah dataset | Kunci uji | Isi tiap hasil |
|---|---|---|
| 2 | `t_test`, `mann_whitney`, `kolmogorov_smirnov` | `statistic`, `p_value`, `significant` |
| 3 atau lebih | `anova` | `f_statistic`, `p_value`, `significant` |
| 3 atau lebih | `kruskal_wallis` | `h_statistic`, `p_value`, `significant` |

`significant` bernilai true jika `p_value` di bawah 0.05.

Pada `dashboard` dengan dua dataset atau lebih, kunci `performance_comparisons` membandingkan rata-rata tiap dataset dengan baseline. Setiap perbandingan memakai kunci `BASELINE_vs_DATASET`, misalnya `Milvus_vs_Redis`, dan berisi:

| Kunci | Keterangan |
|---|---|
| `baseline_mean` | Rata-rata dataset pertama. |
| `comparison_mean` | Rata-rata dataset yang dibandingkan. |
| `improvement_percentage` | `(baseline_mean - comparison_mean) / baseline_mean * 100`. Positif berarti rata-ratanya lebih rendah dari baseline. |
| `is_better` | True jika `improvement_percentage` lebih dari 0. Ini menganggap nilai yang lebih rendah lebih baik. |

## `show()`

Menampilkan grafik terakhir dengan `matplotlib.pyplot.show()`. Tidak melakukan apa-apa jika belum ada grafik.

**Mengembalikan:** `None`.

## `save(filename, dpi=300, bbox_inches="tight")`

Menyimpan grafik terakhir ke file. Tidak melakukan apa-apa jika belum ada grafik.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `filename` | `str` | Wajib | Path file tujuan. Format mengikuti ekstensinya, misalnya `.png`. |
| `dpi` | `int` | `300` | Resolusi gambar. |
| `bbox_inches` | `str` | `"tight"` | Diteruskan ke `Figure.savefig`. |

**Mengembalikan:** `None`.

## `clear()`

Menutup grafik terakhir dan mengosongkan `current_fig` serta `current_ax`.

**Mengembalikan:** `None`.

## `create_chart_from_csv(chart_gen, csv_file, config)`

Membaca kolom sebuah file CSV sebagai dataset, lalu memanggil `create_comparison_chart`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `chart_gen` | `ChartGenerator` | Wajib | Pembuat grafik yang dipakai. |
| `csv_file` | `str` | Wajib | Path ke file CSV. |
| `config` | `dict` | Wajib | Konfigurasi grafik, ditambah dua kunci di tabel berikut. Kunci `data` diisi dari CSV. |

Kunci tambahan di `config`:

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `data_columns` | `list[str]` | `[]` | Kolom yang menjadi dataset. Nama kolom menjadi nama dataset. Kolom yang tidak ada di file dilewati. |
| `label_column` | `str` atau `None` | `None` | Kolom yang menjadi `labels`. Diabaikan jika tidak ada di file. |

**Mengembalikan:** `dict` statistik dari `create_comparison_chart`.

## `batch_create_charts(chart_gen, configs)`

Membuat satu grafik untuk setiap konfigurasi di sebuah daftar. Untuk setiap grafik, fungsi ini mencetak kemajuan, menggambar, menyimpan dan menampilkan jika diminta, lalu memanggil `clear()`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `chart_gen` | `ChartGenerator` | Wajib | Pembuat grafik yang dipakai. |
| `configs` | `list[dict]` | Wajib | Daftar konfigurasi grafik, ditambah dua kunci di tabel berikut. |

Kunci tambahan di setiap konfigurasi:

| Kunci | Tipe | Default | Keterangan |
|---|---|---|---|
| `save_filename` | `str` | Tidak ada | Jika ada, grafik disimpan ke file ini. |
| `show` | `bool` | `True` | Jika `True`, grafik ditampilkan dengan `show()`. |

**Mengembalikan:** `list[dict]` berisi statistik setiap grafik, dalam urutan `configs`.

## Lihat juga

- [Membuat grafik perbandingan](../panduan/membuat-grafik.md) untuk langkah pemakaian.
- [Helper kecil](helper.md) untuk `TimerDecorator` dan `save_latency_to_csv`, yang menyiapkan data untuk grafik.
