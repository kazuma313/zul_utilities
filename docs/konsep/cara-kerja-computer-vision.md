# Cara kerja Computer Vision

`zul.computer_vision` terdiri dari fungsi-fungsi kecil yang masing-masing mengerjakan satu hal: menggambar teks di sudut frame, menghitung lintasan garis, mengukur lama di zona, dan seterusnya. Halaman ini menjelaskan keputusan di balik fungsi-fungsi itu: kenapa satu orang diwakili satu titik, kenapa garis menunggu beberapa frame, kenapa grace berbeda dari batas kredit, dan seterusnya.

Fungsi-fungsi ini dipisahkan dari proyek analitik video sebuah toko sepatu dengan dua kamera CCTV. Angka di halaman ini diukur pada rekaman kedua kamera itu, di proyek asalnya.

## Fungsi kecil yang dirangkai sendiri

Setiap modul punya satu tugas dan tidak tahu modul lain dipakai untuk apa:

- `detection` mengubah frame menjadi `Detections`: kotak, keypoint, dan id track sebagai array NumPy.
- `geometry`, `pose`, `zones`, `timers`, dan `distance` hanya menerima array NumPy dan id track. Modul ini tidak tahu model apa yang dipakai, dan bisa diuji dengan data buatan.
- `draw` dan `masks` menggambar atau menyembunyikan bagian frame.

Dengan pemisahan ini, tidak ada fungsi yang terikat pada satu kasus. "Berapa orang yang menghadap rak lebih dari 3 detik" adalah rangkaian `zone_membership`, `facing_zone_targets`, dan `ConditionTimer`. "Berapa orang yang masuk setelah melihat etalase" adalah `ConditionTimer` dan `LineCounter`. Mengganti model cukup dengan mengganti file bobot di `load_model`.

Semua hitungan memakai id track, bukan jumlah kotak di setiap frame. Orang yang terlihat selama 300 frame tetap satu orang. `ByteTracker` membuang deteksi yang track-nya belum dikonfirmasi. Di proyek asal, 105 dari 493 deteksi (21%) belum punya track yang dikonfirmasi, dan meloloskannya menambah satu orang palsu ke setiap hitungan.

## Satu titik per orang

`PolygonZone`, `LineCounter`, dan `zone_membership` menerima satu titik per orang, bukan kotak. Kamu yang memilih titiknya dengan `box_anchors(boxes, ratio)`, karena titik yang tepat bergantung pada pertanyaannya.

Titik kaki (`ratio=1.0`) cocok untuk garis dan area di lantai, misalnya ambang pintu: kaki adalah tempat orang menyentuh lantai. Untuk area yang dihadapi orang, misalnya rak, titik kaki memberi jawaban yang salah. Pada potongan 300 frame dari kamera dalam toko, titik kaki menempatkan dua pengunjung di lorong tempat mereka berdiri. Titik di sekitar kepala, 1/6 dari atas kotak, menempatkan keduanya di rak yang mereka hadapi dan raih.

Apa pun titiknya, poligon harus menutupi tempat titik itu berada. Untuk titik kepala, poligon rak harus menutupi tempat kepala pengunjung berada saat melihat rak itu, bukan hanya lantai di depannya.

## Poligon

Titik yang tepat berada di tepi poligon dihitung di dalam, sama dengan `cv2.pointPolygonTest`. Hitungannya memakai NumPy, sehingga satu panggilan memeriksa semua orang di frame tanpa OpenCV. Hasilnya diuji sama dengan OpenCV, termasuk untuk titik di sudut dan tepi poligon.

`zone_membership` memberi setiap titik ke poligon pertama yang memuatnya. Urutan poligon menentukan pemilik area yang tumpang tindih. `PolygonZone` tidak punya aturan itu: satu orang bisa dihitung di dua `PolygonZone` yang tumpang tindih.

## Garis

`LineCounter` menentukan sisi sebuah titik dari tanda perkalian silang antara arah garis dan posisi titik itu. Aturan ini sama dengan `LineZone` milik supervision, jadi urutan titik garis yang sama memberi arah masuk yang sama.

