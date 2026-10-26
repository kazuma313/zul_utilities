/**
 * Bagian yang dipakai bersama oleh semua susunan: pemeriksa teks, ikon, dan skrip
 * pemeriksa tata letak. Susunan sendiri ada di bangun.mjs (produk) dan linimasa.mjs.
 */
import fs from 'node:fs';
import path from 'node:path';
import { IKON, KATA_KABUR, AMBIGU } from './skema.mjs';

export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function dataUri(berkas) {
  const ext = path.extname(berkas).slice(1).toLowerCase();
  const tipe = ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' ? 'image/jpeg' : `image/${ext || 'png'}`;
  return `data:${tipe};base64,${fs.readFileSync(berkas).toString('base64')}`;
}

export const ikon = (nama, ukuran, warna, tebal = 1.8) =>
  `<svg width="${ukuran}" height="${ukuran}" viewBox="0 0 24 24" fill="none" stroke="${warna}" stroke-width="${tebal}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${IKON[nama]}</svg>`;

/** Awalan hex warna + transparansi: "#e9a23b" dan 0.15 menjadi "#e9a23b26". */
export const alfa = (hex, bagian) => `${hex}${Math.round(Math.max(0, Math.min(1, bagian)) * 255).toString(16).padStart(2, '0')}`;

/**
 * Pembuat pemeriksa isian teks: wajib ada, tidak melebihi batas, tidak kabur, tidak ambigu.
 * `G` dan `P` mencatat GAGAL dan PERINGATAN, `semuaTeks` menampung teks untuk dihitung katanya.
 */
export function buatTeks(G, P, semuaTeks, BATAS) {
  return (lokasi, nilai, kunciBatas, { satuan = true, sorot = false } = {}) => {
    if (typeof nilai !== 'string' || !nilai.trim()) {
      G(lokasi, 'isian ini kosong atau bukan teks. Tulis kalimat pendek di antara tanda kutip.');
      return;
    }
    const polos = nilai.replace(/\*/g, '');
    semuaTeks.push(polos);
    const batas = BATAS[kunciBatas];
    if (batas && polos.length > batas) {
      G(lokasi, `terlalu panjang (${polos.length} huruf, maksimal ${batas}). Perpendek, buang kata yang tidak perlu. Teks sekarang: "${polos}"`);
    }
    if (/\p{Extended_Pictographic}/u.test(nilai)) G(lokasi, 'jangan pakai emoji. Pakai kata biasa, gambarnya sudah disediakan oleh ikon.');
    if (!sorot && nilai.includes('*')) G(lokasi, 'tanda * hanya boleh dipakai di contoh.jawab_utama untuk menyorot angka. Hapus tanda *.');
    for (const k of KATA_KABUR) {
      if (new RegExp(`(^|\\W)${k.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')}(\\W|$)`, 'i').test(polos)) {
        G(lokasi, `kata "${k}" tidak jelas. Ganti dengan fakta yang bisa diperiksa (angka, nama, atau contoh).`);
      }
    }
    for (const a of AMBIGU) if (a.re.test(polos)) G(lokasi, a.pesan);
    if (satuan && /\d[\d.,–-]*\s*[.!?]?\s*$/.test(polos)) {
      P(lokasi, 'kalimat berakhir pada angka tanpa satuan. Tambahkan satuannya (juta, ribu, %, kali, bulan, orang).');
    }
  };
}

/**
 * Skrip yang dijalankan di dalam peramban setelah huruf selesai dimuat: mencari teks yang
 * bertumpuk atau keluar lembar. Hasilnya ditaruh di <pre id="qa"> untuk dibaca bangun.mjs.
 * Setiap elemen yang ingin diperiksa diberi atribut data-teks.
 */
export const SKRIP_QA = `<script>
window.addEventListener('load', async () => {
  await document.fonts.ready;
  const hasil = [];
  const kotak = [...document.querySelectorAll('[data-teks]')].map((el) => {
    const r = document.createRange(); r.selectNodeContents(el); const b = r.getBoundingClientRect();
    return { n: el.dataset.teks, x0: b.left, y0: b.top, x1: b.right, y1: b.bottom };
  }).filter((k) => k.x1 > k.x0 && k.y1 > k.y0);
  for (let i = 0; i < kotak.length; i++) {
    const a = kotak[i];
    if (a.x0 < 8 || a.y0 < 8 || a.x1 > 1072 || a.y1 > 1348) hasil.push(a.n + ' keluar dari batas lembar');
    for (let j = i + 1; j < kotak.length; j++) {
      const b = kotak[j];
      if (a.x0 < b.x1 - 2 && b.x0 < a.x1 - 2 && a.y0 < b.y1 - 5 && b.y0 < a.y1 - 5) hasil.push(a.n + ' bertumpuk dengan ' + b.n);
    }
  }
  const pre = document.createElement('pre'); pre.id = 'qa'; pre.style.display = 'none'; pre.textContent = JSON.stringify(hasil); document.body.appendChild(pre);
});
</script>`;

// ── warna yang menyesuaikan jumlah butir

const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const hexDari = (v) => `#${v.map((n) => Math.round(Math.max(0, Math.min(255, n))).toString(16).padStart(2, '0')).join('')}`;

/** Campuran dua warna hex: t = 0 menghasilkan a, t = 1 menghasilkan b. */
export const campur = (a, b, t) => {
  const [x, y] = [rgb(a), rgb(b)];
  return hexDari(x.map((n, i) => n + (y[i] - n) * t));
};

/** n warna yang berjalan dari fase1 lewat fase2 ke fase3 pada merek (atau aksen, koin3, biru1). */
export function paletKe(w, n) {
  const awal = w.fase1 ?? w.aksen;
  const tengah = w.fase2 ?? w.koin3;
  const akhir = w.fase3 ?? w.biru1;
  if (n <= 1) return [awal];
  return Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1);
    return t <= 0.5 ? campur(awal, tengah, t * 2) : campur(tengah, akhir, (t - 0.5) * 2);
  });
}

/** Warna teks yang terbaca di atas warna latar hex: gelap untuk latar terang, terang untuk latar gelap. */
export function kontras(hex, w) {
  const [r, g, b] = rgb(hex).map((n) => n / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.55 ? w.aksen_teks : w.teks;
}

/** Pembuat paragraf berposisi mutlak dan label bagian, dengan id untuk pemeriksa tumpang tindih. */
export const pembuatP = (w) => {
  const P = (id, kiri, atas, lebar, gaya, isi) =>
    `<p data-teks="${id}" style="position:absolute;left:${kiri}px;top:${atas}px;${lebar ? `width:${lebar}px;` : ''}margin:0;${gaya}">${isi}</p>`;
  const label = (id, kiri, atas, isi) => P(id, kiri, atas, 0, `font-size:20px;font-weight:600;letter-spacing:3px;color:${w.aksen}`, isi);
  return { P, label };
};
