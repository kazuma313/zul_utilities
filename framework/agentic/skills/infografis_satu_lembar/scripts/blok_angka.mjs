/**
 * Blok angka: 2 sampai 4 angka persen sebagai cincin, dengan arti tiap angka di bawahnya.
 *
 * Bentuk: { "jenis": "angka", "judul",
 *           "angka": [{ "nilai": 0 sampai 100, "tampil", "arti" }] }
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, muatBaris } from './umum.mjs';

const garis = (n) => (n <= 2 ? 156 : n === 3 ? 140 : 124);

export const blokAngka = {
  jenis: 'angka',

  periksa(b, L, { G, teks }) {
    teks(`${L}.judul`, b.judul, 'angka.judul', { satuan: false });
    const [mn, mx] = J.angka;
    if (!Array.isArray(b.angka) || b.angka.length < mn || b.angka.length > mx) {
      G(`${L}.angka`, `harus berisi ${mn} sampai ${mx} angka, masing-masing { "nilai", "tampil", "arti" }.`);
      return;
    }
    b.angka.forEach((a, i) => {
      const T = `${L}.angka[${i}]`;
      if (typeof a?.nilai !== 'number' || a.nilai < 0 || a.nilai > 100) G(`${T}.nilai`, 'harus angka 0 sampai 100 (tanpa tanda kutip dan tanpa %). Contoh: 69.57');
      teks(`${T}.tampil`, a?.tampil, 'angka.tampil', { satuan: false });
      if (typeof a?.tampil === 'string' && /%$/.test(a.tampil.trim()) && typeof a?.nilai === 'number') {
        const baca = Number(a.tampil.replace('%', '').replace(',', '.'));
        if (Number.isFinite(baca) && Math.abs(baca - a.nilai) > 0.01) G(`${T}.tampil`, `angkanya (${a.tampil}) harus sama dengan nilai (${a.nilai}).`);
      }
      teks(`${T}.arti`, a?.arti, 'angka.arti');
      if (typeof a?.arti === 'string' && a.arti.trim().split(/\s+/).length < 3) G(`${T}.arti`, 'terlalu singkat. Jelaskan artinya dengan minimal 3 kata.');
    });
    if (b.angka.length > 1 && new Set(b.angka.map((a) => a?.arti)).size === 1) G(`${L}.angka`, 'semua angka punya arti yang sama. Bedakan artinya.');
  },

  tinggi(b) {
    const alami = 40 + garis(b.angka.length) + 14 + 56;
    return { alami, maks: alami + 90 };
  },

  gambar(b, k) {
    const { y, h, w, id, P, label, paletKe } = k;
    const n = b.angka.length;
    const palet = paletKe(n);
    const alami = 40 + garis(n) + 14 + 56;
    const D = garis(n) + Math.min(40, Math.max(0, h - alami) * 0.6);
    const lebar = 984 / n;
    const r = (D - 22) / 2;
    const keliling = 2 * Math.PI * r;
    // angka di tengah mengecil bila tidak muat di bagian dalam cincin
    const ukuranTampil = (a) => muatBaris(a.tampil, D - 44, Math.round(D * 0.21), 0.68);
    const cincin = b.angka
      .map((a, i) => {
        const cx = 48 + lebar * (i + 0.5);
        const atas = y + 40;
        return `<div style="position:absolute;left:${(cx - D / 2).toFixed(1)}px;top:${atas.toFixed(1)}px;width:${D.toFixed(1)}px;height:${D.toFixed(1)}px">
<svg width="${D.toFixed(1)}" height="${D.toFixed(1)}" viewBox="0 0 ${D.toFixed(1)} ${D.toFixed(1)}" aria-hidden="true"><circle cx="${D / 2}" cy="${D / 2}" r="${r.toFixed(1)}" fill="none" stroke="${w.lingkar}" stroke-width="18"/><circle cx="${D / 2}" cy="${D / 2}" r="${r.toFixed(1)}" fill="none" stroke="${palet[i]}" stroke-width="18" stroke-linecap="round" stroke-dasharray="${((a.nilai / 100) * keliling).toFixed(1)} ${keliling.toFixed(1)}" transform="rotate(-90 ${D / 2} ${D / 2})"/></svg>
<p data-teks="${id}-${i}-tampil" style="position:absolute;left:0;top:${(D / 2 - ukuranTampil(a) / 2).toFixed(1)}px;width:${D.toFixed(1)}px;margin:0;text-align:center;white-space:nowrap;font-size:${ukuranTampil(a)}px;font-weight:600;line-height:1;letter-spacing:-1px;color:${palet[i]}">${esc(a.tampil)}</p>
</div>
${P(`${id}-${i}-arti`, cx - lebar / 2 + 14, atas + D + 14, lebar - 28, `text-align:center;font-size:22px;line-height:1.2;color:${w.teks2}`, esc(a.arti))}`;
      })
      .join('\n');

    return `${label(`${id}-judul`, 48, y, esc(b.judul.toUpperCase()))}
${cincin}`;
  },
};
