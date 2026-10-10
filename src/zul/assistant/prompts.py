"""
Prompt siap pakai untuk code assistant yang tersambung ke MCP server Zul.

Gunanya:
    Prompt memberi assistant urutan kerja yang sama dengan cara Zul ditulis:
    baca aturan, cari fungsi yang sudah ada, tiru modul yang mirip, lalu
    periksa hasilnya. Di Claude Code, prompt MCP muncul sebagai perintah
    garis miring, misalnya /mcp__zul__tulis_modul_zul. Hanya butuh library
    standar.

Cara pakai:
    from zul.assistant.prompts import tulis_modul_zul

    print(tulis_modul_zul("garis penghitung berbentuk lingkaran"))
    print(evaluasi_retrieval("bandingkan Redis rrf dan hybrid"))
"""

from __future__ import annotations


def tulis_modul_zul(topik: str) -> str:
    """Langkah menulis modul baru di dalam Zul dengan gaya dan aturan Zul."""
    return f"""Tulis modul baru di dalam paket Zul tentang: {topik}

Ikuti langkah berikut dengan tool dari MCP server zul:
1. Panggil `conventions` dan ikuti semua aturannya.
2. Panggil `list_modules`. Jika fungsi yang dibutuhkan sudah ada, pakai
   fungsi itu dan jangan menulis ulang.
3. Pilih modul yang paling mirip, lalu baca dengan `read_source`, misalnya
   `zul.computer_vision.zones` untuk alat hitung, `zul.evaluation.retrievers`
   untuk antarmuka yang implementasinya bisa diganti, `zul.evaluation.judge`
   untuk alur evaluasi, atau `zul.adapters.opencv` untuk adapter library.
4. Jika butuh library pihak ketiga, periksa lisensinya (MIT, BSD, atau
   Apache 2.0), lalu impor library itu hanya di file baru zul/adapters/.
5. Tulis modulnya dengan docstring Gunanya dan Cara pakai, blok komentar
   berjudul, dan paragraf komentar berbentuk anak tangga.
6. Tulis test di tests/ dengan data buatan, tanpa server atau model.
7. Panggil `check_code` untuk setiap file baru dan perbaiki semua temuannya.
"""


def pakai_zul(tugas: str) -> str:
    """Langkah menyelesaikan tugas di proyekmu dengan fungsi Zul yang sudah ada."""
    return f"""Selesaikan tugas berikut dengan fungsi-fungsi dari paket Zul: {tugas}

Ikuti langkah berikut dengan tool dari MCP server zul:
1. Panggil `search_docs` dengan kata kunci dari tugas ini.
2. Panggil `find_examples` untuk contoh kode yang sudah diuji.
3. Panggil `module_guide` untuk setiap modul yang akan dipakai, supaya nama
   fungsi, argumen, dan nilai kembaliannya tepat.
4. Tulis kode yang merangkai fungsi Zul itu. Jangan menulis ulang fungsi
   yang sudah ada di Zul, dan sebutkan extra Zul yang perlu di-install.
"""


def evaluasi_retrieval(tujuan: str) -> str:
    """Langkah menulis script evaluasi retrieval dan RAG dengan zul.evaluation."""
    return f"""Tulis script evaluasi retrieval dengan zul.evaluation untuk: {tujuan}

Ikuti langkah berikut dengan tool dari MCP server zul:
1. Panggil `read_doc` untuk `panduan/mengevaluasi-retrieval`, lalu
   `module_guide` untuk setiap modul zul.evaluation yang akan dipakai.
2. Susun script dengan urutan ini, satu fungsi Zul untuk setiap langkah:
   `load_qa_dataset`, lalu retriever (`RedisRetriever`, `MilvusRetriever`, atau
   `FunctionRetriever`), lalu `run_rag` dengan `out_path`, lalu
   `retrieval_hit_stats`, lalu `evaluate_rag` dan `save_report`. Untuk beberapa
   percobaan, bandingkan hasilnya dengan `compare_reports`.
3. Baca kunci dan alamat server dari environment variable (`RAGAS_JUDGE_*`,
   `REDIS_*`, `MILVUS_*`), jangan menulisnya di kode. Model penilai harus
   berbeda dari model yang dinilai.
4. Mulai dari `RETRIEVAL_METRICS`. Tambahkan `GENERATION_METRICS` hanya jika
   `run_rag` diberi generator, misalnya `ChatGenerator`.
5. Jangan mengimpor ragas langsung, karena ragas 0.4 hanya bisa diimpor lewat
   `zul.adapters.ragas`. Sebutkan extra yang perlu di-install, misalnya
   `zul[evaluation,redis,llm]`.
"""
