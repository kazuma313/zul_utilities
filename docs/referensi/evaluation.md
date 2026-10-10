# Evaluasi retrieval

Semua fungsi di paket `zul.evaluation`: dataset tanya-jawab, potongan dokumen, index, retriever, generator, menjalankan RAG, hit rate, skor ragas, laporan, latensi, dan pengaturan. Langkah pemakaiannya ada di [Mengevaluasi retrieval dan RAG](../panduan/mengevaluasi-retrieval.md).

Data mengalir sebagai list dict dengan nama kolom ragas. Untuk dianalisis dengan pandas, tulis `pandas.DataFrame(rows)`.

| Modul | Isi | Extra |
|---|---|---|
| [`dataset`](#dataset) | Membaca dataset, menyimpan dan membaca hasil | Tidak ada; `.xlsx` butuh `evaluation` |
| [`documents`](#documents) | PDF menjadi potongan per halaman atau rekursif | `pdf` |
| [`indexing`](#indexing) | Embedding setiap potongan, skema index Redis | Tidak ada |
| [`milvus_store`](#milvus_store) | Collection Milvus hybrid | `milvus` |
| [`retrievers`](#retrievers) | `RedisRetriever`, `MilvusRetriever`, `FunctionRetriever` | Tidak ada |
| [`generation`](#generation) | `ChatGenerator` | Tidak ada |
| [`runner`](#runner) | `run_rag`, `length_summary` | Tidak ada |
| [`hits`](#hits) | Hit rate dan MRR tanpa penilai | Tidak ada |
| [`judge`](#judge) | `evaluate_rag` dan model penilai | `evaluation` |
| [`reports`](#reports) | `EvalReport`, menyimpan dan membandingkan laporan | Tidak ada |
| [`latency`](#latency) | Latensi dan QPS | Tidak ada |
| [`config`](#config) | Pengaturan dari environment variable | Tidak ada |

`RedisRetriever` dan `MilvusRetriever` menerima objek database dari luar, jadi extra `redis` atau `milvus` dibutuhkan untuk objek itu, bukan untuk modul `retrievers`.

## Kolom data

Dataset dan hasil memakai nama kolom berikut:

| Kolom | Tipe | Isi |
|---|---|---|
| `user_input` | `str` | Pertanyaan. |
| `reference` | `str` | Jawaban acuan. |
| `reference_contexts` | `list[str]` atau `None` | Potongan dokumen acuan. |
| `file_name` | `str` atau `None` | Dokumen asal. |
| `dataset` | `str` | Nama file dataset tanpa ekstensi. |
| `retrieved_contexts` | `list[str]` | Konteks hasil retrieval. Hanya di hasil `run_rag`. |
| `response` | `str` | Jawaban generator; kosong untuk retrieval saja. Hanya di hasil `run_rag`. |
| `retriever`, `generator`, `top_k` | `str`, `str`, `int` | Keterangan percobaan. Hanya di hasil `run_rag`. |

## dataset

`from zul.evaluation.dataset import ...`

### `load_qa_dataset(*paths, column_map=None)`

Membaca satu atau beberapa file tanya-jawab dan menggabungkannya. Baris tanpa pertanyaan dilewati.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `*paths` | `str` atau `Path` | Wajib | File `.xlsx`, `.csv`, `.json`, atau `.jsonl`. |
| `column_map` | `dict[str, str]` atau `None` | `None` | Pemetaan tambahan `{nama kolom asal: nama baku}`. Menimpa `DEFAULT_COLUMNS` untuk nama yang sama. |

Nama kolom asal dicocokkan tanpa membedakan huruf besar dan kecil. `DEFAULT_COLUMNS` memetakan `question`, `query`, dan `pertanyaan` ke `user_input`; `answer`, `ground_truth`, dan `jawaban` ke `reference`; `context`, `contexts`, dan `konteks` ke `reference_contexts`; serta `law`, `source`, dan `sumber` ke `file_name`.

**Mengembalikan:** `list[dict]` dengan kolom `user_input`, `reference`, `reference_contexts`, `file_name`, dan `dataset`.

**Melempar:** `ValueError` jika tidak ada file, atau kolom `user_input` atau `reference` tidak ditemukan. Pesannya menyebut kolom yang ada.

### `describe_dataset(rows)`

**Mengembalikan:** `dict` dengan kunci `jumlah`, `per_dataset` (jumlah baris per file), `punya_reference_contexts`, `rata_panjang_pertanyaan`, dan `rata_panjang_reference`.

### `read_table(path)`

Membaca baris file `.xlsx` (sheet pertama), `.csv`, `.json` (satu list objek), atau `.jsonl` (satu objek per baris) sebagai `list[dict]`, tanpa mengganti nama kolom. **Melempar:** `ValueError` untuk ekstensi lain.

### `as_text_list(value)`

Mengubah teks, list, list berbentuk JSON, atau list berbentuk repr Python seperti `['a', 'b']` menjadi `list[str]`. Sel kosong menjadi `None`.

### `save_results(rows, path)`

Menyimpan baris ke `.csv` atau `.jsonl`; folder tujuan dibuat jika belum ada. Di CSV, kolom berisi list ditulis sebagai JSON. **Mengembalikan:** `Path` file itu. **Melempar:** `ValueError` untuk ekstensi lain.

### `load_results(path)`

Membaca hasil dari `save_results`, atau CSV lama yang ditulis pandas. Kolom list dikembalikan sebagai `list[str]`, kolom indeks tanpa nama dibuang, `top_k` menjadi `int`, dan `response` kosong menjadi `""`.

## documents

`from zul.evaluation.documents import ...` Butuh extra `pdf`.

### `Chunk`

Dataclass satu potongan: `content` (`str`), `source` (nama file PDF), `chunk_index` (`int`), `page` (`int` atau `None`, hanya untuk per halaman), dan `strategy` (`"per_page"` atau `"recursive"`).

### Fungsi

| Fungsi | Mengembalikan |
|---|---|
| `find_pdfs(folder)` | `list[Path]` semua `.pdf` di folder dan subfoldernya, terurut. Melempar `FileNotFoundError` jika folder tidak ada. |
| `read_pdf_pages(path)` | `list[str]` teks setiap halaman. |
| `chunk_per_page(path)` | Satu `Chunk` per halaman yang tidak kosong. |
| `chunk_recursive(path, chunk_size=4000, overlap=450, separators=None)` | Teks seluruh PDF dipotong per paragraf, baris, lalu spasi. |
| `chunk_folder(folder, strategy="recursive", **options)` | Potongan semua PDF di folder. `options` diteruskan ke `chunk_recursive`. Melempar `ValueError` untuk strategi lain. |
| `chunks_to_records(chunks, text_field="content")` | `list[dict]` datar; teks disimpan di kolom `text_field`. |
| `length_stats(chunks)` | `dict` dengan `jumlah`, `min`, `max`, dan `rata` panjang potongan. |

## indexing

`from zul.evaluation.indexing import ...`

### `embed_records(records, embedder, *, text_field="content", vector_field="content_embedding_vector", as_bytes=True, durations=None, show_progress=True)`

Mengembalikan salinan setiap record dengan vektor embedding dari kolom `text_field`. Record asal tidak diubah.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `records` | iterable `dict` | Wajib | Record dari `chunks_to_records`, atau dict lain berisi teks. |
| `embedder` | objek | Wajib | Objek dengan method `embed(text)`, misalnya `AIService`. Hasilnya boleh berupa list atau objek dengan atribut `vector`. |
| `as_bytes` | `bool` | `True` | `True` menulis bytes float32 untuk Redis storage hash; `False` menulis list float untuk Milvus. |
| `durations` | `list[float]` atau `None` | `None` | Jika diberikan, durasi setiap panggilan embedding dalam detik ditambahkan ke list ini. |
| `show_progress` | `bool` | `True` | Menampilkan progress bar jika extra `evaluation` ter-install. |

### `redis_schema(name, prefix, dims, *, algorithm="hnsw", distance_metric="cosine", text_field="content", vector_field="content_embedding_vector", storage="hash")`

**Mengembalikan:** skema RedisVL berbentuk `dict` dengan satu field teks dan satu field vektor float32, untuk `RedisVectorDB.create_index`.

### `to_vector_bytes(vector)`

**Mengembalikan:** vektor sebagai bytes float32.

## milvus_store

`from zul.evaluation.milvus_store import MilvusHybridStore` Butuh extra `milvus`.

### `MilvusHybridStore(settings=None)`

Tersambung ke Milvus dari `MilvusSettings`, bawaannya `MilvusSettings.from_env()`. Database `settings.db_name` dibuat jika belum ada, lalu dipakai.

| Method | Keterangan |
|---|---|
| `ensure_collection(name, dims, *, text_field="content", vector_field="content_embedding_vector", sparse_field="content_embedding_sparse")` | Membuat collection jika belum ada, dengan primary key INT64 auto-id, field teks dengan analyzer, vektor dense dengan index HNSW COSINE, dan vektor sparse dari fungsi BM25. Mengembalikan `True` jika baru dibuat. |
| `insert(name, records, batch_size=200)` | Memasukkan record per batch dan mengembalikan jumlahnya. Vektor harus berupa list float. |
| `hybrid_search(name, query_text, query_vector, *, limit=5, output_fields=None, rrf_k=100, ...)` | Pencarian vektor dense dan BM25, digabung dengan RRF. Mengembalikan satu daftar berisi daftar hasil; setiap hasil punya kunci `entity`. |
| `drop_collection(name)` | Menghapus collection beserta datanya, jika ada. |

## retrievers

`from zul.evaluation.retrievers import ...`

Setiap retriever punya atribut `name` dan method `retrieve(query, top_k=5)` yang mengembalikan `list[str]`. Kelas apa pun dengan bentuk itu memenuhi protokol `Retriever`.

### `RedisRetriever(db, embedder, mode="hybrid", text_field="content", vector_field="content_embedding_vector", alpha=0.7, rrf_k=100, text_scorer="BM25", name="")`

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `db` | `RedisVectorDB` | Wajib | Database yang index-nya sudah dipasang dengan `create_index`. |
| `embedder` | objek | Wajib | Objek dengan method `embed(text)`. Tidak dipanggil di mode `text`. |
| `mode` | `str` | `"hybrid"` | `"vector"`, `"text"` (BM25), `"hybrid"`, atau `"rrf"`. |
| `alpha` | `float` | `0.7` | Bobot skor vektor di mode `hybrid`: 0 teks saja, 1 vektor saja. |
| `rrf_k` | `int` | `100` | Konstanta K di mode `rrf`. |
| `text_scorer` | `str` | `"BM25"` | Penilai full-text di mode `text`, `hybrid`, dan `rrf`. |
| `name` | `str` | `""` | Label hasil; bawaannya `redis-<mode>`. |

**Melempar:** `ValueError` saat dibuat jika `mode` tidak dikenal.

### `MilvusRetriever(store, embedder, collection, text_field="content", rrf_k=100, name="milvus-hybrid")`

Retriever hybrid di atas `MilvusHybridStore`.

### `FunctionRetriever(fn, name="function")`

Retriever dari fungsi `fn(query, top_k) -> list[str]`. Hasilnya dipotong menjadi `top_k` teks.

### `fuse(*ranked_lists, k=100)`

Menggabungkan beberapa daftar konteks dengan Reciprocal Rank Fusion. **Mengembalikan:** `list[str]` terurut dari skor tertinggi.

### `embed_vector(embedder, text)`

**Mengembalikan:** vektor embedding sebagai `list[float]`, dari hasil `embed` berupa list atau objek dengan atribut `vector`.

## generation

`from zul.evaluation.generation import ...`

### `ChatGenerator(model, prompt_template=DEFAULT_PROMPT, max_context_chars=24000, name="chat")`

Membuat jawaban dengan method `answer(question, contexts)`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `model` | objek | Wajib | Objek dengan method `chat(prompt)` yang mengembalikan teks atau objek dengan atribut `content`, misalnya `AIService`. |
| `prompt_template` | `str` | `DEFAULT_PROMPT` | Template dengan `{contexts}` dan `{question}`. |
| `max_context_chars` | `int` | `24000` | Batas panjang gabungan konteks; `0` berarti tanpa batas. |
| `name` | `str` | `"chat"` | Label hasil. |

`DEFAULT_PROMPT` meminta model menjawab hanya dari konteks, menulis "Tidak ditemukan di dokumen" jika jawabannya tidak ada, dan menjawab ringkas dalam bahasa Indonesia. `format_contexts(contexts)` menomori konteks sebagai `[1]`, `[2]`, dan seterusnya.

## runner

`from zul.evaluation.runner import ...`

### `run_rag(rows, retriever, generator=None, *, top_k=5, out_path=None, resume=True, show_progress=True)`

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `rows` | `list[dict]` | Wajib | Dataset dari `load_qa_dataset`. |
| `retriever` | retriever | Wajib | Objek dengan `name` dan `retrieve(query, top_k)`. |
| `generator` | generator atau `None` | `None` | Objek dengan `name` dan `answer(question, contexts)`. `None` membuat `response` kosong. |
| `top_k` | `int` | `5` | Jumlah konteks per pertanyaan. |
| `out_path` | `str`, `Path`, atau `None` | `None` | File `.csv` atau `.jsonl` yang ditulis ulang setiap kali satu pertanyaan selesai. |
| `resume` | `bool` | `True` | Lewati pertanyaan yang sudah ada di `out_path`. Pertanyaan dikenali dari `user_input` dan `dataset`. |
| `show_progress` | `bool` | `True` | Menampilkan progress bar jika extra `evaluation` ter-install. |

**Mengembalikan:** satu `dict` hasil per pertanyaan, dengan urutan yang sama dengan `rows`. Kolomnya ada di [Kolom data](#kolom-data).

### `length_summary(results)`

**Mengembalikan:** `dict` dengan `jumlah`, rata-rata panjang `user_input`, `retrieved_contexts` (total panjang konteks per pertanyaan), `response`, dan `reference`, serta `konteks_kosong`.

## hits

`from zul.evaluation.hits import ...`

### `retrieval_hit_stats(results, *, threshold=0.6)`

Menghitung hit rate dan Mean Reciprocal Rank tanpa penilai. Sebuah konteks dianggap tepat jika kemiripannya dengan acuan paling sedikit `threshold`. Acuannya `reference_contexts` jika ada di salah satu baris; jika tidak, jawaban acuan. Baris tanpa konteks atau tanpa acuan tidak dihitung.

**Mengembalikan:** `dict` dengan `n` (baris yang dihitung), `hit_rate`, `mrr`, `threshold`, dan `sumber` (`"reference_contexts"` atau `"reference"`).

### `similarity(a, b)` dan `first_hit_rank(contexts, targets, threshold=0.6)`

`similarity` mengembalikan kemiripan dua teks dari 0 sampai 1, tanpa membedakan huruf besar dan jumlah spasi; nilainya 1 jika salah satu teks memuat yang lain. `first_hit_rank` mengembalikan peringkat pertama (mulai dari 1) konteks yang cocok, atau `None`.

## judge

`from zul.evaluation.judge import ...` Butuh extra `evaluation`.

### Konstanta metrik

| Nama | Isi |
|---|---|
| `RETRIEVAL_METRICS` | `context_precision`, `context_recall` |
| `GENERATION_METRICS` | `faithfulness`, `answer_relevancy` |
| `DEFAULT_METRICS` | `RETRIEVAL_METRICS` ditambah `GENERATION_METRICS` |
| `NONLLM_METRICS` | `context_precision_nonllm`, `context_recall_nonllm` |
| `KNOWN_METRICS` | Semua metrik di atas |

Kelas ragas di balik setiap nama ada di `zul.adapters.ragas.METRIC_CLASSES`. Skor dikembalikan dengan nama pendek ini, bukan nama kelas ragas.

### `evaluate_rag(results, metrics=DEFAULT_METRICS, *, name="", judge=None, judge_embeddings=None, judge_config=None, judge_backend="instructor", timeout=180, max_workers=8, batch_size=None, raise_exceptions=False, show_progress=True)`

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `results` | `list[dict]`, `str`, atau `Path` | Wajib | Hasil `run_rag`, atau path file `.csv`/`.jsonl`-nya. |
| `metrics` | daftar `str` | `DEFAULT_METRICS` | Nama dari `KNOWN_METRICS`. |
| `name` | `str` | `""` | Label percobaan; bawaannya nama retriever di hasil, atau `"rag"`. |
| `judge` | objek atau `None` | `None` | LLM penilai; jika `None` dibuat dengan `make_judge`. |
| `judge_embeddings` | objek atau `None` | `None` | Embedding penilai untuk `answer_relevancy`; jika `None` dibuat dengan `make_judge_embeddings`. |
| `judge_config` | `JudgeConfig` atau `None` | `None` | Bawaannya `JudgeConfig.from_env()`. |
| `judge_backend` | `str` | `"instructor"` | Lihat `make_judge`. |
| `timeout` | `int` | `180` | Batas detik setiap panggilan penilai. |
| `max_workers` | `int` | `8` | Jumlah panggilan penilai yang berjalan bersamaan. |
| `batch_size` | `int` atau `None` | `None` | Jumlah baris per batch ragas. |
| `raise_exceptions` | `bool` | `False` | `True` untuk berhenti di error pertama. Jika `False`, skor yang gagal bernilai `None`. |
| `show_progress` | `bool` | `True` | Menampilkan progress bar ragas. |

Metrik `faithfulness` dan `answer_relevancy` dilewati jika semua `response` kosong. Penilai tidak dibuat jika hanya metrik `*_nonllm` yang dipilih.

**Mengembalikan:** `EvalReport`. `meta` berisi `n`, `metrik_dilewati`, `judge` (ringkasan pengaturan penilai dengan kunci disamarkan, atau `None`), `retriever`, `generator`, `top_k`, dan `waktu` (UTC).

**Melempar:** `ValueError` jika hasil kosong, ada metrik yang tidak dikenal, tidak ada metrik yang bisa dijalankan, kunci penilai kosong, atau metrik `*_nonllm` dipilih tetapi ada baris tanpa `reference_contexts`.

### `make_judge(config=None, backend="instructor")`

Membuat LLM penilai dari `JudgeConfig`. Backend `"instructor"` memakai client `AsyncOpenAI` dan meminta jawaban berbentuk JSON, sehingga beberapa baris dinilai bersamaan. Backend `"langchain"` memakai chat model LangChain, untuk endpoint yang menolak keluaran JSON atau tool calling. **Melempar:** `ValueError` jika kunci kosong atau backend tidak dikenal.

### `make_judge_embeddings(config=None)`

Membuat embedding penilai untuk `answer_relevancy` dari model embedding LangChain. **Melempar:** `ValueError` jika kunci embedding kosong.

### `select_metrics(results, metrics)` dan `to_samples(results, need_reference_contexts=False)`

`select_metrics` mengembalikan pasangan `(metrik yang dijalankan, metrik yang dilewati)`. `to_samples` menyusun kolom ragas dari setiap hasil; `response` dan `reference_contexts` hanya ikut jika tidak kosong.

## reports

`from zul.evaluation.reports import ...`

### `EvalReport`

Dataclass dengan `name` (`str`), `metrics` (`list[str]`), `summary` (`dict` rata-rata setiap metrik; `None` jika semua skornya gagal), `rows` (`list[dict]` sampel dan skornya), dan `meta` (`dict`).

### Fungsi

| Fungsi | Keterangan |
|---|---|
| `save_report(report, out_dir, name=None)` | Menulis `<nama>.scores.json` (name, summary, metrics, meta) dan `<nama>.rows.csv`. Mengembalikan pasangan path keduanya. |
| `load_report(path)` | Isi file `.scores.json` sebagai `dict`. |
| `compare_reports(*paths)` | Satu `dict` per file `.scores.json`: `name`, skor setiap metrik, dan `n`. |
| `summarize_scores(rows, metrics)` | Rata-rata setiap metrik dari skor per baris; skor `None` dilewati. |

## latency

`from zul.evaluation.latency import ...`

### `measure_latency(fn, inputs, *, repeats=1, workers=1, label="")`

Memanggil `fn(x)` untuk setiap input sebanyak `repeats` kali, dengan `workers` thread bersamaan. QPS dihitung dari waktu dinding. **Mengembalikan:** `LatencyStats`.

### `LatencyStats`

Dataclass dengan `label`, `calls`, `wall_seconds`, `qps`, `mean`, `p50`, `p95`, `p99`, `min`, dan `max`. Semua durasi dalam detik. `as_dict()` mengembalikan semuanya sebagai `dict`.

### `summarize_times(times, label="", wall_seconds=None)` dan `save_times_csv(series, path)`

`summarize_times` meringkas durasi yang dicatat dengan cara lain, misalnya `TimerDecorator(fungsi, verbose=False).get_all_times()`; tanpa `wall_seconds`, QPS dihitung dari total durasi. `save_times_csv` menyimpan beberapa deret durasi ke satu CSV, satu kolom per deret; panjang deret boleh berbeda.

## config

`from zul.evaluation.config import ...`

| Kelas | Dibaca dari | Keterangan |
|---|---|---|
| `JudgeConfig` | `RAGAS_JUDGE_MODEL` (bawaan `gpt-4o-mini`), `RAGAS_JUDGE_API_KEY` atau `OPENAI_API_KEY`, `RAGAS_JUDGE_BASE_URL`, `RAGAS_EMBEDDING_MODEL` (bawaan `text-embedding-3-small`), `RAGAS_EMBEDDING_API_KEY`, `RAGAS_EMBEDDING_BASE_URL` | Kunci dan alamat embedding memakai milik model penilai jika kosong. `validate()` melempar `ValueError` jika kunci penilai kosong. |
| `RedisSettings` | `REDIS_URL`, atau `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_USERNAME`, `REDIS_DB` | `connect()` mengembalikan `RedisVectorDB`; butuh extra `redis`. |
| `MilvusSettings` | `MILVUS_URI`, `MILVUS_PORT`, `MILVUS_DB` | `address` berisi alamat lengkap untuk `MilvusClient`. |

Setiap kelas dibuat dari environment dengan `from_env()`. `JudgeConfig` dan `RedisSettings` punya `safe_summary()`, yang menyamarkan kunci dan kata sandi menjadi empat karakter terakhirnya, misalnya `…1234`.

## Halaman terkait

- [Mengevaluasi retrieval dan RAG](../panduan/mengevaluasi-retrieval.md)
- [Lapisan adapter](../konsep/lapisan-adapter.md), termasuk penambal impor di adapter ragas.
- [RedisHelper](redis.md) dan [MilvusHelper](milvus.md)
