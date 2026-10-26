# Prompt satu tempelan (untuk AI tanpa fitur skill)

Pakai ini di AI yang tidak mengenal folder skill, termasuk model kecil. Tempel **bagian A**, lalu tempel isi `contoh/kosong.json` di bawahnya, lalu tulis fakta produk Anda. AI cukup menjawab dengan JSON. Anda menjalankan `node scripts/cek.mjs isi.json` dan `node scripts/bangun.mjs isi.json` sendiri.

## Bagian A (tempel ini)

```
Tugasmu: mengisi sebuah berkas JSON untuk infografis satu lembar. Kamu tidak menggambar.

Aturan:
1. Jawab HANYA dengan JSON yang valid. Tanpa penjelasan, tanpa tanda ```.
2. Tiru bentuk JSON di bawah persis: nama kunci sama, jumlah butir sama.
3. Ganti setiap teks di antara [ ] dengan isi dari fakta yang kuberikan. Jangan mengarang angka. Kalau faktanya tidak ada, tulis "KURANG: <apa yang kurang>" di tempat itu.
4. Kalimat pendek, paling banyak 10 kata. Satu ide per isian. Perhatikan batas huruf di dalam [ ].
5. Setiap angka harus punya satuan (juta, ribu, %, kali, bulan, orang).
6. Arti angka ditulis dengan kata sehari-hari. Salah: "paham". Benar: "tahu dan terampil merawatnya".
7. Jangan pakai kata: terbaik, terlengkap, canggih, inovatif, dll, dan lain-lain.
8. Jangan tulis "tanpa jual produk". Tulis produk apa yang tidak dijual, misalnya "Tidak menjual bibit".
9. Tanpa emoji. Tanda * hanya untuk menyorot angka di contoh.jawab_utama, tepat sepasang.
10. Nama ikon hanya dari daftar ini: pensil, kalkulator, obrolan, buku, perisai, orang, label, video, tabel, grafik, dokumen, centang, dompet, koin, jam, gembok, ponsel, keranjang, lokasi, petir, bintang.
11. Angka "nilai" di masalah.ukuran adalah angka 0 sampai 100 tanpa tanda kutip, dan harus sama dengan "tampil".
```

## Bagian B (tempel di bawah Bagian A)

Isi file `contoh/kosong.json`, lalu tulis: `Fakta produk saya: ...`

## Susunan linimasa

Untuk satu periode sejarah atau proses yang terbagi tiga masa, pakai Bagian A-linimasa di bawah dan tempel isi `contoh/kosong_linimasa.json` sebagai Bagian B.

```
Tugasmu: mengisi sebuah berkas JSON untuk infografis linimasa. Kamu tidak menggambar.

Aturan:
1. Jawab HANYA dengan JSON yang valid. Tanpa penjelasan, tanpa tanda ```.
2. Tiru bentuk JSON di bawah persis: nama kunci sama, jumlah butir sama (3 masa, 3 sampai 7 peristiwa, 3 tujuan).
3. Ganti setiap teks di antara [ ] dengan isi dari fakta yang kuberikan. Jangan mengarang tahun atau nama. Kalau faktanya tidak ada, tulis "KURANG: <apa yang kurang>".
4. Semua tahun adalah angka tanpa tanda kutip. Tahun selesai satu masa sama dengan tahun mulai masa berikutnya. Jangan menulis lama masa atau jumlah tahun: skrip menghitungnya.
5. Setiap peristiwa punya tahun di dalam seluruh periode. Peristiwa berulang (misalnya beberapa letusan) cukup satu butir: tahun awal, "sampai" tahun akhir, dan "titik" berisi tahun-tahunnya.
6. Teks pendek: perhatikan batas huruf di dalam [ ]. Tanpa emoji. Jangan pakai kata: terbaik, terlengkap, canggih, inovatif, dll, dan lain-lain.
7. "ikon" hanya dari daftar: pensil, kalkulator, obrolan, buku, perisai, orang, label, video, tabel, grafik, dokumen, centang, dompet, koin, jam, gembok, ponsel, keranjang, lokasi, petir, bintang, api, gunung, mahkota, jalan, pohon, candi, panah, pedang, surya.
8. "sebaran.utama" adalah nomor tujuan yang paling banyak dituju: 0, 1, atau 2.
9. "sumber" wajib: penulis dan tahun, atau lembaga.
```

## Susunan adaptif

Untuk informasi selain produk, pakai Bagian A-adaptif di bawah. Tempel isi `contoh/kosong_adaptif.json` dan, bila perlu, potongan blok dari `references/katalog_blok.md` sebagai Bagian B.

```
Tugasmu: mengisi sebuah berkas JSON untuk infografis satu lembar yang disusun dari blok. Kamu tidak menggambar.

Aturan:
1. Jawab HANYA dengan JSON yang valid. Tanpa penjelasan, tanpa tanda ```.
2. Pilih 2 sampai 4 blok menurut bentuk informasinya, satu jenis paling banyak sekali:
   - pita_waktu: urutan tahun dengan masa dan peristiwa
   - tahap: tahapan berurutan yang masing-masing punya ciri
   - alur: satu pusat mengalir ke 2 sampai 4 tujuan
   - banding: dua pihak dibandingkan pada 3 sampai 5 hal
   - langkah: 3 sampai 5 langkah urut
   - angka: 2 sampai 4 angka persen
   Taruh blok yang paling penting di paling atas. Bagian informasi yang tidak cocok dengan blok mana pun jangan dipaksakan: tulis "KURANG: <bagian itu>".
3. Tiru bentuk blok persis seperti di katalog: nama kunci sama, jumlah butir sama.
4. Jangan mengarang angka, tahun, atau nama. Kalau faktanya tidak ada, tulis "KURANG: <apa yang kurang>".
5. Semua tahun dan angka "nilai" adalah angka tanpa tanda kutip. Tahun selesai satu masa sama dengan tahun mulai masa berikutnya. Jangan menulis lama masa atau jumlah tahun: skrip menghitungnya.
6. Teks pendek: perhatikan batas huruf di dalam [ ]. Tanpa emoji. Jangan pakai kata: terbaik, terlengkap, canggih, inovatif, dll, dan lain-lain.
7. "ikon" hanya dari daftar: pensil, kalkulator, obrolan, buku, perisai, orang, label, video, tabel, grafik, dokumen, centang, dompet, koin, jam, gembok, ponsel, keranjang, lokasi, petir, bintang, api, gunung, mahkota, jalan, pohon, candi, panah, pedang, surya.
8. Bila isinya terlalu padat, pemeriksa akan melapor. Kurangi satu blok atau kurangi butirnya.
9. "sumber" wajib: penulis dan tahun, atau lembaga.
```

## Setelah AI menjawab

1. Simpan jawabannya sebagai `isi.json`.
2. `node scripts/cek.mjs isi.json`. Kalau ada GAGAL, tempel pesannya ke AI dan minta: "Perbaiki JSON ini sesuai pesan, jawab hanya JSON."
3. `node scripts/bangun.mjs isi.json`. Hasil di folder `hasil/`.
