# Dokumentasi

Sumber situs dokumentasi Zul yang terbit di https://zulkit.my.id/. Situs ini mendokumentasikan framework: paket `zul`, skill pool, dan boilerplate di `framework/`. File ini sendiri tidak ikut terbit.

| Folder | Isi |
|---|---|
| `index.md` | Beranda situs. |
| [`tutorial/`](tutorial/) | Belajar sambil mengerjakan, dari nol sampai hasil yang berjalan. |
| [`panduan/`](panduan/) | Langkah untuk satu tugas tertentu. |
| [`referensi/`](referensi/) | Fakta untuk dicari: fungsi, parameter, perintah, dan format. |
| [`konsep/`](konsep/) | Alasan di balik rancangan Zul. |
| [`blog/`](blog/) | Catatan bertanggal: `posts/` untuk tulisan, `resources/` untuk gambar dan file setiap tulisan. |
| [`assets/`](assets/) | Logo, gambar, CSS, dan JavaScript playground. |
| `hexagonal.md`, `playground.md` | Dua halaman lepas yang tetap ada di menu. |
| [`overrides/`](overrides/) | Template tema Material yang ditimpa, yaitu header situs. Tidak terbit. |
| [`tools/`](tools/) | `new_post.py` untuk tulisan blog, `docs_hooks.py` untuk versi di header, dan test keduanya. Tidak terbit. |

Susunan menu, tema, dan plugin blog diatur di [`mkdocs.yml`](../mkdocs.yml) di root repository. Template header ada di [`overrides/`](overrides/), dan versi Zul di header diambil oleh [`tools/docs_hooks.py`](tools/docs_hooks.py). Keduanya tidak ikut terbit, karena dikecualikan lewat `exclude_docs`.

`tutorial/`, `panduan/`, `referensi/`, dan `konsep/` juga ikut masuk wheel paket `zul` sebagai `zul/_docs`, supaya MCP server Zul bisa mencari dan membacanya.

## Melihat di komputer sendiri

Dari root repository:

```bash
uv run mkdocs serve
```

Situs terbuka di http://127.0.0.1:8001 dan dimuat ulang setiap kali file disimpan. Sebelum push, bangun situsnya dengan pemeriksaan yang sama seperti di GitHub:

```bash
uv run mkdocs build --strict
```

## Menulis tulisan blog

```bash
uv run python docs/tools/new_post.py "Judul tulisan" --kategori RAG
```

Perintah itu membuat `blog/posts/<tanggal>-<judul>.md` dan folder `blog/resources/<tanggal>-<judul>/`. Setiap tulisan wajib punya `date.created` dan paragraf ringkasan di atas `<!-- more -->`; tanpa keduanya build gagal. Tulisan dengan `draft: true` tidak terbit.

## Menerbitkan

Push ke `main` yang mengubah `docs/`, `mkdocs.yml`, `pyproject.toml`, atau `uv.lock` menjalankan workflow [`.github/workflows/docs.yml`](../.github/workflows/docs.yml). Workflow itu membangun situs dengan `mkdocs build --strict`, lalu menerbitkannya ke GitHub Pages. Pull request hanya dibangun, tidak diterbitkan.

## Test

| Perintah | Menguji |
|---|---|
| `uv run pytest docs/tools/tests` | `new_post.py` dan `docs_hooks.py`. |
| `uv run pytest framework/tests/test_computer_vision_docs.py` | Contoh kode di panduan computer vision tetap berjalan dan gambarnya sama. |

## Halaman terkait

- [Menulis tulisan blog](panduan/menulis-blog.md) dan [Format tulisan blog](referensi/blog.md)
- [Menerbitkan dokumentasi](panduan/menerbitkan-dokumentasi.md) dan [Workflow dokumentasi](referensi/workflow-dokumentasi.md)
- [Berkontribusi](panduan/berkontribusi.md), termasuk gaya penulisan dokumentasi
