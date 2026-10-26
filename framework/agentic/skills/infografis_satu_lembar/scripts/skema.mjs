/**
 * Skema infografis satu lembar: ikon yang boleh dipakai, batas panjang tiap isian,
 * dan daftar kalimat yang membingungkan. Dipakai bersama oleh cek.mjs dan bangun.mjs.
 *
 * Batas panjang dihitung dari tata letak yang tetap (ukuran huruf dan lebar kotak),
 * jadi isian yang lolos pemeriksaan hampir pasti muat di gambar.
 */

/** Ikon garis 24×24. Nama ikon ditulis di JSON; modelnya cukup memilih nama. */
export const IKON = {
  pensil: '<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M14 7l3 3"/>',
  kalkulator: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8"/><path d="M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
  obrolan: '<path d="M4 5h16v11H10l-5 4v-4H4z"/><path d="M8 9h8M8 12h5"/>',
  buku: '<path d="M5 4h13v16H7a2 2 0 0 1-2-2z"/><path d="M5 18a2 2 0 0 1 2-2h11"/>',
  perisai: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 5-5"/>',
  orang: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  label: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1"/><path d="M4 4l16 16"/>',
  video: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9l5 3-5 3z"/>',
  tabel: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
  grafik: '<path d="M5 20V11M12 20V4M19 20v-7"/>',
  dokumen: '<path d="M5 3h9l4 4v6"/><path d="M5 3v18h6"/><circle cx="16" cy="17" r="3.5"/><path d="M18.6 19.6L21 22"/>',
  centang: '<path d="M5 12l4.5 4.5L19 7"/>',
  dompet: '<path d="M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7l12-3v3"/><circle cx="16" cy="13.5" r="1.2"/>',
  koin: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/>',
  jam: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  gembok: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  ponsel: '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
  keranjang: '<path d="M5 8h14l-1.2 11H6.2z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
  lokasi: '<path d="M12 21s7-6 7-11a7 7 0 0 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  petir: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  bintang: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
};

/** Panjang maksimum (jumlah huruf) tiap isian teks. */
export const BATAS = {
  'kepala.judul_1': 18,
  'kepala.judul_2': 22,
  'kepala.tujuan': 48,
  'masalah.kalimat_awal+akhir': 62,
  'masalah.ukuran.tampil': 7,
  'masalah.ukuran.arti': 34,
  'masalah.sumber': 80,
  'masalah.judul_tambal': 34,
  'masalah.tambal.teks': 26,
  'solusi.simpul.nama': 10,
  'solusi.simpul.rincian': 38,
  'contoh.judul': 18,
  'contoh.tanya': 46,
  'contoh.jawab_utama': 38,
  'contoh.jawab_rinci': 44,
  'contoh.label.teks': 30,
  'contoh.label.jumlah': 56,
  'paket.catatan': 48,
  'paket.nama': 10,
  'paket.harga': 12,
  'kaki': 60,
};

/** Kata dan kalimat yang membuat pembaca bertanya "maksudnya apa?". */
export const KATA_KABUR = [
  'dll', 'dsb', 'dan sebagainya', 'dan lain-lain', 'berbagai macam', 'banyak sekali',
  'terbaik', 'terlengkap', 'revolusioner', 'canggih', 'inovatif', 'solusi lengkap', 'all-in-one',
];

/** Kalimat yang pernah dinilai ambigu oleh pengguna. */
export const AMBIGU = [
  {
    re: /\b(tanpa|tidak)\s+(me)?jual\s+produk\s*$/i,
    pesan: 'Kalimat ini ambigu: pembaca mengira Anda tidak menjual apa pun. Sebut produk apa yang tidak dijual, misalnya "Tidak menjual bibit".',
  },
  {
    re: /^\s*paham\b[^,.]{0,12}$/i,
    pesan: 'Kata "paham" saja tidak berarti apa-apa. Tulis paham tentang apa dan bisa apa, misalnya "tahu dan terampil merawatnya".',
  },
  {
    re: /\b(ideal|cukup|layak|wajar)\s*$/i,
    pesan: 'Kata penilaian tanpa angka. Tulis angkanya dan artinya, misalnya "ideal: 15–30 hari".',
  },
];

export const JUMLAH = { ukuran: 2, tambal: 3, simpul: 4, label: 3, paket_min: 2, paket_maks: 4 };
export const KATA_MAKS = 260;
