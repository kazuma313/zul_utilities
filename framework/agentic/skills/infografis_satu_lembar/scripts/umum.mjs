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
