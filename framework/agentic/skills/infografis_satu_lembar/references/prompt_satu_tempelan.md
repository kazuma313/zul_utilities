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

## Setelah AI menjawab

1. Simpan jawabannya sebagai `isi.json`.
2. `node scripts/cek.mjs isi.json`. Kalau ada GAGAL, tempel pesannya ke AI dan minta: "Perbaiki JSON ini sesuai pesan, jawab hanya JSON."
3. `node scripts/bangun.mjs isi.json`. Hasil di folder `hasil/`.
