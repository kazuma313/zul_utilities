#!/usr/bin/env node
/**
 * Menggambar infografis satu lembar 4:5 (1080×1350) dari isi.json.
 * Susunannya dipilih dari isian "susunan": produk (bawaan), linimasa, atau adaptif.
 *
 *   node scripts/bangun.mjs isi.json                 # hasil di ./hasil/
 *   node scripts/bangun.mjs isi.json --keluar folder # folder lain
 *   node scripts/bangun.mjs isi.json --tanpa-gambar  # hanya infografis.html (tanpa Chrome)
 *
 * Tanpa paket tambahan. Butuh Node 18+ dan Chrome atau Edge untuk membuat PNG dan PDF
 * (atau setel CHROME_PATH). Selalu memeriksa isi.json lebih dulu (sama dengan cek.mjs).
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { IKON } from './skema.mjs';
import { bacaJson, periksa, MEREK_DIR } from './cek.mjs';
import { linimasaKeAdaptif } from './linimasa.mjs';
import { bangunAdaptif } from './adaptif.mjs';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function dataUri(berkas) {
  const ext = path.extname(berkas).slice(1).toLowerCase();
  const tipe = ext === 'svg' ? 'image/svg+xml' : ext === 'jpg' ? 'image/jpeg' : `image/${ext || 'png'}`;
  return `data:${tipe};base64,${fs.readFileSync(berkas).toString('base64')}`;
}

const ikon = (nama, ukuran, warna, tebal = 1.8) =>
  `<svg width="${ukuran}" height="${ukuran}" viewBox="0 0 24 24" fill="none" stroke="${warna}" stroke-width="${tebal}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${IKON[nama]}</svg>`;

/** "Cocok *kangkung*" → teks biasa dengan bagian bertanda * diwarnai aksen. */
const sorot = (s, warna) => esc(s).replace(/\*([^*]+)\*/g, `<span style="color:${warna}">$1</span>`);

