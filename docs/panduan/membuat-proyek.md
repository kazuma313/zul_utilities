# Membuat proyek baru

Proyek baru dibuat dari template `hexa` dengan `zul build hexa`, lalu disiapkan sampai bisa dijalankan.

**Sebelum mulai:** Zul sudah terpasang ([Memasang Zul](memasang-zul.md)) dan `zul --version` berjalan.

## Langkah-langkah

1. Buat proyek. Ganti `NAMA_PROYEK` dengan nama folder yang kamu inginkan:

    ```shell
    zul build hexa --name NAMA_PROYEK
    ```

    Zul menanyakan konfirmasi, lalu menyalin template ke folder baru bernama `NAMA_PROYEK`. Jika folder itu sudah ada, Zul berhenti dan tidak mengubah apa pun.

2. Masuk ke folder proyek:

    ```shell
    cd NAMA_PROYEK
    ```

3. Buat virtual environment, aktifkan, lalu pasang dependency:

    ```shell
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
    ```

    Di Windows, aktifkan environment dengan `.venv\Scripts\activate`. File `requirements-dev.txt` memasang isi `requirements.txt` ditambah `pytest` dan `httpx` untuk test.

4. Salin contoh file environment:

    ```shell
    cp .env.example .env
    ```

    Di Windows, gunakan `copy .env.example .env`. Isi nilainya mengikuti [Mengatur model dan API key](mengatur-llm.md).

## Membuat proyek tanpa pertanyaan

Di script atau CI tidak ada yang menjawab pertanyaan konfirmasi. Tambahkan `--yes` untuk melewatinya:

```shell
zul build hexa --name NAMA_PROYEK --yes
```

Jika `--name` tidak diberikan, Zul menanyakan nama proyek secara interaktif.

## Memeriksa hasilnya

Jalankan test bawaan proyek:

```shell
pytest
```

Test itu tidak membutuhkan API key. Baris terakhir keluarannya:

```text
4 passed
```

## Halaman terkait

- [Menjalankan aplikasi](menjalankan-aplikasi.md) untuk menyalakan server.
- [Struktur proyek](../referensi/struktur-proyek.md) untuk isi setiap folder yang baru dibuat.
- [Perintah zul](../referensi/cli.md) untuk semua opsi `zul build hexa`.
- [Arsitektur hexagonal](../konsep/arsitektur-hexagonal.md) untuk alasan di balik susunan foldernya.
