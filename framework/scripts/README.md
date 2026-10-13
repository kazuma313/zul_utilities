# Tool repository

Script untuk merawat repository ini. Semuanya dijalankan dari root repository.

| Script | Gunanya |
|---|---|
| `comment_style.py` | Memeriksa paragraf komentar berbentuk anak tangga. Isinya ada di `zul.assistant.comment_style`. |
| `new_post.py` | Membuat tulisan blog baru di `docs/blog/posts/`. |
| `docs_hooks.py` | Hook MkDocs yang menaruh versi Zul di header situs. Dipanggil oleh `mkdocs.yml`. |
| `mask_api_keys.py` | Menyamarkan API key yang tidak sengaja tertulis di file repository. |

Contoh pemakaian:

```bash
uv run python scripts/comment_style.py framework/src framework/tests framework/project scripts --fix
uv run python scripts/new_post.py "Judul tulisan" --kategori RAG
uv run python scripts/mask_api_keys.py --dry-run
```

Test untuk `new_post.py` dan `docs_hooks.py`:

```bash
uv run pytest scripts/tests
```
