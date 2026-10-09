# Cara kerja aturan perilaku di video

`zul.computer_vision` dipisahkan dari proyek analitik video sebuah toko sepatu di mal, dengan dua kamera CCTV: satu menghadap pintu, satu di dalam toko. Halaman ini menjelaskan aturan yang mengubah deteksi per frame menjadi angka seperti "berapa lama orang ini memperhatikan rak", dan alasan di balik setiap aturan.

Angka di halaman ini diukur pada rekaman kedua kamera itu. Kecuali disebut lain, angkanya berasal dari proyek asal, sebelum kodenya dipindahkan ke Zul.

## Model dan aturan terpisah

Pekerjaan setiap frame terbagi dua lapis:

- **Model** mendeteksi orang, membaca keypoint pose, dan memberi id track. Lapisan ini ada di `detection` dan butuh ultralytics.
- **Aturan** menentukan zona, arah hadap, lintasan garis, dan durasi. Lapisan ini ada di `geometry`, `pose`, `crossing`, dan `analytics`, dan hanya butuh NumPy.

Hasil model diserahkan ke aturan sebagai `Detections`, wadah array NumPy biasa. Aturan tidak tahu model apa yang dipakai, jadi mengganti model cukup dengan mengganti file bobot di `load_model`. Aturan juga bisa diuji dengan track buatan, tanpa model dan tanpa video.

Semua hitungan memakai id track, bukan jumlah kotak di setiap frame. Orang yang terlihat selama 300 frame tetap satu orang. Track yang belum dikonfirmasi dibuang. Di proyek asal, 105 dari 493 deteksi (21%) belum punya track yang dikonfirmasi, dan meloloskannya menambah satu orang palsu ke setiap hitungan.

## Satu orang, satu titik di kepala

Aturan zona menghitung orang, bukan kotak, jadi setiap orang diwakili satu titik. Titik itu ada di tengah kotak secara horizontal, 1/6 dari atas, di sekitar kepala.

Titik di kaki terdengar lebih wajar, karena kaki menyentuh lantai. Pada potongan 300 frame dari kamera dalam toko, kedua titik memberi jawaban berbeda untuk dua pengunjung yang sama. Titik kaki menempatkan mereka di lorong tempat mereka berdiri. Titik kepala menempatkan mereka di rak yang mereka hadapi dan raih. Yang ingin diukur adalah rak yang diperhatikan seseorang, jadi titik kepala yang dipakai.

Akibatnya, poligon rak harus menutupi tempat kepala pengunjung berada saat melihat rak itu, bukan hanya lantai di depannya.

## Membaca arah hadap

Arah kepala dibaca dari keypoint wajah: dari titik tengah telinga yang terlihat ke hidung.

Masalahnya, pengunjung yang sedang melihat rak biasanya membelakangi kamera di dalam toko. Wajahnya tidak terlihat, jadi tidak ada keypoint wajah. Versi pertama aturan perhatian membuang semua waktu itu, padahal itu kasus yang paling sering, bukan pengecualian.

Bahu tetap terlihat. Garis bahu `s = bahu kanan − bahu kiri` yang diputar 90 derajat, `(s.y, −s.x)`, memberi arah badan. Model pose memberi label bahu secara anatomis: saat orang menghadap kamera, bahu kanannya tampak di kiri gambar, dan saat membelakangi kamera, di kanan. Karena itu satu rumus sudah membedakan menghadap dan membelakangi, tanpa cabang `if`.

Arah badan diperiksa terhadap arah kepala pada 815 pose:

| Keypoint yang terlihat | Jumlah frame | Bagian |
|---|---|---|
| Kepala dan bahu | 310 | 38% |
| Hanya bahu, yang sebelumnya dibuang | 494 | 61% |
| Tidak keduanya | 11 | 1% |

Pada 310 pose dengan kepala dan bahu, selisih kedua arah bernilai tengah 58 derajat. Sebanyak 92% berselisih kurang dari 90 derajat, dan tidak ada yang berselisih lebih dari 135 derajat, yang akan terjadi jika tanda rumusnya terbalik. Arah kepala tetap dipakai jika ada, karena kepala bergerak lepas dari badan. Dengan arah dari bahu, waktu perhatian satu pengunjung yang membelakangi kamera sepanjang waktu naik dari 0,2 menjadi 25,0 detik.

Bahu yang jaraknya kurang dari 4 piksel tidak memberi arah, karena orang yang terlihat dari samping tidak punya garis bahu yang jelas.

## Kerucut menghadap

Seseorang dihitung menghadap sebuah target jika arah hadapnya, diukur dari titik kepala, berselisih paling banyak `FACING_CONE_DEG` dari arah ke target. Kerucut 90 derajat berarti seluruh setengah bidang di depan orang itu.

Kerucut itu menentukan hasilnya. Waktu perhatian dua pengunjung di rak yang sama, dengan kerucut berbeda:

