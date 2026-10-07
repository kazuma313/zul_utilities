# Memakai helper kecil

Helper kecil di `zul.utilities` yang tidak punya panduan sendiri: embedding palsu untuk test, logger, pengukur waktu, pembaca PDF, penyimpan hasil eksperimen, dan pengubah Document menjadi JSON. Setiap bagian berdiri sendiri.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang ([Memasang Zul](memasang-zul.md)). Tiga tugas membutuhkan extra: membaca PDF memakai extra `pdf`, menyimpan latency ke CSV memakai extra `analysis`, dan menjalankan graph LangGraph memakai extra `llm`. Perintah pemasangannya ada di bagian masing-masing.

## Membuat embedding palsu untuk test

`FakeEmbeddingModel` menghasilkan vektor acak dengan dimensi yang kamu tentukan, sehingga alur insert dan search di vector database bisa diuji tanpa model embedding, GPU, atau API key.

1. Buat model dengan dimensi yang sama dengan field vektor di database-mu:

    ```python
    from zul.utilities.fake_embedding import FakeEmbeddingModel

    model = FakeEmbeddingModel(dimension=768, seed=42)
    ```

2. Ubah satu teks atau daftar teks menjadi vektor dengan `encode`:

    ```python
    print(model.encode("hallo").shape)
    print(model.encode(["a", "b", "c"]).shape)
    ```

    Hasilnya selalu berbentuk dua dimensi, satu baris per teks:

    ```text
    (1, 768)
    (3, 768)
    ```

3. Untuk mendapat satu vektor datar, panggil `flatten()` pada hasilnya:

    ```python
    vector = model.encode("hallo").flatten()
    ```

    Teks yang sama selalu menghasilkan vektor yang sama untuk `seed` yang sama, termasuk di proses Python yang berbeda. Data yang kamu simpan hari ini bisa dicari lagi besok dengan query yang sama.

> [!NOTE]
> Vektornya acak, jadi kemiripan antar teks tidak punya arti. `FakeEmbeddingModel` menguji bahwa pipeline berjalan, bukan bahwa hasil pencarian relevan.

## Menulis log ke console dan file

1. Ambil logger dengan `get_logger`, lalu pakai seperti logger Python biasa:

    ```python
    from zul.utilities.logger import get_logger

    logger = get_logger()
    logger.info("mulai memproses %d dokumen", 120)
    ```

    Tanpa argumen, logger bernama `my_service` dan menulis ke console serta ke `logs/app.log`. Folder file log dibuat jika belum ada. Setiap baris log berbentuk seperti ini:

    ```text
    2026-10-01 17:13:40,496 | INFO | my_service | mulai memproses 120 dokumen
    ```

2. Untuk nama, level, dan file lain, kirim ketiganya sebagai argumen:

    ```python
    logger = get_logger("ingestion", level="DEBUG", log_file="logs/ingestion.log")
    ```

    Memanggil `get_logger` lagi dengan nama yang sama mengembalikan logger yang sama dan tidak menggandakan keluarannya. `level` dan `log_file` hanya dipakai pada pemanggilan pertama untuk nama itu.

## Mengukur waktu eksekusi

1. Untuk mencetak durasi setiap pemanggilan sebuah fungsi, pasang decorator `timer_func`:

    ```python
    from zul.utilities.script_helper.eval_performance import TimerDecorator, timer_func


    @timer_func
    def ingest(documents):
        ...
    ```

2. Untuk menyimpan setiap durasi, pasang `TimerDecorator`:

    ```python
    @TimerDecorator
    def search(query):
        ...


    for query in ["satu", "dua", "tiga"]:
        search(query)
    ```

    Kedua decorator mencetak satu baris per pemanggilan, misalnya `Function 'search' executed in 0.0000s`.

3. Baca durasi yang terkumpul dari fungsi yang sudah diberi `TimerDecorator`:

    ```python
    print(search.get_average_time())   # rata-rata, dalam detik
    print(search.get_all_times())      # semua durasi
    search.reset_times()               # menghapus semua catatan
    ```

4. Untuk membandingkan dua implementasi, berikan durasinya ke `ChartGenerator`. Contoh berikut mengandaikan dua fungsi yang sudah diberi `TimerDecorator`, yaitu `search_milvus` dan `search_redis`:

    ```python
    from zul.utilities.analysis import ChartGenerator

    chart = ChartGenerator()
    chart.create_comparison_chart({
        "chart_type": "box",
        "data": {
            "Milvus": search_milvus.get_all_times(),
            "Redis": search_redis.get_all_times(),
        },
        "ylabel": "Detik",
    })
    chart.save("latency.png")
    ```

    Langkah lengkapnya ada di [Membuat grafik perbandingan](membuat-grafik.md).

## Membaca dan memotong PDF

`PDFProcessor` membaca teks yang tertanam di PDF dan memotongnya menjadi chunk, sebagai langkah awal pipeline RAG. Untuk PDF hasil scan, pakai OCR di [Mengubah dokumen menjadi teks](membaca-dokumen-ocr.md).

