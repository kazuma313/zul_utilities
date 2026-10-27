/**
 * Susunan "adaptif": lembar 4:5 yang disusun dari 2 sampai 4 blok visual. Setiap blok dipilih
 * menurut bentuk informasinya, lalu tingginya menyesuaikan jumlah butir dan sisa ruang lembar.
 *
 *   pita_waktu  urutan tahun         tahap    tahapan berurutan
 *   alur        sebaran atau akibat  banding  dua pihak berhadapan
 *   langkah     cara melakukan       angka    angka persen
 *
 * Satu jenis blok dipakai paling banyak sekali. Pemeriksa menghitung lebih dulu apakah semua
 * blok muat di lembar, dan melaporkan cara memperbaikinya bila tidak.
 */
import { IKON, BATAS_ADAPTIF, JUMLAH_ADAPTIF as J, AREA_BLOK as AREA, JENIS_BLOK } from './skema.mjs';
import { esc, alfa, paletKe, pembuatP, periksaKaki, SKRIP_QA } from './umum.mjs';
import { blokPita, adaTahun } from './blok_pita.mjs';
import { blokTahap } from './blok_tahap.mjs';
import { blokAlur } from './blok_alur.mjs';
import { blokBanding } from './blok_banding.mjs';
import { blokLangkah } from './blok_langkah.mjs';
import { blokAngka } from './blok_angka.mjs';

export { BATAS_ADAPTIF };

const BLOK = {
  pita_waktu: blokPita,
  tahap: blokTahap,
  alur: blokAlur,
  banding: blokBanding,
  langkah: blokLangkah,
  angka: blokAngka,
};

const ringkasPita = (b) => {
  const masa = b.masa;
  const awal = masa[0].mulai;
  const akhir = masa[masa.length - 1].selesai;
  return { masa, awal, akhir, total: akhir - awal };
};

// ── pemeriksaan

