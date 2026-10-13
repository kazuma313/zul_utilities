# Proyek mandiri

Proyek kecil yang berdiri sendiri, masing-masing dengan dependency dan README-nya.

| Folder | Isi | Cara menjalankan |
|---|---|---|
| [`folder_migrator/`](folder_migrator/) | Memindahkan folder dalam jumlah besar dengan checkpoint, supaya bisa dilanjutkan jika terputus. | [README](folder_migrator/README.md) dan [CARA_PAKAI](folder_migrator/CARA_PAKAI.md) |
| [`indonesian_ner_nodejs/`](indonesian_ner_nodejs/) | Named entity recognition bahasa Indonesia di Node.js dengan model ONNX. | [README](indonesian_ner_nodejs/README.md) |

Test `folder_migrator` bisa dijalankan dari root repository:

```bash
uv run pytest research/proyek/folder_migrator -q
```