1. Pasang Zul dengan extra `pdf`:

    ```shell
    pip install "zul[pdf] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Baca teks per halaman atau sebagai satu string:

    ```python
    from zul.utilities.script_helper.read_pdf2 import PDFProcessor

    pdf = PDFProcessor()

    pages = pdf.read_pdf_pages("peraturan.pdf")           # daftar teks, satu per halaman
    text = pdf.read_pdf_as_single_text("peraturan.pdf")   # satu string
    ```

3. Potong menjadi chunk. Hasilnya adalah daftar `Document` LangChain:

    ```python
    chunks = pdf.chunk_recursive_character_splitter(
        "peraturan.pdf",
        chunk_size=1000,
        overlap=200,
    )

    per_page = pdf.chunk_per_page("peraturan.pdf")
    ```

4. Periksa kegagalan. Method `PDFProcessor` tidak melempar exception saat PDF gagal dibaca. Mereka mengembalikan `None` atau daftar kosong, dan pesan kesalahannya tersimpan di `pdf.last_error`:

    ```python
    pages = pdf.read_pdf_pages("rusak.pdf")

    if pages is None:
        print(pdf.last_error)
    ```

5. Untuk meringkas satu folder berisi PDF, termasuk subfoldernya, panggil `process_folder`:

    ```python
    summary = pdf.process_folder("dokumen/")

    print(summary["total_files"], summary["total_pages"], summary["failed_files"])
    ```

## Menyimpan hasil eksperimen

Dua fungsi menyimpan hasil ke folder `data/` di direktori kerja saat ini. Folder itu dibuat jika belum ada. Modul ini mengimpor `pandas`, jadi pasang extra `analysis` lebih dulu.

1. Pasang Zul dengan extra `analysis`:

    ```shell
    pip install "zul[analysis] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Simpan teks, misalnya hasil OCR, ke file Markdown. Nama file ditulis tanpa ekstensi:

    ```python
    from zul.utilities.script_helper.save_file import save_latency_to_csv, save_text_to_md

    save_text_to_md("# Hasil OCR\n\nIsi dokumen.", "hasil_ocr")
    ```

    Kode itu menulis `data/hasil_ocr.md`.

3. Simpan daftar latency ke CSV. Setiap kunci dict menjadi satu kolom, jadi semua daftar harus sama panjang:

    ```python
    save_latency_to_csv(
        {"short": [0.11, 0.12], "long": [0.31, 0.29]},
        file_name="latency_milvus",
    )
    ```

    Kode itu menulis `data/latency_milvus.csv` dengan isi berikut:

    ```text title="data/latency_milvus.csv"
    short,long
    0.11,0.31
    0.12,0.29
    ```

## Mengubah Document menjadi JSON

1. Berikan daftar `Document` LangChain, misalnya `chunks` dari `PDFProcessor`, ke `documents_to_custom_json`:

    ```python
    from langchain_core.documents import Document

    from zul.utilities.script_helper.json_helper import documents_to_custom_json

    documents = [
        Document(page_content="isi satu", metadata={"source": "a.pdf", "page": 1}),
        Document(page_content="isi dua"),
    ]

    json_text = documents_to_custom_json(documents)
    ```

    `json_text` adalah string JSON. `page_content` dan setiap kunci `metadata` menjadi kunci di tingkat atas.

2. Untuk mengganti nama kunci agar cocok dengan skema tujuan, berikan `key_mapping`. Untuk mendapat objek Python, bukan string, set `return_dict=True`:

    ```python
    rows = documents_to_custom_json(
        documents,
        key_mapping={"page_content": "text", "source": "url"},
        return_dict=True,
    )
    print(rows)
    ```

    Kode itu mencetak:

    ```text
    [{'text': 'isi satu', 'url': 'a.pdf', 'page': 1}, {'text': 'isi dua'}]
    ```

## Menjalankan graph LangGraph terkecil

Modul `react_graph` berisi graph satu node sebagai titik awal memahami `StateGraph`, sebelum membaca agent yang lebih lengkap di proyek hasil `zul build hexa`.

1. Pasang Zul dengan extra `llm`:

    ```shell
    pip install "zul[llm] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

2. Impor graph yang sudah ter-compile, lalu panggil dengan state awal:

    ```python
    from zul.utilities.react_graph import graph

    print(graph.invoke({"a": "hello"}))
    ```

    Node di graph itu mengganti nilai `a`, jadi kode itu mencetak:

    ```text
    {'a': 'goodbye'}
    ```

Cara kerja graph agent yang sebenarnya ada di [Cara kerja agent ReAct](../konsep/agent-react.md).

## Memeriksa hasilnya

Untuk memastikan helper bisa diimpor dari environment-mu, jalankan:

```shell
python -c "from zul.utilities.fake_embedding import FakeEmbeddingModel; print(FakeEmbeddingModel(dimension=4).encode('halo').shape)"
```

Perintah itu mencetak bentuk vektornya:

```text
(1, 4)
```

## Halaman terkait

- [Referensi helper kecil](../referensi/helper.md) untuk semua parameter, nilai kembalian, dan path impor lama.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) dan [Menyimpan dan mencari vektor di Redis](memakai-redis.md) untuk memakai `FakeEmbeddingModel` dan pengukur waktu.
- [Membuat grafik perbandingan](membuat-grafik.md) untuk menggambar durasi yang terkumpul.
- [Mengubah dokumen menjadi teks](membaca-dokumen-ocr.md) untuk PDF hasil scan.
