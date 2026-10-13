---
name: silabus-belajar
description: Menyusun silabus belajar (learning path) untuk satu topik sebagai halaman HTML visual - kemampuan akhir, peta belajar, kartu modul dengan pertanyaan utama dan tujuan belajar, jadwal mingguan, proyek akhir, sumber, dan progress yang bisa dicentang. Gunakan skill ini SETIAP KALI user ingin belajar sesuatu secara bertahap atau butuh rencana belajar - misalnya "buatkan silabus", "kurikulum", "roadmap belajar", "rencana belajar", "learning path", "study plan", "saya mau belajar X dari nol", "ajari saya X step by step", "buatkan kursus tentang X", atau minta mengubah dokumen/PDF/link menjadi rencana belajar bermodul - bahkan jika user tidak menyebut kata silabus atau HTML. Skill ini pasangan materi-belajar - skill ini menyusun rencana modulnya, materi-belajar menulis isi tiap modul (setelah silabus jadi, materi Modul 1 langsung dibuat dengan materi-belajar). Untuk penjelasan satu dokumen atau satu konsep dalam satu halaman tanpa rencana belajar, pakai explainer-awam.
---

# Silabus belajar

Skill ini mengubah "saya mau belajar X" menjadi **halaman silabus**: peta belajar yang berisi kemampuan akhir, modul berurutan, jadwal, proyek akhir, dan sumber.

Isi tiap modul ditulis oleh skill pasangannya, `materi-belajar`, satu halaman per modul. Kartu modul di silabus adalah kontrak untuk skill itu: judul, pertanyaan utama, tujuan belajar, istilah, latihan, dan sumber yang tertulis di kartu akan diambil apa adanya saat materinya dibuat. Karena itu kartu modul harus ditulis cukup jelas untuk dikerjakan tanpa bertanya lagi.

Pakai format ini setiap kali skill terpicu, tanpa menanyakan format dulu. Pengecualian: user eksplisit minta jawaban singkat di chat, atau minta format lain (Word, PDF, slide).

## File di skill ini

- `assets/template-silabus.html` - kerangka halaman silabus: CSS lengkap (mode gelap, ramah HP), kartu modul, progress yang tersimpan di browser, jadwal, proyek akhir. Selalu mulai dari sini.
- `references/diagram-recipes.md` - resep diagram SVG. Untuk silabus yang dipakai adalah resep 9 "Peta modul".
- `references/contoh-silabus.html` - contoh silabus jadi (Bitcoin). Standar untuk ukuran modul, cara menulis tujuan belajar, dan jadwal. Jangan salin isinya ke topik lain.

## Workflow

### Permintaan pertama

1. **Kenali pelajarnya** dari pesan user: topik, tujuan (untuk apa belajar ini), level awal, waktu yang tersedia, tenggat, sumber yang diberikan. Yang tidak disebut, isi dengan asumsi wajar (default: pemula dari nol, 3-4 jam per minggu, tujuan paham cara kerja dan bisa memakainya) dan tulis asumsi itu di kotak "Silabus ini dibuat dengan asumsi" supaya user bisa mengoreksi. Bertanya dulu hanya kalau topiknya sendiri tidak jelas; pertanyaan beruntun sebelum ada hasil membuat user menunggu untuk hal yang lebih cepat dikoreksi setelah melihat drafnya.
2. **Kumpulkan sumber.** User memberi dokumen, PDF, atau link: baca sampai habis, itulah sumber utama. Tanpa dokumen: cari 3-6 sumber kredibel (dokumen resmi, regulator, buku atau kursus yang diakui). Semua angka, nama, dan klaim di materi harus berasal dari sumber, bukan dari ingatan.
3. **Rancang mundur.** Tentukan dulu 4-6 kemampuan akhir ("Setelah selesai, Anda bisa…"), lalu proyek akhir yang membuktikannya, baru modul yang mengantar ke sana. Dimulai dari daftar isi buku menghasilkan silabus yang lengkap tapi tidak jelas gunanya.
4. **Susun modul** mengikuti "Aturan menyusun silabus" di bawah.
5. **Pilih satu contoh berjalan** untuk seluruh silabus: tokoh lokal (Budi, Sari, Andi) dan angka konkret yang dipakai dari Modul 1 sampai modul terakhir.
6. **Bangun halaman silabus** dari `assets/template-silabus.html`, simpan sebagai `silabus-<topik>.html`. Ganti semua `{{...}}`, hapus komentar petunjuk, dan gambar peta modul mengikuti resep 9.
7. **Cek checklist** di akhir file ini, lalu publish.
8. **Buat materi Modul 1 dengan skill `materi-belajar`:** baca SKILL.md skill itu dan ikuti workflow-nya, dengan kartu Modul 1 sebagai kontraknya. User datang untuk belajar, bukan hanya untuk melihat rencana, jadi permintaan pertama selalu menghasilkan sesuatu yang bisa langsung dipelajari. Lewati langkah ini kalau user eksplisit minta silabusnya saja, atau kalau skill `materi-belajar` tidak terpasang (sebutkan itu di pesan penutup).
9. **Tautkan.** Setelah materi di-publish, ganti `<span class="soon">` pada kartu Modul 1 dengan link `Buka materi →` ke URL materi, lalu publish ulang silabus dengan `url` artifact-nya.
10. **Pesan chat penutup** 2-4 kalimat: jumlah modul, total waktu, asumsi yang diambil, dan cara melanjutkan ("ketik *lanjut modul 2*"). Jangan mengulang isi halaman di chat.

