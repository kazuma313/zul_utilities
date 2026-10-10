# Mengevaluasi retrieval dan RAG

Panduan ini menilai seberapa tepat retriever-mu mengambil konteks, dan seberapa baik jawaban yang dibuat dari konteks itu, dengan [ragas](https://docs.ragas.io/). Langkahnya sama untuk Redis, Milvus, atau retriever buatanmu sendiri: baca dataset tanya-jawab, jalankan retrieval untuk setiap pertanyaan, periksa cepat tanpa model penilai, lalu nilai dengan ragas.

**Sebelum mulai:** kamu butuh dataset tanya-jawab (.xlsx, .csv, .json, atau .jsonl) berisi pertanyaan dan jawaban acuan, serta API key untuk model penilai. Install Zul dengan extra `evaluation`, ditambah extra untuk tempat penyimpananmu:

```shell
pip install "zul[evaluation,redis,llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Ganti `redis` dengan `milvus` untuk Milvus. Tambahkan `pdf` jika index-nya juga dibangun dari PDF.

## Mencoba tanpa server

Contoh berikut menjalankan alurnya dengan retriever sederhana dan tanpa API key, untuk memastikan dataset-mu terbaca. Simpan dataset kecil sebagai `qa.csv`:

```text title="qa.csv"
question,answer
Apa itu mistika?,Mistika adalah ajaran kebatinan.
Bagaimana Engels membedakan filsuf?,Engels membedakan idealis dan materialis.
```

Lalu jalankan script ini di folder yang sama:

```python
import re

from zul.evaluation.dataset import load_qa_dataset
from zul.evaluation.hits import retrieval_hit_stats
from zul.evaluation.retrievers import FunctionRetriever
from zul.evaluation.runner import run_rag

DOKUMEN = [
    "Dialektika membahas pertentangan.",
    "Mistika adalah ajaran kebatinan.",
    "Engels membedakan idealis dan materialis.",
]


def kata(teks):
    return set(re.findall(r"\w+", teks.lower()))


def cari(pertanyaan, k):
    urutan = sorted(DOKUMEN, key=lambda teks: -len(kata(pertanyaan) & kata(teks)))
    return urutan[:k]


rows = load_qa_dataset("qa.csv")
results = run_rag(rows, FunctionRetriever(cari, name="kata-sama"), top_k=2)
print(results[0]["retrieved_contexts"])
print(retrieval_hit_stats(results))
```

Script itu mencetak konteks untuk pertanyaan pertama, lalu hit rate dan MRR:

```text
['Mistika adalah ajaran kebatinan.', 'Dialektika membahas pertentangan.']
{'n': 2, 'hit_rate': 1.0, 'mrr': 1.0, 'threshold': 0.6, 'sumber': 'reference'}
```

Bagian berikutnya mengganti retriever sederhana itu dengan Redis atau Milvus, lalu menambahkan penilaian ragas.

## Mengisi environment variable

Kunci dan alamat server dibaca dari environment variable, tidak ditulis di kode. Model penilai ragas sengaja dipisah dari model yang dinilai: penilai sebaiknya model yang lebih kuat, karena skor dari model yang menilai jawabannya sendiri tidak berarti apa-apa.

| Variabel | Untuk |
|---|---|
| `RAGAS_JUDGE_MODEL`, `RAGAS_JUDGE_API_KEY`, `RAGAS_JUDGE_BASE_URL` | Model penilai. Tanpa `RAGAS_JUDGE_API_KEY`, yang dipakai `OPENAI_API_KEY`. Tanpa base URL, yang dipakai OpenAI. |
| `RAGAS_EMBEDDING_MODEL`, `RAGAS_EMBEDDING_API_KEY`, `RAGAS_EMBEDDING_BASE_URL` | Embedding penilai, hanya untuk `answer_relevancy`. Kunci dan alamatnya memakai milik model penilai jika kosong. |
| `REDIS_URL`, atau `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_USERNAME`, `REDIS_DB` | Redis Stack yang menyimpan index. |
| `MILVUS_URI`, `MILVUS_PORT`, `MILVUS_DB` | Milvus. |
| `LLM_*` dan `EMBEDDING_*` | Model yang dinilai, lewat `AIService`. Lihat [Mengatur model dan API key](mengatur-llm.md). |

Di notebook atau script, muat file `.env` dengan `python-dotenv` sebelum memanggil fungsi Zul:

```python
from dotenv import load_dotenv

load_dotenv()
```

## Membaca dataset tanya-jawab

`load_qa_dataset` membaca satu atau beberapa file dan menggabungkannya. Nama kolom seperti `question`, `answer`, `ground_truth`, `context`, `pertanyaan`, dan `jawaban` dikenali otomatis:

```python
from zul.evaluation.dataset import describe_dataset, load_qa_dataset

rows = load_qa_dataset("data/question_answer.xlsx", "data/rag_evaluation.xlsx")
print(describe_dataset(rows))
```

Jika nama kolommu berbeda, beri pemetaannya dengan `column_map={"tanya": "user_input", "jawab": "reference"}`. Kolom `dataset` di setiap baris berisi nama file asalnya, jadi hasil dari beberapa file tetap bisa dipisah saat dianalisis.

## Menyiapkan retriever

Retriever apa pun cukup punya method `retrieve(query, top_k)`. Pilih salah satu berikut.

### Redis

Pasang index yang sudah terisi, lalu buat `RedisRetriever` dengan mode pencariannya. `create_index(schema, overwrite=False)` tidak menghapus isi index yang sudah ada:

```python
from zul.evaluation.config import RedisSettings
from zul.evaluation.indexing import redis_schema
from zul.evaluation.retrievers import RedisRetriever
from zul.utilities.embedding_service import AIService

ai = AIService.from_env()
db = RedisSettings.from_env().connect()
db.create_index(redis_schema("recursive_qwen", prefix="recursive", dims=2560))

retriever = RedisRetriever(db, ai, mode="rrf", rrf_k=100)
```

Mode yang tersedia adalah `vector`, `text` (BM25), `hybrid` (skor digabung Redis dengan bobot `alpha`), dan `rrf` (pencarian vektor dan teks dijalankan terpisah, lalu peringkatnya digabung).

### Milvus

`MilvusHybridStore` membuat collection dengan vektor dense dan BM25, lalu `MilvusRetriever` mencarinya secara hybrid:

```python
from zul.evaluation.config import MilvusSettings
from zul.evaluation.milvus_store import MilvusHybridStore
from zul.evaluation.retrievers import MilvusRetriever

store = MilvusHybridStore(MilvusSettings.from_env())
retriever = MilvusRetriever(store, ai, collection="recursive_qwen")
```

### Fungsi sendiri

Untuk API luar atau pencarian buatanmu, bungkus fungsinya: `FunctionRetriever(lambda query, k: [...], name="api-saya")`.

## Menjalankan retrieval dan jawaban

`run_rag` mengambil konteks untuk setiap pertanyaan. Dengan `ChatGenerator`, jawaban juga dibuat dari konteks itu:

```python
from zul.evaluation.generation import ChatGenerator
from zul.evaluation.runner import length_summary, run_rag

results = run_rag(
    rows, retriever, ChatGenerator(ai), top_k=5, out_path="outputs/redis-rrf.csv"
)
print(length_summary(results))
```

Hasil ditulis ke `out_path` setiap kali satu pertanyaan selesai. Jika proses terputus, misalnya karena koneksi putus, jalankan perintah yang sama lagi: pertanyaan yang sudah ada di file itu dilewati. Untuk menilai retrieval saja, hilangkan generator-nya: `run_rag(rows, retriever, top_k=5)`.

`length_summary` mencetak rata-rata panjang setiap kolom dan `konteks_kosong`, yaitu jumlah pertanyaan tanpa konteks. Angka itu harus 0 sebelum hasilnya dinilai.

## Memeriksa cepat tanpa penilai

Sebelum membayar model penilai, hitung hit rate dan MRR dari kemiripan teks:

```python
from zul.evaluation.hits import retrieval_hit_stats

print(retrieval_hit_stats(results))
```

Jika dataset punya kolom konteks acuan (`reference_contexts`), konteks yang terambil dibandingkan dengan konteks itu. Jika tidak, yang dicari adalah jawaban acuan di dalam konteks. Cara kedua kasar, tetapi cukup untuk membandingkan tren antar retriever.

## Menilai dengan ragas

`evaluate_rag` menilai hasil dengan metrik yang kamu pilih, lalu `save_report` menyimpan ringkasan dan skor per baris:

```python
from zul.evaluation.judge import RETRIEVAL_METRICS, evaluate_rag
from zul.evaluation.reports import save_report

report = evaluate_rag(results, metrics=RETRIEVAL_METRICS, name="redis-rrf")
print(report)
save_report(report, "outputs")
```

Metrik yang tersedia:

| Metrik | Menilai | Butuh |
|---|---|---|
| `context_precision` | Konteks yang relevan ada di peringkat atas. | Penilai, jawaban acuan |
| `context_recall` | Semua yang dibutuhkan jawaban acuan ikut terambil. | Penilai, jawaban acuan |
| `faithfulness` | Jawaban hanya berisi hal yang ada di konteks. | Penilai, jawaban |
| `answer_relevancy` | Jawaban menjawab pertanyaannya. | Penilai, embedding penilai, jawaban |
| `context_precision_nonllm`, `context_recall_nonllm` | Sama dengan dua metrik pertama, dengan kemiripan teks. | Konteks acuan |

`RETRIEVAL_METRICS` berisi dua metrik pertama, dan `DEFAULT_METRICS` berisi empat metrik pertama. Metrik yang butuh jawaban dilewati otomatis jika hasilnya tanpa jawaban, dan namanya dicatat di `report.meta["metrik_dilewati"]`.

Untuk membandingkan beberapa percobaan dalam satu tabel:

```python
import pandas as pd

from zul.evaluation.reports import compare_reports

table = compare_reports("outputs/redis-rrf.scores.json", "outputs/milvus-hybrid.scores.json")
print(pd.DataFrame(table).set_index("name"))
```

## Membangun index dari PDF

Untuk membandingkan cara memotong dokumen, potong PDF-nya, beri embedding, lalu masukkan ke index baru:

```python
from zul.evaluation.documents import chunk_folder, chunks_to_records, length_stats
from zul.evaluation.indexing import embed_records, redis_schema

chunks = chunk_folder("data/pdf", strategy="recursive", chunk_size=4000, overlap=450)
print(length_stats(chunks))

db.create_index(redis_schema("recursive_qwen", prefix="recursive", dims=2560))
db.insert_data(embed_records(chunks_to_records(chunks), ai), batch_size=100)
```

`strategy="per_page"` membuat satu potongan per halaman. Untuk Milvus, tulis vektornya sebagai list dengan `embed_records(..., as_bytes=False)`, lalu masukkan dengan `store.ensure_collection(nama, dims=2560)` dan `store.insert(nama, records)`.

## Mengukur latensi

`measure_latency` memanggil retriever untuk setiap pertanyaan, berulang dan dengan beberapa thread, lalu meringkas p50, p95, p99, dan QPS:

```python
from zul.evaluation.latency import measure_latency

questions = [row["user_input"] for row in rows]
stats = measure_latency(
    lambda q: retriever.retrieve(q, top_k=5), questions, repeats=10, workers=8
)
print(stats)
```

## Jika skornya bermasalah

Tabel berikut mencantumkan masalah yang paling sering muncul beserta penyelesaiannya:

| Gejala | Penyebab | Penyelesaian |
|---|---|---|
| Semua skor bernilai `None` | Penilai gagal menjawab, misalnya melewati batas waktu. | Naikkan `timeout`, atau jalankan dengan `raise_exceptions=True` untuk melihat error-nya. |
| Error tentang JSON atau tool calling dari endpoint penilai | Endpoint-nya tidak mendukung keluaran terstruktur. | Pakai `evaluate_rag(..., judge_backend="langchain")`. |
| `Kunci model penilai kosong` | `RAGAS_JUDGE_API_KEY` dan `OPENAI_API_KEY` kosong. | Isi salah satunya, lalu muat ulang `.env`. |
| `Metrik *_nonllm butuh reference_contexts` | Ada baris dataset tanpa konteks acuan. | Pakai metrik dengan penilai, atau lengkapi kolom konteks di dataset. |

## Halaman terkait

- [Referensi: Evaluasi retrieval](../referensi/evaluation.md)
- [Redis](memakai-redis.md) dan [Milvus](memakai-milvus.md) untuk menyiapkan index.
- [LLM dan embedding](memanggil-llm-dan-embedding.md) untuk `AIService`.
