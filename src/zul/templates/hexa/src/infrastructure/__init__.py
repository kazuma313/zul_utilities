"""
Layer Infrastructure: BAGAIMANA aplikasi berbicara dengan dunia luar.

Gunanya:
    Berisi adapter keluar: implementasi konkret untuk LLM, tools, memory,
    database, dan layanan pihak ketiga. Layer lain tidak peduli isinya;
    mereka hanya menerima objek jadi lewat parameter.

Isi folder:
    AI/                llm (provider model), tools, memory (checkpointer)
    database/          implementasi repository (PostgreSQL, MongoDB, ...)
    connections/       koneksi yang dipakai bersama (pool database, Redis)
    external/          client API pihak ketiga
    logging_config.py  konfigurasi logging aplikasi

Aturan dependensi:
    Boleh import dari `src.domain` dan `src.application`.
    Tidak di-import oleh keduanya. Yang menyambungkan adapter ke use case
    adalah controller di `src/interface/` (composition root).
"""
