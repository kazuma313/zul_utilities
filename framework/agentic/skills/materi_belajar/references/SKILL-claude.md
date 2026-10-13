---
name: materi-belajar
description: Membuat materi pembelajaran satu modul sebagai halaman HTML visual untuk orang awam - tujuan belajar, bab dengan struktur Apa/Bagaimana/Mengapa penting, kotak istilah, diagram, demo interaktif, rangkuman, kuis pilihan ganda, latihan, dan kamus istilah (gaya explainer-awam yang dijadikan pelajaran). Gunakan skill ini SETIAP KALI user minta materi untuk dipelajari - misalnya "buatkan materi modul 2", "lanjut modul berikutnya", "buatkan materinya", "bahan ajar", "modul pembelajaran", "lesson", "pelajaran tentang X", "ajari saya X lengkap dengan kuis/latihan", "ubah dokumen/PDF/link ini jadi materi belajar", atau menyebut modul dari sebuah silabus - bahkan jika user tidak menyebut kata HTML atau kuis. Skill ini pasangan silabus-belajar - silabus-belajar menyusun rencana modul, skill ini menulis isi tiap modulnya. Untuk menyusun urutan modul dan jadwal pakai silabus-belajar; untuk penjelasan satu dokumen tanpa kuis dan latihan pakai explainer-awam.
---

# Materi belajar

Skill ini menghasilkan satu halaman HTML yang mengajarkan **satu modul** kepada orang yang belum punya latar belakang di bidangnya. Bedanya dengan penjelasan biasa: pembaca tahu sejak awal apa yang harus bisa ia lakukan, dan di akhir ia bisa mengecek sendiri apakah sudah bisa.

Template dan aturan bahasanya sama dengan skill `explainer-awam` (Apa / Bagaimana / Mengapa penting, kotak istilah, diagram, demo interaktif, kamus), ditambah tujuan belajar, kuis, dan latihan. Skill ini berdiri sendiri; semua yang dibutuhkan ada di folder ini.

Pakai format ini setiap kali skill terpicu, tanpa menanyakan format dulu. Pengecualian: user eksplisit minta jawaban singkat di chat, atau minta format lain (Word, PDF, slide).

## File di skill ini

- `assets/template.html` - kerangka halaman: CSS lengkap (mode gelap, ramah HP), semua komponen, script kuis, dan placeholder `{{...}}`. Selalu mulai dari sini.
- `references/diagram-recipes.md` - resep diagram SVG. Baca sebelum menggambar diagram pertama.
- `references/contoh-materi.html` - contoh materi jadi (Modul 3 dari silabus Bitcoin: Hash dan blockchain). Standar untuk nada bahasa, ukuran bab, demo, soal kuis, dan latihan. Jangan salin isinya ke topik lain.

## Workflow

1. **Ambil kontrak modul.** Kontrak modul adalah hal yang sudah dijanjikan ke pembaca: judul, pertanyaan utama, tujuan belajar, istilah yang dipelajari, latihan, sumber, posisi modul (N dari M), modul sebelum dan sesudahnya, contoh berjalan, dan warna aksen.
   - **Ada silabus** (dibuat skill `silabus-belajar`, atau diberikan user): baca kartu modulnya dari file silabus di `/mnt/user-data/outputs/`, dari link artifact (Artifact tool action `read`), atau dari teks yang ditempel user. Kontrak diambil apa adanya. Materi yang tujuan belajarnya berbeda dari silabus membuat pembaca merasa dijanjikan satu hal dan diberi hal lain.
   - **Tidak ada silabus** (materi lepas): tulis sendiri kontraknya, yaitu satu pertanyaan utama, 2-4 tujuan belajar, dan 3-6 istilah. Kalau topiknya tidak muat dalam satu modul (lebih dari 3 jam belajar), kerjakan bagian pertamanya dan sebutkan di pesan penutup bahwa sisanya lebih cocok disusun sebagai silabus.
