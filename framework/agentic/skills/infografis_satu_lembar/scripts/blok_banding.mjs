/**
 * Blok banding: dua pihak berhadapan, dengan 3 sampai 5 baris pembanding di sepanjang
 * satu garis tengah. Baris yang jelas dimenangkan salah satu pihak boleh ditandai.
 *
 * Bentuk: { "jenis": "banding", "judul",
 *           "kiri": { "nama", "ikon" }, "kanan": { "nama", "ikon" },
 *           "baris": [{ "topik", "kiri", "kanan", "unggul"?: "kiri" atau "kanan" }] }
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, ikon, alfa, kontras } from './umum.mjs';

const dasar = 100;
const tinggiBaris = 58;

export const blokBanding = {
  jenis: 'banding',

  periksa(b, L, { G, teks, cekIkon, objek }) {
    teks(`${L}.judul`, b.judul, 'banding.judul', { satuan: false });
    for (const sisi of ['kiri', 'kanan']) {
      if (objek(b[sisi], `${L}.${sisi}`)) {
        teks(`${L}.${sisi}.nama`, b[sisi].nama, 'banding.nama', { satuan: false });
        cekIkon(`${L}.${sisi}.ikon`, b[sisi].ikon);
      }
    }
    const [mn, mx] = J.baris;
    if (!Array.isArray(b.baris) || b.baris.length < mn || b.baris.length > mx) {
      G(`${L}.baris`, `harus berisi ${mn} sampai ${mx} baris pembanding, masing-masing { "topik", "kiri", "kanan" }.`);
      return;
    }
    b.baris.forEach((r, i) => {
      const T = `${L}.baris[${i}]`;
      teks(`${T}.topik`, r?.topik, 'banding.topik', { satuan: false });
      teks(`${T}.kiri`, r?.kiri, 'banding.sisi', { satuan: false });
      teks(`${T}.kanan`, r?.kanan, 'banding.sisi', { satuan: false });
      if (r?.unggul !== undefined && r.unggul !== 'kiri' && r.unggul !== 'kanan') G(`${T}.unggul`, 'harus "kiri" atau "kanan", atau hapus isian ini bila tidak ada yang unggul.');
    });
  },

  tinggi(b) {
    const alami = dasar + b.baris.length * tinggiBaris + 8;
    return { alami, maks: alami + 120 };
  },

  gambar(b, k) {
    const { y, h, w, id, P, label, paletKe } = k;
    const n = b.baris.length;
    const [warnaKiri, warnaKanan] = paletKe(2);
    const pitch = (h - dasar - 8) / n;
    const kepala = (sisi, warna, kiri) => `<div style="position:absolute;left:${kiri}px;top:${y + 34}px;width:440px;height:52px;box-sizing:border-box;border-radius:26px;border:2px solid ${warna};background:${alfa(warna, 0.2)};display:flex;flex-direction:row;align-items:center;justify-content:center;gap:12px">${ikon(b[sisi].ikon, 28, warna, 1.9)}<p data-teks="${id}-${sisi}-nama" style="margin:0;font-size:25px;font-weight:700;line-height:1.1;color:${w.teks}">${esc(b[sisi].nama)}</p></div>`;
    const baris = b.baris
      .map((r, i) => {
        const atas = y + dasar + i * pitch;
        const tinggi = pitch - 8;
        const menang = r.unggul;
        const teksSisi = (sisi, kiri, rata) => {
          const unggul = menang === sisi;
          const warna = sisi === 'kiri' ? warnaKiri : warnaKanan;
          return `<div style="position:absolute;left:${kiri}px;top:${(atas + (tinggi - 26) / 2).toFixed(1)}px;width:408px;height:26px;display:flex;flex-direction:row;align-items:center;justify-content:${rata === 'kanan' ? 'flex-end' : 'flex-start'};gap:10px">${rata === 'kiri' && unggul ? ikon('centang', 22, warna, 2.4) : ''}<p data-teks="${id}-${i}-${sisi}" style="margin:0;font-size:22px;line-height:1.1;font-weight:${unggul ? 700 : 400};color:${unggul ? w.teks : w.teks2}">${esc(r[sisi])}</p>${rata === 'kanan' && unggul ? ikon('centang', 22, warna, 2.4) : ''}</div>`;
        };
        return `<div style="position:absolute;left:48px;top:${atas.toFixed(1)}px;width:984px;height:${tinggi.toFixed(1)}px;border-radius:20px;background:${i % 2 === 0 ? alfa(w.teks, 0.045) : 'transparent'}"></div>
${menang ? `<div style="position:absolute;left:${menang === 'kiri' ? 48 : 540}px;top:${atas.toFixed(1)}px;width:492px;height:${tinggi.toFixed(1)}px;border-radius:${menang === 'kiri' ? '20px 0 0 20px' : '0 20px 20px 0'};background:linear-gradient(${menang === 'kiri' ? 90 : 270}deg,${alfa(menang === 'kiri' ? warnaKiri : warnaKanan, 0.22)},transparent 80%)"></div>` : ''}
${teksSisi('kiri', 48, 'kanan')}
${teksSisi('kanan', 624, 'kiri')}
<div style="position:absolute;left:465px;top:${(atas + (tinggi - 30) / 2).toFixed(1)}px;width:150px;height:30px;box-sizing:border-box;border-radius:15px;border:1.5px solid ${alfa(w.aksen, 0.55)};background:${w.latar};display:flex;align-items:center;justify-content:center"><p data-teks="${id}-${i}-topik" style="margin:0;font-size:14px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;line-height:1;color:${w.aksen}">${esc(r.topik)}</p></div>`;
      })
      .join('\n');

    return `${label(`${id}-judul`, 48, y, esc(b.judul.toUpperCase()))}
${kepala('kiri', warnaKiri, 48)}
${kepala('kanan', warnaKanan, 592)}
<div style="position:absolute;left:518px;top:${y + 38}px;width:44px;height:44px;box-sizing:border-box;border-radius:22px;background:${w.latar2};border:2px solid ${alfa(w.teks, 0.25)};display:flex;align-items:center;justify-content:center"><p style="margin:0;font-size:15px;font-weight:700;letter-spacing:1px;line-height:1;color:${kontras(w.latar2, w)}">VS</p></div>
<div style="position:absolute;left:539px;top:${y + 86}px;width:2px;height:${h - 94}px;background:repeating-linear-gradient(180deg,${alfa(w.teks, 0.2)} 0 6px,transparent 6px 12px)"></div>
${baris}`;
  },
};
