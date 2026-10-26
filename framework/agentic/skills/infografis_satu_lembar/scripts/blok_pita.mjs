/**
 * Blok pita_waktu: pita berskala untuk urutan tahun. Lebar tiap potongan sebanding dengan
 * lama masanya, dan peristiwa penting dipasang di atas dan di bawah pita.
 *
 * Bentuk: { "jenis": "pita_waktu", "masa": [{ "nama", "mulai", "selesai" }],
 *           "peristiwa": [{ "tahun", "teks", "ikon", "sampai"?, "titik"? }] }
 */
import { JUMLAH_ADAPTIF as J } from './skema.mjs';
import { esc, ikon, alfa, kontras } from './umum.mjs';

export const TAHUN_MIN = 1;
export const TAHUN_MAKS = 2100;
export const adaTahun = (v) => Number.isInteger(v) && v >= TAHUN_MIN && v <= TAHUN_MAKS;

const X0 = 48;
const LEBAR = 984;
const LB = 176; // lebar label peristiwa
const TINGGI_PITA = 46;
const ALAMI = 382;
const jepit = (v, a, b) => Math.max(a, Math.min(b, v));

/**
 * Memasang label peristiwa di atas atau di bawah pita tanpa saling menimpa. Dipakai oleh
 * pemeriksa (untuk melaporkan peristiwa yang tidak muat) dan oleh penggambar.
 */
export function tataPeristiwa(peristiwa, awal, akhir) {
  const x = (t) => X0 + ((t - awal) / (akhir - awal)) * LEBAR;
  const ujung = { atas: 0, bawah: 0 };
  const hasil = [];
  const bentrok = [];
  [...peristiwa]
    .sort((a, b) => a.tahun - b.tahun)
    .forEach((e, i) => {
      const ex = x(e.tahun);
      const kiri = jepit(ex - 16, X0, X0 + LEBAR - LB);
      const urutan = i % 2 === 0 ? ['atas', 'bawah'] : ['bawah', 'atas'];
      let sisi = urutan.find((s) => kiri >= ujung[s] + 10);
      if (!sisi) {
        bentrok.push(e);
        sisi = urutan[0];
      }
      ujung[sisi] = Math.max(ujung[sisi], kiri + LB);
      hasil.push({ e, ex, kiri, sisi });
    });
  return { hasil, bentrok };
}