2. **Baca sumber modul ini sampai habis.** URL atau PDF: ambil dengan web_fetch. File upload: baca dari disk. Tanpa dokumen: cari sumber yang kredibel dulu. Semua angka, nama, dan klaim harus berasal dari sumber, bukan dari ingatan.
3. **Petakan 3-6 bab dari tujuan belajar.** Setiap tujuan belajar harus punya bab yang mengajarkannya, dan setiap bab harus melayani minimal satu tujuan. Bab yang tidak melayani tujuan mana pun dibuang, semenarik apa pun isinya. Urutkan dengan sebab-akibat: bab pertama membuka masalah (di Modul 2 dan seterusnya: celah yang ditinggalkan modul sebelumnya), tiap bab menutup celah bab sebelumnya, bab terakhir menyisakan celah untuk modul berikutnya.
4. **Temukan konsep tersulit** di modul ini dan rancang demo interaktif untuknya (lihat "Demo interaktif").
5. **Tulis bab** mengikuti aturan bahasa. Pakai contoh berjalan yang sama dengan modul lain di silabus (tokoh dan angkanya).
6. **Tulis kuis dan latihan** dari tujuan belajar, bukan dari isi bab (lihat "Kuis" dan "Latihan").
7. **Bangun HTML** dari `assets/template.html`, simpan sebagai `<topik>-modul-<N>.html` (materi lepas: `materi-<topik>.html`). Ganti semua `{{...}}`, hapus komentar petunjuk dan blok yang tidak dipakai.
8. **Cek checklist** di akhir file ini. Demo dan kuis dicek dengan benar-benar menjalankannya kalau ada browser otomatis (mis. Playwright); kalau tidak ada, telusuri script-nya baris demi baris.
9. **Publikasikan dan tautkan.** Di claude.ai: simpan di `/mnt/user-data/outputs/`, lalu Artifact tool action `publish` dengan favicon emoji yang relevan. Kalau modul ini bagian dari silabus: link eyebrow mengarah ke URL silabus, lalu di file silabus ganti `<span class="soon">Materi belum dibuat</span>` pada kartu modul ini dengan `<a class="open" href="URL materi" target="_blank" rel="noopener">Buka materi →</a>` dan publish ulang silabus dengan `url` artifact-nya. Tanpa Artifact tool: `present_files`, dan tautan memakai nama file.
10. **Pesan chat penutup** 2-4 kalimat: isi halaman (jumlah bab, diagram, demo, soal), lalu cara melanjutkan ("ketik *lanjut modul N+1*"). Jangan mengulang isi halaman di chat.

**Beberapa modul sekaligus** ("buatkan semua modul"): kerjakan berurutan, satu file per modul. Jangan menggabungkan beberapa modul dalam satu halaman, karena halaman yang terlalu panjang tidak selesai dibaca.

**Revisi:** edit file yang sama lalu publish ulang dengan `url` artifact sebelumnya. Kalau revisi mengubah tujuan belajar, kartu modul di silabus ikut diubah supaya keduanya tetap sama.

## Aturan bahasa

Aturan ini sama dengan `explainer-awam` dan berasal dari koreksi langsung user, jadi prioritasnya paling tinggi.

**Istilah umum tidak diterjemahkan.** Pakai hash, block, blockchain, node, wallet, fee, mining, exchange, startup, revenue, AI, model, dan sejenisnya apa adanya, karena itulah kata yang akan ditemui pembaca di luar. Jangan membuat padanan buatan lalu memakainya sebagai pengganti istilah.

- Salah: "Hash adalah sidik jari digital…" lalu sepanjang halaman menulis "sidik jari halaman ini".
- Benar: "Hash adalah kode unik dengan panjang tetap yang dihasilkan dari sebuah data." Analogi boleh dipakai sekali untuk menjelaskan, tapi istilahnya tetap "hash".

**Kata sehari-hari tetap sehari-hari.** Jangan membakukan atau mengindonesiakan berlebihan. Tulis seperti orang menjelaskan ke teman.

**Tidak bertele-tele.** Kalimat pendek, satu ide per paragraf, tanpa pembuka basa-basi. Kalau satu kalimat cukup, jangan pakai tiga.

