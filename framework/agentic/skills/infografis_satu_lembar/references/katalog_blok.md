# Katalog blok susunan adaptif

Susunan `adaptif` menyusun lembar dari 2 sampai 4 blok. Pilih blok menurut **bentuk informasinya**, bukan menurut selera. Satu jenis blok dipakai paling banyak sekali, dan urutan di dalam `blok` adalah urutan dari atas ke bawah.

Blok pertama menentukan angka sorotan di kepala bila `kepala.sorot` tidak diisi: pita waktu menghasilkan jumlah tahun, langkah menghasilkan jumlah langkah, dan seterusnya. Angka itu dihitung skrip, jadi jangan menulisnya sendiri.

## Memilih blok

| Bentuk informasi | Blok | Contoh isi |
| --- | --- | --- |
| Urutan tahun, dengan masa dan peristiwa | `pita_waktu` | Sejarah sebuah kota |
| Tahapan berurutan yang masing-masing punya ciri | `tahap` | Fase tumbuh, tahap proyek |
| Satu pusat yang mengalir ke beberapa tujuan | `alur` | Ke mana penduduk pergi, ke mana hasil dijual |
| Dua pihak yang dibandingkan pada beberapa hal | `banding` | Kota A dan kota B, pot dan tanah |
| Cara melakukan sesuatu, urut dari awal sampai akhir | `langkah` | Cara menanam, cara mendaftar |
| Dua sampai empat angka persen | `angka` | Hasil survei |

Bila informasinya tidak masuk satu pun bentuk di atas, jangan dipaksakan. Pakai susunan `produk` atau minta pengguna memperjelas isinya.

Tinggi tiap blok menyesuaikan jumlah butirnya dan sisa ruang lembar. Bila isinya melebihi lembar, `cek.mjs` melaporkan `terlalu padat` beserta tinggi tiap blok. Kurangi satu blok atau kurangi butirnya.

## pita_waktu

**Pakai bila** informasinya berjalan dari tahun ke tahun. **Tanyakan:** masa apa saja beserta tahun mulai dan selesainya, dan peristiwa penting di dalamnya.

- 2 sampai 5 masa berurutan. Tahun selesai satu masa sama dengan tahun mulai masa berikutnya.
- 2 sampai 7 peristiwa dengan `tahun`, `teks` (maks 30 huruf), dan `ikon`. Peristiwa yang berulang cukup satu butir dengan `sampai` dan `titik`.
- Lebar tiap masa sebanding dengan lamanya. Skrip menghitung lama tiap masa dan jumlah tahun seluruhnya.
- Peristiwa yang tahunnya terlalu berdekatan tidak muat. `cek.mjs` menyebutnya; gabungkan atau hapus salah satu.

<!-- blok:pita_waktu -->
```json
{
  "jenis": "pita_waktu",
  "masa": [
    { "nama": "Masa Tumbuh", "mulai": 1900, "selesai": 1950 },
    { "nama": "Masa Ramai", "mulai": 1950, "selesai": 2000 }
  ],
  "peristiwa": [
    { "tahun": 1900, "teks": "Desa pertama berdiri", "ikon": "lokasi" },
    { "tahun": 1975, "teks": "Jalan raya dibuka", "ikon": "jalan" }
  ]
}
```

## tahap

**Pakai bila** ada 2 sampai 5 tahapan, masing-masing dengan satu atau dua ciri. **Tanyakan:** nama tiap tahap dan cirinya.

- 2 sampai 3 tahap tampil sebagai kartu yang turun seperti anak tangga. 4 sampai 5 tahap tampil sebagai baris yang menjorok.
- `angka`, `satuan`, dan `rentang` boleh diisi. Bila kosong, yang tampil adalah nomor urut.
- Dengan `"ikuti_pita": true`, jumlah tahap harus sama dengan jumlah masa di blok `pita_waktu`, dan lama, satuan, serta rentang dihitung dari pita. Jangan mengisi `angka`, `satuan`, atau `rentang` pada mode ini.

