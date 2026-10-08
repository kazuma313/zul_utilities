# Model lokal untuk skill belajar

Skill `silabus_belajar` dan `materi_belajar` bisa dijalankan dengan model Ollama di laptop sendiri. Halaman ini membandingkan tiga model, `gemma3:4b`, `qwen3:4b`, dan `qwen3:8b`, pada empat tugas yang sama, dengan jawaban yang ditulis Claude sebagai pembanding.

Hasil singkatnya:

- Ketiga model menghasilkan halaman yang bisa dipakai untuk semua tugas. Setelah perbaikan di putaran pertama, semua tugas selesai pada percobaan pertama.
- Untuk silabus, skill memakai `gemma3:4b`. Model ini selesai dalam 30-40 detik, dan model yang lebih besar tidak menulis silabus yang lebih lengkap.
- Untuk materi, skill memakai `qwen3:8b`. Hanya model ini yang menulis semua angka dengan benar, tetapi butuh 3,5 sampai 5,5 menit per materi.
- Semua model menulis fakta yang salah atau istilah karangan, dan kode tidak bisa menangkapnya. Isi halaman tetap harus dibaca sebelum dipakai belajar.

## Cara membandingkan

Setiap model mendapat permintaan yang sama untuk empat tugas:

| Tugas | Permintaan |
|---|---|
| Silabus reksa dana | Topik "Reksa dana", level pemula, tujuan "bisa memilih reksa dana sendiri tanpa ikut-ikutan rekomendasi", 3 jam per minggu. |
| Silabus Python | Topik "Python untuk analisis data", level pemula, tujuan "bisa menganalisis data penjualan sendiri tanpa rumus manual", 4 jam per minggu. |
| Materi reksa dana | Kartu modul 2 dari silabus pembanding: NAB dan cara nilai investasi berubah. |
| Materi Python | Kartu modul 3 dari silabus pembanding: membaca data dengan pandas. |

Kedua materi memakai kartu modul dari silabus yang sama, supaya semua model menulis untuk tujuan belajar yang sama.

Pembandingnya adalah empat jawaban JSON yang ditulis Claude dengan aturan skill yang sama, lalu dibangun dengan kode yang sama. Keempatnya lolos semua pemeriksaan tanpa peringatan.

Semua model dijalankan di laptop yang sama: Ryzen 7 5800HS, RAM 23 GB, dan RTX 3060 Laptop 6 GB. Ollama 0.32.6 dijalankan dengan `OLLAMA_VULKAN=0` supaya memakai GPU NVIDIA. Setiap tugas dijalankan sekali per model, dengan temperature 0,3. Model dijalankan bergantian, tidak bersamaan, supaya Ollama tidak menukar model di GPU.

Perbandingan ini berjalan dua putaran. Putaran pertama memakai versi awal skill. Masalah yang ditemukan diperbaiki, lalu semua tugas dijalankan lagi di putaran kedua. Angka di halaman ini berasal dari putaran kedua, kecuali disebut lain.

## Waktu

Waktu per tugas di putaran kedua, dalam detik. Tugas pertama setiap model sudah termasuk waktu memuat model:

| Model | Silabus reksa dana | Silabus Python | Materi reksa dana | Materi Python | Token per detik | Layer di GPU |
|---|---|---|---|---|---|---|
| `gemma3:4b` | 38 | 29 | 61 | 56 | 40-63 | 35 dari 35 |
| `qwen3:4b` | 49 | 46 | 132 | 93 | 21-39 | 37 dari 37 |
| `qwen3:8b` | 246 | 140 | 329 | 222 | 7,5-10 | 25-26 dari 37 |

`qwen3:8b` tidak muat seluruhnya di GPU 6 GB. Sekitar sepertiga layer-nya berjalan di CPU, karena itu model ini 4 sampai 6,5 kali lebih lambat dari `gemma3:4b`.

## Isi silabus

Hasil membaca silabus putaran kedua, dibandingkan dengan silabus pembanding:

| Model | Konsep inti yang ada | Kesalahan |
|---|---|---|
| `gemma3:4b` | Reksa dana: NAB, modul model bisnis, modul risiko. Python: pandas, CSV, data kosong, dan matplotlib, dengan membersihkan data sebelum analisis. | Dua nama biaya karangan, "Fee Penyerap" dan "Fee Barang Beredar". "Reksa buka" dan "reksa tutup" untuk reksa dana terbuka dan tertutup. Sharpe ratio dan alpha untuk pemula. |
| `qwen3:4b` | Modul model bisnis dan risiko. Pandas dan matplotlib. | Tanpa NAB. Tanpa modul membersihkan data. Istilah terlalu umum, seperti "Data" dan "Penjualan". |
| `qwen3:8b` | Modul model bisnis dan risiko. | Tanpa NAB. Tanpa pandas, dan "fungsi SUM" dari Excel ditulis untuk Python. Tanpa modul membersihkan data. |

