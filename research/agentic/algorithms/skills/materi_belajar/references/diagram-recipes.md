# Resep diagram SVG

Semua diagram memakai kelas CSS dari `assets/template.html`, jadi otomatis mendukung mode gelap. Jangan menulis warna hex langsung di SVG.

## Aturan dasar

- `viewBox="0 0 360 H"`, konten di x=20..340. Lebar 360 membuat teks tetap terbaca di HP; di desktop SVG dibatasi max-width 440px.
- Tata letak **vertikal** (atas ke bawah). Maksimal 3 kotak sejajar dalam satu baris.
- Tinggi H = elemen paling bawah + 20.
- Teks SVG tidak bisa wrap otomatis. Hitung lebar sebelum menaruh teks:
  - `.tx` (13px bold): ±7,2 px per karakter
  - `.ts` (11,5px): ±6,3 px per karakter
  - Lebar kotak minimal = lebar teks terpanjang + 24.
  - Terlalu panjang? Pendekkan teksnya, jangan kecilkan font.
- Teks di dalam kotak: y = tengah kotak + 5 (baseline).
- Garis tidak boleh menembus kotak lain. Pakai path berbentuk L jika perlu.
- Setiap `<svg>` wajib punya `role="img"` dan `aria-label`.

## Kelas yang tersedia

| Kelas | Fungsi |
|---|---|
| `bx` | Kotak netral |
| `bo` | Kotak aksen (hal yang disorot) |
| `bt` | Kotak teal (sah, jujur, hasil, keuntungan) |
| `br` | Kotak merah (masalah, penipu, risiko) |
| `dash` | Wadah putus-putus (kelompok/jaringan) |
| `tx` | Teks judul kotak |
| `ts` | Teks keterangan |
| `tm` / `to` | Teks monospace biasa / aksen (untuk kode, hash, alamat) |
| `tr` | Teks peringatan merah |
| `ln` | Garis netral |
| `lo` | Garis aksen |
| `lt` | Garis teal |
| `lr` | Garis merah putus-putus |
| `marker-end="url(#ah)"` / `url(#aho)` | Panah netral / aksen |

Warna harus bermakna: aksen = fokus, teal = baik/hasil, merah = buruk/risiko, netral = sisanya. Maksimal dua warna selain netral per diagram.

## 1. Aliran vertikal (langkah, proses)

Kotak 320×40 (satu baris) atau 320×56 (judul + keterangan), jarak 20–26px, panah di tengah.

```svg
<svg viewBox="0 0 360 200" role="img" aria-label="...">
<rect class="bx" x="20" y="20" width="320" height="40" rx="8"/><text class="tx" x="36" y="45">1. Langkah pertama</text>
<line class="ln" x1="180" y1="60" x2="180" y2="76" marker-end="url(#ah)"/>
<rect class="bo" x="20" y="80" width="320" height="40" rx="8"/><text class="tx" x="36" y="105">2. Langkah yang disorot</text>
<line class="ln" x1="180" y1="120" x2="180" y2="136" marker-end="url(#ah)"/>
<rect class="bt" x="20" y="140" width="320" height="40" rx="8"/><text class="tx" x="36" y="165">3. Hasil akhir</text>
</svg>
```

## 2. Aliran model bisnis (untuk modul yang membahas model bisnis)

Kotak 320×56 berisi nama pihak (`tx`) dan apa yang ia lakukan/bayar (`ts`). Pihak = netral, pekerja utama = aksen, hasil/uang yang diterima = teal. Akhiri dengan teks `↻` jika siklusnya berulang.

```svg
<svg viewBox="0 0 360 300" role="img" aria-label="Model bisnis ...">
<rect class="bx" x="20" y="20" width="320" height="56" rx="8"/>
<text class="tx" x="180" y="44" text-anchor="middle">Pengguna</text>
<text class="ts" x="180" y="63" text-anchor="middle">Bayar biaya layanan</text>
<line class="ln" x1="180" y1="76" x2="180" y2="102" marker-end="url(#ah)"/>
<rect class="bo" x="20" y="106" width="320" height="56" rx="8"/>
<text class="tx" x="180" y="130" text-anchor="middle">Penyedia layanan</text>
<text class="ts" x="180" y="149" text-anchor="middle">Keluar biaya server dan tim</text>
<line class="ln" x1="180" y1="162" x2="180" y2="188" marker-end="url(#ah)"/>
<rect class="bt" x="20" y="192" width="320" height="56" rx="8"/>
<text class="tx" x="180" y="216" text-anchor="middle">Pendapatan</text>
<text class="ts" x="180" y="235" text-anchor="middle">Fee, langganan, komisi</text>
<text class="ts" x="180" y="280" text-anchor="middle">↻ Siklus berulang</text>
</svg>
```

