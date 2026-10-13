# Boilerplate proyek

Aplikasi lengkap yang dibangun di atas paket `zul`, untuk disalin sebagai awal proyek baru. Setiap boilerplate punya `pyproject.toml`, test, dan README sendiri, jadi bisa berdiri sebagai repository terpisah.

| Folder | Isi |
|---|---|
| [`computer_vision/`](computer_vision/) | Analitik video CCTV: deteksi dan pelacakan orang, garis dan zona penghitung, lama kunjungan, perhatian, kontak, video beranotasi, CSV, dan Docker. |

Boilerplate berbeda dari template `zul build hexa`. Template disalin oleh perintah `zul` dan tidak mengimpor Zul, sedangkan boilerplate adalah aplikasi yang mengimpor `zul` sebagai library.

## Dibaca oleh code assistant

MCP server Zul punya tool `list_projects` dan `read_project`, sehingga code assistant bisa membaca boilerplate ini dan menirunya saat menulis aplikasi baru. Caranya ada di [MCP server](https://zulkit.my.id/referensi/mcp/).

## Menjalankan test

Dari root repository:

```bash
uv run pytest framework/project/computer_vision
```
