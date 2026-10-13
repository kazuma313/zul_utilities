# Framework

Semua kode yang membentuk Zul: paket Python `zul`, skill pool untuk agent, notebook contoh, boilerplate proyek, dan studi yang menguji pilihan di dalamnya. Dokumentasinya terpisah, di folder [`docs/`](../docs/) dan di situs https://zulkit.my.id.

| Folder | Isi | Test |
|---|---|---|
| [`src/zul/`](src/zul/) | Paket `zul`: perintah `zul`, utilities, computer vision, evaluasi, adapter library, dan MCP server. | `uv run pytest` |
| [`tests/`](tests/) | Test paket `zul`, termasuk aturan lapisan adapter dan lisensi dependency. | |
| [`agentic/`](agentic/) | Skill pool: `skills/` (ada model AI di dalamnya) dan `utilities/` (script tanpa model). | `uv run pytest framework/agentic` |
| [`notebooks/`](notebooks/) | Notebook contoh pemakaian utilities Zul. | Dijalankan manual |
| [`project/`](project/) | Boilerplate aplikasi yang dibangun di atas `zul`, untuk disalin ke proyek baru. | Lihat README tiap proyek |
| [`studies/`](studies/) | Studi yang membandingkan model atau cara kerja untuk framework, lengkap dengan data dan laporannya. | Lihat README tiap studi |

Semua perintah dijalankan dari root repository, karena `pyproject.toml`, `uv.lock`, dan `.venv` ada di sana.

## Menyiapkan lingkungan

```bash
uv sync --inexact
```

`--inexact` menjaga library yang di-install di luar `uv.lock`, misalnya dependency skill pool seperti `yt-dlp`, supaya tidak terhapus.

## Menjalankan test

```bash
uv run pytest
```

Perintah itu hanya menguji paket `zul` di `framework/tests`. Skill pool diuji terpisah:

```bash
uv run pytest framework/agentic
```

## Gaya kode

Paket `zul`, test-nya, dan boilerplate di `project/` mengikuti gaya kode Zul:

```bash
uv run black framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
```

Skill pool, notebook, dan studi punya gaya sendiri, jadi tidak ikut diperiksa. Aturannya ada di [Berkontribusi](../docs/panduan/berkontribusi.md).
