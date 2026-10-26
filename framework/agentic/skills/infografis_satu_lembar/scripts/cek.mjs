#!/usr/bin/env node
/**
 * Memeriksa isi.json sebelum digambar. Pesannya pendek dan menyebut perbaikannya,
 * supaya model kecil bisa memperbaiki sendiri.
 *
 *   node scripts/cek.mjs isi.json
 *
 * Keluar dengan kode 1 bila ada GAGAL. PERINGATAN tidak menghentikan, tapi sebaiknya diperbaiki.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { IKON, BATAS, BATAS_LINIMASA, JUMLAH, KATA_MAKS } from './skema.mjs';
import { buatTeks } from './umum.mjs';
import { periksaLinimasa } from './linimasa.mjs';

export const SUSUNAN = ['produk', 'linimasa'];

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const MEREK_DIR = path.join(HERE, '..', 'merek');

export function periksa(c) {
  const gagal = [];
  const peringatan = [];
  const G = (lokasi, pesan) => gagal.push(`GAGAL      ${lokasi}: ${pesan}`);
  const P = (lokasi, pesan) => peringatan.push(`PERINGATAN ${lokasi}: ${pesan}`);
  const semuaTeks = [];

  const objek = (v, lokasi) => {
    if (v && typeof v === 'object' && !Array.isArray(v)) return true;
    G(lokasi, 'bagian ini harus ada dan berupa objek { ... }. Salin dari contoh/kosong.json.');
    return false;
  };

  const susunan = c.susunan ?? 'produk';
  if (!SUSUNAN.includes(susunan)) {
    G('susunan', `harus salah satu dari: ${SUSUNAN.join(', ')}. Hapus isian ini untuk memakai susunan produk.`);
    return { gagal, peringatan, kata: 0 };
  }
  const teks = buatTeks(G, P, semuaTeks, susunan === 'linimasa' ? BATAS_LINIMASA : BATAS);

  // ── merek
  if (typeof c.merek !== 'string' || !/^[\w-]+$/.test(c.merek) || !fs.existsSync(path.join(MEREK_DIR, `${c.merek}.json`))) {
    const ada = fs.existsSync(MEREK_DIR) ? fs.readdirSync(MEREK_DIR).filter((f) => f.endsWith('.json')).map((f) => f.replace('.json', '')) : [];
    G('merek', `nama merek tidak ditemukan. Pilih salah satu: ${ada.join(', ') || '(belum ada)'}.`);
  }

  if (susunan === 'linimasa') {
    periksaLinimasa(c, { G, teks, objek });
  } else {
  // ── kepala
  if (objek(c.kepala, 'kepala')) {
    teks('kepala.judul_1', c.kepala.judul_1, 'kepala.judul_1', { satuan: false });
    teks('kepala.judul_2', c.kepala.judul_2, 'kepala.judul_2', { satuan: false });
    teks('kepala.tujuan', c.kepala.tujuan, 'kepala.tujuan', { satuan: false });
  }

  // ── masalah
  if (objek(c.masalah, 'masalah')) {
    const m = c.masalah;
    teks('masalah.kalimat_awal', m.kalimat_awal, null, { satuan: false });
    teks('masalah.kalimat_akhir', m.kalimat_akhir, null, { satuan: false });
    const panjang = `${m.kalimat_awal ?? ''} ${m.kalimat_akhir ?? ''}`.length;
    if (panjang > BATAS['masalah.kalimat_awal+akhir']) {
      G('masalah.kalimat_awal + kalimat_akhir', `gabungan terlalu panjang (${panjang} huruf, maksimal ${BATAS['masalah.kalimat_awal+akhir']}).`);
    }
    if (!Array.isArray(m.ukuran) || m.ukuran.length !== JUMLAH.ukuran) {
      G('masalah.ukuran', `harus berisi tepat ${JUMLAH.ukuran} ukuran, masing-masing { "nilai", "tampil", "arti" }.`);
    } else {
      m.ukuran.forEach((u, i) => {
        const L = `masalah.ukuran[${i}]`;
        if (typeof u?.nilai !== 'number' || u.nilai < 0 || u.nilai > 100) G(`${L}.nilai`, 'harus angka 0 sampai 100 (tanpa tanda kutip dan tanpa %). Contoh: 69.57');
        teks(`${L}.tampil`, u?.tampil, 'masalah.ukuran.tampil', { satuan: false });
        if (typeof u?.tampil === 'string' && /%$/.test(u.tampil.trim()) && typeof u?.nilai === 'number') {
          const baca = Number(u.tampil.replace('%', '').replace(',', '.'));
          if (Number.isFinite(baca) && Math.abs(baca - u.nilai) > 0.01) G(`${L}.tampil`, `angkanya (${u.tampil}) harus sama dengan nilai (${u.nilai}).`);
        }
        teks(`${L}.arti`, u?.arti, 'masalah.ukuran.arti');
        if (typeof u?.arti === 'string' && u.arti.trim().split(/\s+/).length < 3) {
          G(`${L}.arti`, 'terlalu singkat. Jelaskan artinya dengan minimal 3 kata, misalnya "tahu dan terampil merawatnya", bukan "paham".');
        }
      });
      if (m.ukuran[0]?.arti && m.ukuran[0].arti === m.ukuran[1]?.arti) G('masalah.ukuran', 'kedua ukuran punya arti yang sama. Bedakan artinya.');
    }
    teks('masalah.sumber', m.sumber, 'masalah.sumber', { satuan: false });
    if (typeof m.sumber === 'string' && m.sumber.trim().length < 6) G('masalah.sumber', 'sebutkan sumber angka (lembaga dan tahun). Jangan pakai angka tanpa sumber.');
    teks('masalah.judul_tambal', m.judul_tambal, 'masalah.judul_tambal', { satuan: false });
    if (!Array.isArray(m.tambal) || m.tambal.length !== JUMLAH.tambal) {
      G('masalah.tambal', `harus berisi tepat ${JUMLAH.tambal} hal yang dilakukan orang sekarang, masing-masing { "ikon", "teks" }.`);
    } else {
      m.tambal.forEach((t, i) => {
        if (!IKON[t?.ikon]) G(`masalah.tambal[${i}].ikon`, `nama ikon "${t?.ikon}" tidak ada. Pilih dari: ${Object.keys(IKON).join(', ')}.`);
        teks(`masalah.tambal[${i}].teks`, t?.teks, 'masalah.tambal.teks', { satuan: false });
      });
    }
  }

  // ── solusi
  if (objek(c.solusi, 'solusi')) {
    if (!Array.isArray(c.solusi.simpul) || c.solusi.simpul.length !== JUMLAH.simpul) {
      G('solusi.simpul', `harus berisi tepat ${JUMLAH.simpul} simpul, masing-masing { "ikon", "nama", "rincian" }.`);
    } else {
      c.solusi.simpul.forEach((s, i) => {
        if (!IKON[s?.ikon]) G(`solusi.simpul[${i}].ikon`, `nama ikon "${s?.ikon}" tidak ada. Pilih dari: ${Object.keys(IKON).join(', ')}.`);
        teks(`solusi.simpul[${i}].nama`, s?.nama, 'solusi.simpul.nama', { satuan: false });
        teks(`solusi.simpul[${i}].rincian`, s?.rincian, 'solusi.simpul.rincian', { satuan: false });
      });
    }
  }

  // ── contoh (percakapan)
  if (objek(c.contoh, 'contoh')) {
    const x = c.contoh;
    teks('contoh.judul', x.judul, 'contoh.judul', { satuan: false });
    teks('contoh.tanya', x.tanya, 'contoh.tanya');
    teks('contoh.jawab_utama', x.jawab_utama, 'contoh.jawab_utama', { sorot: true });
    if (typeof x.jawab_utama === 'string') {
      const n = (x.jawab_utama.match(/\*/g) || []).length;
      if (n !== 2) G('contoh.jawab_utama', 'sorot angka jawaban dengan sepasang tanda *, misalnya "Cocok: *kangkung dan bayam*".');
    }
    teks('contoh.jawab_rinci', x.jawab_rinci, 'contoh.jawab_rinci');
    if (!Array.isArray(x.label) || x.label.length !== JUMLAH.label) {
      G('contoh.label', `harus berisi tepat ${JUMLAH.label} label pembeda, masing-masing { "ikon", "teks" }.`);
    } else {
      let jumlah = 0;
      x.label.forEach((l, i) => {
        if (!IKON[l?.ikon]) G(`contoh.label[${i}].ikon`, `nama ikon "${l?.ikon}" tidak ada. Pilih dari: ${Object.keys(IKON).join(', ')}.`);
        teks(`contoh.label[${i}].teks`, l?.teks, 'contoh.label.teks', { satuan: false });
        jumlah += typeof l?.teks === 'string' ? l.teks.length : 0;
      });
      if (jumlah > BATAS['contoh.label.jumlah']) G('contoh.label', `jumlah huruf ketiga label (${jumlah}) melebihi ${BATAS['contoh.label.jumlah']}, labelnya tidak muat satu baris. Perpendek.`);
    }
  }

  // ── paket
  if (objek(c.paket, 'paket')) {
    teks('paket.catatan', c.paket.catatan, 'paket.catatan', { satuan: false });
    const n = c.paket.isi?.length;
    if (!Array.isArray(c.paket.isi) || n < JUMLAH.paket_min || n > JUMLAH.paket_maks) {
      G('paket.isi', `harus berisi ${JUMLAH.paket_min} sampai ${JUMLAH.paket_maks} paket, urut dari termurah. Tiap paket { "nama", "harga" }.`);
    } else {
      c.paket.isi.forEach((p, i) => {
        teks(`paket.isi[${i}].nama`, p?.nama, 'paket.nama', { satuan: false });
        teks(`paket.isi[${i}].harga`, p?.harga, 'paket.harga', { satuan: false });
      });
    }
  }

  teks('kaki', c.kaki, 'kaki', { satuan: false });
  }

  const kata = semuaTeks.join(' ').split(/\s+/).filter(Boolean).length;
  if (kata > KATA_MAKS) P('seluruh isi', `${kata} kata, terlalu banyak untuk infografis. Targetnya di bawah ${KATA_MAKS}. Buang kalimat yang tidak penting.`);

  return { gagal, peringatan, kata };
}

