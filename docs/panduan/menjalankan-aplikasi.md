# Menjalankan aplikasi

Halaman ini menunjukkan cara menyalakan REST API proyekmu: untuk pengembangan, dan di dalam container.

**Sebelum mulai:** dependency proyek sudah terpasang dan `.env` sudah berisi API key. Lihat [Membuat proyek baru](membuat-proyek.md) dan [Mengatur model dan API key](mengatur-llm.md).

## Menjalankan server pengembangan

Dari root proyek, jalankan:

```shell
uvicorn src.interface.http.main:app --reload
```

Server berjalan di `http://localhost:8000`. Opsi `--reload` memulai ulang server setiap kali kode berubah. Jangan memakai opsi itu di produksi.

Untuk memakai port lain, tambahkan `--port`:

```shell
uvicorn src.interface.http.main:app --reload --port 9000
```

## Menjalankan di container

1. Bangun image dari root proyek. Ganti `NAMA_IMAGE` dengan nama yang kamu inginkan:

    ```shell
    docker build -f dockerfile/Dockerfile -t NAMA_IMAGE .
    ```

2. Jalankan container dengan variabel dari `.env`:

    ```shell
    docker run --env-file .env -p 8000:8000 NAMA_IMAGE
    ```

Image hanya memuat `requirements.txt` dan folder `src`. File `.env` tidak ikut disalin ke dalam image; variabelnya diberikan saat container dijalankan.

> [!WARNING]
> Sebelum menjalankan di produksi, isi `PLAYGROUND_ENABLED=false` atau hapus barisnya. Playground menampilkan argumen dan hasil setiap tool kepada siapa pun yang bisa membuka halamannya.

## Memeriksa hasilnya

Panggil endpoint pemeriksa:

```shell
curl http://localhost:8000/health
```

Server yang hidup menjawab:

```json
{"status": "ok"}
```

Untuk mencoba endpoint lain dari browser, buka dokumentasi interaktif buatan FastAPI di `http://localhost:8000/docs`. Untuk mencoba agent sambil melihat langkahnya, buka [Playground](../playground.md).

## Lihat juga

- [HTTP API](../referensi/http-api.md) untuk bentuk request dan respons setiap endpoint.
- [Menyimpan percakapan di database](menyimpan-percakapan.md), yang wajib dilakukan sebelum menjalankan lebih dari satu worker.