Dua aturan tambahan mencegah hitungan palsu:

- **Segmen, bukan garis tak terbatas.** Titik yang proyeksinya jatuh di luar kedua ujung garis diabaikan, sehingga orang yang lewat di samping garis tidak dihitung.
- **Bertahan di sisi baru.** Lintasan baru dihitung setelah track berada di sisi baru selama `minimum_frames` frame. Kotak yang bergetar tepat di garis tidak tercatat masuk dan keluar berulang kali.

Akibat aturan kedua, frame tempat lintasan dihitung sedikit lebih lambat dari saat orang itu benar-benar melewati garis.

## Hadir dan kondisi

Berada di sebuah zona belum berarti melakukan sesuatu di zona itu. Orang yang menyeberangi lorong menempati poligon yang sama dengan orang yang membaca label harga. Karena itu ada dua timer:

- `ZoneTimer` mengukur **kehadiran**: siapa berada di zona mana, dan berapa lama. Angkanya menjawab "seberapa ramai zona ini".
- `ConditionTimer` mengukur waktu saat sebuah **kondisi** benar, misalnya menghadap zona itu. Angkanya menjawab "apakah zona ini menahan perhatian orang".

Ambang `minimum_s` menentukan rentang mana yang dicatat, dan nilainya perlu diukur, bukan ditebak. Di proyek asal, ambang perhatian awalnya 5 detik. Dengan nilai itu, dua dari empat rak tidak mencatat perhatian apa pun selama 4 menit, karena setiap tatapan ke rak itu berlangsung 3 sampai 5 detik. Ambang 5 detik menyembunyikan separuh rak, bukan memisahkan orang yang melihat dari orang yang lewat, jadi proyek asal menurunkannya ke 3 detik.

## Grace dan batas kredit

Track bisa hilang beberapa frame, misalnya saat orang tertutup orang lain. Timer menangani jeda itu dengan dua aturan yang berbeda:

- **Grace** menjaga sebuah kunjungan atau rentang tetap terbuka selama jedanya pendek. Tanpa grace, track yang hilang sebentar menjadi dua kunjungan.
- **Batas kredit** membatasi berapa banyak waktu yang dihitung dari satu pengamatan: `min(2 × jarak antar frame, 0,25 × minimum_s)`. Dua pengamatan berjarak 5 detik bukan bukti 5 detik tanpa putus.

Keduanya tidak boleh disamakan: grace setahun tidak boleh menjadi setahun perhatian. Di proyek asal, menyamakan keduanya pernah menjadi bug. Satu rentang yang sama terukur 24,9 detik dengan grace sebagai batas, dan 20,6 detik dengan batas kredit, kelebihan hitung 21%.

Batas kredit sengaja diikat ke `minimum_s`. Dengan batas tetap, ambang 0,5 detik bisa terpenuhi oleh satu frame setelah track sempat hilang.

Waktu keluar sebuah kunjungan adalah saat orang itu terakhir terlihat, bukan saat grace habis.

## Membaca arah hadap

Arah kepala dibaca dari keypoint wajah: dari titik tengah telinga yang terlihat ke hidung. Masalahnya, orang yang sedang melihat rak sering membelakangi kamera, jadi wajahnya tidak terlihat.

Bahu tetap terlihat. Garis bahu `s = bahu kanan − bahu kiri` yang diputar 90 derajat, `(s.y, −s.x)`, memberi arah badan. Model pose memberi label bahu sesuai badan orangnya: saat orang menghadap kamera, bahu kanannya tampak di kiri gambar, dan saat membelakangi kamera, di kanan. Karena itu satu rumus sudah membedakan menghadap dan membelakangi, tanpa cabang `if`.

Arah badan diperiksa terhadap arah kepala pada 815 pose dari kamera dalam toko:

