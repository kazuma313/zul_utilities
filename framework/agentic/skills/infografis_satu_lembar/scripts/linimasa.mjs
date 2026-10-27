/**
 * Susunan "linimasa": satu periode sejarah yang dibagi tiga masa, dengan pita waktu
 * berskala, peristiwa penting, tiga kartu masa, dan diagram ke mana penduduk pergi.
 *
 * Model hanya mengisi tahun dan teks pendek. Skala pita, lama tiap masa, dan jumlah
 * tahun seluruhnya dihitung di sini, jadi tidak ada angka yang perlu dikarang model.
 */
import { IKON, BATAS_LINIMASA as B, JUMLAH_LINIMASA as J, TAHUN_MIN, TAHUN_MAKS } from './skema.mjs';
import { periksaKaki } from './umum.mjs';

const adaTahun = (v) => Number.isInteger(v) && v >= TAHUN_MIN && v <= TAHUN_MAKS;

// ── pemeriksaan

export function periksaLinimasa(c, { G, teks, objek }) {
  const cekIkon = (lokasi, nama) => {
    if (!IKON[nama]) G(lokasi, `nama ikon "${nama}" tidak ada. Pilih dari: ${Object.keys(IKON).join(', ')}.`);
  };

  if (objek(c.kepala, 'kepala')) {
    teks('kepala.judul_1', c.kepala.judul_1, 'kepala.judul_1', { satuan: false });
    teks('kepala.judul_2', c.kepala.judul_2, 'kepala.judul_2', { satuan: false });
    teks('kepala.tujuan', c.kepala.tujuan, 'kepala.tujuan', { satuan: false });
    teks('kepala.angka_arti', c.kepala.angka_arti, 'kepala.angka_arti', { satuan: false });
  }

  // periode: tiga masa berurutan tanpa lubang
  let awal = null;
  let akhir = null;
  if (!Array.isArray(c.periode) || c.periode.length !== J.periode) {
    G('periode', `harus berisi tepat ${J.periode} masa berurutan, masing-masing { "nama", "mulai", "selesai", "ikon", "poin" }.`);
  } else {
    c.periode.forEach((p, i) => {
      const L = `periode[${i}]`;
      teks(`${L}.nama`, p?.nama, 'periode.nama', { satuan: false });
      for (const k of ['mulai', 'selesai']) {
        if (!adaTahun(p?.[k])) G(`${L}.${k}`, `harus tahun berupa bilangan bulat tanpa tanda kutip, antara ${TAHUN_MIN} dan ${TAHUN_MAKS}. Contoh: 1389`);
      }
      if (adaTahun(p?.mulai) && adaTahun(p?.selesai) && p.selesai <= p.mulai) G(`${L}.selesai`, `harus lebih besar dari mulai (${p.mulai}).`);
      const sebelum = c.periode[i - 1];
      if (i > 0 && adaTahun(sebelum?.selesai) && adaTahun(p?.mulai) && p.mulai !== sebelum.selesai) {
        G(`${L}.mulai`, `harus ${sebelum.selesai}, sama dengan akhir masa sebelumnya, supaya pita waktu tidak berlubang atau tumpang tindih.`);
      }
      cekIkon(`${L}.ikon`, p?.ikon);
      if (!Array.isArray(p?.poin) || p.poin.length !== J.poin) G(`${L}.poin`, `harus berisi tepat ${J.poin} butir teks pendek.`);
      else p.poin.forEach((t, j) => teks(`${L}.poin[${j}]`, t, 'periode.poin', { satuan: false }));
    });
    const pertama = c.periode[0]?.mulai;
    const terakhir = c.periode[J.periode - 1]?.selesai;
    if (adaTahun(pertama) && adaTahun(terakhir) && terakhir > pertama) [awal, akhir] = [pertama, terakhir];
  }

  // peristiwa: penanda di pita waktu
  const n = c.peristiwa?.length;
  if (!Array.isArray(c.peristiwa) || n < J.peristiwa_min || n > J.peristiwa_maks) {
    G('peristiwa', `harus berisi ${J.peristiwa_min} sampai ${J.peristiwa_maks} peristiwa, masing-masing { "tahun", "teks", "ikon" } dan boleh ditambah "sampai" dan "titik".`);
  } else {
    c.peristiwa.forEach((e, i) => {
      const L = `peristiwa[${i}]`;
      const dalam = (v) => adaTahun(v) && (awal === null || (v >= awal && v <= akhir));
      if (!dalam(e?.tahun)) G(`${L}.tahun`, `harus tahun bilangan bulat di dalam pita waktu${awal ? ` (${awal} sampai ${akhir})` : ''}, tanpa tanda kutip.`);
      if (e?.sampai !== undefined && (!dalam(e.sampai) || e.sampai < e.tahun)) G(`${L}.sampai`, 'harus tahun di dalam pita waktu dan tidak lebih kecil dari tahun mulai.');
      if (e?.titik !== undefined) {
        const batasAtas = e.sampai ?? akhir ?? TAHUN_MAKS;
        if (!Array.isArray(e.titik) || e.titik.length > J.titik_maks || e.titik.some((t) => !adaTahun(t) || t < e.tahun || t > batasAtas)) {
          G(`${L}.titik`, `harus daftar paling banyak ${J.titik_maks} tahun, masing-masing di antara tahun dan sampai.`);
        }
      }
      teks(`${L}.teks`, e?.teks, 'peristiwa.teks', { satuan: false });
      cekIkon(`${L}.ikon`, e?.ikon);
    });
  }

  // sebaran: dari satu pusat ke tiga tujuan
  if (objek(c.sebaran, 'sebaran')) {
    const s = c.sebaran;
    teks('sebaran.judul', s.judul, 'sebaran.judul', { satuan: false });
    teks('sebaran.pusat', s.pusat, 'sebaran.pusat', { satuan: false });
    if (!Array.isArray(s.tujuan) || s.tujuan.length !== J.tujuan) {
      G('sebaran.tujuan', `harus berisi tepat ${J.tujuan} tujuan, masing-masing { "ikon", "nama", "arti", "arah" }.`);
    } else {
      s.tujuan.forEach((t, i) => {
        const L = `sebaran.tujuan[${i}]`;
        cekIkon(`${L}.ikon`, t?.ikon);
        teks(`${L}.nama`, t?.nama, 'sebaran.tujuan.nama', { satuan: false });
        teks(`${L}.arti`, t?.arti, 'sebaran.tujuan.arti', { satuan: false });
        teks(`${L}.arah`, t?.arah, 'sebaran.tujuan.arah', { satuan: false });
      });
    }
    if (s.utama !== undefined && !(Number.isInteger(s.utama) && s.utama >= 0 && s.utama < J.tujuan)) {
      G('sebaran.utama', `harus 0, 1, atau 2: nomor tujuan yang paling banyak dituju (dimulai dari 0), atau hapus isian ini.`);
    }
  }

  teks('sumber', c.sumber, 'sumber', { satuan: false });
  if (typeof c.sumber === 'string' && c.sumber.trim().length < 6) G('sumber', 'sebutkan sumbernya (penulis dan tahun, atau lembaga). Jangan memakai fakta tanpa sumber.');
  teks('kaki', c.kaki, 'kaki', { satuan: false });
  periksaKaki(c, G);
}

// ── gambar: susunan linimasa adalah bentuk khusus susunan adaptif (pita waktu, tahap, alur)

export function linimasaKeAdaptif(c) {
  return {
    susunan: 'adaptif',
    merek: c.merek,
    kepala: {
      judul_1: c.kepala.judul_1,
      judul_2: c.kepala.judul_2,
      tujuan: c.kepala.tujuan,
      sorot: { nilai: 'lama_pita', arti: c.kepala.angka_arti },
    },
    blok: [
      {
        jenis: 'pita_waktu',
        masa: c.periode.map(({ nama, mulai, selesai }) => ({ nama, mulai, selesai })),
        peristiwa: c.peristiwa,
      },
      {
        jenis: 'tahap',
        ikuti_pita: true,
        items: c.periode.map(({ nama, ikon, poin }) => ({ nama, ikon, poin })),
      },
      { jenis: 'alur', judul: c.sebaran.judul, pusat: c.sebaran.pusat, tujuan: c.sebaran.tujuan, ...(c.sebaran.utama !== undefined ? { utama: c.sebaran.utama } : {}) },
    ],
    sumber: c.sumber,
    kaki: c.kaki,
  };
}