<!-- blok:tahap -->
```json
{
  "jenis": "tahap",
  "items": [
    { "nama": "Bibit", "ikon": "pohon", "poin": ["Biji disemai di wadah kecil"], "angka": "1", "satuan": "minggu" },
    { "nama": "Tumbuh", "ikon": "surya", "poin": ["Daun mulai muncul"], "angka": "3", "satuan": "minggu" },
    { "nama": "Panen", "ikon": "keranjang", "poin": ["Batang dipotong"], "angka": "1", "satuan": "hari" }
  ]
}
```

## alur

**Pakai bila** satu hal mengalir ke 2 sampai 4 tujuan. **Tanyakan:** apa pusatnya, ke mana alirannya, dan tujuan mana yang paling banyak dituju.

- `pusat` maksimal 9 huruf. Tiap tujuan punya `ikon`, `nama`, `arti`, dan `arah`.
- `utama` adalah nomor tujuan yang paling banyak dituju, dimulai dari 0. Panahnya digambar lebih tebal.

<!-- blok:alur -->
```json
{
  "jenis": "alur",
  "judul": "Ke mana hasil panen pergi",
  "pusat": "Kebun",
  "tujuan": [
    { "ikon": "keranjang", "nama": "Dapur sendiri", "arti": "dimakan keluarga", "arah": "Rumah" },
    { "ikon": "dompet", "nama": "Pasar", "arti": "dijual ke tetangga", "arah": "Luar" }
  ],
  "utama": 0
}
```

## banding

**Pakai bila** dua pihak dibandingkan pada 3 sampai 5 hal. **Tanyakan:** siapa kedua pihaknya, hal apa yang dibandingkan, dan pada hal mana salah satu jelas lebih unggul.

- `topik` maksimal 11 huruf. Isi tiap sisi maksimal 28 huruf.
- `unggul` ("kiri" atau "kanan") diisi hanya bila satu pihak jelas menang. Bila tidak jelas, hapus isiannya.

<!-- blok:banding -->
```json
{
  "jenis": "banding",
  "judul": "Pot atau tanah langsung",
  "kiri": { "nama": "Pot", "ikon": "keranjang" },
  "kanan": { "nama": "Tanah", "ikon": "lokasi" },
  "baris": [
    { "topik": "Tempat", "kiri": "Balkon sempit pun bisa", "kanan": "Butuh halaman" },
    { "topik": "Perawatan", "kiri": "Mudah dipindah", "kanan": "Tetap di tempat", "unggul": "kiri" },
    { "topik": "Hasil", "kiri": "Lebih sedikit", "kanan": "Lebih banyak", "unggul": "kanan" }
  ]
}
```

## langkah

**Pakai bila** pembaca perlu mengikuti 3 sampai 5 langkah. **Tanyakan:** langkah apa saja, urut dari yang pertama.

- `nama` maksimal 12 huruf, satu kata kerja. `rincian` maksimal 30 huruf.
- Langkah dinomori dan digambar di sepanjang jalur berkelok yang berujung panah.

<!-- blok:langkah -->
```json
{
  "jenis": "langkah",
  "judul": "Cara menanam kangkung",
  "langkah": [
    { "ikon": "keranjang", "nama": "Siapkan", "rincian": "pot, tanah, dan biji kangkung" },
    { "ikon": "pensil", "nama": "Semai", "rincian": "tabur biji, tutup tanah tipis" },
    { "ikon": "jam", "nama": "Rawat", "rincian": "siram pagi dan sore" },
    { "ikon": "centang", "nama": "Panen", "rincian": "potong saat setinggi 25 cm" }
  ]
}
```

## angka

**Pakai bila** ada 2 sampai 4 angka persen yang perlu dibaca sekilas. **Tanyakan:** angkanya, artinya dalam kata sehari-hari, dan sumbernya (diisi di `sumber`).

- `nilai` adalah angka 0 sampai 100 tanpa tanda kutip. `tampil` adalah teks yang tampil di tengah cincin dan harus sama dengan `nilai` bila berakhiran %.
- `arti` minimal 3 kata. Jangan mengubah angka menjadi "7 dari 10 orang".

<!-- blok:angka -->
```json
{
  "jenis": "angka",
  "judul": "Contoh angka fiktif",
  "angka": [
    { "nilai": 78, "tampil": "78%", "arti": "ingin menanam sayur sendiri" },
    { "nilai": 41, "tampil": "41%", "arti": "berhasil panen sayurnya" }
  ]
}
```
