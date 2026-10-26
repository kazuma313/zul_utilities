---
name: infografis-satu-lembar
description: Membuat infografis satu lembar rasio 4:5 (1080x1350, siap diunggah ke Instagram) dalam tiga susunan. Susunan adaptif menyusun lembar dari 2 sampai 4 blok yang dipilih menurut bentuk informasinya (pita waktu, tahap, alur, perbandingan, langkah, angka persen), dan tinggi tiap blok menyesuaikan isinya. Susunan produk menjelaskan produk atau jasa lewat masalah, solusi, contoh cara kerja, dan harga. Susunan linimasa adalah rakitan siap pakai untuk satu periode sejarah yang terbagi tiga masa. Pakai saat pengguna meminta infografis, poster ringkasan, atau konten Instagram penjelas. Model hanya mengisi satu berkas JSON berisi teks pendek, lalu skrip memeriksa dan menggambarnya, jadi aman dipakai model kecil.
---

# Infografis satu lembar 4:5

## Yang perlu kamu ingat

- Kamu **tidak menggambar**. Kamu hanya mengisi `isi.json`. Skrip yang memeriksa dan menggambar.
- **Sedikit teks, banyak gambar.** Setiap isian punya batas huruf. Kalimat pendek, satu ide.
- **Jangan mengarang angka.** Angka dan nama harus datang dari pengguna atau dokumen yang diberikan, dan angka masalah harus punya sumber.
- Jangan mengubah isi folder `scripts/`.

## Pilih susunan dulu

| Isi dari pengguna | Susunan | Isian `susunan` | Cetakan |
| --- | --- | --- | --- |
| Produk atau jasa: masalah, solusi, contoh cara kerja, harga | produk | tidak perlu diisi | `contoh/kosong.json` |
| Informasi lain yang bentuknya berbeda-beda: urutan tahun, tahapan, aliran, dua hal yang dibandingkan, cara melakukan sesuatu, angka persen | **adaptif** | `"susunan": "adaptif"` | `contoh/kosong_adaptif.json` |
| Satu periode sejarah yang terbagi **tiga masa** dengan peristiwa dan ke mana akibatnya mengalir | linimasa (rakitan siap pakai dari blok adaptif) | `"susunan": "linimasa"` | `contoh/kosong_linimasa.json` |

Jika pengguna belum jelas, tanyakan: "Apakah ini menjelaskan produk, atau informasi lain?" Selain produk, pakai **adaptif**: kamu tidak memaksa isinya masuk ke satu cetakan, tetapi memilih blok yang cocok dengan bentuk informasinya.

### Memilih blok untuk susunan adaptif

Baca dulu isi yang diberikan pengguna, lalu tanyakan pada tiap bagiannya: bentuk informasi apa ini?

| Bentuk informasi | Blok |
| --- | --- |
| Berjalan dari tahun ke tahun, ada masa dan peristiwa | `pita_waktu` |
| Tahapan berurutan, masing-masing punya ciri | `tahap` |
| Satu pusat mengalir ke beberapa tujuan | `alur` |
| Dua pihak dibandingkan pada beberapa hal | `banding` |
| Cara melakukan sesuatu, urut dari awal | `langkah` |
| Dua sampai empat angka persen | `angka` |

Aturannya:

- Pakai 2 sampai 4 blok, satu jenis paling banyak sekali. Urutan di `blok` adalah urutan dari atas ke bawah. Taruh blok yang paling penting di paling atas, karena blok pertama juga menentukan angka sorotan di kepala.
- Bila bagian informasi tidak cocok dengan satu pun bentuk, **jangan dipaksakan** ke blok yang salah. Sebutkan bagian itu ke pengguna dan tanyakan apakah boleh dibuang atau dipersingkat.
- Tinggi blok menyesuaikan jumlah butir dan sisa ruang. Bila `cek.mjs` melapor `terlalu padat`, kurangi satu blok atau kurangi butirnya. Jangan memperkecil teks.
- Lama masa, jumlah tahun, dan angka sorotan di kepala dihitung skrip. Jangan menulisnya sendiri.
- Bentuk lengkap tiap blok, batas huruf, dan contoh yang sudah lolos pemeriksaan ada di `references/katalog_blok.md`. Salin potongan blok dari sana.

## Di mana menjalankan perintah

Skrip ada di folder skill ini (disebut `<skill>`, yaitu "Base directory" yang diberikan platform). Kamu biasanya berada di folder kerja pengguna, bukan di folder skill. Karena itu:

- Tulis `isi.json` di **folder kerja pengguna**.
- Panggil skrip dengan **alamat lengkap**: `node "<skill>/scripts/cek.mjs" isi.json` dan `node "<skill>/scripts/bangun.mjs" isi.json --keluar hasil`.
- `--keluar hasil` menaruh hasilnya di folder `hasil/` di folder kerja itu.
- Contoh dan cetakan ada di `<skill>/contoh/`. Salin `kosong.json` ke folder kerja sebagai `isi.json`.