### Permintaan lanjutan

- **"Lanjut modul N" atau "buatkan semua modul":** itu pekerjaan skill `materi-belajar`. Tugas skill ini hanya memperbarui status materi di kartu modul.
- **Revisi silabus** ("padatkan jadi 2 minggu", "saya sudah paham dasar-dasarnya"): edit file silabus yang sama dan publish ulang dengan `url` sebelumnya. Kalau tujuan belajar sebuah modul berubah, materi modul yang sudah dibuat ikut disesuaikan.

Di claude.ai: simpan di `/mnt/user-data/outputs/` lalu Artifact tool action `publish` dengan favicon emoji yang relevan. Tanpa Artifact tool: `present_files`.

## Aturan menyusun silabus

**4-8 modul, masing-masing 1-3 jam.** Modul yang lebih besar dari itu dipecah. Topik yang butuh lebih dari 8 modul dibagi menjadi beberapa tahap, dan tahap pertama dikerjakan dulu.

**Satu modul menjawab satu pertanyaan utama.** Tulis pertanyaannya di kartu modul ("Kalau tidak ada bank, siapa yang mencatat?"). Pertanyaan membuat pembaca tahu apa yang dicari; judul topik saja tidak.

**Tujuan belajar harus bisa dibuktikan.** 2-4 per modul, dengan kata kerja yang hasilnya bisa dicek: menjelaskan, menghitung, membaca, membandingkan, membuat. Hindari "memahami" dan "mengetahui", karena pembaca tidak bisa menilai sendiri apakah sudah tercapai. Setiap tujuan belajar nanti diuji soal kuis atau latihan di materinya.

**Urutan mengikuti ketergantungan.** Modul tidak boleh memakai istilah yang baru dijelaskan di modul sesudahnya. Kelompokkan modul ke 2-3 tahap (misalnya Fondasi → Inti → Penerapan) dan sambungkan antar modul dengan sebab-akibat: modul ini menyisakan celah, modul berikutnya menutupnya.

**Setiap modul punya latihan dengan hasil nyata**, sesuatu yang bisa dilihat atau ditunjukkan (hitungan, tabel perbandingan, penjelasan lima kalimat, tangkapan layar), bukan "baca lagi bab ini".

**Topik yang menyangkut produk, perusahaan, industri, atau instrumen keuangan wajib punya satu modul tentang model bisnis atau insentif:** siapa memberi apa, siapa mendapat apa, dan mengapa tiap pihak mau ikut. Topik yang menyangkut uang juga wajib membahas risiko.

**Jadwal realistis.** Total jam = jumlah jam modul + proyek akhir. Bagi ke minggu sesuai waktu yang tersedia, dan sisakan waktu untuk mengulang. Setiap minggu punya "hasil nyata".

## Aturan bahasa

Aturan ini sama dengan `explainer-awam` dan `materi-belajar`, dan berasal dari koreksi langsung user, jadi prioritasnya paling tinggi.

**Istilah umum tidak diterjemahkan.** Pakai hash, block, blockchain, node, wallet, fee, mining, exchange, startup, revenue, AI, model, dan sejenisnya apa adanya, karena itulah kata yang akan ditemui pembaca di luar. Jangan membuat padanan buatan lalu memakainya sebagai pengganti istilah.

