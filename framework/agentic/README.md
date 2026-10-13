# Skill pool

Alat untuk agent AI, dipisah menurut ada atau tidaknya model di dalamnya:

| Folder | Isi | Contoh |
|---|---|---|
| [`skills/`](skills/) | Skill yang di dalamnya ada model AI yang bekerja, dengan model lokal lewat Ollama atau model lain. | `mind_map`, `silabus_belajar`, `materi_belajar`, `contextual_retrieval`, `pptx_research` |
| [`utilities/`](utilities/) | Script tanpa model. | `youtube_transcript`, `crypto_snapshot`, `crypto_chart`, `calculator`, `web_search` |

Setiap folder skill memakai format yang sama:

| File | Isi |
|---|---|
| `METADATA.md` | Front matter: nama, deskripsi, model yang sudah diuji. |
| `SKILL.md` | Petunjuk untuk agent: kapan dipakai dan cara memanggilnya. |
| `<nama>_skill.py` | Entry point berisi tool LangChain (`@tool`). |
| `scripts/` | Script yang bisa dijalankan sendiri dari terminal. |
| `tests/` | Test tanpa jaringan dan tanpa model. |

Kebutuhan model dan mesin untuk setiap skill ada di [`skills/REQUIREMENTS.md`](skills/REQUIREMENTS.md).

## Memakai dari agent

Folder ini harus ada di `sys.path`, supaya skill bisa diimpor sebagai `skills.<nama>` dan script sebagai `utilities.<nama>`:

```python
import sys

sys.path.insert(0, "framework/agentic")

from utilities.youtube_transcript.youtube_transcript_skill import fetch_transcript_tool
```

Aplikasi lain yang dulu mengimpor dari `research/agentic/algorithms` perlu mengganti path itu menjadi `framework/agentic`.

## Menjalankan test

Dari root repository:

```bash
uv run pytest framework/agentic
```

Test tidak butuh jaringan atau model. Mengimpor `utilities.docx` membuat folder `framework/agentic/app/` yang kosong; folder itu boleh dihapus.

## Dokumentasi

Panduan setiap skill ada di situs dokumentasi, bagian [Panduan](https://zulkit.my.id/panduan/), misalnya [Membuat mind map](https://zulkit.my.id/panduan/membuat-mindmap/) dan [Mengambil transcript YouTube](https://zulkit.my.id/panduan/mengambil-transcript-youtube/). Sumbernya di [`docs/panduan/`](../../docs/panduan/).