export function periksaAdaptif(c, { G, teks, objek }) {
  let salah = false;
  const Gx = (lokasi, pesan) => {
    salah = true;
    G(lokasi, pesan);
  };
  const cekIkon = (lokasi, nama) => {
    if (!IKON[nama]) Gx(lokasi, `nama ikon "${nama}" tidak ada. Pilih dari: ${Object.keys(IKON).join(', ')}.`);
  };

  if (objek(c.kepala, 'kepala')) {
    teks('kepala.judul_1', c.kepala.judul_1, 'kepala.judul_1', { satuan: false });
    teks('kepala.judul_2', c.kepala.judul_2, 'kepala.judul_2', { satuan: false });
    teks('kepala.tujuan', c.kepala.tujuan, 'kepala.tujuan', { satuan: false });
  }

  const [bMin, bMaks] = J.blok;
  if (!Array.isArray(c.blok) || c.blok.length < bMin || c.blok.length > bMaks) {
    Gx('blok', `harus berisi ${bMin} sampai ${bMaks} blok. Pilih blok menurut bentuk informasinya: ${JENIS_BLOK.join(', ')}.`);
  } else {
    const dipakai = new Set();
    c.blok.forEach((b, i) => {
      const L = `blok[${i}]`;
      if (!BLOK[b?.jenis]) {
        Gx(`${L}.jenis`, `harus salah satu dari: ${JENIS_BLOK.join(', ')}.`);
      } else if (dipakai.has(b.jenis)) {
        Gx(`${L}.jenis`, `blok ${b.jenis} sudah dipakai. Satu jenis blok paling banyak sekali; pilih jenis lain.`);
      }
      dipakai.add(b?.jenis);
    });
    const pitaBlok = c.blok.find((b) => b?.jenis === 'pita_waktu');
    let pita = null;
    c.blok.forEach((b, i) => {
      if (!BLOK[b?.jenis]) return;
      BLOK[b.jenis].periksa(b, `blok[${i}]`, { G: Gx, teks, cekIkon, objek, pita: null });
    });
    // pita dihitung setelah blok pita diperiksa, supaya blok tahap bisa membandingkan jumlah masa
    if (pitaBlok && Array.isArray(pitaBlok.masa) && pitaBlok.masa.length >= J.masa[0] && pitaBlok.masa.every((p) => adaTahun(p?.mulai) && adaTahun(p?.selesai))) {
      pita = ringkasPita(pitaBlok);
    }
    c.blok.forEach((b, i) => {
      if (b?.jenis !== 'tahap' || !b.ikuti_pita) return;
      const L = `blok[${i}]`;
      if (!pita) Gx(`${L}.ikuti_pita`, 'butuh blok pita_waktu yang sah di lembar ini. Tambahkan blok itu, atau hapus "ikuti_pita".');
      else if (Array.isArray(b.items) && b.items.length !== pita.masa.length) Gx(`${L}.items`, `harus berisi ${pita.masa.length} tahap, sama dengan jumlah masa di pita_waktu.`);
    });

    // sorot di kepala: bisa dihapus (otomatis), "tanpa", atau { "nilai", "arti" }
    if (c.kepala && c.kepala.sorot !== undefined && c.kepala.sorot !== 'tanpa') {
      const s = c.kepala.sorot;
      if (!s || typeof s !== 'object') {
        Gx('kepala.sorot', 'harus { "nilai", "arti" }, "tanpa", atau hapus isian ini supaya dibuat otomatis dari blok pertama.');
      } else {
        if (s.nilai === 'lama_pita') {
          if (!pitaBlok) Gx('kepala.sorot.nilai', '"lama_pita" butuh blok pita_waktu. Tulis angkanya sendiri, atau tambahkan blok itu.');
        } else {
          teks('kepala.sorot.nilai', s.nilai, 'kepala.sorot.nilai', { satuan: false });
        }
        teks('kepala.sorot.arti', s.arti, 'kepala.sorot.arti', { satuan: false });
      }
    }

    // muat atau tidak
    if (!salah) {
      const tersedia = AREA.bawah - AREA.atas;
      const butuh = c.blok.reduce((j, b) => j + BLOK[b.jenis].tinggi(b).alami, 0) + AREA.jarak * (c.blok.length - 1);
      if (butuh > tersedia) {
        const rincian = c.blok.map((b) => `${b.jenis} ${BLOK[b.jenis].tinggi(b).alami}`).join(', ');
        Gx('blok', `terlalu padat: isinya butuh ${butuh} piksel dari ${tersedia} yang tersedia (${rincian}). Kurangi satu blok, atau kurangi jumlah butir, misalnya tahap, baris pembanding, atau langkah.`);
      }
    }
  }

  teks('sumber', c.sumber, 'sumber', { satuan: false });
  if (typeof c.sumber === 'string' && c.sumber.trim().length < 6) Gx('sumber', 'sebutkan sumbernya (penulis dan tahun, atau lembaga). Jangan memakai fakta tanpa sumber.');
  teks('kaki', c.kaki, 'kaki', { satuan: false });
  periksaKaki(c, Gx);
}

// ── gambar

/** Membagi tinggi tersedia ke blok: tinggi alami dulu, sisanya dilebarkan sampai batas maksimum tiap blok. */
function bagiTinggi(blok) {
  const ukuran = blok.map((b) => BLOK[b.jenis].tinggi(b));
  const tinggi = ukuran.map((u) => u.alami);
  const tersedia = AREA.bawah - AREA.atas;
  let sisa = tersedia - tinggi.reduce((a, b) => a + b, 0) - AREA.jarak * (blok.length - 1);
  for (let putaran = 0; putaran < 4 && sisa > 0.5; putaran++) {
    const longgar = ukuran.map((u, i) => Math.max(0, u.maks - tinggi[i]));
    const jumlah = longgar.filter((v) => v > 0).length;
    if (!jumlah) break;
    const bagian = sisa / jumlah;
    longgar.forEach((v, i) => {
      if (v <= 0) return;
      const tambah = Math.min(v, bagian);
      tinggi[i] += tambah;
      sisa -= tambah;
    });
  }
  const jarakEkstra = blok.length > 1 ? Math.min(30, sisa / (blok.length - 1)) : 0;
  sisa -= jarakEkstra * (blok.length - 1);
  return { tinggi, jarak: AREA.jarak + jarakEkstra, mulai: AREA.atas + Math.max(0, sisa) / 2 };
}

