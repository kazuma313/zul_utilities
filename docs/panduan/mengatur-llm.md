# Mengatur model dan API key

Proyek hasil `zul build hexa` membaca API key, nama model, dan alamat endpoint dari `.env`, jadi ketiganya bisa diganti, termasuk ke endpoint selain OpenAI.

**Sebelum mulai:** kamu punya proyek hasil `zul build hexa` dengan file `.env` di root-nya. Rinciannya ada di [Membuat proyek baru](membuat-proyek.md).

## Mengisi API key

1. Buka file `.env` di root proyek.

2. Isi `OPENAI_API_KEY`:

    ```ini title=".env"
    OPENAI_API_KEY=API_KEY
    ```

    Ganti `API_KEY` dengan key milikmu.

3. Jika server sedang berjalan, hentikan lalu jalankan lagi. File `.env` hanya dibaca saat aplikasi mulai.

Variabel yang sudah diset di shell atau di container tidak ditimpa oleh isi `.env`. Di produksi, kamu bisa mengeset variabelnya langsung di platform deployment tanpa file `.env`.

## Mengganti model

Semua agent di proyek memakai model yang disebut di `LLM_MODEL`. Untuk menggantinya, ubah nilainya di `.env`:

```ini title=".env"
LLM_MODEL=gpt-4o
```

Jika `LLM_MODEL` tidak diisi, proyek memakai `gpt-4o-mini`.

> [!WARNING]
> Model yang kamu pilih harus mendukung *tool calling*. Tanpa itu, agent tidak bisa meminta tool dan selalu menjawab langsung.

## Memakai endpoint selain OpenAI

Server seperti vLLM, LiteLLM, LM Studio, dan Ollama menyediakan API yang kompatibel dengan OpenAI. Untuk memakainya, arahkan `LLM_BASE_URL` ke server itu dan isi nama modelnya:

```ini title=".env"
OPENAI_API_KEY=API_KEY
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=NAMA_MODEL
```

Ganti `API_KEY` dengan key server-mu, alamat di `LLM_BASE_URL` dengan alamat server-mu, dan `NAMA_MODEL` dengan nama model yang tersedia di sana. Jika server tidak memakai autentikasi, isi `OPENAI_API_KEY` dengan teks apa saja; variabelnya tetap harus ada.

## Memakai provider dengan paket LangChain sendiri

Untuk provider yang punya paket LangChain sendiri, tulis adapter baru. Adapter adalah fungsi yang mengembalikan chat model LangChain.

1. Install paket provider-nya dan tambahkan ke `requirements.txt`.

2. Buat file baru di `src/infrastructure/AI/llm/` berisi fungsi `get_llm_model`. Bentuknya mengikuti `openai.py` di folder yang sama: baca pengaturan dari environment, lalu kembalikan chat model.

3. Di setiap controller yang merakit agent, ganti impor `get_llm_model` supaya menunjuk ke file barumu. Controller-nya ada di `src/interface/http/controllers/`.

Layer application tidak perlu diubah, karena agent menerima chat model lewat parameter.

## Memeriksa hasilnya

Jalankan server, lalu kirim satu pesan:

```shell
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Halo\"}"
```

Jika key dan model benar, respons berisi `answer`. Jika `OPENAI_API_KEY` kosong, server menjawab dengan status `500` dan log-nya memuat `OPENAI_API_KEY not found!`. Key baru diperiksa saat agent pertama kali dirakit, yaitu pada pesan pertama, jadi `GET /health` tetap menjawab walau key belum diisi.

## Menjaga kerahasiaan key

- Simpan API key hanya di `.env` atau di pengaturan platform deployment. File `.env` sudah ada di `.gitignore` proyek.
- Jangan menulis key di kode, notebook, atau file config yang di-commit. Key yang pernah ter-commit tetap ada di riwayat git walau barisnya sudah dihapus. Ganti key seperti itu dengan yang baru.

## Halaman terkait

- [Environment variable](../referensi/konfigurasi.md) untuk daftar lengkap variabel dan nilai bawaannya.
- [Arsitektur hexagonal](../konsep/arsitektur-hexagonal.md) untuk alasan adapter LLM tinggal di layer infrastructure.
