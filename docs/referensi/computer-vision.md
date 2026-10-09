# Computer Vision

Fungsi-fungsi di `zul.computer_vision` untuk video: deteksi dan tracking, garis dan poligon penghitung, timer, arah hadap, jarak, gambar, dan masker. Setiap fungsi mengerjakan satu hal dan bisa dirangkai sendiri. Cara memakainya ada di panduan, mulai dari [Mendeteksi dan melacak orang](../panduan/mendeteksi-dan-melacak-orang.md), dan alasan di balik rancangannya ada di [Cara kerja Computer Vision](../konsep/cara-kerja-computer-vision.md).

Tabel berikut memetakan setiap modul ke isinya dan extra yang dibutuhkan:

| Modul | Isi | Extra |
|---|---|---|
| [`geometry`](#geometry) | Titik jangkar kotak, poligon, zona, dan arah. | Tidak ada |
| [`pose`](#pose) | Arah kepala dan badan dari keypoint COCO-17. | Tidak ada |
| [`zones`](#zones) | Poligon penghitung dan garis penghitung. | Tidak ada |
| [`timers`](#timers) | Lama di zona dan lama sebuah kondisi benar. | Tidak ada |
| [`distance`](#distance) | Jarak dalam meter dan lama dua orang berdekatan. | Tidak ada |
| [`config`](#config) | Config dari YAML dan validasinya. | Tidak ada |
| [`report`](#report) | CSV dengan satu baris per catatan. | Tidak ada |
| [`draw`](#draw) | Teks di sudut, kotak, bentuk, kerangka, garis dan poligon penghitung, jejak, dan heatmap. | `vision` |
| [`masks`](#masks) | Menghitamkan area, blur, dan pixelate. | `vision` |
| [`video`](#video) | Membaca dan menulis video, dan mengukur kecepatan. | `vision` |
| [`tracking`](#tracking) | ByteTrack: id yang sama untuk orang yang sama di setiap frame. | `tracking` |
| [`detection`](#detection) | Model RF-DETR: kotak orang dan 17 keypoint, atau kotak 80 kelas COCO. | `detection` |
| [`weights`](#weights) | Mengunduh bobot model ke folder proyek. | `detection` |

Modul tanpa extra hanya mengimpor NumPy dan PyYAML, yang ada di instalasi dasar Zul. Mengimpor `zul.computer_vision` tidak memuat modul apa pun, jadi OpenCV dan RF-DETR baru dimuat saat modul yang membutuhkannya diimpor.

Modul-modul ini tidak mengimpor OpenCV, RF-DETR, lap, atau PyYAML sendiri. Semuanya dipakai lewat `zul.adapters.opencv`, `zul.adapters.rfdetr`, `zul.adapters.lap`, dan `zul.adapters.yaml`. Alasannya ada di [Lapisan adapter](../konsep/lapisan-adapter.md).

Semua koordinat memakai sistem gambar: x ke kanan, y ke bawah, dalam piksel frame asli. Kotak selalu berformat xyxy: `(x1, y1, x2, y2)`. Waktu selalu dalam detik dari awal video, dan nomor frame adalah nomor frame di video sumber.

## geometry

Lokasi: `zul.computer_vision.geometry`. Hanya membutuhkan NumPy.

### Kotak

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `box_anchor(xyxy, ratio=0.5)` | `ndarray (2,)` | Titik di tengah horizontal kotak, `ratio` dari atas. `ratio=1/6` jatuh di sekitar kepala, `ratio=1` di kaki. |
| `box_anchors(boxes, ratio=0.5)` | `ndarray (n, 2)` | `box_anchor` untuk setiap baris array `(n, 4)`. |
| `foot_points(boxes)` | `ndarray (n, 2)` | Titik tengah bawah setiap kotak. |
| `box_heights(boxes)` | `ndarray (n,)` | Tinggi setiap kotak dalam piksel. |
| `shrink_to_point(points, size=1.0)` | `ndarray (n, 4)` | Kotak selebar `2 × size` di sekeliling setiap titik, untuk alat yang hanya menerima kotak. |

### Poligon dan zona

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `as_polygon(polygon)` | `ndarray (n, 2)` float | Poligon dari list atau array apa pun. |
| `as_polygon_list(value)` | `list[ndarray]` int32 | Satu poligon atau daftar poligon, misalnya dari config, sebagai daftar poligon. Poligon dengan kurang dari 3 titik dibuang. `None` atau list kosong menjadi `[]`. |
| `polygon_centroid(polygon)` | `ndarray (2,)` | Rata-rata titik sudut poligon. |
| `points_in_polygon(polygon, points)` | `ndarray (n,)` bool | Apakah setiap titik ada di dalam poligon. Titik tepat di tepi dihitung di dalam, sama dengan `cv2.pointPolygonTest(...) >= 0`. Poligon dengan kurang dari 3 titik memberi semua `False`. |
| `point_in_polygon(polygon, point)` | `bool` | `points_in_polygon` untuk satu titik. |
| `zone_membership(polygons, points)` | `ndarray (n,)` int | Indeks poligon pertama yang memuat setiap titik, atau `-1` di luar semua poligon. Titik di area yang tumpang tindih masuk ke poligon yang ditulis lebih dulu. |
| `count_per_zone(zone_count, membership)` | `list[int]` | Jumlah titik per zona dari hasil `zone_membership`. |
| `line_midpoint(points)` | `ndarray (2,)` atau `None` | Titik tengah garis dua titik. `None` jika `points` berisi kurang dari dua titik. |

### Arah

Arah adalah vektor satuan di sistem koordinat gambar.

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `unit(vector)` | `ndarray` atau `None` | Vektor dengan panjang 1. `None` jika panjangnya di bawah `EPSILON` (`1e-6`). |
| `angle_between(first, second)` | `float` | Sudut antara dua vektor dalam derajat, 0 sampai 180. `NaN` jika salah satunya vektor nol. |
| `points_toward(direction, origin, target, cone_deg=90.0)` | `bool` | True jika sudut antara `direction` dan arah dari `origin` ke `target` paling besar `cone_deg`. `False` jika `direction` bernilai `None`. `True` jika `origin` sama dengan `target`. |
| `euclidean(first, second)` | `float` | Jarak garis lurus antara dua titik. |
| `direction_angle(direction)` | `float` atau `None` | Sudut arah dalam derajat: 0 ke kanan, 90 ke bawah, 180 ke kiri. |

## pose

Lokasi: `zul.computer_vision.pose`. Hanya membutuhkan NumPy.

Fungsi di modul ini membaca keypoint COCO-17 dari model pose, misalnya model keypoint RF-DETR: `xy` berbentuk `(17, 2)` per orang dan `confidence` berbentuk `(17,)`. Keypoint dengan confidence di bawah `min_confidence` dianggap tidak terlihat. `confidence=None` berarti semua keypoint terlihat.

### Konstanta

| Nama | Nilai | Keterangan |
|---|---|---|
| `NOSE`, `LEFT_EYE`, `RIGHT_EYE`, `LEFT_EAR`, `RIGHT_EAR` | `0` sampai `4` | Indeks keypoint wajah. |
| `LEFT_SHOULDER`, `RIGHT_SHOULDER` | `5`, `6` | Indeks keypoint bahu. |
| `FACE_KEYPOINTS` | `(0, 1, 2, 3, 4)` | Kelima keypoint wajah. |
| `SKELETON_EDGES` | 19 pasangan indeks | Garis kerangka yang digambar `draw.draw_skeleton`. |
| `DEFAULT_MIN_CONFIDENCE` | `0.35` | Nilai bawaan `min_confidence`. |
| `DEFAULT_MIN_SHOULDER_SPAN_PX` | `4.0` | Nilai bawaan `min_shoulder_span_px`. |
| `DEFAULT_ANCHOR_RATIO` | `1/6` | Nilai bawaan `anchor_ratio`: titik kepala. |

### Arah satu orang

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `face_direction(xy, confidence=None, min_confidence=0.35)` | `ndarray (2,)` atau `None` | Arah kepala: dari titik tengah telinga yang terlihat ke hidung. `None` jika hidung atau kedua telinga tidak terlihat. |
| `body_direction(xy, confidence=None, min_confidence=0.35, min_shoulder_span_px=4.0)` | `ndarray (2,)` atau `None` | Arah badan: garis bahu `s = kanan − kiri` diputar 90 derajat menjadi `(s.y, −s.x)`. `None` jika salah satu bahu tidak terlihat, atau jarak kedua bahu di bawah `min_shoulder_span_px`. |
| `facing_direction(xy, confidence=None, min_confidence=0.35, min_shoulder_span_px=4.0)` | `(ndarray atau None, str)` | Arah kepala jika ada, selain itu arah badan. Sumbernya `"head"`, `"body"`, atau `""` jika keduanya tidak ada. |
| `face_box(xy, confidence=None, min_confidence=0.35)` | `ndarray (4,)` atau `None` | Kotak xyxy di sekeliling keypoint wajah yang terlihat. `None` jika kurang dari dua yang terlihat. |

### Arah semua orang di satu frame

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `facing_directions(keypoints_xy, keypoints_conf=None, min_confidence=0.35, min_shoulder_span_px=4.0)` | `(list, list[str])` | `facing_direction` untuk setiap orang di array `(n, 17, 2)`. `keypoints_xy=None` memberi `([], [])`. |
| `facing_target(boxes, directions, target, cone_deg=90.0, anchor_ratio=1/6)` | `list[bool]` | Apakah arah setiap orang, diukur dari titik kepalanya, menunjuk ke satu `target`. `target=None` memberi semua `False`. |
| `zone_targets(polygons, anchors=None)` | `list[ndarray]` | Titik yang harus dihadapi per zona: `anchors` jika jumlahnya sama dengan jumlah poligon, selain itu centroid setiap poligon. |
| `facing_zone_targets(boxes, directions, membership, targets, cone_deg=90.0, anchor_ratio=1/6)` | `list[bool]` | Apakah setiap orang menghadap target zona tempat ia berada. `False` untuk orang di luar semua zona (`-1`) atau tanpa arah. |

### Pose dari model lain

Saat orang dideteksi oleh satu model dan pose oleh model lain, pasangkan keduanya dengan fungsi berikut:

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `match_poses_to_boxes(boxes, keypoints_xy)` | `dict[int, int]` | Indeks kotak ke indeks pose, untuk kotak yang memuat hidung pose itu. Setiap pose dipasangkan sekali, ke kotak pertama yang memuatnya. |
| `by_box(pairing, values, count, empty=None)` | `list` | Nilai per pose disusun ulang menjadi per kotak, sepanjang `count`. Kotak tanpa pose mendapat `empty`. |

## zones

Lokasi: `zul.computer_vision.zones`. Hanya membutuhkan NumPy.

Kedua kelas menerima satu titik per orang, misalnya dari `geometry.box_anchors`, dan id track-nya. Gambar keduanya dengan [`draw_polygon_zone` dan `draw_line_counter`](#garis-dan-poligon-penghitung).

### `PolygonZone(polygon, label="")`

Satu poligon yang menghitung orang di dalamnya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `polygon` | list titik atau array `(n, 2)` | Wajib | Titik sudut poligon dalam piksel. Melempar `ValueError` jika kurang dari 3 titik. |
| `label` | `str` | `""` | Nama poligon, ditulis oleh `draw_polygon_zone`. |

| Anggota | Keterangan |
|---|---|
| `update(points, tracker_ids=None)` | Maju satu frame. Mengembalikan array bool per baris: apakah titiknya di dalam poligon. Tanpa `tracker_ids`, hanya `current_count` yang diperbarui. |
| `contains(points)` | Array bool per titik, tanpa mengubah hitungan. Titik tepat di tepi dihitung di dalam. |
| `current_count` | Jumlah titik di dalam poligon pada `update` terakhir. |
| `total_count` | Jumlah id track berbeda yang pernah di dalam poligon. |
| `centroid` | Rata-rata titik sudut poligon. |
| `polygon`, `label` | Sesuai parameter. `polygon` disimpan sebagai array int32. |

### `LineCounter(start, end, minimum_frames=3, label="")`

Satu segmen garis yang menghitung lintasan masuk dan keluar per track.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `start`, `end` | `(x, y)` | Wajib | Kedua ujung garis. Sisi kiri saat berjalan dari `start` ke `end` di gambar adalah sisi masuk. Melempar `ValueError` jika keduanya sama. |
| `minimum_frames` | `int` | `3` | Jumlah frame sebuah track harus berada di sisi baru sebelum lintasannya dihitung. |
| `label` | `str` | `""` | Nama garis, ditulis oleh `draw_line_counter`. |

Titik yang proyeksinya jatuh di luar kedua ujung garis diabaikan. Aturan sisinya sama dengan `LineZone` milik supervision.

| Anggota | Keterangan |
|---|---|
| `update(points, tracker_ids)` | Maju satu frame. Mengembalikan `(crossed_in, crossed_out)`: dua `list[bool]`, satu nilai per baris, True di frame saat lintasan baris itu dihitung. `tracker_ids=None` tidak menghitung apa pun. |
| `sides(points)` | `(inside, in_band)`: dua array bool, apakah setiap titik di sisi masuk dan apakah di rentang segmen. |
| `in_count`, `out_count` | Jumlah lintasan masuk dan keluar sejauh ini. |
| `midpoint` | Titik tengah garis, misalnya target arah hadap. |
| `in_normal` | Vektor satuan tegak lurus garis, menunjuk ke sisi masuk. |

## timers

Lokasi: `zul.computer_vision.timers`. Tidak membutuhkan library di luar Python.

Timer menerima id track dan hasil uji per frame, lalu mengembalikan catatan dengan awal, akhir, dan durasi. `tracker_ids=None` dianggap frame tanpa orang. Waktu dalam detik dari awal video.

### Catatan

Semua catatan adalah dataclass. Kolom berakhiran `_s` dalam detik.

| Kelas | Field | Property |
|---|---|---|
| `ZoneVisit` | `visit_id`, `track_id`, `zone_index`, `zone_name`, `enter_frame`, `enter_time_s`, `exit_frame`, `exit_time_s` | `duration_s` |
| `Spell` | `spell_id`, `track_id`, `group`, `group_name`, `start_frame`, `start_time_s`, `end_frame`, `end_time_s`, `active_s` | `span_s`: lama track terlihat, termasuk saat kondisinya tidak benar |

### `ZoneTimer(zone_labels, grace_s=1.0)`

Mengubah keanggotaan zona per frame menjadi kunjungan.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `zone_labels` | `list[str]` | Wajib | Nama zona, urut sesuai indeks zona. |
| `grace_s` | `float` | `1.0` | Kunjungan ditutup jika track tidak terlihat di zona selama `grace_s` detik atau lebih. |

Kunjungan juga ditutup seketika saat track pindah ke zona lain. Waktu keluar adalah saat track terakhir terlihat.

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `update(frame_number, timestamp_s, tracker_ids, membership)` | `list[ZoneVisit]` | Maju satu frame. `membership` berisi indeks zona per baris, `-1` di luar semua zona, misalnya dari `geometry.zone_membership`. Mengembalikan kunjungan yang selesai di frame ini. |
| `close_all()` | `list[ZoneVisit]` | Menutup semua kunjungan yang masih terbuka, di akhir video. |
| `dwell_s(track_id, timestamp_s)` | `float` atau `None` | Lama track di zonanya sekarang. |
| `zone_of(track_id)` | `int` atau `None` | Zona track sekarang. |
| `unique_visitors(zone_index)` | `int` | Jumlah id track berbeda yang pernah di zona itu. |
| `visit_count(zone_index)` | `int` | Jumlah kunjungan ke zona itu, termasuk yang masih terbuka. |

Atribut `completed` berisi semua kunjungan yang sudah ditutup.

### `ConditionTimer(minimum_s=0.0, grace_s=1.0, frame_period_s=1/30, max_gap_frame_periods=2, max_gap_threshold_fraction=0.25, group_labels=None)`

Mencatat berapa lama sebuah kondisi benar untuk setiap track, per grup jika `groups` diisi.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `minimum_s` | `float` | `0.0` | Waktu aktif minimum agar sebuah rentang dicatat. |
| `grace_s` | `float` | `1.0` | Rentang ditutup jika track tidak terlihat lebih dari `grace_s` detik. |
| `frame_period_s` | `float` | `1/30` | Jarak waktu antar frame yang diproses, yaitu `stride / fps`. |
| `max_gap_frame_periods` | `int` | `2` | Bagian pertama batas kredit, dalam kelipatan `frame_period_s`. |
| `max_gap_threshold_fraction` | `float` | `0.25` | Bagian kedua batas kredit, dalam pecahan `minimum_s`. Tidak dipakai jika `minimum_s` bernilai 0. |
| `group_labels` | `list[str]` atau `None` | `None` | Nama grup untuk `Spell.group_name`, urut sesuai indeks grup. |

Satu track di satu grup adalah satu rentang, dibuka saat track itu pertama terlihat. Setiap frame saat kondisinya benar menambah waktu sejak frame aktif sebelumnya, paling banyak `credit_cap_s`. Rentang dengan `active_s` di bawah `minimum_s` dibuang saat ditutup.

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `update(frame_number, timestamp_s, tracker_ids, active, groups=None)` | `list[Spell]` | Maju satu frame. `active` berisi hasil kondisi per baris. `groups`, misalnya indeks zona, memisahkan rentang per grup; baris dengan grup `-1` dilewati. Mengembalikan rentang yang ditutup di frame ini dan mencapai `minimum_s`. |
| `close_all()` | `list[Spell]` | Menutup semua rentang yang masih terbuka, di akhir video. |
| `active_s(track_id, group=None)` | `float` | Waktu aktif rentang yang sedang terbuka. |
| `reached(track_id, group=None)` | `bool` | Apakah track itu sudah mencapai `minimum_s`, di rentang terbuka atau yang sudah dicatat. |
| `count(group=None)` | `int` | Jumlah rentang yang sudah dicatat. `group=None` berarti semua grup. |
| `qualified(group=None)` | `int` | `count`, ditambah rentang terbuka yang sudah mencapai `minimum_s`. |
| `people(group=None)` | `int` | Jumlah id track berbeda dengan rentang yang dicatat. |
| `seconds(group=None)` | `float` | Total `active_s` rentang yang dicatat. |

Atribut `completed` berisi semua rentang yang dicatat, dan `credit_cap_s` berisi batas kredit.

### `credit_cap(frame_period_s, threshold_s, periods, fraction)`

Mengembalikan waktu maksimum yang dihitung dari satu jeda antar pengamatan: `min(periods × frame_period_s, fraction × threshold_s)`. `ConditionTimer` memakainya untuk `credit_cap_s`.

## distance

Lokasi: `zul.computer_vision.distance`. Hanya membutuhkan NumPy.

Jarak diukur dari kaki ke kaki, lalu dibagi rata-rata skala kedua orang. Skala satu orang adalah tinggi kotaknya dibagi `person_height_m`. Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh.

| Nama | Mengembalikan | Keterangan |
|---|---|---|
| `DEFAULT_PERSON_HEIGHT_M` | `1.7` | Tinggi orang dewasa yang dipakai sebagai penggaris. |
| `pixels_per_metre(boxes, person_height_m=1.7)` | `ndarray (n,)` | Jumlah piksel per meter di tempat setiap orang berdiri. |
| `distance_m(first_box, second_box, person_height_m=1.7)` | `float` | Jarak antara dua orang dalam meter. `NaN` jika kedua kotak tidak punya tinggi. |
| `pairs_within(boxes, max_distance_m=2.0, first=None, second=None, person_height_m=1.7)` | `list[(int, int, float)]` | `(baris_a, baris_b, meter)` untuk setiap pasangan yang jaraknya paling jauh `max_distance_m`. Tanpa `first` dan `second`, setiap pasangan muncul sekali dengan `baris_a < baris_b`. Dengan keduanya, berupa mask bool, `baris_a` dari `first` dan `baris_b` dari `second`. |

### `PairTimer(minimum_s=1.0, grace_s=1.0, ordered=False)`

Mengubah pasangan dari `pairs_within` per frame menjadi kontak.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `minimum_s` | `float` | `1.0` | Durasi minimum agar sebuah kontak dicatat. `0` mencatat setiap pertemuan. |
| `grace_s` | `float` | `1.0` | Kontak ditutup jika pasangan itu tidak berdekatan lebih dari `grace_s` detik. |
| `ordered` | `bool` | `False` | Dengan `False`, pasangan (a, b) dan (b, a) adalah kontak yang sama, dengan id terkecil di `first_id`. Dengan `True`, urutannya dipertahankan, misalnya staf selalu di `first_id`. |

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `update(frame_number, timestamp_s, tracker_ids, pairs)` | `list[Contact]` | Membuka atau memperpanjang kontak untuk setiap pasangan. Mengembalikan kontak yang ditutup di frame ini dan memenuhi `minimum_s`. |
| `close_all()` | `list[Contact]` | Menutup semua kontak yang masih terbuka. |
| `contacts_per_track()` | `dict[int, int]` | Jumlah kontak tercatat per id track, dihitung dari kedua sisi pasangan. |

`Contact` adalah dataclass dengan field `contact_id`, `first_id`, `second_id`, `start_frame`, `start_time_s`, `end_frame`, `end_time_s`, dan `closest_m`, jarak terdekat selama kontak, serta property `duration_s`. Atribut `completed` berisi semua kontak yang dicatat.

## config

Lokasi: `zul.computer_vision.config`. Membutuhkan PyYAML, yang ada di instalasi dasar.

Satu scene terdiri dari file dasar dan file per kamera. Kunci di luar `settings:` adalah geometri scene, misalnya `POLYGON`. Blok `settings:` berisi pengaturan aturan.

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `load_scene(base_path, scene_path=None)` | `dict` | `read_yaml` untuk kedua file, lalu `merge_scene`. |
| `read_yaml(path)` | `dict` | Isi satu file YAML. File yang tidak ada menjadi `{}`. |
| `merge_scene(base, scene)` | `dict` | Kunci `scene` menimpa kunci `base`. Blok `settings` digabung per nama. Kunci `"overrides"` berisi nama pengaturan dasar yang ditimpa, urut abjad. |
| `validate_settings(settings, *groups)` | `dict[str, Any]` | Nilai setiap pengaturan yang dideklarasikan dataclass di `groups`, setelah diperiksa. |
| `first_present(config, *keys)` | Nilai atau `None` | Nilai kunci pertama yang terisi, untuk kunci yang punya lebih dari satu nama. |
| `changed_settings(base, current)` | `list[str]` | Baris `NAMA: lama -> baru` untuk setiap pengaturan yang berbeda dari `base`. |

`validate_settings` melempar `ConfigError` dalam kasus berikut:

- Ada kunci yang tidak dideklarasikan. Pesannya menyebut nama terdekat, misalnya `CONFIDENSE (maksudnya CONFIDENCE?)`.
- Ada pengaturan yang dideklarasikan tetapi belum diisi. Pesannya menyebut nama dataclass-nya.
- Tipe nilai berbeda dari deklarasi. Nilai `int` diterima untuk `float` dan diubah menjadi `float`, tetapi `bool` tidak. Untuk tipe generik seperti `list[str]`, hanya `list`-nya yang diperiksa.

`read_yaml` melempar `ConfigError` jika YAML tidak valid, dengan nomor barisnya, atau jika isinya bukan mapping. `ConfigError` adalah turunan `ValueError`.

## report

Lokasi: `zul.computer_vision.report`. Tidak membutuhkan library di luar Python.

### `RecordWriter(path, columns)`

Menulis catatan ke CSV, satu baris per catatan.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `path` | `str` atau `Path` | File CSV. Foldernya dibuat jika belum ada. |
| `columns` | `list[str]` atau kelas dataclass | Nama kolom, berupa field atau property catatan. Dengan kelas dataclass, kolomnya adalah semua field kelas itu. |

Pakai `RecordWriter` dengan `with`. Header ditulis saat file dibuka, jadi video tanpa kejadian tetap menghasilkan CSV dengan header.

| Anggota | Keterangan |
|---|---|
| `write(records)` | Menulis setiap catatan sebagai satu baris, lalu menyimpan file ke disk. Kolom yang tidak ada di catatan dan nilai `None` menjadi sel kosong. Angka desimal dibulatkan ke 3 angka di belakang koma. Melempar `RuntimeError` jika dipanggil di luar `with`. |
| `rows` | Jumlah baris yang sudah ditulis. |

## draw

Lokasi: `zul.computer_vision.draw`. Membutuhkan extra `vision`.

Warna ditulis sebagai string `"#RRGGBB"` atau tuple BGR. Semua fungsi `draw_*` menggambar langsung di `scene` dan mengembalikan `scene` yang sama.

### Warna dan teks

| Fungsi | Keterangan |
|---|---|
| `bgr(color)` | Warna sebagai tuple BGR untuk OpenCV. |
| `track_color(track_id, saturation=0.85)` | Warna BGR yang tetap untuk satu id track. Id yang berdekatan mendapat warna yang jauh berbeda. |
| `text_size(text, scale=0.5, thickness=1)` | Lebar dan tinggi teks dalam piksel. |
| `draw_text(scene, text, origin, color=(255, 255, 255), scale=0.55, thickness=1)` | Teks tanpa latar. `origin` adalah titik kiri garis dasar teks. |
| `draw_corner_text(scene, lines, corner=Corner.TOP_LEFT, color=(255, 255, 255), scale=0.55, thickness=1, margin=12, line_height=26, top=None, background=(0, 0, 0))` | Beberapa baris teks menempel ke satu sudut frame. `Corner` berisi `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, dan `BOTTOM_RIGHT`. `top` menggeser baris pertama di sudut atas ke bawah, misalnya agar tidak menutupi cap waktu video CCTV. `background=None` menggambar teks tanpa latar. |

### Kotak dan label

| Fungsi | Keterangan |
|---|---|
| `draw_box(scene, xyxy, color, style=BoxStyle.CORNER, thickness=2, corner_length=14, fill_alpha=0.25, dash=8)` | Satu kotak. `BoxStyle` berisi `CORNER`, `RECT`, `DASHED`, dan `FILLED`. |
| `draw_label(scene, text, anchor, color, text_color=(0, 0, 0), scale=0.4, thickness=1, padding=2, above=True)` | Teks di atas pelat berwarna. `anchor` adalah sudut kiri bawah pelat, atau sudut kiri atasnya jika `above=False`. |
| `draw_labelled_box(scene, xyxy, label, color, style=BoxStyle.CORNER, **box_options)` | Kotak dan keterangannya di atas sudut kiri atas. |

### Bentuk

| Fungsi | Keterangan |
|---|---|
| `draw_polygons(scene, polygons, color, thickness=2, fill_alpha=0.0)` | Garis tepi beberapa poligon, dengan isi transparan jika `fill_alpha` di atas 0. |
| `draw_line(scene, start, end, color, thickness=2)` | Satu garis. |
| `draw_arrow(scene, origin, direction, color, length, thickness=2, tip_ratio=0.35)` | Panah sepanjang `length` piksel dari `origin` searah `direction`. |
| `draw_point(scene, point, color, radius=4)` | Satu titik penuh. |
| `draw_link(scene, start, end, color, label="", thickness=2, scale=0.45)` | Garis antara dua titik, dengan keterangan berpelat di tengahnya, misalnya jarak dalam meter. |
| `draw_skeleton(scene, keypoints_xy, keypoints_conf=None, min_confidence=0.35, color="#E0E0E0", vertex_color="#FFFFFF", thickness=1, radius=3)` | Kerangka pose untuk setiap orang, hanya dari keypoint dengan confidence cukup. `keypoints_xy=None` tidak menggambar apa pun. |

### Garis dan poligon penghitung

| Fungsi | Keterangan |
|---|---|
| `draw_line_counter(scene, counter, color="#FF4081", thickness=2, in_text="masuk", out_text="keluar", scale=0.5, arrow_length=30.0)` | Garis `LineCounter`, panah ke sisi masuk di tengah garis, dan jumlah lintasan di sisi keluar, diawali label garis jika ada. |
| `draw_polygon_zone(scene, zone, color="#00d4ff", thickness=2, fill_alpha=0.2, text=None, scale=0.5)` | Poligon `PolygonZone` dan keterangannya di tengah poligon. Tanpa `text`, isinya `current_count` dan `total_count`, diawali label poligon jika ada. |

### Jejak dan heatmap

`TrackTrace(length=40)` mengingat `length` titik terakhir setiap track.

| Anggota | Keterangan |
|---|---|
| `update(points, tracker_ids)` | Menambahkan titik frame ini. Panggil sekali per frame. Track yang tidak muncul selama `length` pemanggilan dilupakan. |
| `paths` | `dict[int, deque]`: titik setiap id track, dari yang terlama. |

`HeatMap(width, height, radius=20, decay=1.0)` menjumlahkan kehadiran per piksel.

| Anggota | Keterangan |
|---|---|
| `update(points)` | Menambahkan 1 di lingkaran berjari-jari `radius` di sekeliling setiap titik. Dengan `decay` di bawah 1, nilai lama dikalikan `decay` lebih dulu. |
| `values` | Array float32 `(height, width)` berisi jumlahnya. |

| Fungsi | Keterangan |
|---|---|
| `draw_traces(scene, trace, color=None, thickness=2)` | Jejak setiap track sebagai garis. Tanpa `color`, warnanya `track_color` id itu. |
| `draw_heatmap(scene, heatmap, alpha=0.5, colormap="jet")` | Mewarnai area yang pernah ditempati, makin sering makin panas. Area yang jarang ditempati makin transparan. `colormap` bisa `jet`, `turbo`, `inferno`, `viridis`, atau `hot`; nama lain melempar `ValueError`. |

## masks

Lokasi: `zul.computer_vision.masks`. Membutuhkan extra `vision`.

| Fungsi | Keterangan |
|---|---|
| `polygon_mask(polygons, width, height, keep_inside=False)` | Masker seukuran frame. Dengan `keep_inside=False`, area di dalam poligon dihitamkan. Dengan `keep_inside=True`, area di luar poligon yang dihitamkan. `None` jika tidak ada poligon dengan 3 titik atau lebih. |
| `combine_masks(*masks)` | Gabungan beberapa masker, dengan `None` dilewati. `None` jika semuanya `None`. |
| `apply_mask(image, mask)` | Salinan frame dengan area masker dihitamkan. Frame asli jika `mask` bernilai `None`. |
| `blur_boxes(scene, boxes, kernel=25)` | Mengaburkan isi setiap kotak di `scene` langsung. `kernel` lebih besar berarti lebih kabur. |
| `pixelate_boxes(scene, boxes, pixel_size=12)` | Mengubah isi setiap kotak di `scene` menjadi blok seukuran `pixel_size` piksel. |

Bagian kotak di luar tepi frame dipotong, dan kotak yang tidak punya luas setelah dipotong dilewati.

## video

Lokasi: `zul.computer_vision.video`. Membutuhkan extra `vision`.

### `VideoInfo(width, height, fps, total_frames)`

Ukuran, kecepatan, dan jumlah frame sebuah video. Dataclass yang tidak bisa diubah.

| Anggota | Keterangan |
|---|---|
| `VideoInfo.from_path(path)` | Membaca info dari file video. Melempar `FileNotFoundError` jika video tidak bisa dibuka. FPS yang terbaca 0 diganti 30. |
| `slice(start=0, end=None, stride=1)` | Info video hasil potongan: `fps` dibagi `stride`, supaya durasinya sama dengan sumber, dan `total_frames` adalah jumlah frame yang dihasilkan `read_frames` dengan argumen yang sama. |

### `read_frames(path, start=0, end=None, stride=1)`

Menghasilkan `(nomor_frame, detik, frame)` untuk setiap frame ke-`stride`, dari `start` sampai sebelum `end`. `nomor_frame` adalah nomor di video sumber, dan `detik` adalah `nomor_frame / fps`. Frame berformat BGR. Melempar `FileNotFoundError` jika video tidak bisa dibuka.

### `save_image(path, image)` dan `read_image(path)`

`save_image` menyimpan frame BGR sebagai file gambar, dengan format mengikuti ekstensi, misalnya `.png` atau `.jpg`. Foldernya dibuat jika belum ada, dan fungsinya mengembalikan `Path` file itu. `read_image` membaca file gambar sebagai frame BGR, dan melempar `FileNotFoundError` jika file tidak ada atau bukan gambar.

### `VideoWriter(path, info, codec="mp4v")`

Menulis video dengan ukuran dan FPS dari `info`. Pakai dengan `with`. Folder `path` dibuat jika belum ada.

| Anggota | Keterangan |
|---|---|
| `write(frame)` | Menulis satu frame. Melempar `RuntimeError` jika dipanggil di luar `with`. |
| `frames` | Jumlah frame yang sudah ditulis. |

Membuka `VideoWriter` melempar `OSError` jika OpenCV tidak bisa menulis file dengan `codec` itu.

### `FpsMeter(window=30)` dan `Pacer(fps)`

`FpsMeter` mengukur kecepatan proses. Panggil `start()` sebelum memproses satu frame dan `stop()` sesudahnya. `fps` berisi rata-rata dari `window` frame terakhir, dan `full` bernilai True setelah `window` frame terukur.

`Pacer` menahan pratinjau agar tidak lebih cepat dari video aslinya. `wait_ms()` mengembalikan milidetik yang perlu ditunggu sebelum frame berikutnya, minimal 1, untuk `waitKey` milik OpenCV.

## tracking

Lokasi: `zul.computer_vision.tracking`. Membutuhkan extra `tracking`.

ByteTrack (Zhang dkk., 2022), ditulis sendiri di Zul dengan NumPy. Pemasangan track dengan deteksi memakai `zul.adapters.lap`. Pada 500 frame video toko, hasilnya sama dengan implementasi ByteTrack ultralytics yang dipakai sebelumnya: deteksi yang sama ter-track, id-nya konsisten, dan selisih kotaknya di bawah 0,001 piksel.

### `ByteTracker(frame_rate=30.0, high_threshold=0.35, low_threshold=0.1, new_track_threshold=0.25, lost_track_buffer=30, match_threshold=0.8)`

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `frame_rate` | `float` | `30.0` | FPS frame yang diproses, yaitu `VideoInfo.slice(...).fps`. |
| `high_threshold` | `float` | `0.35` | Skor minimum deteksi untuk tahap pemasangan pertama. |
| `low_threshold` | `float` | `0.1` | Deteksi dengan skor di atas nilai ini, tetapi di bawah `high_threshold`, dipakai di tahap kedua untuk menyambung track yang sudah ada. |
| `new_track_threshold` | `float` | `0.25` | Skor minimum untuk membuka track baru. |
| `lost_track_buffer` | `int` | `30` | Berapa lama track yang hilang disimpan, dalam frame pada 30 FPS. Nilainya disesuaikan dengan `frame_rate`. |
| `match_threshold` | `float` | `0.8` | Ambang biaya pemasangan di tahap pertama. Biaya adalah 1 dikurangi IoU dikali skor deteksi. |

| Method | Keterangan |
|---|---|
| `update(detections)` | Mengembalikan deteksi frame ini yang sudah punya track, dengan `tracker_id` terisi. `detections` boleh objek apa pun yang punya `xyxy`, `confidence`, dan `class_id`, bisa dipotong dengan indeks, dan berupa dataclass, misalnya `Detections`. `xyxy` diganti kotak hasil filter Kalman, dan kolom lain, termasuk keypoint, tetap sejajar dengan kotaknya. Frame tanpa deteksi mengembalikan hasil kosong dengan `tracker_id` berupa array kosong. |
| `step(xyxy, scores, class_ids)` | Versi `update` untuk array mentah. Mengembalikan daftar `Track` yang aktif, masing-masing dengan `track_id`, `xyxy`, `score`, `class_id`, dan `row`, yaitu indeks baris deteksi asalnya. |

Track baru baru dikembalikan setelah cocok lagi di frame berikutnya, kecuali di frame pertama. Track yang hilang lebih lama dari `lost_track_buffer` dihapus, dan orang yang kembali setelahnya mendapat id baru. Id dimulai dari 1 untuk setiap `ByteTracker`.

## detection

Lokasi: `zul.computer_vision.detection`. Membutuhkan extra `detection`.

Model dijalankan lewat `zul.adapters.rfdetr`, dengan RF-DETR berlisensi Apache 2.0. `ByteTracker` juga bisa diimpor dari modul ini, untuk kode yang ditulis sebelum tracking dipisahkan.

### `Detections`

Deteksi satu frame sebagai array NumPy yang sejajar per baris: baris ke-i di setiap field adalah orang yang sama.

| Field | Bentuk | Keterangan |
|---|---|---|
| `xyxy` | `(n, 4)` | Kotak. |
| `confidence` | `(n,)` | Skor deteksi. |
| `class_id` | `(n,)` int | Id kategori COCO. Orang adalah kelas `1`. |
| `tracker_id` | `(n,)` int atau `None` | Id track, diisi `ByteTracker.update`. |
| `keypoints_xy` | `(n, 17, 2)` atau `None` | Keypoint COCO dari model keypoint. |
| `keypoints_conf` | `(n, 17)` atau `None` | Confidence setiap keypoint. |

| Anggota | Keterangan |
|---|---|
| `len(detections)` | Jumlah deteksi. |
| `detections[index]` | Deteksi baru dengan semua field dipotong bersama, dengan mask bool atau daftar indeks. |
| `rescale(scale)` | Membagi `xyxy` dan `keypoints_xy` dengan `scale`, untuk koordinat dari frame yang diperkecil `standardise_frame`. |
| `Detections.from_arrays(arrays)` | Deteksi dari dict berkunci `xyxy`, `confidence`, `class_id`, `keypoints_xy`, dan `keypoints_conf`, misalnya hasil adapter model lain. |

### Fungsi

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `load_model(model="keypoint", weights=None, half=True, device=None)` | Model RF-DETR | `model` adalah `keypoint`, untuk kotak orang dan 17 keypoint, atau `nano`, `small`, `medium`, `large`, untuk kotak 80 kelas COCO. Tanpa `weights`, bobot diunduh ke `~/.roboflow/models` saat pertama dipakai. `half` memakai float16 jika GPU tersedia. Nama lain melempar `ValueError`. |
| `standardise_frame(image, size=640)` | `(image, scale)` | Memperkecil frame sampai sisi terpanjangnya `size` piksel, dengan rasio tetap. Frame yang lebih kecil tidak diperbesar, dan `scale`-nya 1. |
| `detect(model, image, confidence=0.5, classes=None, nms_iou=0.7)` | `Detections` | Inference satu frame BGR. `classes` menyaring id kategori COCO, misalnya `[1]`. Kotak yang IoU-nya dengan kotak berskor lebih tinggi melebihi `nms_iou` dibuang; `None` mematikan penyaringan ini. |

RF-DETR kadang memberi dua kotak yang hampir sama untuk satu orang. Pada video toko, 9 sampai 12 pasang kotak kembar muncul di 30 frame, karena itu `detect` menyaringnya secara bawaan.

## weights

Lokasi: `zul.computer_vision.weights`. Membutuhkan extra `detection` dan koneksi ke storage rilis RF-DETR.

### `fetch(path, download=True)`

Memastikan file bobot model ada di `path`. Mengembalikan `(bisa_dipakai, keterangan)`.

| Kondisi | Hasil |
|---|---|
| File sudah ada | `(True, "ada ... MB")` |
| File belum ada dan `download=False` | `(False, "belum ada")` |
| Berhasil diunduh | `(True, "diunduh ... MB")`. Unduhannya dicek dengan MD5. |
| Nama file bukan bobot yang dirilis RF-DETR | `(False, "GAGAL ...")` |

Nama file di `path` harus sama dengan nama bobot rilis RF-DETR, misalnya `rf-detr-keypoint-preview-xlarge.pth`. Nama bawaan setiap model ada di `zul.adapters.rfdetr.default_weights(nama)`. Untuk mengganti file yang terpotong, hapus filenya, lalu panggil `fetch` lagi.
