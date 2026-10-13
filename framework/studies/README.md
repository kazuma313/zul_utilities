# Studi

Percobaan yang membandingkan pilihan untuk framework: model mana yang dipakai sebuah skill, atau cara kerja mana yang lebih baik. Setiap studi menyimpan script, data, dan hasilnya, supaya bisa dijalankan ulang dan dibandingkan.

| Studi | Pertanyaan | Laporan |
|---|---|---|
| [`contextual_retrieval_assessment/`](contextual_retrieval_assessment/) | Model lokal mana yang paling cocok untuk skill `contextual_retrieval`? | [README](contextual_retrieval_assessment/README.md) |
| [`learning_skills_comparison/`](learning_skills_comparison/) | gemma3:4b, qwen3:4b, atau qwen3:8b untuk skill `silabus_belajar` dan `materi_belajar`? | [README](learning_skills_comparison/README.md) dan [Model lokal untuk skill belajar](https://zulkit.my.id/konsep/model-lokal-untuk-skill-belajar/) |
| [`file_reader_comparison/`](file_reader_comparison/) | Model mana yang paling baik membaca gambar untuk skill belajar? | [README](file_reader_comparison/README.md) |
| [`retrieval_evaluation/`](retrieval_evaluation/) | Chunk per halaman atau rekursif, dan Redis `hybrid` atau `rrf`, dinilai dengan ragas. | [README](retrieval_evaluation/README.md) |

Semua script dijalankan dari root repository dengan `uv run`, karena `.venv` ada di sana. Kebanyakan studi butuh Ollama dengan model yang disebut di README-nya.
