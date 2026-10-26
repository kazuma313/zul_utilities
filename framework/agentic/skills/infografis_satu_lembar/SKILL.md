---
name: infografis-satu-lembar
description: Membuat infografis satu lembar rasio 4:5 (1080x1350, siap diunggah ke Instagram) untuk menjelaskan sebuah produk atau jasa lewat masalah, solusi, contoh cara kerja, dan harga. Pakai saat pengguna meminta infografis, poster ringkasan produk, atau konten Instagram penjelas. Model hanya mengisi satu berkas JSON berisi teks pendek, lalu skrip memeriksa dan menggambarnya, jadi aman dipakai model kecil.
---

# Infografis satu lembar 4:5

## Yang perlu kamu ingat

- Kamu **tidak menggambar**. Kamu hanya mengisi `isi.json`. Skrip yang memeriksa dan menggambar.
- **Sedikit teks, banyak gambar.** Setiap isian punya batas huruf. Kalimat pendek, satu ide.
- **Jangan mengarang angka.** Angka dan nama harus datang dari pengguna atau dokumen yang diberikan, dan angka masalah harus punya sumber.
- Jangan mengubah isi folder `scripts/`.

## Di mana menjalankan perintah

Skrip ada di folder skill ini (disebut `<skill>`, yaitu "Base directory" yang diberikan platform). Kamu biasanya berada di folder kerja pengguna, bukan di folder skill. Karena itu:

- Tulis `isi.json` di **folder kerja pengguna**.
- Panggil skrip dengan **alamat lengkap**: `node "<skill>/scripts/cek.mjs" isi.json` dan `node "<skill>/scripts/bangun.mjs" isi.json --keluar hasil`.
- `--keluar hasil` menaruh hasilnya di folder `hasil/` di folder kerja itu.
- Contoh dan cetakan ada di `<skill>/contoh/`. Salin `kosong.json` ke folder kerja sebagai `isi.json`.

Perintah di bawah ditulis singkat (`node scripts/...`). Ganti `scripts/` dengan `<skill>/scripts/` bila kamu tidak berada di folder skill.

## Langkah (kerjakan berurutan)

**1. Kumpulkan fakta.** Kalau belum ada, tanyakan ke pengguna dalam satu pesan berisi daftar bernomor:

1. Nama produk dan satu kalimat tujuannya.
2. Masalah yang dipecahkan, dua angka pendukung beserta sumbernya (lembaga dan tahun), dan arti tiap angka dalam kata sehari-hari.
3. Tiga hal yang dilakukan orang sekarang untuk mengatasi masalah itu.
4. Empat fitur utama beserta isinya.
5. Satu contoh pertanyaan pengguna dan jawabannya, lengkap dengan angka.
6. Harga paket (2 sampai 4), urut dari termurah.
7. Batasan produk yang perlu dinyatakan (misalnya "Tidak menjual bibit").

Bila ada yang belum dijawab, tulis apa yang kurang dan berhenti. **Jangan mengisinya dengan karanganmu.**

**2. Isi `isi.json`.** Salin `contoh/kosong.json` menjadi `isi.json`. Ganti setiap teks di antara `[ ... ]` dengan isi sebenarnya. `contoh/tanam_kota.json` adalah contoh yang sudah benar dan lolos pemeriksaan; tirulah bentuknya. Semua angka dan nama di contoh itu fiktif.

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

`pensil`, `kalkulator`, `obrolan`, `buku`, `perisai`, `orang`, `label`, `video`, `tabel`, `grafik`, `dokumen`, `centang`, `dompet`, `koin`, `jam`, `gembok`, `ponsel`, `keranjang`, `lokasi`, `petir`, `bintang`.

Pilih ikon yang artinya paling dekat dengan isiannya. Nama di luar daftar ini ditolak oleh `cek.mjs`.

## Bentuk isian

Lihat `contoh/tanam_kota.json`. Ringkasnya: `kepala` (judul dua baris dan tujuan), `masalah` (kalimat, dua ukuran bergambar cincin, sumber, tiga hal yang dilakukan orang sekarang), `solusi` (empat simpul), `contoh` (satu tanya jawab dengan tiga label), `paket` (2 sampai 4 harga), dan `kaki` (catatan penutup). Jumlah butir di tiap daftar harus persis seperti contoh.

## Kalau ada kendala

- **Tidak ada Chrome atau Edge:** jalankan `node scripts/bangun.mjs isi.json --tanpa-gambar`, lalu buka `hasil/infografis.html` di peramban. Chrome di lokasi lain: setel variabel `CHROME_PATH`.
- **Tidak bisa menjalankan perintah sama sekali:** tulis isi `isi.json` yang lolos aturan di atas, lalu minta pengguna menjalankan dua perintah di langkah 3 dan 4.
- **Merek lain:** salin `merek/tanam_kota.json` menjadi `merek/<nama>.json`, ganti warna, huruf, dan logo, lalu isi `"merek": "<nama>"` di `isi.json`. Logo boleh dikosongkan (`null`); lingkaran logo diisi huruf pertama nama merek.
- **Rasio lain atau lebih dari satu lembar:** di luar skill ini.
