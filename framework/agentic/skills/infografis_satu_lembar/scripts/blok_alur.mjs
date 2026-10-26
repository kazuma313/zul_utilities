/**
 * Blok alur: diagram dari satu pusat ke 2 sampai 4 tujuan, untuk sebaran, akibat, atau
 * hasil. Tujuan yang paling banyak dituju diberi panah tebal.
 *
 * Bentuk: { "jenis": "alur", "judul", "pusat",
 *           "tujuan": [{ "ikon", "nama", "arti", "arah" }], "utama"?: nomor tujuan }
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, ikon, alfa } from './umum.mjs';

const ALAMI = 221;

export const blokAlur = {
  jenis: 'alur',

  periksa(b, L, { G, teks, cekIkon }) {
    teks(`${L}.judul`, b.judul, 'alur.judul', { satuan: false });
    teks(`${L}.pusat`, b.pusat, 'alur.pusat', { satuan: false });
    const [mn, mx] = J.alur;
    if (!Array.isArray(b.tujuan) || b.tujuan.length < mn || b.tujuan.length > mx) {
      G(`${L}.tujuan`, `harus berisi ${mn} sampai ${mx} tujuan, masing-masing { "ikon", "nama", "arti", "arah" }.`);
      return;
    }
    b.tujuan.forEach((t, i) => {
      const T = `${L}.tujuan[${i}]`;
      cekIkon(`${T}.ikon`, t?.ikon);
      teks(`${T}.nama`, t?.nama, 'alur.nama', { satuan: false });
      teks(`${T}.arti`, t?.arti, 'alur.arti', { satuan: false });
      teks(`${T}.arah`, t?.arah, 'alur.arah', { satuan: false });
    });
    if (b.utama !== undefined && !(Number.isInteger(b.utama) && b.utama >= 0 && b.utama < b.tujuan.length)) {
      G(`${L}.utama`, `harus nomor tujuan yang paling banyak dituju, dimulai dari 0 (0 sampai ${b.tujuan.length - 1}), atau hapus isian ini.`);
    }
  },

  tinggi: () => ({ alami: ALAMI, maks: 330 }),

  gambar(b, k) {
    const { y, h, w, id, P, label } = k;
    const n = b.tujuan.length;
    const PUSAT_X = 170;
    const CHIP_KIRI = 430;
    const kk = Math.min(1.15, Math.max(1, h / ALAMI));
    const tinggiChip = 50 * kk;
    const areaAtas = y + 51;
    const areaTinggi = h - 64;
    const pitch = n > 1 ? Math.min(66 * kk, (areaTinggi - tinggiChip) / (n - 1)) : 0;
    const total = tinggiChip + pitch * (n - 1);
    const mulai = areaAtas + (areaTinggi - total) / 2;
    const atasChip = b.tujuan.map((_, i) => mulai + i * pitch);
    const pusatY = areaAtas + areaTinggi / 2;

    const panah = b.tujuan
      .map((_, i) => {
        const tengah = atasChip[i] + tinggiChip / 2 - y;
        const utama = b.utama === i;
        return `<path d="M ${PUSAT_X + 56} ${(pusatY - y).toFixed(1)} C ${PUSAT_X + 150} ${(pusatY - y).toFixed(1)}, ${CHIP_KIRI - 90} ${tengah.toFixed(1)}, ${CHIP_KIRI - 6} ${tengah.toFixed(1)}" fill="none" stroke="${utama ? w.aksen : alfa(w.aksen, 0.6)}" stroke-width="${utama ? 8 : 3}" stroke-linecap="round" marker-end="url(#${id}-k${utama ? 'U' : 'B'})"/>`;
      })
      .join('\n');
    const chip = b.tujuan
      .map((t, i) => {
        const utama = b.utama === i;
        return `<div style="position:absolute;left:${CHIP_KIRI}px;top:${atasChip[i].toFixed(1)}px;width:602px;height:${tinggiChip.toFixed(1)}px;box-sizing:border-box;border-radius:${(tinggiChip / 2).toFixed(1)}px;background:${w.kartu};${utama ? `border:2px solid ${w.aksen};` : ''}display:flex;flex-direction:row;align-items:center;gap:12px;padding:0 10px 0 8px">
<div style="width:${Math.round(34 * kk)}px;height:${Math.round(34 * kk)}px;border-radius:${Math.round(17 * kk)}px;background:${w.latar};display:flex;align-items:center;justify-content:center;flex-shrink:0">${ikon(t.ikon, Math.round(20 * kk), w.aksen, 2)}</div>
<div style="flex:1;min-width:0"><p data-teks="${id}-${i}-nama" style="margin:0;font-size:${Math.round(22 * kk)}px;font-weight:600;line-height:1.1;color:${w.teks}">${esc(t.nama)}</p><p data-teks="${id}-${i}-arti" style="margin:0;font-size:${Math.round(18 * kk)}px;line-height:1.1;color:${w.teks2}">${esc(t.arti)}</p></div>
<p data-teks="${id}-${i}-arah" style="margin:0;padding:4px 12px;border:1.5px solid ${alfa(w.aksen, 0.55)};border-radius:999px;font-size:16px;letter-spacing:1.5px;text-transform:uppercase;line-height:1.1;color:${w.aksen};flex-shrink:0">${esc(t.arah)}</p>
</div>`;
      })
      .join('\n');

    return `<div style="position:absolute;left:28px;top:${y}px;width:1024px;height:${h}px;border-radius:44px;background:${w.latar2}"></div>
${label(`${id}-judul`, 56, y + 17, esc(b.judul.toUpperCase()))}
<svg width="1080" height="${h}" viewBox="0 0 1080 ${h}" style="position:absolute;left:0;top:${y}px" aria-hidden="true">
<defs>
<marker id="${id}-kU" markerUnits="userSpaceOnUse" markerWidth="22" markerHeight="22" refX="17" refY="11" orient="auto"><path d="M0 0L22 11L0 22z" fill="${w.aksen}"/></marker>
<marker id="${id}-kB" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto"><path d="M0 0L14 7L0 14z" fill="${alfa(w.aksen, 0.6)}"/></marker>
</defs>
<circle cx="${PUSAT_X}" cy="${(pusatY - y).toFixed(1)}" r="68" fill="none" stroke="${w.aksen}" stroke-opacity="0.4" stroke-width="2" stroke-dasharray="6 6"/>
${panah}
</svg>
<div style="position:absolute;left:${PUSAT_X - 52}px;top:${(pusatY - 52).toFixed(1)}px;width:104px;height:104px;border-radius:52px;background:${w.pusat}"></div>
${P(`${id}-pusat`, PUSAT_X - 52, pusatY - 12, 104, `text-align:center;font-size:20px;font-weight:600;line-height:1.2;color:${w.teks}`, esc(b.pusat))}
<div style="position:absolute;left:${PUSAT_X - 12}px;top:${(pusatY - 46).toFixed(1)}px">${ikon('candi', 24, w.aksen, 2)}</div>
${chip}`;
  },
};
