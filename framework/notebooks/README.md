# Notebook contoh

Notebook Jupyter berisi contoh pemakaian utilities Zul, dan beberapa percobaan yang memanggil library secara langsung.

| Notebook | Isi | Extra Zul |
|---|---|---|
| `milvus.ipynb` | Menyimpan dan mencari vektor dengan `MilvusHelper`. | `milvus` |
| `redis_vector.ipynb` | Index dan pencarian vektor dengan `RedisVectorDB`. | `redis` |
| `fake_embedding.ipynb` | `FakeEmbeddingModel` untuk test tanpa model. | Tidak ada |
| `ocr/` | OCR file, gambar, tabel, HTML, dan PPTX dengan `DoclingVLMConverter`; `ocr_cloud_vlm.ipynb` memakai Gemini. | `ocr`, `gemini` |
| `logging.ipynb` | Konfigurasi `logging` bawaan Python. | Tidak ada |
| `load_model.ipynb`, `ollama.ipynb`, `langchain_v1.ipynb` | Memanggil LLM langsung lewat OpenAI, Ollama, dan agent LangChain, tanpa paket `zul`. | Tidak ada |
| `elasticsearch.ipynb` | Memakai Elasticsearch langsung, tanpa paket `zul`. | Tidak ada |
| `training_yolo.ipynb` | Melatih YOLO dengan ultralytics, yang tidak dipakai paket `zul`. Hasilnya di `research/arsip/runs/`. | Tidak ada |
| `chart_generator.ipynb` | Masih kosong. | |

## Menjalankan

Pilih kernel dari `.venv` di root repository, lalu jalankan sel dari atas. Extra yang dibutuhkan setiap notebook ada di tabel di atas. Cara meng-install-nya ada di [Instalasi Zul](https://zulkit.my.id/panduan/instalasi-zul/).

Kunci API dibaca dari `.env` di root repository. Jangan menulis kunci langsung di sel notebook. Jika sempat tertulis, samarkan sebelum commit:

```bash
uv run python scripts/mask_api_keys.py --dry-run
```

## Dokumentasi

Penjelasan lengkap setiap utility ada di situs dokumentasi, bagian [Panduan](https://zulkit.my.id/panduan/) dan [Referensi](https://zulkit.my.id/referensi/).
