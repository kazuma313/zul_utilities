/**
 * Blok langkah: 3 sampai 5 langkah bernomor di sepanjang jalur berkelok yang berujung panah.
 *
 * Bentuk: { "jenis": "langkah", "judul", "langkah": [{ "ikon", "nama", "rincian" }] }
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, ikon, alfa, kontras } from './umum.mjs';

const ALAMI = 250;

export const blokLangkah = {
  jenis: 'langkah',

  periksa(b, L, { G, teks, cekIkon }) {
    teks(`${L}.judul`, b.judul, 'langkah.judul', { satuan: false });
    const [mn, mx] = J.langkah;
    if (!Array.isArray(b.langkah) || b.langkah.length < mn || b.langkah.length > mx) {
      G(`${L}.langkah`, `harus berisi ${mn} sampai ${mx} langkah, masing-masing { "ikon", "nama", "rincian" }.`);
      return;
    }
    b.langkah.forEach((s, i) => {
      const T = `${L}.langkah[${i}]`;
      cekIkon(`${T}.ikon`, s?.ikon);
      teks(`${T}.nama`, s?.nama, 'langkah.nama', { satuan: false });
      teks(`${T}.rincian`, s?.rincian, 'langkah.rincian', { satuan: false });
    });
  },

  tinggi: () => ({ alami: ALAMI, maks: 370 }),

  gambar(b, k) {
    const { y, h, w, id, P, label, paletKe } = k;
    const n = b.langkah.length;
    const palet = paletKe(n);
    const e = Math.max(0, h - ALAMI);
    const lebar = 984 / n;
    const kk = 1 + Math.min(0.25, e / 340);
    const goyang = 22 + e * 0.12;
    const dasarRel = 100 + e * 0.3; // tinggi simpul genap dari atas blok
    const titik = b.langkah.map((_, i) => ({ x: 48 + lebar * (i + 0.5), y: dasarRel - (i % 2 === 1 ? goyang : 0) }));

    // jalur halus dari tepi kiri, lewat semua simpul, sampai tepi kanan (koordinat relatif terhadap blok)
    const f = (v) => v.toFixed(1);
    let jalur = `M 48 ${f(titik[0].y)} L ${f(titik[0].x - 40)} ${f(titik[0].y)}`;
    for (let i = 0; i < n; i++) {
      const dari = i === 0 ? { x: titik[0].x - 40, y: titik[0].y } : titik[i - 1];
      const ke = titik[i];
      const tengah = (dari.x + ke.x) / 2;
      jalur += ` C ${f(tengah)} ${f(dari.y)}, ${f(tengah)} ${f(ke.y)}, ${f(ke.x)} ${f(ke.y)}`;
    }
    jalur += ` L 1030 ${f(titik[n - 1].y)}`;

    const simpul = b.langkah
      .map((s, i) => {
        const { x } = titik[i];
        const cy = y + titik[i].y;
        const warna = palet[i];
        return `<div style="position:absolute;left:${f(x - 34 * kk)}px;top:${f(cy - 34 * kk)}px;width:${f(68 * kk)}px;height:${f(68 * kk)}px;box-sizing:border-box;border-radius:${f(34 * kk)}px;border:4px solid ${warna};background:${w.latar};display:flex;align-items:center;justify-content:center">${ikon(s.ikon, Math.round(30 * kk), warna, 2)}</div>
<div style="position:absolute;left:${f(x - 34 * kk)}px;top:${f(cy - 42 * kk)}px;width:28px;height:28px;border-radius:14px;background:${warna};display:flex;align-items:center;justify-content:center"><p data-teks="${id}-${i}-nomor" style="margin:0;font-size:16px;font-weight:700;line-height:1;color:${kontras(warna, w)}">${i + 1}</p></div>
${P(`${id}-${i}-nama`, x - lebar / 2 + 12, cy + 46 * kk, lebar - 24, `text-align:center;font-size:${Math.round(24 * kk)}px;font-weight:600;line-height:1.1;color:${w.teks}`, esc(s.nama))}
${P(`${id}-${i}-rincian`, x - lebar / 2 + 12, cy + 80 * kk, lebar - 24, `text-align:center;font-size:${Math.round(19 * kk)}px;line-height:1.18;color:${w.teks2}`, esc(s.rincian))}`;
      })
      .join('\n');

    return `${label(`${id}-judul`, 48, y, esc(b.judul.toUpperCase()))}
<svg width="1080" height="${h}" viewBox="0 0 1080 ${h}" style="position:absolute;left:0;top:${y}px" aria-hidden="true">
<defs><marker id="${id}-kepala" markerUnits="userSpaceOnUse" markerWidth="16" markerHeight="16" refX="12" refY="8" orient="auto"><path d="M0 0L16 8L0 16z" fill="${alfa(w.teks, 0.55)}"/></marker></defs>
<path d="${jalur}" fill="none" stroke="${alfa(w.teks, 0.4)}" stroke-width="3" stroke-dasharray="3 9" stroke-linecap="round" marker-end="url(#${id}-kepala)"/>
</svg>
${simpul}`;
  },
};
