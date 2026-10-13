# Studi evaluasi retrieval: Redis, chunking, dan ragas

Folder ini berisi studi perbandingan retrieval di Redis: chunk per halaman lawan chunk rekursif, dan mode `hybrid` lawan `rrf`, dinilai dengan ragas. Kodenya ada di paket Zul, `zul.evaluation`. Folder ini hanya berisi notebook, script, dan data studinya.

Cara memakai fungsinya ada di dokumentasi Zul: panduan [Mengevaluasi retrieval dan RAG](../../../docs/panduan/mengevaluasi-retrieval.md) dan referensi [Evaluasi retrieval](../../../docs/referensi/evaluation.md).

| File | Isi |
| --- | --- |
| `pipline_performance_redis_from_sgd.ipynb` | Chunking, embedding, mengisi index Redis, dan latensi query per panjang pertanyaan. |
| `RAG_eval_redis.ipynb` | Menjalankan RAG untuk setiap varian index dan mode, lalu menilainya dengan ragas. |
| `run_eval.py` | Langkah yang sama dari terminal. |
| `data/` | Dataset tanya-jawab dan PDF. Tidak ikut repo, kecuali `latency_questions.example.json`. |
| `outputs/` | Hasil RAG, skor ragas, dan latensi. Tidak ikut repo. |
| `_arsip_rag_eval/` | Salinan paket `rag_eval` sebelum dipindah ke `zul.evaluation`. Tidak ikut repo; boleh dihapus. |

## Menyiapkan

Dari akar repo `zul_utilites`:

```bash
uv sync --inexact --extra evaluation --extra redis --extra pdf --extra llm
```

Isi `.env` di akar repo dengan model yang dinilai (`LLM_*`, `EMBEDDING_*`), model penilai (`RAGAS_JUDGE_*`, `RAGAS_EMBEDDING_*`), dan Redis (`REDIS_URL` atau `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`). Daftar lengkapnya ada di panduan.

## Menjalankan ulang

1. Jalankan `pipline_performance_redis_from_sgd.ipynb` sekali untuk mengisi index `recursives_redis_sgd` dan `pages_redis_sgd`.
2. Jalankan `RAG_eval_redis.ipynb`. Hasil RAG ditulis ke `outputs/<varian>.csv` sambil berjalan, jadi proses yang terputus dilanjutkan dari pertanyaan yang belum selesai.

Dari terminal, di folder ini:

```bash
uv run python run_eval.py dataset data/question_answer.xlsx
uv run python run_eval.py rag data/question_answer.xlsx --index recursives_redis_sgd --prefix recursive --dims 2560 --mode rrf --out outputs/redis-recursive-rrf.csv
uv run python run_eval.py hits outputs/redis-recursive-rrf.csv
uv run python run_eval.py ragas outputs/redis-recursive-rrf.csv --metrics context_precision,context_recall
uv run python run_eval.py compare outputs/*.scores.json
```

Skor yang disimpan memakai nama metrik pendek, misalnya `context_precision`. File `.scores.json` dari versi `rag_eval` lama memakai nama kelas ragas, misalnya `llm_context_precision_with_reference`, jadi kolomnya terpisah saat dibandingkan.
