/**
 * Susunan "linimasa": satu periode sejarah yang dibagi tiga masa, dengan pita waktu
 * berskala, peristiwa penting, tiga kartu masa, dan diagram ke mana penduduk pergi.
 *
 * Model hanya mengisi tahun dan teks pendek. Skala pita, lama tiap masa, dan jumlah
 * tahun seluruhnya dihitung di sini, jadi tidak ada angka yang perlu dikarang model.
 */
import { IKON, BATAS_LINIMASA as B, JUMLAH_LINIMASA as J, TAHUN_MIN, TAHUN_MAKS } from './skema.mjs';
import { esc, ikon, alfa, SKRIP_QA } from './umum.mjs';

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
}

// ── gambar

export function bangunLinimasa(c, m) {
  const w = m.warna;
  const font = `'${m.font}', Arial, sans-serif`;
  const fase = [w.fase1 ?? w.aksen, w.fase2 ?? w.koin3, w.fase3 ?? w.biru1];
  const teksFase = [w.aksen_teks, w.teks, w.teks];
  const { periode } = c;
  const awal = periode[0].mulai;
  const akhir = periode[J.periode - 1].selesai;
  const total = akhir - awal;
  const X0 = 48;
  const LEBAR = 984;
  const BAR_ATAS = 520;
  const BAR_TINGGI = 46;
  const x = (t) => X0 + ((t - awal) / total) * LEBAR;
  const faseDari = (t) => (t < periode[1].mulai ? 0 : t < periode[2].mulai ? 1 : 2);
  const jepit = (v, a, b) => Math.max(a, Math.min(b, v));

  const P = (id, kiri, atas, lebar, gaya, isi) =>
    `<p data-teks="${id}" style="position:absolute;left:${kiri}px;top:${atas}px;${lebar ? `width:${lebar}px;` : ''}margin:0;${gaya}">${isi}</p>`;
  const label = (id, kiri, atas, isi) => P(id, kiri, atas, 0, `font-size:20px;font-weight:600;letter-spacing:3px;color:${w.aksen}`, isi);

  // latar: bata merah Trowulan yang memudar ke bawah, dan matahari yang kehilangan cahaya
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

  // pita waktu
  const potongan = periode
    .map((p, i) => {
      const kiri = x(p.mulai) + (i > 0 ? 2 : 0);
      const lebar = x(p.selesai) - x(p.mulai) - (i > 0 ? 2 : 0);
      const bulat = `${i === 0 ? 23 : 6}px ${i === J.periode - 1 ? 23 : 6}px ${i === J.periode - 1 ? 23 : 6}px ${i === 0 ? 23 : 6}px`;
      const akhirGradien = i === J.periode - 1 ? 0.22 : 0.62;
      const adaTitik = c.peristiwa.some((e) => (e.titik ?? []).some((t) => t >= p.mulai && t < p.selesai));
      const terakhir = i === J.periode - 1;
      return `<div style="position:absolute;left:${kiri.toFixed(1)}px;top:${BAR_ATAS}px;width:${lebar.toFixed(1)}px;height:${BAR_TINGGI}px;border-radius:${bulat};background:linear-gradient(90deg,${fase[i]},${alfa(fase[i], akhirGradien)})"></div>
${adaTitik ? '' : P(`masa-${i}-pita`, kiri + 14, BAR_ATAS + 11, 0, `font-size:22px;font-weight:600;line-height:1.1;color:${teksFase[i]}`, `${p.selesai - p.mulai} tahun`)}
${terakhir ? P('tahun-akhir', x(p.selesai) - 14 - 70, BAR_ATAS + 11, 70, `text-align:right;font-size:22px;font-weight:600;line-height:1.1;color:${teksFase[i]}`, `${p.selesai}`) : ''}`;
    })
    .join('\n');

  const peristiwa = [...c.peristiwa]
    .sort((a, b) => a.tahun - b.tahun)
    .map((e, i) => {
      const atas = i % 2 === 0;
      const ex = x(e.tahun);
      const warna = fase[faseDari(e.tahun)];
      const LB = 176;
      const kiriLabel = jepit(ex - 16, X0, X0 + LEBAR - LB);
      const pusatY = atas ? 478 : 612;
      const tahunTeks = e.sampai && e.sampai !== e.tahun ? `${e.tahun}–${e.sampai}` : `${e.tahun}`;
      const batang = atas
        ? `<div style="position:absolute;left:${(ex - 1).toFixed(1)}px;top:${pusatY + 20}px;width:2px;height:${BAR_ATAS - pusatY - 20}px;background:${warna}"></div>`
        : `<div style="position:absolute;left:${(ex - 1).toFixed(1)}px;top:${BAR_ATAS + BAR_TINGGI}px;width:2px;height:${pusatY - 20 - BAR_ATAS - BAR_TINGGI}px;background:${warna}"></div>`;
      const kurung = e.sampai && e.sampai > e.tahun
        ? `<div style="position:absolute;left:${ex.toFixed(1)}px;top:${atas ? BAR_ATAS - 9 : BAR_ATAS + BAR_TINGGI + 5}px;width:${(x(e.sampai) - ex).toFixed(1)}px;height:4px;border-radius:2px;background:${warna}"></div>`
        : '';
      const titik = (e.titik ?? [])
        .map((t) => `<div style="position:absolute;left:${(x(t) - 10).toFixed(1)}px;top:${BAR_ATAS + 13}px;width:20px;height:20px;display:flex;align-items:center;justify-content:center">${ikon('gunung', 20, teksFase[faseDari(t)], 2.2)}</div>`)
        .join('');
      const bulat = `<div style="position:absolute;left:${(ex - 20).toFixed(1)}px;top:${pusatY - 20}px;width:40px;height:40px;box-sizing:border-box;border-radius:20px;border:3px solid ${warna};background:${w.latar};display:flex;align-items:center;justify-content:center">${ikon(e.ikon, 22, warna, 2)}</div>`;
      const labelAtas = atas ? 372 : 642;
      const isiLabel = `<div style="position:absolute;left:${kiriLabel.toFixed(1)}px;top:${labelAtas}px;width:${LB}px">
<p data-teks="peristiwa-${i}-tahun" style="margin:0;font-size:22px;font-weight:700;line-height:1.1;color:${warna}">${tahunTeks}</p>
<p data-teks="peristiwa-${i}-teks" style="margin:3px 0 0;font-size:19px;line-height:1.15;color:${w.teks2}">${esc(e.teks)}</p>
</div>`;
      return batang + kurung + titik + bulat + isiLabel;
    })
    .join('\n');

  // tiga kartu masa, turun seperti anak tangga
  const kartu = periode
    .map((p, i) => {
      const kiri = 48 + i * 334;
      const atas = 748 + i * 22;
      const lama = p.selesai - p.mulai;
      return `<div style="position:absolute;left:${kiri}px;top:${atas}px;width:316px;height:270px;box-sizing:border-box;border-radius:28px;border-top:6px solid ${fase[i]};background:linear-gradient(180deg,${alfa(fase[i], 0.2)},${w.kartu} 62%)"></div>
<div style="position:absolute;left:${kiri + 22}px;top:${atas + 16}px;display:flex;flex-direction:row;align-items:baseline;gap:10px"><p data-teks="masa-${i}-lama" style="margin:0;font-size:66px;font-weight:700;line-height:1;letter-spacing:-2px;color:${fase[i]}">${lama}</p><p data-teks="masa-${i}-satuan" style="margin:0;font-size:24px;line-height:1;color:${w.teks2}">tahun</p></div>
<div style="position:absolute;left:${kiri + 316 - 22 - 32}px;top:${atas + 24}px">${ikon(p.ikon, 32, fase[i], 1.8)}</div>
${P(`masa-${i}-nama`, kiri + 22, atas + 92, 272, `font-size:27px;font-weight:600;line-height:1.1;color:${w.teks}`, esc(p.nama))}
${P(`masa-${i}-rentang`, kiri + 22, atas + 124, 0, `font-size:19px;line-height:1.1;color:${w.redup}`, `${p.mulai}–${p.selesai}`)}
${p.poin
  .map(
    (t, j) => `<div style="position:absolute;left:${kiri + 22}px;top:${atas + 156 + j * 56}px;width:272px;display:flex;flex-direction:row;gap:10px"><div style="width:8px;height:8px;border-radius:4px;background:${fase[i]};margin-top:8px;flex-shrink:0"></div><p data-teks="masa-${i}-poin-${j}" style="margin:0;font-size:20px;line-height:1.18;color:${w.teks2}">${esc(t)}</p></div>`,
  )
  .join('\n')}`;
    })
    .join('\n');

  // sebaran: dari pusat ke tiga tujuan
  const s = c.sebaran;
  const PUSAT_X = 170;
  const PUSAT_Y = 1212;
  const CHIP_KIRI = 430;
  const CHIP_ATAS = [1136, 1194, 1252];
  const panah = s.tujuan
    .map((t, i) => {
      const tengah = CHIP_ATAS[i] + 25 - 1085;
      const utama = s.utama === i;
      const warna = utama ? w.aksen : alfa(w.aksen, 0.6);
      return `<path d="M ${PUSAT_X + 56} ${PUSAT_Y - 1085} C ${PUSAT_X + 150} ${PUSAT_Y - 1085}, ${CHIP_KIRI - 90} ${tengah}, ${CHIP_KIRI - 6} ${tengah}" fill="none" stroke="${warna}" stroke-width="${utama ? 8 : 3}" stroke-linecap="round" marker-end="url(#kepala${utama ? 'U' : 'B'})"/>`;
    })
    .join('\n');
  const chip = s.tujuan
    .map((t, i) => {
      const utama = s.utama === i;
      return `<div style="position:absolute;left:${CHIP_KIRI}px;top:${CHIP_ATAS[i]}px;width:602px;height:50px;box-sizing:border-box;border-radius:25px;background:${w.kartu};${utama ? `border:2px solid ${w.aksen};` : ''}display:flex;flex-direction:row;align-items:center;gap:12px;padding:0 10px 0 8px">
<div style="width:34px;height:34px;border-radius:17px;background:${w.latar};display:flex;align-items:center;justify-content:center;flex-shrink:0">${ikon(t.ikon, 20, w.aksen, 2)}</div>
<div style="flex:1;min-width:0"><p data-teks="tujuan-${i}-nama" style="margin:0;font-size:22px;font-weight:600;line-height:1.1;color:${w.teks}">${esc(t.nama)}</p><p data-teks="tujuan-${i}-arti" style="margin:0;font-size:18px;line-height:1.1;color:${w.teks2}">${esc(t.arti)}</p></div>
<p data-teks="tujuan-${i}-arah" style="margin:0;padding:4px 12px;border:1.5px solid ${alfa(w.aksen, 0.55)};border-radius:999px;font-size:16px;letter-spacing:1.5px;text-transform:uppercase;line-height:1.1;color:${w.aksen};flex-shrink:0">${esc(t.arah)}</p>
</div>`;
    })
    .join('\n');

  const nama = P('nama-merek', 48, 40, 0, `font-size:22px;font-weight:600;letter-spacing:6px;color:${w.redup}`, esc(m.nama));

  return `<!doctype html>
<html lang="id"><head><meta charset="utf-8"><title>Infografis ${esc(c.kepala.judul_1)} ${esc(c.kepala.judul_2)}</title>
${m.font_url ? `<link rel="stylesheet" href="${m.font_url}">` : ''}
<style>@page{size:1080px 1350px;margin:0}html,body{margin:0;width:1080px;height:1350px;background:${w.latar}}</style></head>
<body>
<div style="position:relative;width:1080px;height:1350px;overflow:hidden;background:${w.latar};font-family:${font};color:${w.teks}">
${latar}

${nama}
<h1 data-teks="judul" style="position:absolute;left:48px;top:84px;width:640px;margin:0;font-size:84px;font-weight:600;line-height:1;letter-spacing:-3px;color:${w.teks}">${esc(c.kepala.judul_1)}<br><span style="background:linear-gradient(90deg,${fase[0]},${fase[1]} 60%,${fase[2]});-webkit-background-clip:text;background-clip:text;color:transparent">${esc(c.kepala.judul_2)}</span></h1>
${P('tujuan', 48, 268, 600, `font-size:25px;line-height:1.2;color:${w.teks2}`, esc(c.kepala.tujuan))}
${P('angka-besar', 700, 102, 280, `text-align:center;font-size:116px;font-weight:700;line-height:1;letter-spacing:-4px;color:${w.teks}`, `${total}`)}
${P('angka-arti', 700, 250, 280, `text-align:center;font-size:25px;line-height:1.1;color:${w.teks2}`, esc(c.kepala.angka_arti))}
${P('angka-rentang', 700, 284, 280, `text-align:center;font-size:20px;line-height:1.1;letter-spacing:2px;color:${fase[0]}`, `${awal}–${akhir}`)}

${label('label-pita', 48, 336, 'PITA WAKTU BERSKALA')}
${potongan}
${peristiwa}

${kartu}

<div style="position:absolute;left:28px;top:1085px;width:1024px;height:221px;border-radius:44px;background:${w.latar2}"></div>
${label('label-sebaran', 56, 1102, esc(s.judul.toUpperCase()))}
<svg width="1080" height="221" viewBox="0 0 1080 221" style="position:absolute;left:0;top:1085px" aria-hidden="true">
<defs>
<marker id="kepalaU" markerUnits="userSpaceOnUse" markerWidth="22" markerHeight="22" refX="17" refY="11" orient="auto"><path d="M0 0L22 11L0 22z" fill="${w.aksen}"/></marker>
<marker id="kepalaB" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto"><path d="M0 0L14 7L0 14z" fill="${alfa(w.aksen, 0.6)}"/></marker>
</defs>
<circle cx="${PUSAT_X}" cy="${PUSAT_Y - 1085}" r="68" fill="none" stroke="${w.aksen}" stroke-opacity="0.4" stroke-width="2" stroke-dasharray="6 6"/>
${panah}
</svg>
<div style="position:absolute;left:${PUSAT_X - 52}px;top:${PUSAT_Y - 52}px;width:104px;height:104px;border-radius:52px;background:${w.pusat}"></div>
${P('pusat', PUSAT_X - 52, PUSAT_Y - 12, 104, `text-align:center;font-size:20px;font-weight:600;line-height:1.2;color:${w.teks}`, esc(s.pusat))}
<div style="position:absolute;left:${PUSAT_X - 12}px;top:${PUSAT_Y - 46}px">${ikon('candi', 24, w.aksen, 2)}</div>
${chip}

${P('kaki', 48, 1319, 984, `font-size:18px;line-height:1.2;color:${w.redup}`, esc(`Sumber: ${c.sumber}. ${c.kaki}`))}

</div>
${SKRIP_QA}
</body></html>`;
}