export function bacaJson(berkas) {
  let mentah;
  try {
    mentah = fs.readFileSync(berkas, 'utf8');
  } catch {
    return { galat: `Berkas "${berkas}" tidak bisa dibaca. Periksa nama dan lokasinya.` };
  }
  try {
    return { isi: JSON.parse(mentah) };
  } catch (e) {
    const pos = Number((/position (\d+)/.exec(e.message) || [])[1]);
    const baris = Number.isFinite(pos) ? mentah.slice(0, pos).split('\n').length : '?';
    return {
      galat: `JSON rusak di sekitar baris ${baris}: ${e.message}. Biasanya karena koma kurang atau berlebih, tanda kutip tidak berpasangan, atau teks diapit tanda kutip tunggal. Salin lagi dari contoh/kosong.json.`,
    };
  }
}

// ── jalankan dari terminal
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const berkas = process.argv[2];
  if (!berkas) {
    console.error('Cara pakai: node scripts/cek.mjs isi.json');
    process.exit(2);
  }
  const { isi, galat } = bacaJson(berkas);
  if (galat) {
    console.log('GAGAL      ' + galat);
    process.exit(1);
  }
  const { gagal, peringatan, kata } = periksa(isi);
  [...gagal, ...peringatan].forEach((l) => console.log(l));
  console.log(gagal.length ? `\nBELUM LOLOS: ${gagal.length} gagal, ${peringatan.length} peringatan. Perbaiki yang GAGAL lalu jalankan lagi.` : `\nLOLOS: 0 gagal, ${peringatan.length} peringatan, ${kata} kata.`);
  process.exit(gagal.length ? 1 : 0);
}