Konsep inti tidak selalu muncul. NAB adalah dasar untuk menghitung nilai investasi reksa dana, tetapi hanya ada di 2 dari 5 silabus reksa dana `gemma3:4b`: putaran pertama, putaran kedua, dan tiga run untuk contoh di [panduan](../panduan/membuat-silabus-dan-materi.md). `qwen3:4b` dan `qwen3:8b` tidak menulisnya sama sekali. Silabus pembanding memuat NAB di modul 2.

Run contoh untuk panduan juga menulis istilah yang keliru: "Sharia Fee", yang bukan nama biaya reksa dana, dan "peran komisioner" di modul model bisnis.

## Isi materi

Hasil membaca materi putaran kedua:

| Model | Angka yang salah | Konsep yang salah |
|---|---|---|
| `gemma3:4b` | 1. Kuis menulis Rp39.000 untuk 300 × Rp50, padahal hasilnya Rp15.000, dan tidak ada pilihan jawaban yang benar. Pemeriksa hitungan menangkapnya. | Keuntungan reksa dana disebut kena pajak bagi investor, padahal di Indonesia keuntungan itu bukan objek pajak penghasilan bagi pemegang unit. NAB disebut harga per unit. Kuis menyebut kolom jumlah penjualan bertipe float, padahal kolom itu berisi bilangan bulat. |
| `qwen3:4b` | 2, tidak tertangkap. Untung Rp30.000 ditulis tanpa hitungan, padahal 400 × Rp50 = Rp20.000. Rp500.000 ÷ Rp1.300 ditulis 384,48 unit, padahal 384,62. | Jumlah unit disebut berubah ketika NAB naik atau turun, di bab, demo, kuis, dan latihan. Yang berubah adalah nilainya; jumlah unit tetap. |
| `qwen3:8b` | 0. Semua hitungan ditulis lengkap. | NAB disebut nilai per unit. `data['harga'].sum()` disebut total penjualan, padahal itu menjumlahkan harga satuan. Jumlah barang disamakan dengan jumlah baris. |

Di putaran pertama, `gemma3:4b` menulis 4 angka yang salah di materi reksa dana, sedangkan `qwen3:8b` tidak salah satu angka pun. Dalam dua putaran, `qwen3:8b` menulis semua angka dengan benar di keempat materinya.

Beberapa kelemahan muncul di semua model:

- NAB, yaitu nilai seluruh isi reksa dana, disamakan dengan NAB per unit.
- Setiap materi hanya berisi 3 bab dan 4 soal, jumlah paling sedikit yang diizinkan. Materi pembanding berisi 4 bab dan 5 soal.
- Tidak ada model yang membuat soal pertama untuk mengulang modul sebelumnya, walaupun permintaannya menyebut itu.
- Sebagian bab mengulang bab sebelumnya, dan sebagian soal hanya menguji hafalan, misalnya "Apa yang dimaksud dengan NAB per unit?".

