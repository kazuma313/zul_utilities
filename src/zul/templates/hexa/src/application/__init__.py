"""
Layer Application: APA yang dilakukan aplikasi, bukan BAGAIMANA caranya.

Gunanya:
    Menyusun alur kerja. Menerima permintaan dari layer interface,
    menjalankan aturan domain dan agent AI, lalu mengembalikan hasil.

Isi folder:
    usecases/   satu aksi bisnis per class (ChatUseCase, ReviewedChatUseCase)
    AI/         agent LangGraph: react, human_in_the_loop, subagents
    dto/        bentuk data yang melintas antar layer
    mappers/    konversi entity <-> DTO
    services/   koordinasi beberapa use case
    prompts/    prompt yang dirakit dari data saat runtime

Aturan dependensi:
    Boleh import dari `src.domain`.
    Jangan import dari `src.infrastructure` atau `src.interface`. LLM,
    tools, dan database diterima lewat parameter (dependency injection),
    sehingga layer ini bisa diuji dengan objek palsu.
"""
