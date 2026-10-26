/**
 * Blok tahap: tahapan berurutan sebagai kartu yang turun seperti anak tangga (2 sampai 3
 * tahap) atau baris yang menjorok bertahap (4 sampai 5 tahap).
 *
 * Bentuk: { "jenis": "tahap", "ikuti_pita": true?,
 *           "items": [{ "nama", "ikon", "poin": [..1 sampai 2], "angka"?, "satuan"?, "rentang"? }] }
 *
 * Dengan "ikuti_pita": true, lama, satuan, dan rentang tiap tahap dihitung dari masa di blok
 * pita_waktu, jadi tidak boleh diisi. Tanpa itu, "angka" boleh diisi; bila kosong, yang
 * tampil adalah nomor urut.
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, ikon, alfa } from './umum.mjs';

const KARTU_MAKS = 3;

export const blokTahap = {
  jenis: 'tahap',

  periksa(b, L, { G, teks, cekIkon }) {
    const [mn, mx] = J.tahap;
    if (b.ikuti_pita !== undefined && typeof b.ikuti_pita !== 'boolean') G(`${L}.ikuti_pita`, 'harus true atau false, tanpa tanda kutip.');
    if (!Array.isArray(b.items) || b.items.length < mn || b.items.length > mx) {
      G(`${L}.items`, `harus berisi ${mn} sampai ${mx} tahap, masing-masing { "nama", "ikon", "poin" }.`);
      return;
    }
    b.items.forEach((it, i) => {
      const T = `${L}.items[${i}]`;
      teks(`${T}.nama`, it?.nama, 'tahap.nama', { satuan: false });
      cekIkon(`${T}.ikon`, it?.ikon);
      const [pMin, pMaks] = J.poin;
      if (!Array.isArray(it?.poin) || it.poin.length < pMin || it.poin.length > pMaks) G(`${T}.poin`, `harus berisi ${pMin} sampai ${pMaks} butir teks pendek.`);
      else it.poin.forEach((t, j) => teks(`${T}.poin[${j}]`, t, 'tahap.poin', { satuan: false }));
      for (const [kunci, batas] of [['angka', 'tahap.angka'], ['satuan', 'tahap.satuan'], ['rentang', 'tahap.rentang']]) {
        if (it?.[kunci] === undefined) continue;
        if (b.ikuti_pita) G(`${T}.${kunci}`, 'jangan diisi: dengan "ikuti_pita" nilainya dihitung dari pita waktu. Hapus isian ini.');
        else teks(`${T}.${kunci}`, it[kunci], batas, { satuan: false });
      }
    });
  },

  tinggi(b) {
    const n = b.items.length;
    if (n <= KARTU_MAKS) {
      const alami = 270 + 22 * (n - 1);
      return { alami, maks: alami + 90 };
    }
    return { alami: n * 66, maks: n * 100 };
  },

  gambar(b, k) {
    const { y, h, w, id, P, paletKe, pita } = k;
    const n = b.items.length;
    const palet = paletKe(b.ikuti_pita ? pita.masa.length : n);
    const info = b.items.map((it, i) => {
      if (b.ikuti_pita) {
        const m = pita.masa[i];
        return { angka: String(m.selesai - m.mulai), satuan: 'tahun', rentang: `${m.mulai}–${m.selesai}` };
      }
      return { angka: it.angka ?? String(i + 1), satuan: it.satuan ?? '', rentang: it.rentang ?? '' };
    });
    return n <= KARTU_MAKS ? kartu(b, k, palet, info) : baris(b, k, palet, info);

    function kartu() {
      const alami = 270 + 22 * (n - 1);
      const e = Math.max(0, h - alami);
      const lebar = (984 - (n - 1) * 18) / n;
      return b.items
        .map((it, i) => {
          const kiri = 48 + i * (lebar + 18);
          const atas = y + i * 22;
          const dalam = info[i];
          const mulaiPoin = dalam.rentang ? 156 : 130;
          const jarakPoin = 56 + e / 2;
          return `<div style="position:absolute;left:${kiri.toFixed(1)}px;top:${atas}px;width:${lebar.toFixed(1)}px;height:${270 + e}px;box-sizing:border-box;border-radius:28px;border-top:6px solid ${palet[i]};background:linear-gradient(180deg,${alfa(palet[i], 0.2)},${w.kartu} 62%)"></div>
<div style="position:absolute;left:${(kiri + 22).toFixed(1)}px;top:${atas + 16}px;display:flex;flex-direction:row;align-items:baseline;gap:10px"><p data-teks="${id}-${i}-angka" style="margin:0;font-size:66px;font-weight:700;line-height:1;letter-spacing:-2px;color:${palet[i]}">${esc(dalam.angka)}</p>${dalam.satuan ? `<p data-teks="${id}-${i}-satuan" style="margin:0;font-size:24px;line-height:1;color:${w.teks2}">${esc(dalam.satuan)}</p>` : ''}</div>
<div style="position:absolute;left:${(kiri + lebar - 22 - 32).toFixed(1)}px;top:${atas + 24}px">${ikon(it.ikon, 32, palet[i], 1.8)}</div>
${P(`${id}-${i}-nama`, kiri + 22, atas + 92, lebar - 44, `font-size:27px;font-weight:600;line-height:1.1;color:${w.teks}`, esc(it.nama))}
${dalam.rentang ? P(`${id}-${i}-rentang`, kiri + 22, atas + 124, 0, `font-size:19px;line-height:1.1;color:${w.redup}`, esc(dalam.rentang)) : ''}
${it.poin
  .map(
    (t, j) => `<div style="position:absolute;left:${(kiri + 22).toFixed(1)}px;top:${(atas + mulaiPoin + j * jarakPoin).toFixed(1)}px;width:${(lebar - 44).toFixed(1)}px;display:flex;flex-direction:row;gap:10px"><div style="width:8px;height:8px;border-radius:4px;background:${palet[i]};margin-top:8px;flex-shrink:0"></div><p data-teks="${id}-${i}-poin-${j}" style="margin:0;font-size:20px;line-height:1.18;color:${w.teks2}">${esc(t)}</p></div>`,
  )
  .join('\n')}`;
        })
        .join('\n');
    }

    function baris() {
      const pitch = h / n;
      const tinggi = pitch - 6;
      const kk = Math.min(1.2, Math.max(1, pitch / 66));
      return b.items
        .map((it, i) => {
          const geser = i * 12;
          const kiri = 48 + geser;
          const atas = y + i * pitch;
          const dalam = info[i];
          const tinggiPoin = it.poin.length * 25 * kk;
          return `<div style="position:absolute;left:${kiri}px;top:${atas.toFixed(1)}px;width:${984 - geser}px;height:${tinggi.toFixed(1)}px;box-sizing:border-box;border-radius:22px;border-left:6px solid ${palet[i]};background:linear-gradient(90deg,${alfa(palet[i], 0.2)},${w.kartu} 70%)"></div>
<div style="position:absolute;left:${kiri + 24}px;top:${(atas + (tinggi - 40 * kk) / 2).toFixed(1)}px;width:84px"><p data-teks="${id}-${i}-angka" style="margin:0;font-size:${Math.round(38 * kk)}px;font-weight:700;line-height:1;letter-spacing:-1px;color:${palet[i]}">${esc(dalam.angka)}</p></div>
${P(`${id}-${i}-nama`, kiri + 112, atas + (tinggi - (dalam.rentang ? 52 : 28) * kk) / 2, 236, `font-size:${Math.round(24 * kk)}px;font-weight:600;line-height:1.1;color:${w.teks}`, esc(it.nama))}
${dalam.rentang ? P(`${id}-${i}-rentang`, kiri + 112, atas + (tinggi - 52 * kk) / 2 + 30 * kk, 0, `font-size:${Math.round(18 * kk)}px;line-height:1.1;color:${w.redup}`, esc(dalam.rentang)) : ''}
<div style="position:absolute;left:${kiri + 360}px;top:${(atas + (tinggi - tinggiPoin) / 2).toFixed(1)}px;width:${984 - geser - 440}px">${it.poin
            .map((t, j) => `<p data-teks="${id}-${i}-poin-${j}" style="margin:0;font-size:${Math.round(19 * kk)}px;line-height:${Math.round(25 * kk)}px;color:${w.teks2}">${esc(t)}</p>`)
            .join('')}</div>
<div style="position:absolute;left:${kiri + 984 - geser - 50}px;top:${(atas + (tinggi - 28) / 2).toFixed(1)}px">${ikon(it.ikon, 28, palet[i], 1.8)}</div>`;
        })
        .join('\n');
    }
  },
};
