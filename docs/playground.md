---
hide:
  - navigation
  - toc
---

<div class="zul-wide" markdown>

# Playground

Panel ini mengirim pesan ke agent dan menampilkan setiap langkah yang diambilnya sebelum menjawab. Jejak langkahnya tampil di sebelah kanan.

<div class="zul-playground" data-layout="wide">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

<div class="zul-columns" markdown>

<div markdown>

## Menyambungkan ke proyekmu

Tombol status di bilah panel menunjukkan sumber jawabannya. **Simulasi** berarti panel belum terhubung dan menampilkan contoh jawaban untuk fitur bawaan template. **Terhubung** berarti panel menjalankan agent di proyekmu, termasuk fitur yang kamu daftarkan sendiri.

Untuk menyambungkannya:

1. Di file `.env` proyekmu, pastikan baris berikut ada:

    ```ini title=".env"
    PLAYGROUND_ENABLED=true
    ```

2. Dari root proyek, jalankan aplikasinya:

    ```shell
    uvicorn src.interface.http.main:app --reload
    ```

3. Di panel, klik tombol status, lalu klik **Sambungkan**.

Jika API-mu berjalan di alamat selain `http://localhost:8000`, isi alamatnya di kotak **Alamat API proyekmu** sebelum mengklik **Sambungkan**.

</div>

<div markdown>

## Membaca jejak

Setiap titik di rel adalah satu node graph yang selesai dijalankan. Warna titiknya menunjukkan siapa yang bekerja:

| Titik | Yang bekerja | Isi langkah |
|---|---|---|
| Nila | Model | Permintaan tool beserta argumennya, atau teks jawaban. |
| Sian | Tool | Hasil tool. Yang gagal atau ditolak ditandai merah. |
| Kuning | Manusia | Aksi setelah direview: disetujui, diubah, atau ditolak. |

Langkah yang menjorok ke kanan dikerjakan subagent. **Lihat request dan respons** menampilkan request HTTP yang dikirim panel dan JSON mentah yang diterimanya.

Saat agent ingin menjalankan aksi yang butuh persetujuan, panel menampilkan form berwarna kuning. Pilih **Setujui**, **Ubah** (lalu sunting argumennya), atau **Tolak** (lalu tulis alasannya), kemudian klik **Kirim keputusan**.

</div>

</div>

## Halaman terkait

- [Mencoba fitur di playground](panduan/mencoba-di-playground.md): mendaftarkan fitur yang sedang kamu buat supaya muncul di daftar pilihan.
- [Playground API](referensi/playground-api.md): endpoint yang dipanggil panel ini.
- [Membuat agent pertamamu](tutorial/agent-pertama.md): membuat proyek yang bisa disambungkan ke panel ini.

</div>
