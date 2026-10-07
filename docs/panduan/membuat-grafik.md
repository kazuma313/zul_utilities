# Membuat grafik perbandingan

`ChartGenerator` membandingkan dua dataset atau lebih, misalnya latency pencarian di Milvus dan Redis. Satu pemanggilan menghasilkan grafik perbandingan dan ringkasan statistik beserta uji signifikansinya.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang ([Memasang Zul](memasang-zul.md)) dan data berupa daftar angka untuk setiap hal yang dibandingkan.

## Membuat grafik pertama

1. Pasang Zul dengan extra `analysis`:

    ```shell
    pip install "zul[analysis] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Jelaskan grafik dalam satu dict. Kunci `data` berisi dataset yang dibandingkan: nama dataset sebagai kunci, daftar angka sebagai nilai:

    ```python
    chart_config = {
        "chart_type": "bar",
        "data": {
            "Milvus": [12.1, 11.8, 12.4, 12.0],
            "Redis": [9.7, 10.2, 9.9, 10.1],
        },
        "labels": ["Query 1", "Query 2", "Query 3", "Query 4"],
        "title": "Latency pencarian",
        "xlabel": "Query",
        "ylabel": "Latency (ms)",
    }
    ```

3. Gambar grafiknya. `create_comparison_chart` mengembalikan statistiknya:

    ```python
    from zul.utilities.analysis import ChartGenerator

    chart = ChartGenerator()
    stats = chart.create_comparison_chart(chart_config)
    ```

4. Simpan grafik ke file, lalu tutup supaya memori tidak menumpuk saat kamu membuat banyak grafik:

    ```python
    chart.save("latency.png")
    chart.clear()
    ```

    Di notebook, panggil `chart.show()` sebelum `chart.clear()` untuk menampilkan grafik tanpa menyimpannya.

## Memilih tipe grafik

1. Pilih nilai `chart_type` sesuai yang ingin kamu lihat:

    - `bar`: nilai per kategori, dengan selisih persen terhadap dataset pertama.
    - `line`: tren dari waktu ke waktu, dengan garis rata-rata.
    - `box`: sebaran dan kestabilan tiap dataset.
    - `histogram`: bentuk distribusi nilai.
    - `dashboard`: gabungan keempatnya dan ringkasan teks, untuk laporan satu metrik.

2. Pada `bar` dan `dashboard`, tulis sistem yang menjadi acuan sebagai dataset pertama di `data`. Dataset pertama dianggap pembanding (*baseline*).

3. Taruh opsi khusus sebuah tipe di `additional_options`. Contoh berikut mengatur histogram:

    ```python
    before = [102.0, 98.5, 110.2, 95.1, 104.7, 99.3]
    after = [88.4, 91.0, 85.2, 90.6, 87.9, 89.5]

    histogram_stats = chart.create_comparison_chart({
        "chart_type": "histogram",
        "data": {"Sebelum": before, "Sesudah": after},
        "additional_options": {"bins": 30, "overlay": True, "density": True},
    })
    chart.save("distribusi.png")
    chart.clear()
    ```

    Semua kunci konfigurasi dan opsi tiap tipe ada di [Referensi ChartGenerator](../referensi/grafik.md).

## Membaca hasil statistik

Bagian ini memakai `stats` dari grafik `bar` di [Membuat grafik pertama](#membuat-grafik-pertama).

1. Ambil ringkasan statistik sebuah dataset lewat namanya:

    ```python
    milvus = stats["Milvus"]

    print(f"{milvus['mean']:.3f} {milvus['median']:.2f} {milvus['std']:.3f}")
    ```

    Untuk data contoh, kode itu mencetak:

    ```text
    12.075 12.05 0.217
    ```

2. Periksa apakah perbedaannya signifikan. Jika ada dua dataset atau lebih, kunci `statistical_tests` berisi hasil uji. Setiap hasil punya `p_value` dan `significant`, yang bernilai true jika `p_value` di bawah 0.05:

    ```python
    test = stats["statistical_tests"]["t_test"]

    if test["significant"]:
        print(f"Perbedaannya signifikan (p = {test['p_value']:.4f})")
    ```

    Dengan dua dataset, uji yang tersedia adalah `t_test`, `mann_whitney`, dan `kolmogorov_smirnov`. Dengan tiga dataset atau lebih, uji yang tersedia adalah `anova` dan `kruskal_wallis`.

3. Untuk membandingkan rata-rata dengan baseline, buat grafik `dashboard` lalu baca `performance_comparisons`:

    ```python
    dashboard_stats = chart.create_comparison_chart({**chart_config, "chart_type": "dashboard"})
    chart.clear()

    comparison = dashboard_stats["performance_comparisons"]["Milvus_vs_Redis"]
    print(f"{comparison['improvement_percentage']:.1f}")
    ```

    Untuk data contoh, kode itu mencetak selisih rata-rata Redis terhadap Milvus dalam persen:

    ```text
    17.4
    ```

> [!NOTE]
> `improvement_percentage` dan `is_better` menganggap nilai yang lebih rendah lebih baik, seperti pada latency: nilai positif berarti rata-ratanya lebih rendah dari baseline. Untuk metrik yang lebih tinggi lebih baik, seperti throughput atau akurasi, baca tandanya terbalik.

## Membuat grafik dari CSV

1. Siapkan file CSV dengan satu kolom per dataset dan, jika ada, satu kolom label:

    ```text title="hasil_benchmark.csv"
    query,milvus_ms,redis_ms
    q1,12.1,9.7
    q2,11.8,10.2
    q3,12.4,9.9
    ```

2. Panggil `create_chart_from_csv`. Sebut kolom dataset di `data_columns` dan kolom label di `label_column`:

    ```python
    from zul.utilities.analysis import ChartGenerator, create_chart_from_csv

    chart = ChartGenerator()

    csv_stats = create_chart_from_csv(chart, "hasil_benchmark.csv", {
        "chart_type": "line",
        "data_columns": ["milvus_ms", "redis_ms"],
        "label_column": "query",
        "title": "Latency per query",
        "ylabel": "ms",
    })
    chart.save("latency_per_query.png")
    chart.clear()
    ```

    Kolom di `data_columns` yang tidak ada di file dilewati.

## Membuat banyak grafik sekaligus

1. Tulis satu konfigurasi per grafik. Tambahkan `save_filename` agar grafik disimpan, dan `"show": False` saat menjalankan di script atau server supaya grafik tidak dibuka di jendela:

    ```python
    latency = {"Milvus": [12.1, 11.8, 12.4], "Redis": [9.7, 10.2, 9.9]}
    memory = {"Milvus": [512, 520, 508], "Redis": [480, 485, 475]}

    configs = [
        {"chart_type": "bar", "data": latency, "title": "Latency",
         "save_filename": "batch_latency.png", "show": False},
        {"chart_type": "box", "data": memory, "title": "Memory",
         "save_filename": "batch_memory.png", "show": False},
    ]
    ```

2. Berikan daftar itu ke `batch_create_charts`:

    ```python
    from zul.utilities.analysis import ChartGenerator, batch_create_charts

    results = batch_create_charts(ChartGenerator(), configs)
    ```

    `results` berisi satu dict statistik untuk setiap grafik, dalam urutan yang sama.

## Memeriksa hasilnya

Untuk memastikan grafik pertama tersimpan dan statistiknya terhitung, periksa file dan isi `stats` dari [Membuat grafik pertama](#membuat-grafik-pertama):

```python
from pathlib import Path

print(Path("latency.png").exists())
print(sorted(stats))
```

Kode itu mencetak `True`, lalu nama kedua dataset dan kunci hasil uji:

```text
True
['Milvus', 'Redis', 'statistical_tests']
```

Buka `latency.png` untuk melihat grafiknya.

## Halaman terkait

- [Referensi ChartGenerator](../referensi/grafik.md) untuk semua kunci konfigurasi, tipe grafik, dan kunci statistik.
- [Memakai helper kecil](memakai-helper.md) untuk `TimerDecorator`, yang mengumpulkan durasi untuk dibandingkan, dan `save_latency_to_csv`.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) dan [Menyimpan dan mencari vektor di Redis](memakai-redis.md) untuk sistem yang dibandingkan di contoh.
