# Script framework

Alat untuk merawat kode framework. Semuanya dijalankan dari root repository.

| Script | Gunanya |
|---|---|
| `comment_style.py` | Memeriksa paragraf komentar berbentuk anak tangga. Tanpa argumen, semua folder yang mengikuti gaya kode Zul ikut diperiksa. Logikanya ada di `zul.assistant.comment_style`, yang juga dipakai tool MCP `check_code`. |
| `mask_api_keys.py` | Menyamarkan API key yang tidak sengaja tertulis di file, misalnya di notebook, sebelum commit. |

Contoh pemakaian:

```bash
uv run python framework/scripts/comment_style.py
uv run python framework/scripts/comment_style.py --fix
uv run python framework/scripts/mask_api_keys.py --dry-run
```

`--fix` melipat ulang paragraf yang bisa dilipat. Jika pemeriksa menyebut "ubah kalimatnya", ganti satu atau dua kata sampai lolos.

Script untuk dokumentasi dan blog ada di [`docs/tools/`](../../docs/tools/).