export function bangunHtml(c, m) {
  if (c.susunan === 'adaptif') return bangunAdaptif(c, m);
  if (c.susunan === 'linimasa') return bangunAdaptif(linimasaKeAdaptif(c), m);
  const w = m.warna;
  const f = `'${m.font}', Arial, sans-serif`;
  const logoKata = m.logo_kata && fs.existsSync(path.join(MEREK_DIR, m.logo_kata.berkas)) ? m.logo_kata : null;
  const logoLambang = m.logo_lambang && fs.existsSync(path.join(MEREK_DIR, m.logo_lambang.berkas)) ? m.logo_lambang : null;
  // Tanpa logo, lingkaran diisi huruf pertama nama merek supaya tidak tampak kosong.
  const inisial = esc(String(m.nama ?? '?').trim().charAt(0).toUpperCase());
  const lambangKecil = (kiri, atas, lebar, tinggi) =>
    logoLambang
      ? `<img src="${dataUri(path.join(MEREK_DIR, logoLambang.berkas))}" alt="" style="position:absolute;left:${kiri}px;top:${atas}px;width:${lebar}px;height:${tinggi}px;display:block">`
      : `<div aria-hidden="true" style="position:absolute;left:${kiri}px;top:${atas}px;width:${lebar}px;height:${tinggi}px;display:flex;align-items:center;justify-content:center;font-size:${Math.round(tinggi * 0.8)}px;font-weight:700;line-height:1;color:${w.aksen}">${inisial}</div>`;

  const P = (id, kiri, atas, lebar, gaya, isi) =>
    `<p data-teks="${id}" style="position:absolute;left:${kiri}px;top:${atas}px;${lebar ? `width:${lebar}px;` : ''}margin:0;${gaya}">${isi}</p>`;
  const label = (id, kiri, atas, isi) => P(id, kiri, atas, 0, `font-size:22px;font-weight:600;letter-spacing:3px;color:${w.aksen}`, isi);

  const cincin = (kiri, nilai, tampil, arti, warnaBusur, warnaAngka, id) => `
<div style="position:absolute;left:${kiri}px;top:392px;width:150px;height:150px">
<svg width="150" height="150" viewBox="0 0 150 150" aria-hidden="true"><circle cx="75" cy="75" r="60" fill="none" stroke="${w.lingkar}" stroke-width="18"/><circle cx="75" cy="75" r="60" fill="none" stroke="${warnaBusur}" stroke-width="18" stroke-linecap="round" stroke-dasharray="${((nilai / 100) * 376.99).toFixed(1)} 377" transform="rotate(-90 75 75)"/></svg>
<p data-teks="${id}-angka" style="position:absolute;left:0;top:58px;width:150px;margin:0;text-align:center;font-size:30px;font-weight:600;line-height:1;letter-spacing:-1px;color:${warnaAngka}">${esc(tampil)}</p>
</div>
${P(`${id}-arti`, kiri - 30, 552, 210, `text-align:center;font-size:23px;line-height:1.2;color:${w.teks2}`, esc(arti))}`;

  const tambal = (u, atas, i) => `
<div style="position:absolute;left:600px;top:${atas}px;display:flex;flex-direction:row;align-items:center;gap:14px"><div style="width:46px;height:46px;border-radius:23px;background:${w.kartu};display:flex;align-items:center;justify-content:center;flex-shrink:0">${ikon(u.ikon, 26, w.aksen)}</div><p data-teks="tambal-${i}" style="margin:0;font-size:25px;line-height:1.1;color:${w.teks2}">${esc(u.teks)}</p></div>`;

  // susunan: kiri-atas, kiri-bawah, kanan-atas, kanan-bawah
  const simpulHtml = c.solusi.simpul
    .map((s, i) => {
      const kiri = i < 2;
      const baris = i % 2;
      const atasTeks = 678 + baris * 100;
      const atasIkon = 690 + baris * 100;
      const lingkar = `<div style="position:absolute;left:${kiri ? 296 : 720}px;top:${atasIkon}px;width:64px;height:64px;border-radius:32px;background:${w.kartu};display:flex;align-items:center;justify-content:center">${ikon(s.ikon, 32, w.aksen)}</div>`;
      const kotak = `<div style="position:absolute;left:${kiri ? 48 : 800}px;top:${atasTeks}px;width:${kiri ? 240 : 232}px;${kiri ? 'text-align:right' : ''}"><p data-teks="simpul-${i}-nama" style="margin:0;font-size:30px;font-weight:500;line-height:1.1;color:${w.teks}">${esc(s.nama)}</p><p data-teks="simpul-${i}-rincian" style="margin:2px 0 0;font-size:22px;line-height:1.2;color:${w.redup}">${esc(s.rincian)}</p></div>`;
      return lingkar + kotak;
    })
    .join('\n');

  const chip = (l, i) => `<div style="display:flex;flex-direction:row;align-items:center;gap:8px;padding:8px 16px 8px 12px;border-radius:999px;background:${w.latar}">${ikon(l.ikon, 20, w.aksen, 2)}<p data-teks="label-${i}" style="margin:0;font-size:20px;line-height:1;color:${w.teks}">${esc(l.teks)}</p></div>`;

  // paket: koin makin besar dari kiri ke kanan
  const n = c.paket.isi.length;
  const lebarItem = 984 / n;
  const warnaKoin = [w.koin1, w.koin2, w.koin3, w.aksen];
  const paketHtml = c.paket.isi
    .map((p, i) => {
      const d = Math.round(50 + (n === 1 ? 0 : (i * 36) / (n - 1)));
      const kiri = Math.round(48 + i * lebarItem);
      const terakhir = i === n - 1;
      const warna = terakhir ? w.aksen : warnaKoin[Math.round((i * 2) / Math.max(n - 2, 1))] ?? w.koin2;
      const koin = `<div style="position:absolute;left:${kiri}px;top:${Math.round(1264 - d / 2)}px;width:${d}px;height:${d}px;border-radius:${d / 2}px;background:${warna};color:${terakhir ? w.aksen_teks : w.teks};font-size:${Math.round(d * 0.36)}px;font-weight:600;display:flex;align-items:center;justify-content:center">${esc(m.simbol_koin ?? 'Rp')}</div>`;
      const teks = `<div style="position:absolute;left:${kiri + d + 12}px;top:1237px;width:${Math.round(lebarItem - d - 18)}px"><p data-teks="paket-${i}-nama" style="margin:0;font-size:22px;line-height:1.1;color:${w.teks}">${esc(p.nama)}</p><p data-teks="paket-${i}-harga" style="margin:2px 0 0;font-size:24px;font-weight:600;line-height:1.1;color:${w.aksen}">${esc(p.harga)}</p></div>`;
      return koin + teks;
    })
    .join('\n');

  const kepalaLogo = logoKata
    ? `<img src="${dataUri(path.join(MEREK_DIR, logoKata.berkas))}" alt="${esc(m.nama)}" style="position:absolute;left:48px;top:40px;width:${logoKata.lebar}px;height:${logoKata.tinggi}px;display:block">`
    : P('nama-merek', 48, 40, 0, `font-size:34px;font-weight:700;letter-spacing:6px;color:${w.teks}`, esc(m.nama));

  const qa = `<script>
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

  return `<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>Infografis ${esc(m.nama)}</title>
${m.font_url ? `<link rel="stylesheet" href="${m.font_url}">` : ''}
<style>@page{size:1080px 1350px;margin:0}html,body{margin:0;width:1080px;height:1350px;background:${w.latar}}</style></head>
<body>
<div style="position:relative;width:1080px;height:1350px;overflow:hidden;background:${w.latar};font-family:${f};color:${w.teks}">

<div style="position:absolute;left:720px;top:284px;width:420px;height:420px;border-radius:210px;background:${w.latar2}"></div>
<div style="position:absolute;left:28px;top:626px;width:1024px;height:270px;border-radius:44px;background:${w.latar2}"></div>
<div style="position:absolute;left:28px;top:908px;width:1024px;height:282px;border-radius:44px;background:${w.latar2}"></div>

${kepalaLogo}
<h1 data-teks="judul" style="position:absolute;left:48px;top:90px;width:720px;margin:0;font-size:66px;font-weight:400;line-height:1.04;letter-spacing:-3px;color:${w.teks}">${esc(c.kepala.judul_1)}<br><span style="color:${w.redup}">${esc(c.kepala.judul_2)}</span></h1>
${logoLambang ? `<img src="${dataUri(path.join(MEREK_DIR, logoLambang.berkas))}" alt="Lambang ${esc(m.nama)}" style="position:absolute;left:800px;top:26px;width:${logoLambang.lebar}px;height:${logoLambang.tinggi}px;display:block">` : ''}
${P('tujuan', 48, 242, 740, `font-size:26px;line-height:1.2;color:${w.teks2}`, esc(c.kepala.tujuan))}

${label('label-masalah', 48, 298, 'MASALAH')}
${P('kalimat-masalah', 48, 334, 984, `font-size:31px;font-weight:400;line-height:1.1;letter-spacing:-1px;color:${w.teks}`, `${esc(c.masalah.kalimat_awal)} <span style="color:${w.redup}">${esc(c.masalah.kalimat_akhir)}</span>`)}
${cincin(70, c.masalah.ukuran[0].nilai, c.masalah.ukuran[0].tampil, c.masalah.ukuran[0].arti, w.biru1, w.teks, 'ukuran-1')}
${cincin(330, c.masalah.ukuran[1].nilai, c.masalah.ukuran[1].tampil, c.masalah.ukuran[1].arti, w.aksen, w.aksen, 'ukuran-2')}
${P('judul-tambal', 600, 392, 432, `font-size:24px;font-weight:600;line-height:1.15;color:${w.teks}`, esc(c.masalah.judul_tambal))}
${c.masalah.tambal.map((u, i) => tambal(u, 440 + i * 60, i)).join('')}

${label('label-solusi', 48, 642, 'SOLUSI')}
<svg width="1080" height="270" viewBox="0 0 1080 270" style="position:absolute;left:0;top:626px" aria-hidden="true">
<path d="M360 96 C 420 96, 450 94, 494 100" fill="none" stroke="${w.redup}" stroke-opacity="0.55" stroke-width="2" stroke-dasharray="6 6"/>
<path d="M360 196 C 420 196, 450 196, 494 192" fill="none" stroke="${w.redup}" stroke-opacity="0.55" stroke-width="2" stroke-dasharray="6 6"/>
<path d="M720 96 C 660 96, 630 94, 586 100" fill="none" stroke="${w.redup}" stroke-opacity="0.55" stroke-width="2" stroke-dasharray="6 6"/>
<path d="M720 196 C 660 196, 630 196, 586 192" fill="none" stroke="${w.redup}" stroke-opacity="0.55" stroke-width="2" stroke-dasharray="6 6"/>
</svg>
<div style="position:absolute;left:450px;top:682px;width:180px;height:180px;box-sizing:border-box;border-radius:90px;border:2px dashed ${w.aksen};opacity:0.45"></div>
<div style="position:absolute;left:475px;top:707px;width:130px;height:130px;border-radius:65px;background:${w.pusat}"></div>
${lambangKecil(500, 736, 80, 71)}
${simpulHtml}

${label('label-contoh', 48, 924, esc(c.contoh.judul.toUpperCase()))}
${P('catatan-contoh', 330 + Math.max(0, c.contoh.judul.length - 16) * 14, 927, 0, `font-size:20px;line-height:1.2;color:${w.redup}`, 'contoh ilustrasi')}
<div style="position:absolute;left:440px;top:962px;width:592px;height:56px;box-sizing:border-box;padding:0 22px;border-radius:24px 24px 6px 24px;background:${w.balon};display:flex;align-items:center"><p data-teks="tanya" style="margin:0;font-size:24px;line-height:1.2;color:${w.teks}">${esc(c.contoh.tanya)}</p></div>
<div style="position:absolute;left:48px;top:1034px;width:56px;height:56px;border-radius:28px;background:${w.pusat}"></div>
${lambangKecil(58, 1046, 36, 32)}
<div style="position:absolute;left:118px;top:1030px;width:800px;height:148px;box-sizing:border-box;padding:14px 22px;border-radius:6px 24px 24px 24px;background:${w.kartu};display:flex;flex-direction:column;gap:8px">
<p data-teks="jawab-utama" style="margin:0;font-size:30px;font-weight:600;line-height:1.1;color:${w.teks}">${sorot(c.contoh.jawab_utama, w.aksen)}</p>
<p data-teks="jawab-rinci" style="margin:0;font-size:22px;line-height:1.15;color:${w.teks2}">${esc(c.contoh.jawab_rinci)}</p>
<div style="display:flex;flex-direction:row;gap:10px">${c.contoh.label.map(chip).join('')}</div>
</div>

${label('label-paket', 48, 1204, 'PAKET')}
${P('catatan-paket', 150, 1207, 700, `font-size:20px;line-height:1.2;color:${w.redup}`, esc(c.paket.catatan))}
${paketHtml}

${P('kaki', 48, 1322, 984, `font-size:19px;line-height:1.2;color:${w.redup}`, esc(`Sumber angka: ${c.masalah.sumber}. ${c.kaki}`))}

</div>
${qa}
</body></html>`;
}

function cariChrome() {
  const calon = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/snap/bin/chromium',
  ].filter(Boolean);
  return calon.find((p) => fs.existsSync(p));
}

function jalankanChrome(chrome, argumen, url) {
  return execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-sandbox', ...argumen, url], {
    encoding: 'utf8',
    maxBuffer: 1 << 26,
    stdio: ['ignore', 'pipe', 'ignore'],
    timeout: 120000,
  });
}

// ── jalankan dari terminal
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const berkas = args.find((a) => !a.startsWith('--') && args[args.indexOf(a) - 1] !== '--keluar');
  const iKeluar = args.indexOf('--keluar');
  const keluar = path.resolve(iKeluar >= 0 ? args[iKeluar + 1] : 'hasil');
  if (!berkas) {
    console.error('Cara pakai: node scripts/bangun.mjs isi.json [--keluar folder] [--tanpa-gambar]');
    process.exit(2);
  }
  const { isi, galat } = bacaJson(berkas);
  if (galat) {
    console.log('GAGAL      ' + galat);
    process.exit(1);
  }
  const { gagal, peringatan } = periksa(isi);
  [...gagal, ...peringatan].forEach((l) => console.log(l));
  if (gagal.length) {
    console.log(`\nBELUM DIGAMBAR: ${gagal.length} gagal. Perbaiki isi.json lalu jalankan lagi.`);
    process.exit(1);
  }

  const merek = JSON.parse(fs.readFileSync(path.join(MEREK_DIR, `${isi.merek}.json`), 'utf8'));
  fs.mkdirSync(keluar, { recursive: true });
  const berkasHtml = path.join(keluar, 'infografis.html');
  fs.writeFileSync(berkasHtml, bangunHtml(isi, merek));
  console.log(`OK infografis.html  (${berkasHtml})`);
  if (args.includes('--tanpa-gambar')) process.exit(0);

  const chrome = cariChrome();
  if (!chrome) {
    console.log('\nChrome atau Edge tidak ditemukan, jadi PNG dan PDF tidak dibuat. Buka infografis.html di peramban, atau setel CHROME_PATH lalu jalankan lagi.');
    process.exit(0);
  }
  const url = pathToFileURL(berkasHtml).href;
  const profil = fs.mkdtempSync(path.join(os.tmpdir(), 'infografis-'));
  try {
    const dom = jalankanChrome(chrome, ['--dump-dom', '--virtual-time-budget=20000', `--user-data-dir=${profil}`, '--window-size=1080,1350'], url);
    const qa = /<pre id="qa"[^>]*>([\s\S]*?)<\/pre>/.exec(dom);
    const masalah = qa ? JSON.parse(qa[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&')) : null;
    jalankanChrome(chrome, ['--virtual-time-budget=20000', `--user-data-dir=${profil}`, '--window-size=1080,1350', '--force-device-scale-factor=2', `--screenshot=${path.join(keluar, 'infografis.png')}`], url);
    jalankanChrome(chrome, ['--virtual-time-budget=20000', `--user-data-dir=${profil}`, '--no-pdf-header-footer', `--print-to-pdf=${path.join(keluar, 'infografis.pdf')}`], url);
    console.log('OK infografis.png   (2160×2700, rasio 4:5)');
    console.log('OK infografis.pdf   (satu halaman)');
    if (masalah === null) {
      console.log('PERINGATAN pemeriksaan tata letak tidak berjalan (huruf atau jaringan?). Lihat gambarnya sendiri.');
    } else if (masalah.length) {
      masalah.forEach((l) => console.log('BERTUMPUK  ' + l));
      console.log('\nGambar sudah dibuat, tetapi ada teks yang bertumpuk atau keluar lembar. Perpendek teks yang disebut, lalu jalankan lagi.');
      process.exit(3);
    } else {
      console.log('Tata letak: tidak ada teks yang bertumpuk.');
    }
  } finally {
    fs.rmSync(profil, { recursive: true, force: true });
  }
}