Catatan lengkap per tugas ada di `review.json`, lihat [File perbandingan](#file-perbandingan).

## Perubahan setelah putaran pertama

Membaca jawaban kedua putaran menemukan masalah yang bisa diperbaiki dengan kode atau prompt. Perubahan prompt, schema, dan ukuran context dipasang sebelum putaran kedua. Perubahan builder hanya mengubah halaman, bukan jawaban model, jadi halaman putaran kedua dibangun ulang dengan builder terakhir:

| Masalah yang ditemukan | Perubahan |
|---|---|
| `qwen3:4b` menulis satu kalimat berulang-ulang di kolom terakhir sampai batas 7.168 token, dua kali. Materinya gagal setelah 656 detik. | Setiap teks di schema diberi `maxLength`, di atas teks terpanjang yang ditulis model mana pun. Ollama menghentikan teks di batas itu, dan kolom yang mencapai batas dilaporkan sebagai peringatan. Di putaran kedua, materi yang sama selesai dalam 132 detik. |
| `qwen3:8b` hanya mendapat 22 dari 37 layer di GPU, dengan 6,7-7,9 token per detik. | Ukuran context dihitung dari panjang permintaan, 6.144-7.168 token, bukan 12.288. `qwen3:8b` mendapat 25-26 layer dan 7,5-10 token per detik. |
| Semua model menulis 1 jam untuk setiap modul. | Prompt memberi patokan: 1 jam untuk pengenalan istilah, 2 jam untuk latihan hitungan, 3 jam untuk praktik di komputer. Di putaran kedua, tidak ada silabus yang memberi 1 jam untuk semua modul. |
| Kursus Python mendapat modul model bisnis. | Aturan modul model bisnis dan modul risiko hanya dikirim untuk topik tentang uang. |
| Silabus tanpa modul model bisnis lolos pemeriksaan karena memuat kata "keuntungan". | Kata kunci pemeriksaannya diperketat. |
| Di putaran kedua, hitungan "Rp39.000 = 300 x (Rp1.300 - Rp1.250)" lolos, dan hitungan benar "400 x Rp50 = Rp20.000" di tengah rantai ditandai salah. | Pemeriksa hitungan membaca kedua urutan dan setiap pasangan dalam rantai "a = b = c". |
| Hasil modul hanya "Bisa Menjelaskan", judul bab bernomor dobel, bekal dari modul sebelumnya kosong, dan Markdown seperti `*fee*` tampil apa adanya. | Kode memperbaikinya sebelum halaman dibangun. |
| Modul model bisnis memuat istilah "Startup", tersalin dari contoh istilah di prompt. Ini ditemukan setelah putaran kedua. | Daftar contoh istilah dihapus dari prompt. |

## Yang diperiksa kode dan yang tidak

Kode memeriksa dan memperbaiki bentuk halaman, tetapi tidak bisa menilai apakah isinya benar:

| Diperiksa atau diperbaiki kode | Harus dibaca manusia |
|---|---|
| Bentuk JSON dan panjang setiap teks. | Fakta yang salah dan istilah karangan. |
| Kata kerja kabur seperti "Memahami", jam modul 1-3, dan jadwal mingguan. | Konsep yang tertukar, seperti NAB dan NAB per unit. |
| Posisi jawaban benar di kuis, dan "Lihat bab N" di setiap pembahasan. | Angka yang ditulis tanpa hitungannya. |
| Tujuan belajar yang tidak diajarkan atau tidak diuji, dan istilah kartu modul tanpa kotak istilah. | Selisih kecil di bawah 0,5%, yang dianggap pembulatan. |
| Urutan istilah antarmodul, modul risiko dan model bisnis untuk topik uang, dan link yang tidak diberikan pengguna. | Bab yang mengulang bab lain, dan soal yang hanya menguji hafalan. |
| Hitungan yang ditulis lengkap dengan tanda "=". | Konsep inti yang tidak ada di silabus, dan materi di luar kartu modul. |

## Model yang dipakai skill

Dengan `--model auto`, setiap skill memakai model pertama dari daftar ini yang ada di server:

| Skill | Urutan | Alasan |
|---|---|---|
| `silabus_belajar` | `gemma3:4b`, `qwen3:8b`, `qwen3:4b` | Tidak ada model yang selalu memuat konsep inti, dan `gemma3:4b` paling cepat. Baca daftar modulnya, lalu tambahkan konsep yang hilang di JSON. |
| `materi_belajar` | `qwen3:8b`, `gemma3:4b`, `qwen3:4b` | Hanya `qwen3:8b` yang menulis semua angka dengan benar. Untuk hasil dalam 1 menit, pakai `--model gemma3:4b`, lalu periksa setiap angka. |

`qwen3:4b` ada di urutan terakhir untuk kedua skill. Silabusnya tidak lebih lengkap daripada silabus `gemma3:4b` walaupun lebih lambat, dan materi reksa dananya mengajarkan konsep yang salah di setiap bagian.

Cara memperbaiki isi yang salah lalu membangun ulang halamannya tanpa memanggil model ada di [Membuat silabus dan materi belajar](../panduan/membuat-silabus-dan-materi.md#memperbaiki-isi-lalu-membangun-ulang).

## Batasan perbandingan

- Setiap tugas dijalankan sekali per model di setiap putaran. Dengan temperature 0,3, jawaban berikutnya bisa berbeda, seperti NAB yang muncul di 2 dari 5 silabus `gemma3:4b`.
- Hanya dua topik yang diuji, keduanya untuk pemula dan dalam bahasa Indonesia.
- Jawaban dibaca oleh Claude, yang juga menulis jawaban pembanding. Fakta diperiksa dengan pengetahuan umum, bukan dengan sumber resmi.
- Waktu dan jumlah layer di GPU berlaku untuk laptop ini. Di GPU yang lebih besar, `qwen3:8b` muat seluruhnya dan jauh lebih cepat.

## File perbandingan

Semua file ada di `research/learning_skills_comparison/`:

| File | Isi |
|---|---|
| `claude/` | Jawaban pembanding yang ditulis Claude. |
| `gemma3-4b/`, `qwen3-4b/`, `qwen3-8b/` | Jawaban asli setiap model di putaran kedua, beserta halaman HTML-nya. |
| `run1/` | Jawaban dan halaman putaran pertama. |
| `results.json` | Waktu, token, percobaan, dan peringatan setiap tugas. |
| `metrics.json` | Ukuran yang dihitung skrip, seperti jumlah bab, soal hafalan, dan jam modul. |
| `review.json` | Catatan hasil membaca setiap jawaban: angka salah, fakta salah, aturan yang dilanggar, dan konsep yang hilang. |

Perbandingan bisa diulang dengan dua perintah ini. Perintah pertama memanggil ketiga model; perintah kedua menghitung `metrics.json`:

```shell
uv run python research/learning_skills_comparison/run_comparison.py
uv run python research/learning_skills_comparison/score_outputs.py
```

## Halaman terkait

- [Membuat silabus dan materi belajar](../panduan/membuat-silabus-dan-materi.md) untuk langkah memakai kedua skill.