| Kerucut | Pengunjung pertama | Pengunjung kedua |
|---|---|---|
| ±90° | 26,3 detik | 25,0 detik |
| ±60° | 20,6 detik | 18,6 detik |
| ±45° | 20,6 detik | 7,6 detik |
| ±30° | 19,2 detik | Tidak tercatat |

Kerucut ±60° bisa dibela dan memotong kedua angka sekitar seperempat. Proyek asal memakai ±90° supaya sama dengan aturan kamera pintu, bukan karena 90 derajat pasti benar.

## Kehadiran bukan perhatian

Berdiri di dekat rak belum berarti memperhatikannya. Orang yang menyeberangi lorong menempati poligon yang sama dengan orang yang membaca label harga. Karena itu ada dua pelacak:

- `ZoneVisitTracker` mencatat **kehadiran**: siapa berdiri di zona mana, dan berapa lama. Angkanya menjawab "seberapa ramai rak ini".
- `AttentionTracker` mencatat **perhatian**: waktu bertambah hanya saat orang itu berada di zona dan menghadap target zonanya. Angkanya menjawab "apakah rak ini menahan perhatian orang".

Target sebuah zona adalah titik tengah poligonnya, kecuali `POLYGON_ANCHORS` diisi. Titik tengah hanya tepat jika poligon menutupi rak itu sendiri.

Sebuah rentang perhatian dicatat setelah waktu menghadapnya mencapai ambang, yaitu 3 detik. Ambang awalnya 5 detik. Dengan nilai itu, dua dari empat rak tidak mencatat perhatian apa pun selama 4 menit, karena setiap tatapan ke rak itu berlangsung 3 sampai 5 detik. Ambang 5 detik menyembunyikan separuh rak, bukan memisahkan orang yang melihat dari orang yang lewat.

## Grace dan batas kredit

Track bisa hilang sebentar, misalnya saat orang tertutup orang lain. Dua aturan yang berbeda menangani jeda itu:

- **Grace** menjaga sebuah kunjungan atau rentang tetap terbuka selama jedanya pendek, bawaannya 1 detik. Tanpa grace, track yang hilang sebentar menjadi dua kunjungan.
- **Batas kredit** membatasi berapa banyak waktu yang dihitung dari satu pengamatan: `min(2 × jarak antar frame, 0,25 × ambang)`. Dua pengamatan berjarak 5 detik bukan bukti 5 detik menghadap tanpa putus.

Keduanya tidak boleh disamakan: grace setahun tidak boleh menjadi setahun perhatian. Di proyek asal, menyamakan keduanya pernah menjadi bug. Satu rentang yang sama terukur 24,9 detik dengan grace sebagai batas, dan 20,6 detik dengan batas kredit, kelebihan hitung 21%.

Batas kredit sengaja diikat ke ambang. Dengan batas tetap, ambang 0,5 detik bisa terpenuhi oleh satu frame setelah track sempat hilang.

Waktu keluar sebuah kunjungan adalah saat orang itu terakhir terlihat, bukan saat grace habis.

## Minat dan garis pintu

Di kamera pintu, seseorang dihitung berminat setelah tiga syarat terpenuhi bersamaan selama 2 detik:

1. Titik kepalanya ada di area depan toko. Waktu di luar area itu tidak dihitung sama sekali.
2. Wajahnya terlihat, yaitu arah kepalanya terbaca dari keypoint wajah.
3. Kepalanya menghadap titik tengah garis pintu, dalam kerucut ±90°.

Syarat ketiga tidak berlebihan. Kamera berada di samping etalase, jadi orang yang berjalan menjauhi toko tetap memperlihatkan wajahnya. Wajah yang terlihat berarti "kepala orang ini terlihat", bukan "orang ini melihat ke dalam toko".

Garis pintu menentukan hasilnya. Sisi sebuah titik dihitung dari tanda perkalian silang arah garis dengan posisi titik itu, aturan yang sama dengan `LineZone` milik supervision. Garisnya berupa segmen, jadi orang yang lewat di samping ujung garis tidak dihitung. Sebuah lintasan baru dihitung setelah orang itu bertahan di sisi baru selama `MIN_CROSSING_FRAMES` frame, jadi kotak yang bergetar di garis tidak tercatat masuk dan keluar berulang kali.

Hasil yang sudah diberikan tidak pernah turun. `passed_by` bisa berubah menjadi `entered` saat orang itu masuk kemudian, tetapi `entered` tidak pernah kembali menjadi `passed_by`. Label di video dan baris di CSV membaca angka yang sama, jadi keduanya selalu cocok.

## Jarak dalam meter tanpa kalibrasi

`proximity_pairs` mengukur jarak antara dua orang dalam meter, misalnya staf dengan pelanggan. Ambang dalam piksel tidak bisa dipakai, karena orang yang jauh tampak lebih kecil. Pada 1.309 kotak orang dari kamera pintu, satu meter bernilai 55 piksel di ujung jauh lorong dan 89 piksel di dekat kasir. Dua meter berarti 109 piksel di ujung jauh, tetapi 178 piksel di dekat kasir.

