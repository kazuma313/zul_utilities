"""
Evaluasi retrieval dan RAG: fungsi kecil dari dataset sampai skor ragas.

Gunanya:
    Setiap modul mengerjakan satu langkah evaluasi dan bisa dipakai
    sendiri-sendiri. Retriever apa pun cukup punya method
    `retrieve(query, top_k)`, jadi membandingkan Redis dengan Milvus, hybrid
    dengan RRF, atau chunk per halaman dengan chunk rekursif hanya mengganti
    satu objek. Data mengalir sebagai list dict dengan nama kolom ragas:
    user_input, reference, reference_contexts, retrieved_contexts, response.

Modul dan extra yang dibutuhkan:
    dataset       membaca dataset tanya-jawab, menyimpan hasil     tanpa extra
    documents     PDF menjadi potongan per halaman atau rekursif   zul[pdf]
    indexing      embedding setiap potongan, skema index Redis     tanpa extra
    milvus_store  collection Milvus hybrid: dense dan BM25         zul[milvus]
    retrievers    satu antarmuka retrieve: Redis, Milvus, fungsi   tanpa extra
    generation    jawaban dari pertanyaan dan konteks              tanpa extra
    runner        retrieval dan jawaban untuk seluruh dataset      tanpa extra
    hits          hit rate dan MRR tanpa LLM                       tanpa extra
    judge         skor ragas dengan model penilai                  zul[evaluation]
    reports       menyimpan dan membandingkan skor                 tanpa extra
    latency       latensi p50, p95, p99, dan QPS                   tanpa extra
    config        penilai, Redis, dan Milvus dari environment      tanpa extra

    Membaca dataset .xlsx butuh zul[evaluation]. Retriever Redis dan Milvus
    butuh zul[redis] dan zul[milvus] untuk objek database yang diberikan.

Cara pakai:
    from zul.evaluation.dataset import load_qa_dataset
    from zul.evaluation.judge import evaluate_rag
    from zul.evaluation.retrievers import RedisRetriever
    from zul.evaluation.runner import run_rag

    rows = load_qa_dataset("qa.xlsx")
    results = run_rag(rows, RedisRetriever(db, ai, mode="rrf"), top_k=5)
    report = evaluate_rag(results, metrics=["context_precision", "context_recall"])

Paket ini tidak mengimpor modul apa pun saat diimpor, jadi modul yang butuh
ragas atau pypdf hanya dimuat ketika benar-benar dipakai.
"""