- Salah: "Hash adalah sidik jari digital…" lalu sepanjang halaman menulis "sidik jari halaman ini".
- Benar: "Hash adalah kode unik dengan panjang tetap yang dihasilkan dari sebuah data." Analogi boleh dipakai sekali untuk menjelaskan, tapi istilahnya tetap "hash".

**Kata sehari-hari tetap sehari-hari.** Jangan membakukan atau mengindonesiakan berlebihan. Tulis seperti orang menjelaskan ke teman.

**Tidak bertele-tele.** Kalimat pendek, satu ide per paragraf, tanpa pembuka basa-basi.

**Bangun bertahap.** Istilah yang baru diajarkan di modul 4 tidak boleh muncul di kartu modul 1-3. Lompatan konsep adalah penyebab utama pembaca bingung.

**Analogi lokal, satu per konsep.** Uang tunai dan gorengan, arisan RT, BPKB kendaraan, warung dan uang kembalian, bagan turnamen sepak bola. Jangan menumpuk beberapa analogi untuk satu hal.

**Angka konkret** lebih mudah dipahami daripada penjelasan abstrak.

Sapa pembaca dengan "Anda". Bahasa halaman mengikuti bahasa user (default Indonesia).

## Struktur halaman silabus

1. **Hero:** judul pola "Belajar [Topik] dari nol" (sesuaikan kalau levelnya bukan pemula); lead 2-3 kalimat; chip level, jumlah modul, total jam, ritme; kotak "Setelah selesai, Anda bisa"; kotak asumsi; kotak cara memakai; daftar isi.
2. **Peta belajar:** satu diagram (resep 9) yang menunjukkan semua modul, tahapnya, dan proyek akhir.
3. **Modul:** progress bar, lalu satu kartu per modul berisi pertanyaan utama, tujuan belajar, istilah yang dipelajari, latihan, perkiraan waktu, sumber, status materi, dan centang "Selesai".
4. **Jadwal:** tabel `Minggu | Modul | Waktu | Hasil nyata`.
5. **Proyek akhir:** satu tugas yang memakai semua modul, dengan 3-5 kriteria selesai yang bisa dicek sendiri.
6. **Sumber belajar:** tabel sumber dengan link dan dipakai untuk modul mana. Topik keuangan, investasi, atau kripto: tambah catatan "bukan saran keuangan".

## Visual

- **Peta modul** (resep 9) adalah satu-satunya diagram wajib di silabus.
- **Warna bermakna:** aksen = hal yang disorot, teal = hasil/tercapai, merah = risiko, netral = sisanya. Ganti `--accent` jika topik punya warna identitas; materi tiap modul akan memakai warna yang sama. Selain itu jangan mengubah sistem desain, supaya silabus dan semua materinya terlihat sebagai satu paket.

## Aturan teknis

- Satu file HTML self-contained. Font hanya dari Google Fonts (sudah di template). Script inline. Tidak ada gambar dari internet.
- Progress memakai localStorage dengan try/catch (sudah di template). Ganti `{{SLUG}}` dengan nama topik tanpa spasi supaya progress dua silabus tidak tercampur. Atribut `data-mod` tiap kartu harus unik (`m1`, `m2`, …).
- Hak cipta: parafrase sumber dengan kata-kata sendiri. Kutipan langsung jarang, di bawah 15 kata.

## Checklist sebelum publish

- [ ] Kemampuan akhir dan tujuan belajar tiap modul memakai kata kerja yang bisa dibuktikan
- [ ] Setiap modul punya pertanyaan utama, istilah, latihan dengan hasil nyata, perkiraan waktu, dan sumber
- [ ] Tidak ada modul yang memakai istilah dari modul sesudahnya
- [ ] Topik produk, perusahaan, atau keuangan punya modul model bisnis dan membahas risiko
- [ ] Total jam di chip = jumlah jam modul + proyek akhir = jumlah di tabel jadwal
- [ ] Asumsi tentang pelajar tertulis di halaman
- [ ] Peta modul cocok dengan daftar kartu modul, dan tidak ada teks SVG yang keluar dari kotaknya
- [ ] Progress berjalan: centang mengubah bar dan jumlah modul selesai
- [ ] Tidak ada `{{...}}` atau komentar petunjuk yang tertinggal
- [ ] Status materi di kartu modul sesuai (link kalau sudah dibuat)
- [ ] Aman di layar HP dan mode gelap