**Bangun bertahap.** Jangan memakai konsep sebelum dijelaskan. Ini berlaku juga antar modul: istilah yang baru diajarkan di modul sesudahnya tidak boleh muncul di modul ini, walaupun di dunia nyata keduanya selalu disebut bersama (contoh: block dijelaskan tanpa nonce kalau nonce baru muncul di modul berikutnya).

**Analogi lokal, satu per konsep.** Uang tunai dan gorengan, arisan RT, BPKB kendaraan, warung dan uang kembalian, bagan turnamen sepak bola. Jangan menumpuk beberapa analogi untuk satu hal.

**Angka konkret** lebih mudah dipahami daripada penjelasan abstrak ("Budi bayar 0,5 BTC, Sari dapat 0,3 BTC").

Sapa pembaca dengan "Anda". Bahasa halaman mengikuti bahasa user (default Indonesia).

## Struktur halaman

1. **Hero:** eyebrow "Silabus [Topik] · Modul N dari M" dengan link ke silabus (materi lepas: "Materi belajar"); judul modul; lead berisi pertanyaan utama; chip waktu, jumlah bab, jumlah soal; kotak "Setelah modul ini, Anda bisa"; kotak "Bekal dari modul sebelumnya" (mulai Modul 2); kotak cara membaca; daftar isi.
2. **3-6 bab.** Setiap bab punya nomor, judul `h2`, label sumber ("Whitepaper bab 3, Timestamp Server"), lalu tiga bagian `h3`:
   - **Apa** - pengertian
   - **Bagaimana** - cara kerja, dengan diagram atau demo
   - **Mengapa penting** - masalah yang terselesaikan, celah yang masih ada, dan sambungannya ke bab berikutnya

   Judul `h3` boleh divariasikan ("Bagaimana: coba sendiri", "Mengapa penting, dan apa yang masih kurang"), asalkan ketiga pertanyaan terjawab. Setiap istilah baru mendapat kotak `.term` saat **pertama kali** muncul. Istilah dari modul sebelumnya tidak diberi kotak lagi, cukup diingatkan di "Bekal".
3. **Blok model bisnis** kalau kontrak modulnya membahas model bisnis atau insentif: diagram aliran vertikal (resep 2) dan tabel `Pihak | Memberi | Mendapat`.
4. **Rangkuman:** 4-6 poin bernomor yang menceritakan ulang alur modul, diakhiri celah yang tersisa.
5. **Cek pemahaman:** kuis.
6. **Latihan**, lalu kotak "Berikutnya". Di modul terakhir, kotak itu mengarah ke proyek akhir.
7. **Kamus istilah** (`dl.gloss`): istilah baru di modul ini, urut sesuai kemunculan. Topik keuangan, investasi, atau kripto: catatan "bukan saran keuangan".
8. **Footer** dengan link sumber.

## Kuis

Kuis adalah cara pembaca mengetahui apakah tujuan belajarnya tercapai, jadi mutunya menentukan mutu modul.

- **4-6 soal pilihan ganda, 3 pilihan per soal.** Isi array `QUIZ` di script template.
- **Setiap tujuan belajar diuji minimal satu soal** (atau satu latihan, kalau tujuannya berupa praktik).
- **Uji pemakaian, bukan hafalan.** Soal yang baik menaruh konsep di situasi baru: "Andi mengubah satu transaksi di Block 1. Apa akibatnya?". Soal yang lemah meminta definisi: "Apa itu hash?".
- **Pilihan yang salah harus masuk akal**, yaitu kesalahpahaman yang memang sering terjadi ("hash-nya hanya beda satu karakter"). Pilihan yang jelas-jelas ngawur membuat soal bisa dijawab tanpa paham.
- **`why` menjelaskan alasannya dan menyebut bab** yang perlu dibaca ulang. Tulis untuk orang yang menjawab salah.
- **Mulai Modul 2, soal pertama diambil dari modul sebelumnya**, karena mengingat kembali setelah jeda membuat ingatan lebih awet, dan sekaligus mengaktifkan bekal yang dipakai modul ini.
- **Acak posisi jawaban benar.** Teks soal dan pilihan adalah teks biasa, tanpa tag HTML.

## Latihan