/**
 * Angka yang disorot di kepala. Bila tidak diisi, dihitung dari blok pertama (jumlah tahun,
 * langkah, tahap, tujuan, atau baris pembanding), jadi tidak ada angka yang ditulis model.
 */
function sorotDari(c, pita) {
  const s = c.kepala.sorot;
  if (s === 'tanpa') return { inisial: true };
  if (s && typeof s === 'object') {
    const lama = s.nilai === 'lama_pita';
    return { nilai: lama ? String(pita.total) : String(s.nilai), arti: s.arti, rentang: lama ? `${pita.awal}–${pita.akhir}` : '' };
  }
  const b = c.blok[0];
  if (b.jenis === 'pita_waktu') {
    const p = ringkasPita(b);
    return { nilai: String(p.total), arti: 'tahun', rentang: `${p.awal}–${p.akhir}` };
  }
  if (b.jenis === 'langkah') return { nilai: String(b.langkah.length), arti: 'langkah', rentang: '' };
  if (b.jenis === 'tahap') return { nilai: String(b.items.length), arti: 'tahap', rentang: '' };
  if (b.jenis === 'alur') return { nilai: String(b.tujuan.length), arti: 'tujuan', rentang: '' };
  if (b.jenis === 'banding') return { nilai: String(b.baris.length), arti: 'pembanding', rentang: '' };
  return { nilai: b.angka[0].tampil, arti: 'angka pertama', rentang: '' };
}