Selalu dampingi dengan tabel `Pihak | Memberi | Mendapat`.

## 3. Perbandingan dua cara (lama vs baru)

Dua baris, masing-masing diberi judul `tx` di kiri atas. Baris lama netral, baris baru aksen.

```svg
<svg viewBox="0 0 360 200" role="img" aria-label="...">
<text class="tx" x="20" y="24">Cara lama</text>
<rect class="bx" x="20" y="36" width="90" height="44" rx="8"/><text class="tx" x="65" y="62" text-anchor="middle">A</text>
<rect class="bx" x="135" y="36" width="90" height="44" rx="8"/><text class="tx" x="180" y="62" text-anchor="middle">Perantara</text>
<rect class="bx" x="250" y="36" width="90" height="44" rx="8"/><text class="tx" x="295" y="62" text-anchor="middle">B</text>
<line class="ln" x1="110" y1="58" x2="131" y2="58" marker-end="url(#ah)"/>
<line class="ln" x1="225" y1="58" x2="246" y2="58" marker-end="url(#ah)"/>
<text class="tx" x="20" y="122">Cara baru</text>
<rect class="bo" x="20" y="134" width="90" height="44" rx="8"/><text class="tx" x="65" y="160" text-anchor="middle">A</text>
<rect class="bo" x="250" y="134" width="90" height="44" rx="8"/><text class="tx" x="295" y="160" text-anchor="middle">B</text>
<line class="lo" x1="110" y1="156" x2="244" y2="156" marker-end="url(#aho)"/>
</svg>
```

## 4. Kartu berisi baris data (block, akun, produk)

Kotak 320×92 dengan 4 baris teks (judul + 3 baris `ts`), y = atas + 22, 44, 62, 80. Hubungkan kartu dengan panah aksen dan warnai nilai yang tersambung dengan `to`.

```svg
<rect class="bx" x="20" y="20" width="320" height="92" rx="8"/>
<text class="tx" x="36" y="42">Block 1</text>
<text class="ts" x="36" y="64">Prev hash: <tspan class="tm">000000…</tspan></text>
<text class="ts" x="36" y="82">Nonce: 2083</text>
<text class="ts" x="36" y="100">Hash: <tspan class="to">0000a91f…</tspan></text>
<line class="lo" x1="180" y1="112" x2="180" y2="136" marker-end="url(#aho)"/>
```

## 5. Rantai pendek dan percabangan

Kotak kecil 36×30, jarak 10, disambung garis pendek. Cabang turun dengan path L.

```svg
<rect class="bt" x="20" y="44" width="36" height="30" rx="4"/><text class="tx" x="38" y="64" text-anchor="middle">1</text>
<line class="lt" x1="56" y1="59" x2="66" y2="59"/>
<rect class="bt" x="66" y="44" width="36" height="30" rx="4"/><text class="tx" x="84" y="64" text-anchor="middle">2</text>
<path class="lr" d="M84 74 L84 129 L110 129"/>
<rect class="br" x="112" y="114" width="36" height="30" rx="4"/><text class="tx" x="130" y="134" text-anchor="middle">2'</text>
```

## 6. Satu dipecah menjadi beberapa (input → output, pembagian dana)

Kotak sumber penuh di atas, kotak proses, lalu 3 kotak 100×56 di x=20, 130, 240 dengan panah diagonal dari tepi bawah kotak proses.

```svg
<rect class="bx" x="20" y="100" width="320" height="40" rx="8"/><text class="tx" x="180" y="125" text-anchor="middle">Transaksi</text>
<line class="ln" x1="150" y1="140" x2="74" y2="186" marker-end="url(#ah)"/>
<line class="ln" x1="180" y1="140" x2="180" y2="186" marker-end="url(#ah)"/>
<line class="ln" x1="210" y1="140" x2="286" y2="186" marker-end="url(#ah)"/>
<rect class="bt" x="20" y="190" width="100" height="56" rx="8"/>
<rect class="bt" x="130" y="190" width="100" height="56" rx="8"/>
<rect class="bt" x="240" y="190" width="100" height="56" rx="8"/>
```

## 7. Pohon (hierarki, ringkasan bertingkat)

Daun: 4 kotak 62 lebar di x=20, 106, 192, 278 (tengah 51, 137, 223, 309). Tingkat atas: 2 kotak 110 lebar di x=40 dan 210. Puncak: 140 lebar di x=110. Pakai garis `ln` tanpa panah.

## 8. Data angka

Untuk angka dari sumber, jangan gambar grafik SVG manual. Pakai komponen `.bars` (isi array `BARS` di script template) atau tabel HTML biasa.
