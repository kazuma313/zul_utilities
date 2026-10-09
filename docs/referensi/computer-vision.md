# Computer Vision

Modul di `zul.computer_vision` untuk menganalisis perilaku orang di video: deteksi, tracking, zona, arah hadap, dan aturan yang mengubah hasil per frame menjadi catatan. Cara memakainya ada di [Mengukur perhatian pengunjung ke rak](../panduan/mengukur-perhatian-ke-rak.md), dan alasan di balik aturannya ada di [Cara kerja aturan perilaku di video](../konsep/aturan-perilaku-di-video.md).

Tabel berikut memetakan setiap modul ke isinya dan extra yang dibutuhkan:

| Modul | Isi | Extra |
|---|---|---|
| [`geometry`](#geometry) | Titik jangkar kotak, poligon, zona, dan arah. | Tidak ada |
| [`pose`](#pose) | Arah kepala dan badan dari keypoint COCO-17. | Tidak ada |
| [`crossing`](#crossing) | Lintasan masuk dan keluar sebuah garis. | Tidak ada |
| [`analytics`](#analytics) | Kunjungan, perhatian, kontak, dan minat. | Tidak ada |
| [`config`](#config) | Config scene dari YAML dan validasinya. | Tidak ada |
| [`report`](#report) | CSV dengan satu baris per kejadian. | Tidak ada |
| [`draw`](#draw) | Anotasi frame dan masker area. | `vision` |
| [`video`](#video) | Membaca dan menulis video, dan mengukur kecepatan. | `vision` |
| [`detection`](#detection) | Model YOLO, YOLO-World, pose, dan ByteTrack. | `yolo` |
| [`weights`](#weights) | Mengunduh bobot model ke folder proyek. | `yolo` |

Modul tanpa extra hanya mengimpor NumPy dan PyYAML, yang ada di instalasi dasar Zul. Mengimpor `zul.computer_vision` tidak memuat modul apa pun, jadi OpenCV dan ultralytics baru dimuat saat `draw`, `video`, `detection`, atau `weights` diimpor.

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

Fungsi di modul ini membaca keypoint COCO-17 dari model pose, misalnya `yolo11m-pose`: `xy` berbentuk `(17, 2)` per orang dan `confidence` berbentuk `(17,)`. Keypoint dengan confidence di bawah `min_confidence` dianggap tidak terlihat. `confidence=None` berarti semua keypoint terlihat.

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

## crossing

Lokasi: `zul.computer_vision.crossing`. Hanya membutuhkan NumPy.

### `LineCrossing(start, end, minimum_frames=3)`

Menghitung lintasan masuk dan keluar per track di satu segmen garis.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `start`, `end` | `(x, y)` | Wajib | Kedua ujung garis. Sisi kiri saat berjalan dari `start` ke `end` di gambar adalah sisi masuk. |
| `minimum_frames` | `int` | `3` | Jumlah frame sebuah track harus berada di sisi baru sebelum lintasannya dihitung. |

Titik yang proyeksinya jatuh di luar kedua ujung garis diabaikan. Aturan sisinya sama dengan `LineZone` milik supervision, jadi urutan titik yang sama memberi arah masuk yang sama.

| Anggota | Keterangan |
|---|---|
| `update(tracker_ids, points)` | Maju satu frame dengan satu titik per orang. Mengembalikan `(crossed_in, crossed_out)`: dua `list[bool]`, satu nilai per baris. `tracker_ids=None` memberi `([], [])`. |
| `sides(points)` | `(inside, in_band)`: dua array bool, apakah setiap titik di sisi masuk dan apakah di rentang segmen. |
| `in_count`, `out_count` | Jumlah lintasan masuk dan keluar sejauh ini. |
| `midpoint` | Titik tengah garis, misalnya target arah hadap ke pintu. |

## analytics

Lokasi: `zul.computer_vision.analytics`. Hanya membutuhkan NumPy.

Pelacak di modul ini menerima id track dan hasil uji per frame, lalu mengembalikan catatan dengan awal, akhir, dan durasi. Setiap pelacak menerima `tracker_ids=None` sebagai frame tanpa orang.

### Catatan

Semua catatan adalah dataclass. Kolom berakhiran `_s` dalam detik.

| Kelas | Field | Property |
|---|---|---|
| `Visit` | `visit_id`, `track_id`, `zone_index`, `zone_name`, `enter_frame`, `enter_time_s`, `exit_frame`, `exit_time_s` | `duration_s` |
| `Attention` | `attention_id`, `track_id`, `zone_index`, `zone_name`, `start_frame`, `start_time_s`, `end_frame`, `end_time_s`, `looking_s` | `span_s`: lama di zona, termasuk saat tidak menghadapnya |
| `Contact` | `subject_id`, `other_id`, `start_frame`, `start_time_s`, `end_frame`, `end_time_s` | `duration_s` |
| `InterestRecord` | `track_id`, `outcome`, `qualified_frame`, `qualified_time_s`, `crossed_frame`, `crossed_time_s` | `entered` |
| `InterestCounts` | `entered`, `passed_by` | `total` |

### `credit_cap(frame_period_s, threshold_s, periods, fraction)`

Mengembalikan waktu maksimum yang dihitung dari satu jeda antar pengamatan: `min(periods × frame_period_s, fraction × threshold_s)`. `AttentionTracker` dan `InterestTracker` memakainya.

### `ZoneVisitTracker(zone_labels, grace_s=1.0)`

Mengubah keanggotaan zona per frame menjadi kunjungan.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `zone_labels` | `list[str]` | Wajib | Nama zona, urut sesuai indeks zona. |
| `grace_s` | `float` | `1.0` | Kunjungan ditutup jika track tidak terlihat di zona selama `grace_s` detik atau lebih. |

Kunjungan juga ditutup seketika saat track pindah ke zona lain. Waktu keluar adalah saat track terakhir terlihat, bukan saat grace habis.

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `update(frame_number, timestamp_s, tracker_ids, membership)` | `list[Visit]` | Maju satu frame. `membership` dari `geometry.zone_membership`. Mengembalikan kunjungan yang selesai di frame ini. |
| `close_all()` | `list[Visit]` | Menutup semua kunjungan yang masih terbuka, di akhir video. |
| `dwell_s(track_id, timestamp_s)` | `float` atau `None` | Lama track di zonanya sekarang. |
| `zone_of(track_id)` | `int` atau `None` | Zona track sekarang. |
| `unique_visitors(zone_index)` | `int` | Jumlah id track berbeda yang pernah di zona itu. |
| `visit_count(zone_index)` | `int` | Jumlah kunjungan ke zona itu, termasuk yang masih terbuka. |

Atribut `completed` berisi semua kunjungan yang sudah ditutup.

### `AttentionTracker(zone_labels, minimum_s=3.0, grace_s=1.0, frame_period_s=1/30, max_gap_frame_periods=2, max_gap_threshold_fraction=0.25)`

Mencatat perhatian per zona: rentang waktu seseorang berada di zona, dan berapa lama ia menghadapnya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `zone_labels` | `list[str]` | Wajib | Nama zona, urut sesuai indeks zona. |
| `minimum_s` | `float` | `3.0` | Waktu menghadap minimum agar sebuah rentang dicatat. |
| `grace_s` | `float` | `1.0` | Rentang ditutup jika track tidak terlihat di zona lebih dari `grace_s` detik. |
| `frame_period_s` | `float` | `1/30` | Jarak waktu antar frame yang diproses, yaitu `stride / fps`. |
| `max_gap_frame_periods` | `int` | `2` | Bagian pertama batas kredit, dalam kelipatan `frame_period_s`. |
| `max_gap_threshold_fraction` | `float` | `0.25` | Bagian kedua batas kredit, dalam pecahan `minimum_s`. |

Setiap frame saat track menghadap zonanya menambah waktu sejak frame menghadap sebelumnya, paling banyak `credit_cap_s`. Satu track di satu zona adalah satu rentang. Rentang yang `looking_s`-nya di bawah `minimum_s` dibuang saat ditutup.

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `update(frame_number, timestamp_s, tracker_ids, membership, looking)` | `list[Attention]` | Maju satu frame. `looking` dari `pose.facing_zone_targets`. Mengembalikan rentang yang ditutup di frame ini dan memenuhi `minimum_s`. |
| `close_all()` | `list[Attention]` | Menutup semua rentang yang masih terbuka, di akhir video. |
| `looking_s(track_id, zone_index)` | `float` | Waktu menghadap rentang yang sedang terbuka, untuk label di layar. |
| `count(zone_index)` | `int` | Jumlah rentang yang sudah dicatat di zona itu. |
| `qualified(zone_index)` | `int` | `count`, ditambah rentang terbuka yang sudah memenuhi `minimum_s`. |
| `people(zone_index)` | `int` | Jumlah id track berbeda dengan rentang tercatat di zona itu. |
| `seconds(zone_index)` | `float` | Total `looking_s` rentang tercatat di zona itu. |

Atribut `completed` berisi semua rentang yang dicatat, dan `credit_cap_s` berisi batas kredit.

### `proximity_pairs(boxes, is_subject, max_distance_m=2.0, person_height_m=1.7, exclude=None)`

Mengembalikan `list[(baris_subject, baris_lain, meter)]` untuk setiap pasangan subject dan bukan-subject yang jaraknya paling jauh `max_distance_m`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `boxes` | `ndarray (n, 4)` | Wajib | Kotak semua orang di frame. |
| `is_subject` | `list[bool]` | Wajib | True untuk anggota kelompok utama, misalnya staf. |
| `max_distance_m` | `float` | `2.0` | Jarak terjauh yang dihitung dekat, dalam meter. |
| `person_height_m` | `float` | `1.7` | Tinggi orang dewasa yang dipakai sebagai penggaris. |
| `exclude` | `list[bool]` atau `None` | `None` | Baris yang tidak ikut dipasangkan, misalnya orang di lorong mal. Dipakai hanya jika panjangnya sama dengan `boxes`. |

Jarak diukur dari kaki ke kaki, lalu dibagi rata-rata skala kedua orang. Skala satu orang adalah tinggi kotaknya dibagi `person_height_m`. Orang yang jongkok atau terpotong tepi frame terbaca lebih jauh.

### `ProximityLog(minimum_s=1.0, grace_s=1.0)`

Mencatat kontak per anggota kelompok utama dari pasangan `proximity_pairs`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `minimum_s` | `float` | `1.0` | Durasi minimum agar sebuah kontak dicatat. `0` mencatat setiap pertemuan. |
| `grace_s` | `float` | `1.0` | Kontak ditutup jika pasangan itu tidak dekat lebih dari `grace_s` detik. |

| Method | Mengembalikan | Keterangan |
|---|---|---|
| `note_subjects(tracker_ids, is_subject, timestamp_s)` | `None` | Mencatat setiap subject yang terlihat, ada kontak atau tidak. Panggil setiap frame. |
| `update(frame_number, timestamp_s, tracker_ids, pairs)` | `list[Contact]` | Membuka atau memperpanjang kontak untuk setiap pasangan. Mengembalikan kontak yang ditutup di frame ini dan memenuhi `minimum_s`. |
| `close_all()` | `list[Contact]` | Menutup semua kontak yang masih terbuka. |
| `contacts_per_subject()` | `dict[int, int]` | Jumlah kontak per subject, termasuk subject dengan nol kontak. |
| `seconds_per_subject()` | `dict[int, float]` | Total durasi kontak per subject. |
| `idle_subjects()` | `list[int]` | Subject tanpa kontak, urut naik. |
| `average_contacts()` | `float` | Rata-rata kontak per subject, dibagi semua subject yang terlihat. |

Contoh berikut mencatat kontak staf dari satu frame. `staff` berisi `True` untuk setiap baris yang merupakan staf:

```python
from zul.computer_vision.analytics import ProximityLog, proximity_pairs

contacts = ProximityLog(minimum_s=1.0)

# di setiap frame
contacts.note_subjects(people.tracker_id, staff, timestamp_s)
pairs = proximity_pairs(people.xyxy, staff, max_distance_m=2.0)
contacts.update(frame_number, timestamp_s, people.tracker_id, pairs)

# di akhir video
contacts.close_all()
print(contacts.contacts_per_subject(), contacts.average_contacts())
```

### `InterestTracker(threshold_s=2.0, frame_period_s=1/30, max_gap_frame_periods=2, max_gap_threshold_fraction=0.25)`

Mencatat waktu minat per orang, lalu hasilnya: `entered` atau `passed_by`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `threshold_s` | `float` | `2.0` | Waktu minat minimum agar seseorang dihitung berminat. |
| `frame_period_s` | `float` | `1/30` | Jarak waktu antar frame yang diproses, yaitu `stride / fps`. |
| `max_gap_frame_periods`, `max_gap_threshold_fraction` | `int`, `float` | `2`, `0.25` | Batas kredit, seperti di `AttentionTracker`. |

Setiap frame menambah waktu sejak track terakhir terlihat, paling banyak `max_gap_s`, hanya jika `looking`, `in_zone`, dan `facing` ketiganya True untuk track itu. Hasil yang sudah diberikan tidak pernah turun: `passed_by` bisa menjadi `entered`, tetapi tidak sebaliknya.

| Anggota | Keterangan |
|---|---|
| `update(frame_number, timestamp_s, tracker_ids, looking, in_zone=None, facing=None)` | Maju satu frame. `in_zone` dan `facing` yang `None` dianggap True untuk semua. Mengembalikan id yang baru memenuhi `threshold_s` di frame ini. |
| `mark_crossed(tracker_ids, frame_number, timestamp_s)` | Mencatat bahwa track ini melintasi garis masuk. |
| `counts()` | `InterestCounts` saat ini. |
| `outcome_of(track_id)` | `"entered"`, `"passed_by"`, atau `None`. |
| `looking_s(track_id)` | Waktu minat track itu. |
| `label(track_id)` | Teks untuk video: `look 0.5/2s` sebelum memenuhi syarat, lalu `INTERESTED:entered` atau `INTERESTED:passed_by`. |
| `records()` | `list[InterestRecord]`, satu per orang yang berminat, urut menurut id track. |
| `ENTERED`, `PASSED_BY` | Konstanta `"entered"` dan `"passed_by"`. |

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

### Bentuk

| Fungsi | Keterangan |
|---|---|
| `draw_box(scene, xyxy, color, style=BoxStyle.CORNER, thickness=2, corner_length=14, fill_alpha=0.25, dash=8)` | Satu kotak. `BoxStyle` berisi `CORNER`, `RECT`, `DASHED`, dan `FILLED`. |
| `draw_label(scene, text, anchor, color, text_color=(0, 0, 0), scale=0.4, thickness=1, padding=2, above=True)` | Teks di atas pelat berwarna, di atas `anchor` atau di bawahnya jika `above=False`. |
| `draw_labelled_box(scene, xyxy, label, color, style=BoxStyle.CORNER, **box_options)` | Kotak dan keterangannya di atas sudut kiri atas. |
| `draw_text_block(scene, lines, corner=Corner.TOP_LEFT, color=(255, 255, 255), scale=0.55, thickness=1, margin=12, line_height=26, top=None, background=(0, 0, 0))` | Beberapa baris teks menempel ke satu sudut frame. `Corner` berisi `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, dan `BOTTOM_RIGHT`. `top` menggeser baris pertama ke bawah, misalnya agar tidak menutupi cap waktu video CCTV. `background=None` menggambar teks tanpa latar. |
| `draw_polygons(scene, polygons, color, thickness=2, fill_alpha=0.0)` | Garis tepi beberapa poligon, dengan isi transparan jika `fill_alpha` di atas 0. |
| `draw_line(scene, start, end, color, thickness=2)` | Satu garis. |
| `draw_arrow(scene, origin, direction, color, length, thickness=2, tip_ratio=0.35)` | Panah sepanjang `length` piksel dari `origin` searah `direction`. |
| `draw_point(scene, point, color, radius=4)` | Satu titik penuh. |
| `draw_link(scene, start, end, color, label="", thickness=2, scale=0.45)` | Garis antara dua titik dengan keterangan di tengahnya, misalnya jarak dalam meter. |
| `draw_skeleton(scene, keypoints_xy, keypoints_conf=None, min_confidence=0.35, color="#E0E0E0", vertex_color="#FFFFFF", thickness=1, radius=3)` | Kerangka pose untuk setiap orang, hanya dari keypoint dengan confidence cukup. `keypoints_xy=None` tidak menggambar apa pun. |

### Masker

| Fungsi | Keterangan |
|---|---|
| `polygon_mask(polygons, width, height, keep_inside=False)` | Masker seukuran frame. Dengan `keep_inside=False`, area di dalam poligon dihitamkan. Dengan `keep_inside=True`, area di luar poligon yang dihitamkan. `None` jika tidak ada poligon dengan 3 titik atau lebih. |
| `combine_masks(*masks)` | Gabungan beberapa masker, dengan `None` dilewati. `None` jika semuanya `None`. |
| `apply_mask(image, mask)` | Salinan frame dengan area masker dihitamkan. Frame asli jika `mask` bernilai `None`. |

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

### `VideoWriter(path, info, codec="mp4v")`

Menulis video dengan ukuran dan FPS dari `info`. Pakai dengan `with`. Folder `path` dibuat jika belum ada.

| Anggota | Keterangan |
|---|---|
| `write(frame)` | Menulis satu frame. Melempar `RuntimeError` jika dipanggil di luar `with`. |
| `frames` | Jumlah frame yang sudah ditulis. |

Membuka `VideoWriter` melempar `OSError` jika OpenCV tidak bisa menulis file dengan `codec` itu.

### `FpsMeter(window=30)` dan `Pacer(fps)`

`FpsMeter` mengukur kecepatan proses. Panggil `start()` sebelum memproses satu frame dan `stop()` sesudahnya. `fps` berisi rata-rata dari `window` frame terakhir, dan `full` bernilai True setelah `window` frame terukur.

`Pacer` menahan pratinjau agar tidak lebih cepat dari video aslinya. `wait_ms()` mengembalikan milidetik yang perlu ditunggu sebelum frame berikutnya, minimal 1, untuk `cv2.waitKey`.

## detection

Lokasi: `zul.computer_vision.detection`. Membutuhkan extra `yolo`.

### `Detections`

Deteksi satu frame sebagai array NumPy yang sejajar per baris: baris ke-i di setiap field adalah orang yang sama.

| Field | Bentuk | Keterangan |
|---|---|---|
| `xyxy` | `(n, 4)` | Kotak. |
| `confidence` | `(n,)` | Skor deteksi. |
| `class_id` | `(n,)` int | Kelas, sesuai urutan kelas model atau `prompts`. |
| `tracker_id` | `(n,)` int atau `None` | Id track, diisi `ByteTracker.update`. |
| `keypoints_xy` | `(n, 17, 2)` atau `None` | Keypoint dari model pose. |
| `keypoints_conf` | `(n, 17)` atau `None` | Confidence setiap keypoint. |

| Anggota | Keterangan |
|---|---|
| `len(detections)` | Jumlah deteksi. |
| `detections[index]` | Deteksi baru dengan semua field dipotong bersama, dengan mask bool atau daftar indeks. |
| `rescale(scale)` | Membagi `xyxy` dan `keypoints_xy` dengan `scale`, untuk koordinat dari frame yang diperkecil `standardise_frame`. |
| `Detections.from_ultralytics(result)` | Deteksi dari satu `Results` ultralytics. |

### Fungsi

| Fungsi | Mengembalikan | Keterangan |
|---|---|---|
| `load_model(weights, prompts=None)` | Model ultralytics | Tanpa `prompts`, model YOLO atau model pose biasa. Dengan `prompts`, model YOLO-World yang mendeteksi kelas dari teks, misalnya `["person"]`. YOLO-World membutuhkan paket CLIP dari ultralytics. Tanpa paket itu, fungsi ini melempar `ImportError` berisi perintah instalasinya. |
| `standardise_frame(image, size=640)` | `(image, scale)` | Memperkecil frame sampai sisi terpanjangnya `size` piksel, dengan rasio tetap. Frame yang lebih kecil tidak diperbesar, dan `scale`-nya 1. |
| `detect(model, image, confidence=0.20, iou=0.5, imgsz=640, device=None, classes=None)` | `Detections` | Inference satu frame. Model pose ikut mengisi `keypoints_xy` dan `keypoints_conf`. |

### `ByteTracker(frame_rate=30.0, high_threshold=0.35, low_threshold=0.1, new_track_threshold=0.25, lost_track_buffer=30, match_threshold=0.8)`

ByteTrack dari ultralytics, dengan ambang yang cocok untuk skor YOLO-World.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `frame_rate` | `float` | `30.0` | FPS frame yang diproses, yaitu `VideoInfo.slice(...).fps`. |
| `high_threshold` | `float` | `0.35` | Skor minimum deteksi untuk tahap pencocokan pertama. |
| `low_threshold` | `float` | `0.1` | Skor minimum deteksi untuk tahap pencocokan kedua. |
| `new_track_threshold` | `float` | `0.25` | Skor minimum untuk membuka track baru. |
| `lost_track_buffer` | `int` | `30` | Berapa lama track yang hilang disimpan, dalam frame pada 30 FPS. Nilainya disesuaikan dengan `frame_rate`. |
| `match_threshold` | `float` | `0.8` | Ambang pencocokan deteksi dengan track. |

`update(detections)` mengembalikan deteksi frame ini yang sudah punya track, dengan `tracker_id` terisi. Deteksi yang belum dikonfirmasi dibuang: kecuali di frame pertama, track baru baru dikembalikan setelah cocok lagi di frame berikutnya. `xyxy` diganti kotak dari tracker, dan `keypoints_xy` tetap sejajar dengan kotaknya. Frame tanpa deteksi mengembalikan `Detections` kosong dengan `tracker_id` berupa array kosong.

## weights

Lokasi: `zul.computer_vision.weights`. Membutuhkan extra `yolo` dan koneksi ke GitHub.

### `fetch(path, download=True)`

Memastikan file bobot model ada di `path`. Mengembalikan `(bisa_dipakai, keterangan)`.

| Kondisi | Hasil |
|---|---|
| File sudah ada | `(True, "ada ... MB")` |
| File belum ada dan `download=False` | `(False, "belum ada")` |
| Berhasil diunduh | `(True, "diunduh ... MB")` |
| Nama file bukan bobot yang dirilis ultralytics | `(False, "GAGAL ...")` |

Nama file di `path` harus sama dengan nama aset rilis ultralytics, misalnya `yolo11m-pose.pt` atau `yolov8l-worldv2.pt`. Untuk mengganti file yang terpotong, hapus filenya, lalu panggil `fetch` lagi.
