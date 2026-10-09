# Mengukur perhatian pengunjung ke rak

`zul.computer_vision` mengubah video CCTV toko menjadi catatan: siapa memperhatikan rak mana, dan berapa lama. Di panduan ini kamu membuat satu script yang mendeteksi orang dan arah hadapnya, lalu menulis CSV dengan satu baris per rentang perhatian, ditambah video beranotasi.

Orang yang hanya berdiri di dekat rak tidak dihitung. Waktu perhatian baru bertambah saat orang itu menghadap raknya. Alasan aturan ini ada di [Cara kerja aturan perilaku di video](../konsep/aturan-perilaku-di-video.md). Untuk menghitung orang yang masuk lewat pintu, lihat [Menghitung pengunjung yang berminat dan masuk](menghitung-pengunjung-masuk.md).

**Sebelum mulai:** kamu butuh:

- Python 3.11 atau lebih baru.
- Video dari kamera yang tidak bergerak, misalnya file mp4 dari CCTV.
- GPU NVIDIA, sangat disarankan. Di RTX 3060 Laptop, script di panduan ini memproses 500 frame 1280×720 dalam 24 detik. Proyek asal modul ini mengukur CPU sekitar 11 kali lebih lambat dari GPU.

## Menyiapkan model dan koordinat rak