Perintah di bawah ditulis singkat (`node scripts/...`). Ganti `scripts/` dengan `<skill>/scripts/` bila kamu tidak berada di folder skill.

## Langkah (kerjakan berurutan)

**1. Kumpulkan fakta.** Kalau belum ada, tanyakan ke pengguna dalam satu pesan berisi daftar bernomor. Untuk susunan produk:

1. Nama produk dan satu kalimat tujuannya.
2. Masalah yang dipecahkan, dua angka pendukung beserta sumbernya (lembaga dan tahun), dan arti tiap angka dalam kata sehari-hari.
3. Tiga hal yang dilakukan orang sekarang untuk mengatasi masalah itu.
4. Empat fitur utama beserta isinya.
5. Satu contoh pertanyaan pengguna dan jawabannya, lengkap dengan angka.
6. Harga paket (2 sampai 4), urut dari termurah.
7. Batasan produk yang perlu dinyatakan (misalnya "Tidak menjual bibit").

Untuk susunan adaptif, tanyakan dalam satu pesan:

1. Judul dua baris (maksimal 16 dan 20 huruf) dan satu kalimat tentang isinya.
2. Untuk tiap bagian informasi yang ingin ditampilkan, tanyakan sesuai bentuknya (daftar lengkapnya di `references/katalog_blok.md`): tahun mulai dan selesai tiap masa beserta peristiwanya, tahap beserta cirinya, tujuan aliran, dua pihak beserta hal yang dibandingkan, langkah berurutan, atau angka persen beserta artinya.
3. Bagian mana yang paling penting. Bagian itu menjadi blok pertama.
4. Sumber (penulis dan tahun, atau lembaga).

Untuk susunan linimasa, tanyakan:

1. Judul dua baris (maksimal 13 dan 16 huruf) dan satu kalimat tentang periodenya.
2. Tiga masa berurutan: nama, tahun mulai, tahun selesai, dan dua ciri pendek tiap masa. Tahun selesai satu masa sama dengan tahun mulai masa berikutnya.
3. Tiga sampai tujuh peristiwa penting: tahun dan satu frasa pendek tiap peristiwa. Peristiwa yang berulang (misalnya beberapa letusan) cukup satu butir dengan `sampai` dan `titik`.
4. Dari satu pusat ke tiga tujuan: ke mana orangnya pergi, atau ke mana akibatnya mengalir. Beri tahu tujuan mana yang paling banyak dituju.
5. Sumber (penulis dan tahun, atau lembaga).

Bila ada yang belum dijawab, tulis apa yang kurang dan berhenti. **Jangan mengisinya dengan karanganmu.**

**2. Isi `isi.json`.** Salin cetakan susunannya (`contoh/kosong.json`, `contoh/kosong_adaptif.json`, atau `contoh/kosong_linimasa.json`) menjadi `isi.json`. Ganti setiap teks di antara `[ ... ]` dengan isi sebenarnya. Pada susunan adaptif, cetakannya hanya berisi dua blok sebagai contoh: ganti, tambah, atau buang blok sesuai bentuk informasinya, dengan potongan dari `references/katalog_blok.md`. Contoh yang sudah benar dan lolos pemeriksaan:

- `contoh/tanam_kota.json` (produk, semua angkanya fiktif)
- `contoh/adaptif_cara_menanam.json` (adaptif: langkah, perbandingan, angka)
- `contoh/adaptif_dua_kota.json` (adaptif: pita waktu dan perbandingan)
- `contoh/majapahit_masa_pudar.json` (linimasa, dari uraian sejarah dengan sumbernya)

Tirulah bentuknya.

**3. Periksa.**

```bash
node scripts/cek.mjs isi.json
```

Kalau ada baris `GAGAL`, perbaiki persis seperti pesannya, lalu jalankan lagi. Ulangi sampai keluar `LOLOS`. Baris `PERINGATAN` sebaiknya juga diperbaiki.

**4. Gambar.**

```bash
node scripts/bangun.mjs isi.json
```

Hasilnya ada di folder `hasil/`: `infografis.png` (2160×2700), `infografis.pdf`, dan `infografis.html`. Bila muncul baris `BERTUMPUK`, perpendek teks yang disebut lalu jalankan lagi.

**5. Periksa gambar.** Kalau kamu bisa melihat gambar, buka `hasil/infografis.png`. Jawab ya atau tidak:

- Apakah setiap angka punya arti yang bisa dipahami orang awam?
- Apakah ada kata yang bisa membuat orang bertanya "maksudnya apa?"
- Apakah ada teks yang terpotong atau menempel ke teks lain?

Jika ada "ya" untuk pertanyaan kedua atau ketiga, perbaiki `isi.json` dan ulangi langkah 3 dan 4.

