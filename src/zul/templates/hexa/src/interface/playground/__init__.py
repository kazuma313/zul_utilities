"""
Playground: mencoba agent yang sedang kamu buat, langsung dari dokumentasi.

Gunanya:
    Memberi tempat mencoba fitur sebelum endpoint dan test-nya selesai.
    Halaman dokumentasi Zul mengirim pesan ke endpoint `/playground/*` di
    aplikasi ini, lalu menampilkan setiap langkah agent: tool yang
    dipanggil, argumennya, hasilnya, dan aksi yang menunggu persetujuan.

Cara pakai:
    1. Isi `PLAYGROUND_ENABLED=true` di file `.env`.
    2. Jalankan aplikasi: `uvicorn src.interface.http.main:app --reload`.
    3. Buka halaman Playground di dokumentasi Zul.

Isi folder:
    features.py   daftar fitur yang bisa dicoba; tambahkan fiturmu di sini
    runner.py     menjalankan agent dan mencatat langkahnya
    settings.py   pengaturan dari environment variable

Contoh menambah fitur (di `features.py`):
    Feature(
        name="RAG dokumen",
        description="Agent yang mencari jawaban di dokumen internal.",
        build_agent=build_rag_agent,
        examples=("Apa isi kebijakan cuti?",),
    )

Contoh memakainya tanpa browser:
    from src.interface.playground.features import find_feature
    from src.interface.playground.runner import send_message

    agent = find_feature("ReAct").build_agent()
    turn = send_message(agent, "cuaca di sf?", thread_id="coba-1")
"""