export const blokPita = {
  jenis: 'pita_waktu',

  periksa(b, L, { G, teks, cekIkon }) {
    const [mMin, mMaks] = J.masa;
    let awal = null;
    let akhir = null;
    if (!Array.isArray(b.masa) || b.masa.length < mMin || b.masa.length > mMaks) {
      G(`${L}.masa`, `harus berisi ${mMin} sampai ${mMaks} masa berurutan, masing-masing { "nama", "mulai", "selesai" }.`);
    } else {
      b.masa.forEach((p, i) => {
        const T = `${L}.masa[${i}]`;
        teks(`${T}.nama`, p?.nama, 'pita.masa.nama', { satuan: false });
        for (const k of ['mulai', 'selesai']) {
          if (!adaTahun(p?.[k])) G(`${T}.${k}`, `harus tahun berupa bilangan bulat tanpa tanda kutip, antara ${TAHUN_MIN} dan ${TAHUN_MAKS}. Contoh: 1389`);
        }
        if (adaTahun(p?.mulai) && adaTahun(p?.selesai) && p.selesai <= p.mulai) G(`${T}.selesai`, `harus lebih besar dari mulai (${p.mulai}).`);
        const sebelum = b.masa[i - 1];
        if (i > 0 && adaTahun(sebelum?.selesai) && adaTahun(p?.mulai) && p.mulai !== sebelum.selesai) {
          G(`${T}.mulai`, `harus ${sebelum.selesai}, sama dengan akhir masa sebelumnya, supaya pita waktu tidak berlubang atau tumpang tindih.`);
        }
      });
      const pertama = b.masa[0]?.mulai;
      const terakhir = b.masa[b.masa.length - 1]?.selesai;
      if (adaTahun(pertama) && adaTahun(terakhir) && terakhir > pertama) [awal, akhir] = [pertama, terakhir];
    }

    const [pMin, pMaks] = J.peristiwa;
    if (!Array.isArray(b.peristiwa) || b.peristiwa.length < pMin || b.peristiwa.length > pMaks) {
      G(`${L}.peristiwa`, `harus berisi ${pMin} sampai ${pMaks} peristiwa, masing-masing { "tahun", "teks", "ikon" } dan boleh ditambah "sampai" dan "titik".`);
      return;
    }
    let semuaSah = true;
    b.peristiwa.forEach((e, i) => {
      const T = `${L}.peristiwa[${i}]`;
      const dalam = (v) => adaTahun(v) && (awal === null || (v >= awal && v <= akhir));
      if (!dalam(e?.tahun)) {
        semuaSah = false;
        G(`${T}.tahun`, `harus tahun bilangan bulat di dalam pita waktu${awal ? ` (${awal} sampai ${akhir})` : ''}, tanpa tanda kutip.`);
      }
      if (e?.sampai !== undefined && (!dalam(e.sampai) || e.sampai < e.tahun)) {
        semuaSah = false;
        G(`${T}.sampai`, 'harus tahun di dalam pita waktu dan tidak lebih kecil dari tahun mulai.');
      }
      if (e?.titik !== undefined) {
        const atas = e.sampai ?? akhir ?? TAHUN_MAKS;
        if (!Array.isArray(e.titik) || e.titik.length > J.titik_maks || e.titik.some((t) => !adaTahun(t) || t < e.tahun || t > atas)) {
          G(`${T}.titik`, `harus daftar paling banyak ${J.titik_maks} tahun, masing-masing di antara tahun dan sampai.`);
        }
      }
      teks(`${T}.teks`, e?.teks, 'pita.peristiwa.teks', { satuan: false });
      cekIkon(`${T}.ikon`, e?.ikon);
    });
    // Peristiwa yang labelnya saling menimpa dilaporkan sebelum digambar, lengkap dengan caranya.
    if (semuaSah && awal !== null) {
      const { bentrok } = tataPeristiwa(b.peristiwa, awal, akhir);
      for (const e of bentrok) {
        G(`${L}.peristiwa`, `label peristiwa ${e.tahun} ("${e.teks}") tidak punya tempat karena terlalu dekat dengan peristiwa lain. Gabungkan peristiwa yang tahunnya berdekatan menjadi satu butir (pakai "sampai" dan "titik"), atau hapus salah satu.`);
      }
    }
  },

  tinggi: () => ({ alami: ALAMI, maks: 440 }),

  gambar(b, k) {
    const { y, h, w, id, P, label, palet } = k;
    const A = Math.max(0, h - ALAMI) / 2;
    const { masa } = b;
    const awal = masa[0].mulai;
    const akhir = masa[masa.length - 1].selesai;
    const total = akhir - awal;
    const x = (t) => X0 + ((t - awal) / total) * LEBAR;
    const faseDari = (t) => {
      const i = masa.findIndex((m) => t >= m.mulai && t < m.selesai);
      return i === -1 ? masa.length - 1 : i;
    };
    const barTop = y + 184 + A;
    const pusatAtas = y + 142 + A;
    const pusatBawah = barTop + TINGGI_PITA + 46 + A;

    const potongan = masa
      .map((m, i) => {
        const kiri = x(m.mulai) + (i > 0 ? 2 : 0);
        const lebar = x(m.selesai) - x(m.mulai) - (i > 0 ? 2 : 0);
        const awalR = i === 0 ? 23 : 6;
        const akhirR = i === masa.length - 1 ? 23 : 6;
        const adaTitik = b.peristiwa.some((e) => (e.titik ?? []).some((t) => t >= m.mulai && t < m.selesai));
        const terakhir = i === masa.length - 1;
        const warnaTeks = kontras(palet[i], w);
        // potongan sempit hanya memuat angkanya, tanpa kata "tahun"
        const lama = m.selesai - m.mulai;
        const tulisLama = lebar >= 130 ? `${lama} tahun` : `${lama}`;
        return `<div style="position:absolute;left:${kiri.toFixed(1)}px;top:${barTop}px;width:${lebar.toFixed(1)}px;height:${TINGGI_PITA}px;border-radius:${awalR}px ${akhirR}px ${akhirR}px ${awalR}px;background:linear-gradient(90deg,${palet[i]},${alfa(palet[i], terakhir ? 0.22 : 0.62)})"></div>
${adaTitik || lebar < 56 ? '' : P(`${id}-masa-${i}`, kiri + 14, barTop + 11, 0, `font-size:22px;font-weight:600;line-height:1.1;color:${warnaTeks}`, tulisLama)}
${terakhir ? P(`${id}-akhir`, x(m.selesai) - 14 - 70, barTop + 11, 70, `text-align:right;font-size:22px;font-weight:600;line-height:1.1;color:${w.teks}`, `${m.selesai}`) : ''}`;
      })
      .join('\n');

    const { hasil } = tataPeristiwa(b.peristiwa, awal, akhir);
    const penanda = hasil
      .map(({ e, ex, kiri, sisi }, i) => {
        const atas = sisi === 'atas';
        const warna = palet[faseDari(e.tahun)];
        const pusatY = atas ? pusatAtas : pusatBawah;
        const tahunTeks = e.sampai && e.sampai !== e.tahun ? `${e.tahun}–${e.sampai}` : `${e.tahun}`;
        const batang = atas
          ? `<div style="position:absolute;left:${(ex - 1).toFixed(1)}px;top:${pusatY + 20}px;width:2px;height:${barTop - pusatY - 20}px;background:${warna}"></div>`
          : `<div style="position:absolute;left:${(ex - 1).toFixed(1)}px;top:${barTop + TINGGI_PITA}px;width:2px;height:${pusatY - 20 - barTop - TINGGI_PITA}px;background:${warna}"></div>`;
        const kurung = e.sampai && e.sampai > e.tahun
          ? `<div style="position:absolute;left:${ex.toFixed(1)}px;top:${atas ? barTop - 9 : barTop + TINGGI_PITA + 5}px;width:${(x(e.sampai) - ex).toFixed(1)}px;height:4px;border-radius:2px;background:${warna}"></div>`
          : '';
        const titik = (e.titik ?? [])
          .map((t) => `<div style="position:absolute;left:${(x(t) - 10).toFixed(1)}px;top:${barTop + 13}px;width:20px;height:20px;display:flex;align-items:center;justify-content:center">${ikon('gunung', 20, kontras(palet[faseDari(t)], w), 2.2)}</div>`)
          .join('');
        const bulat = `<div style="position:absolute;left:${(ex - 20).toFixed(1)}px;top:${pusatY - 20}px;width:40px;height:40px;box-sizing:border-box;border-radius:20px;border:3px solid ${warna};background:${w.latar};display:flex;align-items:center;justify-content:center">${ikon(e.ikon, 22, warna, 2)}</div>`;
        const labelAtas = atas ? y + 36 : pusatBawah + 30;
        const isi = `<div style="position:absolute;left:${kiri.toFixed(1)}px;top:${labelAtas}px;width:${LB}px">
<p data-teks="${id}-p${i}-tahun" style="margin:0;font-size:22px;font-weight:700;line-height:1.1;color:${warna}">${tahunTeks}</p>
<p data-teks="${id}-p${i}-teks" style="margin:3px 0 0;font-size:19px;line-height:1.15;color:${w.teks2}">${esc(e.teks)}</p>
</div>`;
        return batang + kurung + titik + bulat + isi;
      })
      .join('\n');

    return `${label(`${id}-label`, X0, y, 'PITA WAKTU BERSKALA')}
${potongan}
${penanda}`;
  },
};