export function bangunAdaptif(c, m) {
  const w = m.warna;
  const font = `'${m.font}', Arial, sans-serif`;
  const { P, label } = pembuatP(w);
  const fase = paletKe(w, 3);
  const pitaBlok = c.blok.find((b) => b.jenis === 'pita_waktu');
  const pita = pitaBlok ? ringkasPita(pitaBlok) : null;
  const sorot = sorotDari(c, pita);
  const inisial = esc(String(m.nama ?? '?').trim().charAt(0).toUpperCase());

  // latar: bata merah yang memudar ke bawah, dan matahari yang kehilangan cahaya
  const latar = `<svg width="1080" height="760" style="position:absolute;left:0;top:0" aria-hidden="true">
<defs>
<pattern id="bata" width="96" height="48" patternUnits="userSpaceOnUse"><path d="M0 0H96M0 24H96M0 0V24M48 0V24M24 24V48M72 24V48" stroke="${w.teks}" stroke-opacity="0.085" stroke-width="2" fill="none"/></pattern>
<linearGradient id="pudar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="0.7" stop-color="#000"/></linearGradient>
<mask id="topeng"><rect width="1080" height="760" fill="url(#pudar)"/></mask>
</defs>
<rect width="1080" height="760" fill="url(#bata)" mask="url(#topeng)"/>
</svg>
<div style="position:absolute;left:520px;top:0;width:640px;height:440px;overflow:hidden;-webkit-mask-image:linear-gradient(180deg,#000 58%,transparent 100%);mask-image:linear-gradient(180deg,#000 58%,transparent 100%)">
<svg width="640" height="640" viewBox="0 0 640 640" style="position:absolute;left:0;top:-130px" aria-hidden="true">
<defs><radialGradient id="sinar"><stop offset="0" stop-color="${fase[0]}" stop-opacity="0.5"/><stop offset="0.55" stop-color="${fase[1]}" stop-opacity="0.15"/><stop offset="1" stop-color="${fase[2]}" stop-opacity="0"/></radialGradient></defs>
<circle cx="320" cy="320" r="320" fill="url(#sinar)"/>
${[142, 180, 218, 256, 294]
  .map((r, i) => `<circle cx="320" cy="320" r="${r}" fill="none" stroke="${fase[i < 2 ? 0 : i < 4 ? 1 : 2]}" stroke-opacity="${(0.8 - i * 0.15).toFixed(2)}" stroke-width="${(3.2 - i * 0.5).toFixed(1)}"${i > 1 ? ' stroke-dasharray="2 10" stroke-linecap="round"' : ''}/>`)
  .join('\n')}
</svg>
</div>`;

  const panjang = Math.max(c.kepala.judul_1.length, c.kepala.judul_2.length);
  const ukuranJudul = Math.round(Math.min(84, 590 / (0.56 * panjang)));
  const nilaiUkuran = sorot.inisial ? 130 : Math.round(Math.min(116, 280 / (0.64 * sorot.nilai.length)));
  const kepala = `${P('nama-merek', 48, 40, 0, `font-size:22px;font-weight:600;letter-spacing:6px;color:${w.redup}`, esc(m.nama))}
<h1 data-teks="judul" style="position:absolute;left:48px;top:84px;width:640px;margin:0;font-size:${ukuranJudul}px;font-weight:600;line-height:1;letter-spacing:-3px;color:${w.teks}">${esc(c.kepala.judul_1)}<br><span style="background:linear-gradient(90deg,${fase[0]},${fase[1]} 60%,${fase[2]});-webkit-background-clip:text;background-clip:text;color:transparent">${esc(c.kepala.judul_2)}</span></h1>
${P('tujuan', 48, 268, 600, `font-size:25px;line-height:1.2;color:${w.teks2}`, esc(c.kepala.tujuan))}
${
  sorot.inisial
    ? P('sorot-inisial', 700, 132, 280, `text-align:center;font-size:${nilaiUkuran}px;font-weight:700;line-height:1;color:${fase[0]}`, inisial)
    : `${P('sorot-nilai', 700, 102 + (116 - nilaiUkuran) / 2, 280, `text-align:center;font-size:${nilaiUkuran}px;font-weight:700;line-height:1;letter-spacing:-4px;color:${w.teks}`, esc(sorot.nilai))}
${P('sorot-arti', 700, 250, 280, `text-align:center;font-size:25px;line-height:1.1;color:${w.teks2}`, esc(sorot.arti))}
${sorot.rentang ? P('sorot-rentang', 700, 284, 280, `text-align:center;font-size:20px;line-height:1.1;letter-spacing:2px;color:${fase[0]}`, esc(sorot.rentang)) : ''}`
}`;

  // blok
  const { tinggi, jarak, mulai } = bagiTinggi(c.blok);
  let y = mulai;
  const isiBlok = c.blok
    .map((b, i) => {
      const k = {
        y,
        h: tinggi[i],
        w,
        id: `b${i}`,
        P,
        label,
        pita,
        paletKe: (n) => paletKe(w, n),
        palet: b.jenis === 'pita_waktu' ? paletKe(w, b.masa.length) : paletKe(w, 3),
      };
      const html = BLOK[b.jenis].gambar(b, k);
      y += tinggi[i] + jarak;
      return html;
    })
    .join('\n\n');

  return `<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>Infografis ${esc(c.kepala.judul_1)} ${esc(c.kepala.judul_2)}</title>
${m.font_url ? `<link rel="stylesheet" href="${m.font_url}">` : ''}
<style>@page{size:1080px 1350px;margin:0}html,body{margin:0;width:1080px;height:1350px;background:${w.latar}}</style></head>
<body>
<div style="position:relative;width:1080px;height:1350px;overflow:hidden;background:${w.latar};font-family:${font};color:${w.teks}">
${latar}

${kepala}

${isiBlok}

<p data-teks="kaki" style="position:absolute;left:48px;bottom:10px;width:984px;margin:0;font-size:18px;line-height:1.2;color:${w.redup}">${esc(`Sumber: ${c.sumber}. ${c.kaki}`)}</p>

</div>
${SKRIP_QA}
</body></html>`;
}