| Keypoint yang terlihat | Jumlah frame | Bagian |
|---|---|---|
| Kepala dan bahu | 310 | 38% |
| Hanya bahu | 494 | 61% |
| Tidak keduanya | 11 | 1% |

Tanpa arah dari bahu, 61% pose itu tidak punya arah sama sekali. Pada 310 pose dengan kepala dan bahu, selisih kedua arah bernilai tengah 58 derajat. Sebanyak 92% berselisih kurang dari 90 derajat, dan tidak ada yang berselisih lebih dari 135 derajat, yang akan terjadi jika tanda rumusnya terbalik. Arah kepala tetap didahulukan jika ada, karena kepala bergerak lepas dari badan.

`facing_target` menghitung seseorang menghadap sebuah titik jika selisih sudutnya paling banyak `cone_deg`. Kerucut itu mengubah hasilnya. Waktu perhatian dua pengunjung di rak yang sama, dengan kerucut berbeda:

| Kerucut | Pengunjung pertama | Pengunjung kedua |
|---|---|---|
| ±90° | 26,3 detik | 25,0 detik |
| ±60° | 20,6 detik | 18,6 detik |
| ±45° | 20,6 detik | 7,6 detik |
| ±30° | 19,2 detik | Tidak tercatat |

Nilai bawaannya ±90°, seluruh setengah bidang di depan orang itu. Kerucut ±60° lebih ketat dan memotong kedua angka sekitar seperempat.

## Jarak dari tinggi badan

Ambang jarak dalam piksel tidak bisa dipakai, karena orang yang jauh tampak lebih kecil. Pada 1.309 kotak orang dari kamera pintu, satu meter bernilai 55 piksel di ujung jauh lorong dan 89 piksel di dekat kasir.

`distance_m` memakai setiap orang sebagai penggarisnya sendiri. Orang dewasa tingginya sekitar 1,7 meter, jadi tinggi kotaknya mengubah piksel menjadi meter di tempat ia berdiri, tanpa file kalibrasi. Jarak diukur dari kaki ke kaki, lalu dibagi rata-rata skala kedua orang. Jarak 109 piksel di ujung jauh dan 178 piksel di dekat kasir sama-sama setara dua meter menurut ukuran orang di tempat itu, dan cara ini membacanya sebagai 1,99 dan 2,00 meter.

Harganya: jaraknya mengikuti kotak. Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh.

## Masker dan ukuran input

`masks.apply_mask` menghitamkan area sebelum frame masuk ke model. Deteksi yang tidak diinginkan tidak pernah ada, jadi tidak bisa terhitung dua kali dan tidak masuk ke tracker. Masker digambar sekali di awal, lalu setiap frame cukup satu operasi `bitwise_and`.

Ada kekhawatiran masker memotong badan orang di tepi area. Di kamera dalam toko, semua di luar poligon rak dihitamkan, dan pada 100 frame jumlah deteksi di rak tetap 200, dengan confidence rata-rata 0,732 tanpa masker dan 0,735 dengan masker.

`standardise_frame` memperkecil setiap frame ke 640 piksel di sisi terpanjang, ukuran latih model, dan satu faktor skala mengembalikan koordinatnya. Pada potongan 100 frame, kecepatannya naik dari 8,3 menjadi 13,9 frame per detik, dengan hitungan yang sama. Aturan zona dan kunjungan hanya memakan 0,33 milidetik per frame, dibandingkan 73 milidetik untuk deteksi dan 39 milidetik untuk pose. Yang layak dipercepat hanya modelnya.

## Halaman terkait

- [Mendeteksi dan melacak orang](../panduan/mendeteksi-dan-melacak-orang.md) untuk perulangan frame yang menjadi dasar semua fungsi.
- [Menghitung dengan garis dan poligon](../panduan/menghitung-dengan-garis-dan-poligon.md) dan [Mengukur durasi per orang](../panduan/mengukur-durasi.md) untuk cara memakai fungsi yang dijelaskan di sini.
- [Referensi Computer Vision](../referensi/computer-vision.md) untuk semua fungsi dan parameternya.