- **1-3 tugas.** Kalau kartu modul di silabus sudah menyebut latihan, tugas pertama adalah latihan itu.
- **Setiap tugas menghasilkan sesuatu yang bisa dilihat:** hitungan, tabel, gambar alur, penjelasan beberapa kalimat. "Baca lagi bab 2" bukan latihan.
- **Tulis "Hasil yang diharapkan"** supaya pembaca bisa menilai sendiri tanpa guru.
- Latihan yang paling murah dibuat dan paling berguna adalah yang memakai demo di halaman itu sendiri ("ubah X, catat Y, simpulkan").

## Demo interaktif

Minimal satu per modul, untuk konsep tersulit. Polanya: pembaca mengubah sesuatu → hasilnya langsung berubah. Demo yang baik membuat pembaca **mengalami** tujuan belajarnya: untuk "menjelaskan kenapa mengubah satu block merusak block setelahnya", demonya membiarkan pembaca mengubah satu block dan melihat block berikutnya menjadi tidak sah.

Contoh pola: hash playground, mini blockchain, kalkulator bunga majemuk, slider risiko vs imbal hasil, simulasi pembagian fee, simulasi antrean transaksi. Beri satu kalimat instruksi yang menyebut apa yang diubah dan apa yang harus diperhatikan. Status hasil memakai `.status` dengan `ok` (teal), `no` (aksen), atau `bad` (merah).

## Visual

- **Diagram:** minimal satu per bab yang membahas mekanisme. Satu modul biasanya butuh 3-6 diagram. Ikuti `references/diagram-recipes.md`.
- **Angka dari sumber:** komponen `.bars` atau tabel.
- **Warna bermakna:** aksen = hal yang disorot, teal = sah/hasil/tercapai, merah = masalah/risiko, netral = sisanya. `--accent` mengikuti warna yang dipakai silabusnya. Selain itu jangan mengubah sistem desain, supaya semua modul terlihat sebagai satu paket.

## Aturan teknis

- Satu file HTML self-contained. Font hanya dari Google Fonts (sudah di template). Script inline; library eksternal hanya dari cdnjs.cloudflare.com atau cdn.jsdelivr.net. Tidak ada gambar dari internet.
- `crypto.subtle` tersedia untuk demo hash. Demo yang memakai fungsi async dan input teks perlu menjaga urutan hasil (lihat variabel `seq` di contoh), supaya hasil ketikan lama tidak menimpa yang baru.
- Jika memakai localStorage, bungkus dengan try/catch.
- Hak cipta: parafrase sumber dengan kata-kata sendiri. Kutipan langsung jarang, di bawah 15 kata.

## Checklist sebelum publish

- [ ] Tujuan belajar sama persis dengan kartu modul di silabus (atau dengan kontrak yang ditulis di langkah 1)
- [ ] Setiap tujuan belajar punya bab yang mengajarkannya dan soal atau latihan yang mengujinya
- [ ] Setiap bab menjawab apa, bagaimana, dan mengapa penting, dan menyambung ke bab berikutnya
- [ ] Setiap istilah baru punya kotak `.term` saat pertama muncul dan ada di kamus
- [ ] Tidak ada istilah umum yang diterjemahkan paksa, dan tidak ada istilah dari modul sesudahnya
- [ ] Contoh berjalan (tokoh dan angka) sama dengan modul lain
- [ ] Ada minimal satu demo interaktif, dan sudah dicek berjalan
- [ ] Kuis berjalan: indeks `a` benar, posisi jawaban benar bervariasi, setiap `why` menyebut bab
- [ ] Setiap latihan punya "Hasil yang diharapkan"
- [ ] Semua angka sesuai sumber
- [ ] Tidak ada teks SVG yang keluar dari kotaknya (hitung lebar sesuai `diagram-recipes.md`)
- [ ] Tidak ada `{{...}}` atau komentar petunjuk yang tertinggal
- [ ] Silabus dan materi saling bertaut, dan status materi di kartu modul sudah diperbarui
- [ ] Aman di layar HP dan mode gelap
- [ ] Pesan penutup di chat singkat dan tidak mengulang isi