1. Install Zul dengan extra `yolo`. Extra ini sudah termasuk extra `vision` untuk OpenCV:

    ```shell
    pip install "zul[yolo] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

    Extra `yolo` meng-install ultralytics, yang ikut meng-install PyTorch. Di Windows, PyTorch dari PyPI hanya berjalan di CPU. Untuk GPU NVIDIA, install PyTorch versi CUDA dulu dengan perintah dari [pytorch.org](https://pytorch.org/get-started/locally/), lalu jalankan perintah di atas.

2. Pastikan PyTorch melihat GPU-mu:

    ```shell
    python -c "import torch; print(torch.cuda.is_available())"
    ```

    Perintah itu mencetak `True` jika GPU bisa dipakai. Jika `False`, script tetap jalan di CPU, hanya jauh lebih lambat.

3. Unduh bobot model pose ke folder `models`:

    ```python
    from zul.computer_vision.weights import fetch

    print(fetch("models/yolo11m-pose.pt"))
    ```

    Hasilnya `(True, ...)` dengan keterangan `diunduh` dan ukuran file, sekitar 42 MB. Jika file sudah ada, keterangannya `ada` dan tidak ada yang diunduh. Satu model pose cukup: model ini mendeteksi kotak orang sekaligus keypoint untuk arah hadapnya.

4. Simpan satu frame dari videomu sebagai gambar:

    ```python
    import cv2
    from zul.computer_vision.video import read_frames

    frame_number, timestamp_s, frame = next(read_frames("videos/interior.mp4", start=1000))
    cv2.imwrite("frame.jpg", frame)
    ```

5. Buka `frame.jpg` di editor gambar yang menampilkan posisi kursor, lalu catat titik sudut setiap rak dalam piksel. Pakai koordinat gambar asli, bukan gambar yang diperkecil.

    Gambar poligon yang menutupi rak dan tempat kepala pengunjung berada saat melihat rak itu. Script menguji satu titik di sekitar kepala setiap orang, yaitu 1/6 dari atas kotaknya, bukan titik di kakinya.

6. Tulis koordinat dan pengaturannya di `scene.yaml`:

    ```yaml title="scene.yaml"
    SOURCE_VIDEO_PATH: videos/interior.mp4

    POLYGON:
      - [[12, 222], [200, 261], [446, 719], [25, 719]]
      - [[624, 304], [1220, 719], [450, 717], [305, 451]]
      - [[586, 137], [716, 253], [305, 436], [206, 259]]
      - [[842, 184], [1160, 327], [964, 532], [621, 294]]
    POLYGON_LABELS: [shelf_a, shelf_b, shelf_c, shelf_d]

    settings:
      POSE_MODEL: models/yolo11m-pose.pt
      CONFIDENCE: 0.20
      DETECT_SIZE: 640
      KEYPOINT_CONFIDENCE: 0.35
      HEAD_ANCHOR_RATIO: 0.16666666666666666
      FACING_CONE_DEG: 90.0
      VISIT_GRACE_SECONDS: 1.0
      SHELF_INTEREST_SECONDS: 3.0
    ```

    Ganti `POLYGON` dan `POLYGON_LABELS` dengan rak di videomu. Urutan label mengikuti urutan poligon. Arti setiap pengaturan ada di [Menyesuaikan aturan](#menyesuaikan-aturan).

## Menulis dan menjalankan script

1. Simpan script berikut sebagai `perhatian_rak.py`, di folder yang sama dengan `scene.yaml`:

    ```python title="perhatian_rak.py"
    from dataclasses import dataclass

    from zul.computer_vision import analytics, draw, geometry, pose
    from zul.computer_vision.config import load_scene, validate_settings
    from zul.computer_vision.detection import (
        ByteTracker,
        detect,
        load_model,
        standardise_frame,
    )
    from zul.computer_vision.report import RecordWriter
    from zul.computer_vision.video import VideoInfo, VideoWriter, read_frames

    START, END, STRIDE = 1000, 2500, 3


    @dataclass(frozen=True)
    class Rules:
        POSE_MODEL: str
        CONFIDENCE: float
        DETECT_SIZE: int
        KEYPOINT_CONFIDENCE: float
        HEAD_ANCHOR_RATIO: float
        FACING_CONE_DEG: float
        VISIT_GRACE_SECONDS: float
        SHELF_INTEREST_SECONDS: float


    scene = load_scene("scene.yaml")
    rules = validate_settings(scene["settings"], Rules)
    video_path = scene["SOURCE_VIDEO_PATH"]
    shelves = geometry.as_polygon_list(scene["POLYGON"])
    labels = scene["POLYGON_LABELS"]
    targets = pose.zone_targets(shelves, scene.get("POLYGON_ANCHORS"))
    ratio = rules["HEAD_ANCHOR_RATIO"]

    info = VideoInfo.from_path(video_path)
    output = info.slice(START, END, STRIDE)
    mask = draw.polygon_mask(shelves, info.width, info.height, keep_inside=True)

    model = load_model(rules["POSE_MODEL"])
    tracker = ByteTracker(frame_rate=output.fps)
    visits = analytics.ZoneVisitTracker(labels, grace_s=rules["VISIT_GRACE_SECONDS"])
    attention = analytics.AttentionTracker(
        labels,
        minimum_s=rules["SHELF_INTEREST_SECONDS"],
        frame_period_s=STRIDE / info.fps,
    )
    columns = [
        "attention_id",
        "track_id",
        "zone_name",
        "start_time_s",
        "end_time_s",
        "looking_s",
        "span_s",
    ]

    with RecordWriter("outputs/attention.csv", columns) as csv_file, VideoWriter(
        "outputs/attention.mp4", output
    ) as video:
        for frame_number, timestamp_s, frame in read_frames(video_path, START, END, STRIDE):
            prepared, scale = standardise_frame(
                draw.apply_mask(frame, mask), rules["DETECT_SIZE"]
            )
            people = detect(model, prepared, confidence=rules["CONFIDENCE"])
            people = tracker.update(people.rescale(scale))

            heads = geometry.box_anchors(people.xyxy, ratio)
            membership = geometry.zone_membership(shelves, heads)
            people, membership = people[membership >= 0], membership[membership >= 0]

            directions, sources = pose.facing_directions(
                people.keypoints_xy, people.keypoints_conf, rules["KEYPOINT_CONFIDENCE"]
            )
            looking = pose.facing_zone_targets(
                people.xyxy,
                directions,
                membership,
                targets,
                rules["FACING_CONE_DEG"],
                ratio,
            )
            visits.update(frame_number, timestamp_s, people.tracker_id, membership)
            csv_file.write(
                attention.update(
                    frame_number, timestamp_s, people.tracker_id, membership, looking
                )
            )

            annotated = frame.copy()
            draw.draw_polygons(annotated, shelves, "#00d4ff", fill_alpha=0.2)
            draw.draw_skeleton(annotated, people.keypoints_xy, people.keypoints_conf)
            for box, track_id, zone, direction, source in zip(
                people.xyxy, people.tracker_id, membership, directions, sources
            ):
                seconds = attention.looking_s(track_id, zone)
                label = f"#{track_id} {labels[zone]} {seconds:.1f}s"
                draw.draw_labelled_box(annotated, box, label, draw.track_color(track_id))
                if direction is not None:
                    arrow = "#FFC400" if source == "head" else "#B388FF"
                    head = geometry.box_anchor(box, ratio)
                    draw.draw_arrow(annotated, head, direction, arrow, 40)
            draw.draw_text_block(
                annotated,
                [
                    f"{label}: {attention.qualified(i)} memperhatikan, "
                    f"{visits.visit_count(i)} kunjungan"
                    for i, label in enumerate(labels)
                ],
            )
            video.write(annotated)

        visits.close_all()
        csv_file.write(attention.close_all())

    for i, label in enumerate(labels):
        print(
            f"{label}: {visits.unique_visitors(i)} orang, "
            f"{visits.visit_count(i)} kunjungan, "
            f"{attention.people(i)} memperhatikan, {attention.seconds(i):.1f} s"
        )
    ```

    `START`, `END`, dan `STRIDE` memilih frame 1000 sampai 2500, satu dari setiap tiga frame. Untuk seluruh video, isi `START = 0` dan `END = None`.

2. Jalankan script-nya:

    ```shell
    python perhatian_rak.py
    ```

    Untuk video contoh, script itu mencetak satu baris per rak:

    ```text
    shelf_a: 0 orang, 0 kunjungan, 0 memperhatikan, 0.0 s
    shelf_b: 0 orang, 0 kunjungan, 0 memperhatikan, 0.0 s
    shelf_c: 3 orang, 4 kunjungan, 0 memperhatikan, 0.0 s
    shelf_d: 3 orang, 4 kunjungan, 2 memperhatikan, 52.7 s
    ```

    Tiga orang berdiri di `shelf_c`, tetapi tidak ada yang menghadapnya selama 3 detik. Di `shelf_d`, dua dari tiga orang memperhatikan rak itu, dengan total 52,7 detik.

Setiap frame melewati langkah yang sama:

| Langkah | Fungsi | Gunanya |
|---|---|---|
| Masker | `draw.apply_mask` | Menghitamkan semua di luar rak sebelum deteksi, jadi orang di luar rak tidak pernah terdeteksi. |
| Ukuran input | `standardise_frame`, `Detections.rescale` | Memperkecil frame ke 640 piksel untuk model, lalu mengembalikan koordinatnya ke ukuran asli. |
| Deteksi dan tracking | `detect`, `ByteTracker.update` | Kotak orang, keypoint pose, dan id yang sama untuk orang yang sama di setiap frame. |
| Zona | `box_anchors`, `zone_membership` | Rak tempat titik kepala setiap orang berada, atau -1 di luar semua rak. |
| Arah hadap | `facing_directions`, `facing_zone_targets` | Apakah setiap orang menghadap rak tempat ia berdiri. |
| Aturan | `ZoneVisitTracker`, `AttentionTracker` | Mengubah hasil per frame menjadi kunjungan dan rentang perhatian. |
| Hasil | `RecordWriter`, `VideoWriter` | CSV per rentang perhatian dan video beranotasi. |

## Membaca hasilnya

Script menulis dua file di folder `outputs`.

`outputs/attention.csv` berisi satu baris per rentang perhatian yang mencapai `SHELF_INTEREST_SECONDS`. Untuk video contoh, isinya:

```text
attention_id,track_id,zone_name,start_time_s,end_time_s,looking_s,span_s
1,1,shelf_d,33.333,63.333,26.9,30.0
4,3,shelf_d,35.133,72.933,25.8,37.8
```

Track 3 berada di `shelf_d` selama 37,8 detik (`span_s`), dan 25,8 detik di antaranya menghadap rak itu (`looking_s`). Waktu dihitung dalam detik dari awal video, bukan dari `START`. Kolom `attention_id` tidak berurutan, karena rentang yang tidak mencapai ambang ikut mendapat nomor tetapi tidak ditulis.

`outputs/attention.mp4` berisi video yang sama dengan anotasi berikut:

- Poligon rak berwarna biru.
- Kotak setiap orang dengan id track, nama rak, dan detik perhatian yang sedang berjalan.
- Panah kuning untuk arah kepala, dari hidung dan telinga. Panah ungu untuk arah badan, dari garis bahu, saat wajah tidak terlihat.
- Jumlah orang yang memperhatikan dan jumlah kunjungan per rak, di kiri atas.

CSV ditulis baris per baris. Jika script berhenti di tengah jalan, baris yang sudah ditulis tetap bisa dipakai.

## Menyesuaikan aturan

Pengaturan di `scene.yaml` berikut menentukan apa yang dihitung:

| Pengaturan | Nilai contoh | Arti |
|---|---|---|
| `CONFIDENCE` | `0.20` | Skor minimum sebuah deteksi orang. |
| `DETECT_SIZE` | `640` | Sisi terpanjang frame yang masuk ke model, dalam piksel. |
| `KEYPOINT_CONFIDENCE` | `0.35` | Skor minimum sebuah keypoint. Keypoint di bawahnya dianggap tidak terlihat. |
| `HEAD_ANCHOR_RATIO` | `0.1666…` | Posisi titik yang diuji terhadap poligon, dari atas kotak orang. `1/6` jatuh di sekitar kepala. |
| `FACING_CONE_DEG` | `90.0` | Selisih sudut terbesar antara arah hadap dan arah ke rak yang masih dihitung menghadap. |
| `VISIT_GRACE_SECONDS` | `1.0` | Jeda terpanjang sebuah track boleh hilang tanpa memulai kunjungan baru. |
| `SHELF_INTEREST_SECONDS` | `3.0` | Waktu menghadap minimum agar sebuah rentang ditulis ke CSV. |

Kamu juga bisa mengubah hal berikut:

- **Kerucut yang lebih sempit.** Dengan `FACING_CONE_DEG: 60.0`, proyek asal modul ini mengukur waktu perhatian kedua orang di `shelf_d` sekitar seperempat lebih pendek.
- **Target selain titik tengah poligon.** Script membandingkan arah hadap dengan titik tengah setiap poligon. Jika poligonmu menutupi lantai di depan rak, tambahkan `POLYGON_ANCHORS` di `scene.yaml`, berisi satu titik di rak untuk setiap poligon:

    ```yaml
    POLYGON_ANCHORS:
      - [170, 480]
      - [649, 547]
      - [453, 271]
      - [896, 334]
    ```

- **Kecepatan.** `STRIDE = 3` memproses satu dari setiap tiga frame. Nilai yang lebih besar mempercepat proses, tetapi track lebih mudah tertukar saat orang bergerak cepat.

`validate_settings` menghentikan script jika ada nama pengaturan yang salah ketik, pengaturan yang belum diisi, atau nilai bertipe salah. Untuk menambah pengaturan, tulis namanya di `scene.yaml` dan di dataclass `Rules`.

## Mengatasi masalah

### Sebuah rak selalu 0 kunjungan

Titik kepala orang di depan rak itu tidak jatuh di dalam poligonnya. Untuk melihat posisinya, gambar titik kepala setiap orang yang terdeteksi. Tambahkan dua baris berikut tepat setelah baris `heads = ...`:

```python
        for point in heads:
            draw.draw_point(frame, point, "#FF0000")
```

Jalankan script lagi, lalu buka videonya. Titik merah yang jatuh di luar poligon adalah orang yang tidak dihitung. Perlebar poligon rak itu sampai menutupi titik-titik merah di depannya.

### ConfigError saat script dimulai

Pesannya menyebut apa yang salah, misalnya:

```text
zul.computer_vision.config.ConfigError: settings: kunci tidak dikenal: CONFIDENSE (maksudnya CONFIDENCE?)
```

Betulkan nama atau nilai yang disebut di `scene.yaml`, lalu jalankan lagi.

### FileNotFoundError: video tidak bisa dibuka

Path di `SOURCE_VIDEO_PATH` dibaca relatif terhadap folder tempat kamu menjalankan script. Jalankan script dari folder yang berisi `scene.yaml`, atau isi path lengkapnya.

## Halaman terkait

- [Menghitung pengunjung yang berminat dan masuk](menghitung-pengunjung-masuk.md) untuk kamera yang menghadap pintu toko.
- [Cara kerja aturan perilaku di video](../konsep/aturan-perilaku-di-video.md) untuk alasan di balik titik kepala, arah dari bahu, dan batas kredit waktu.
- [Referensi Computer Vision](../referensi/computer-vision.md) untuk semua fungsi dan parameternya.