Setiap orang menjadi penggarisnya sendiri. Orang dewasa tingginya sekitar 1,7 meter, jadi tinggi kotaknya mengubah piksel menjadi meter di tempat ia berdiri, tanpa file kalibrasi. Jarak diukur dari kaki ke kaki, lalu dibagi rata-rata skala kedua orang. Untuk jarak dua meter yang sebenarnya, cara ini memberi 1,99 meter di ujung jauh dan 2,00 meter di dekat kasir.

Harganya: jaraknya mengikuti kotak. Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh. Angka ini perkiraan.

`ProximityLog` mencatat setiap staf begitu terlihat, ada kontak atau tidak. Staf dengan nol kontak tetap masuk ke penyebut rata-rata. Untuk tiga staf dengan 5, 4, dan 0 kontak, rata-ratanya `(5 + 4 + 0) / 3 = 3,0`. Tanpa staf ketiga, rata-ratanya 4,5, dan angka itu mengukur hal lain.

Modul ini tidak menentukan siapa staf. Di proyek asal, YOLO-World dengan teks "person wearing a red apron" ternyata mendeteksi pakaian merah, bukan celemek, dengan confidence rata-rata 0,271. Isi `is_subject` dengan sumber yang bisa dipercaya, misalnya model yang dilatih dengan seragam toko itu.

## Masker dan ukuran input

Area yang tidak diukur dihitamkan sebelum frame masuk ke model. Deteksi yang tidak diinginkan tidak pernah ada, jadi tidak bisa terhitung dua kali dan tidak masuk ke tracker. Masker digambar sekali di awal, lalu setiap frame cukup satu operasi `bitwise_and`.

Di kamera dalam toko, semua di luar poligon rak dihitamkan. Ada kekhawatiran masker memotong badan orang di tepi rak. Pada 100 frame, jumlah deteksi di rak tetap 200, dengan confidence rata-rata 0,732 tanpa masker dan 0,735 dengan masker. Kamera pintu tidak menghitamkan area di luar lorong, karena orang yang lewat tanpa masuk justru yang diukur. Di kamera itu, hanya area yang memang diabaikan yang dihitamkan.

Setiap frame juga diperkecil ke 640 piksel di sisi terpanjang, ukuran latih model, dan satu faktor skala mengembalikan koordinatnya. Pada potongan 100 frame, kecepatannya naik dari 8,3 menjadi 13,9 frame per detik, dengan hitungan yang sama. Aturan zona dan kunjungan hanya memakan 0,33 milidetik per frame, dibandingkan 73 milidetik untuk deteksi dan 39 milidetik untuk pose. Yang layak dipercepat hanya modelnya.

## Perbedaan dengan proyek asal

Proyek asal mendeteksi orang dengan YOLO-World, membaca pose dengan model pose terpisah, lalu memasangkan keduanya lewat posisi hidung. Tracking-nya memakai ByteTrack dari paket `trackers`, dan zona serta garisnya memakai supervision.

Di Zul, panduan memakai satu model pose untuk kotak dan keypoint sekaligus, ByteTrack dari ultralytics, dan hitungan poligon dengan NumPy. Hitungan poligon itu diuji sama dengan `cv2.pointPolygonTest`, termasuk untuk titik di sudut dan tepi poligon. Script di kedua panduan memberi hasil berikut pada potongan video yang sama dengan proyek asal:

| Potongan | Proyek asal | Zul |
|---|---|---|
| Dalam toko, frame 1000-2500, rak `shelf_d` | 2 orang: 26,3 dari 29,8 detik, dan 24,8 dari 37,7 detik | 2 orang: 26,9 dari 30,0 detik, dan 25,8 dari 37,8 detik |
| Pintu, frame 5200-6300 | 2 orang masuk, melintas pada detik 184,133 dan 188,533 | 3 orang masuk, melintas pada detik 184,133, 186,133, dan 188,533 |

Id track-nya berbeda karena tracker-nya berbeda. Di dalam toko, kedua orang dan waktu perhatiannya cocok dalam selisih sekitar 1 detik. Di pintu, dua lintasan tercatat pada detik yang persis sama. Orang ketiga hanya terhitung di Zul. Di video beranotasi, ia terlihat berjalan masuk ke toko.

## Halaman terkait

- [Mengukur perhatian pengunjung ke rak](../panduan/mengukur-perhatian-ke-rak.md) untuk script lengkap kamera dalam toko.
- [Menghitung pengunjung yang berminat dan masuk](../panduan/menghitung-pengunjung-masuk.md) untuk script lengkap kamera pintu.
- [Referensi Computer Vision](../referensi/computer-vision.md) untuk semua fungsi dan parameternya.
