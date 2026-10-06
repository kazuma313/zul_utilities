# Tutorial

Tutorial adalah pelajaran yang kamu kerjakan dari awal sampai akhir. Di setiap langkah kamu mengetik sesuatu dan melihat hasilnya, sehingga di akhir pelajaran ada sesuatu yang berjalan di komputermu.

Kerjakan ketiganya berurutan. Setiap tutorial melanjutkan proyek dari tutorial sebelumnya.

1. **[Membuat agent pertamamu](agent-pertama.md)**

    Buat proyek dengan `zul build hexa`, jalankan, berbicara dengan agent, lalu beri agent itu tool buatanmu sendiri. Sekitar 20 menit.

2. **[Meminta persetujuan manusia](persetujuan-manusia.md)**

    Buat agent berhenti sebelum mengirim email, lalu setujui, ubah, atau tolak aksinya dari playground. Sekitar 15 menit.

3. **[Membangun tim agent](tim-agent.md)**

    Lihat supervisor membagi tugas ke subagent, lalu tambahkan subagent baru ke timnya. Sekitar 15 menit.

## Yang kamu butuhkan

- Python 3.11 atau lebih baru, dan Zul yang sudah terpasang. Lihat [Memasang Zul](../panduan/memasang-zul.md).
- API key OpenAI, atau endpoint lain yang kompatibel dengan OpenAI.
- Dokumentasi ini dibuka sebagai situs, bukan dibaca di GitHub. Tutorial memakai panel Playground di halamannya, dan panel itu hanya tampil di situs.

Untuk membuka dokumentasi ini sebagai situs, jalankan perintah berikut di folder repository Zul:

```shell
uv run mkdocs serve
```

Lalu buka `http://127.0.0.1:8001`.

## Setelah tutorial

Tutorial sengaja tidak menjelaskan semua hal. Setelah selesai, pakai bagian lain sesuai kebutuhanmu:

- [Panduan](../panduan/index.md) saat kamu punya tugas tertentu.
- [Konsep](../konsep/index.md) saat kamu ingin tahu kenapa sesuatu dirancang begitu.
- [Referensi](../referensi/index.md) saat kamu mencari nama parameter atau bentuk request.