**6. Serahkan.** Sebutkan lokasi `infografis.png` dan `infografis.pdf`. Tambahkan satu kalimat tentang angka yang perlu diperiksa pengguna.

## Aturan isi

Aturan ini dijaga oleh `cek.mjs`, dan semuanya berasal dari koreksi nyata atas infografis yang dibuat lebih dulu.

| Jangan | Tulis begini |
| --- | --- |
| "paham berkebun" (tidak jelas paham apa) | "tahu dan terampil merawatnya" |
| "15–30 hari" berdiri sendiri | "Panen sayur: 15–30 hari", lalu "yaitu sejak biji disemai" |
| "Tanpa jual produk" (pembaca mengira Anda tidak menjual apa pun) | "Tidak menjual bibit" (sebut produk apa) |
| Mengubah angka indeks menjadi "7 dari 10 orang" | Tulis angka itu apa adanya dan jelaskan artinya |
| Tangkapan layar aplikasi | Tidak dipakai. Gambarnya ikon dan bentuk |
| Rencana atau roadmap | Tidak dimasukkan, kecuali diminta |
| Istilah teknis atau bahasa asing tanpa penjelasan | Kata sehari-hari |
| Kata bersayap: terbaik, terlengkap, canggih, inovatif | Fakta: angka, nama, atau contoh |

Aturan umum: satu ide per isian, kalimat paling banyak 10 kata, angka selalu disertai satuan (juta, ribu, %, kali, bulan, orang), tanpa emoji, tanda `*` hanya untuk menyorot angka di `contoh.jawab_utama`.

## Ikon yang boleh dipakai

`pensil`, `kalkulator`, `obrolan`, `buku`, `perisai`, `orang`, `label`, `video`, `tabel`, `grafik`, `dokumen`, `centang`, `dompet`, `koin`, `jam`, `gembok`, `ponsel`, `keranjang`, `lokasi`, `petir`, `bintang`, `api`, `gunung`, `mahkota`, `jalan`, `pohon`, `candi`, `panah`, `pedang`, `surya`.

Pilih ikon yang artinya paling dekat dengan isiannya. Nama di luar daftar ini ditolak oleh `cek.mjs`.

## Bentuk isian

Lihat `contoh/tanam_kota.json`. Ringkasnya: `kepala` (judul dua baris dan tujuan), `masalah` (kalimat, dua ukuran bergambar cincin, sumber, tiga hal yang dilakukan orang sekarang), `solusi` (empat simpul), `contoh` (satu tanya jawab dengan tiga label), `paket` (2 sampai 4 harga), dan `kaki` (catatan penutup). Jumlah butir di tiap daftar harus persis seperti contoh.

Susunan adaptif: `kepala` (`judul_1`, `judul_2`, `tujuan`, dan boleh `sorot`), `blok` (2 sampai 4 blok, tiap blok punya `jenis`), `sumber`, dan `kaki`. `sorot` boleh dihapus (dibuat otomatis dari blok pertama), `"tanpa"` (diganti huruf pertama merek), atau `{ "nilai", "arti" }`; `"nilai": "lama_pita"` memakai jumlah tahun dari blok `pita_waktu`. Isi tiap blok ada di `references/katalog_blok.md`. Pada blok `tahap` dengan `"ikuti_pita": true`, kartunya mengikuti masa di `pita_waktu` dan angkanya dihitung dari sana.

Susunan linimasa: `kepala` (judul dua baris, tujuan, dan arti jumlah tahun), `periode` (tepat 3 masa dengan `nama`, `mulai`, `selesai`, `ikon`, dan 2 `poin`), `peristiwa` (3 sampai 7 butir dengan `tahun`, `teks`, `ikon`, dan boleh `sampai` serta `titik`), `sebaran` (`judul`, `pusat`, tepat 3 `tujuan`, dan `utama` 0 sampai 2), `sumber`, dan `kaki`. Semua tahun ditulis sebagai angka tanpa tanda kutip.

## Kalau ada kendala

- **Tidak ada Chrome atau Edge:** jalankan `node scripts/bangun.mjs isi.json --tanpa-gambar`, lalu buka `hasil/infografis.html` di peramban. Chrome di lokasi lain: setel variabel `CHROME_PATH`.
- **Tidak bisa menjalankan perintah sama sekali:** tulis isi `isi.json` yang lolos aturan di atas, lalu minta pengguna menjalankan dua perintah di langkah 3 dan 4.
- **Merek lain:** salin `merek/tanam_kota.json` menjadi `merek/<nama>.json`, ganti warna, huruf, dan logo, lalu isi `"merek": "<nama>"` di `isi.json`. Logo boleh dikosongkan (`null`); lingkaran logo diisi huruf pertama nama merek.
- **Rasio lain atau lebih dari satu lembar:** di luar skill ini.
