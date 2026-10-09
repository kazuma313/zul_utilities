# Menghitung pengunjung yang berminat dan masuk

Dari kamera yang menghadap pintu toko, `zul.computer_vision` bisa menjawab dua pertanyaan: berapa orang yang lewat menunjukkan minat ke toko, dan berapa dari mereka yang kemudian masuk. Di panduan ini kamu membuat script yang menulis CSV dengan satu baris per orang yang berminat, beserta hasilnya: `entered` atau `passed_by`.

Seseorang dihitung berminat setelah tiga syarat terpenuhi bersamaan selama 2 detik:

1. Titik kepalanya ada di area depan toko, misalnya lorong mal.
2. Wajahnya terlihat oleh kamera.
3. Kepalanya menghadap ke pintu toko.

Orang yang berminat lalu melintasi garis pintu ke arah dalam tercatat `entered`. Yang tidak melintas tercatat `passed_by`. Alasan setiap syarat ada di [Cara kerja aturan perilaku di video](../konsep/aturan-perilaku-di-video.md#minat-dan-garis-pintu).

**Sebelum mulai:** selesaikan bagian [Menyiapkan model dan koordinat rak](mengukur-perhatian-ke-rak.md#menyiapkan-model-dan-koordinat-rak) di panduan perhatian ke rak, langkah 1 sampai 4. Di panduan ini, yang kamu catat dari frame bukan rak, tetapi area depan toko, garis pintu, dan area yang diabaikan.

## Menyiapkan scene pintu

1. Catat koordinat tiga bentuk dari frame kamera pintu, dalam piksel gambar asli:

    | Bentuk | Isi | Gunanya |
    |---|---|---|
    | `INTEREST_POLYGON` | Poligon area tempat orang bisa melihat ke dalam toko, misalnya lorong di depannya. | Waktu minat hanya bertambah di dalam area ini. |
    | `ENTRANCE_LINE` | Dua titik di ambang pintu. | Lintasan ke arah dalam mengubah hasil menjadi `entered`. |
    | `IGNORE_POLYGON` | Poligon area yang tidak perlu dideteksi, misalnya lantai mal di seberang. | Area ini dihitamkan sebelum deteksi. |

2. Tentukan urutan titik garis pintu. Bayangkan kamu berjalan di gambar dari titik pertama ke titik kedua: sisi kirimu adalah sisi dalam toko. Jika arahnya terbalik, tukar urutan kedua titik.

3. Tulis koordinat dan pengaturannya di `entrance.yaml`:

    ```yaml title="entrance.yaml"
    SOURCE_VIDEO_PATH: videos/entrance.mp4

    INTEREST_POLYGON:
      - [1221, 180]
      - [1268, 494]
      - [311, 220]
      - [279, 67]

    ENTRANCE_LINE:
      - [1257, 497]
      - [225, 203]

    IGNORE_POLYGON:
      - [1270, 5]
      - [1276, 354]
      - [1230, 175]
      - [301, 63]
      - [8, 1]

    settings:
      POSE_MODEL: models/yolo11m-pose.pt
      CONFIDENCE: 0.20
      DETECT_SIZE: 640
      KEYPOINT_CONFIDENCE: 0.35
      HEAD_ANCHOR_RATIO: 0.16666666666666666
      FACING_CONE_DEG: 90.0
      INTEREST_THRESHOLD_SECONDS: 2.0
      MIN_CROSSING_FRAMES: 3
    ```

    `INTEREST_THRESHOLD_SECONDS` adalah lama minimum ketiga syarat minat terpenuhi. `MIN_CROSSING_FRAMES` adalah jumlah frame seseorang harus bertahan di sisi baru garis sebelum lintasannya dihitung.

## Menulis dan menjalankan script

1. Simpan script berikut sebagai `minat_pintu.py`, di folder yang sama dengan `entrance.yaml`:

    ```python title="minat_pintu.py"
    from zul.computer_vision import draw, geometry, pose
    from zul.computer_vision.analytics import InterestRecord, InterestTracker
    from zul.computer_vision.config import load_scene
    from zul.computer_vision.crossing import LineCrossing
    from zul.computer_vision.detection import (
        ByteTracker,
        detect,
        load_model,
        standardise_frame,
    )
    from zul.computer_vision.report import RecordWriter
    from zul.computer_vision.video import VideoInfo, VideoWriter, read_frames

    START, END, STRIDE = 5200, 6300, 3

    scene = load_scene("entrance.yaml")
    settings = scene["settings"]
    video_path = scene["SOURCE_VIDEO_PATH"]
    walkway = geometry.as_polygon_list(scene["INTEREST_POLYGON"])
    ignored = geometry.as_polygon_list(scene["IGNORE_POLYGON"])
    line_start, line_end = scene["ENTRANCE_LINE"]
    ratio = settings["HEAD_ANCHOR_RATIO"]

    info = VideoInfo.from_path(video_path)
    output = info.slice(START, END, STRIDE)
    mask = draw.polygon_mask(ignored, info.width, info.height)

    model = load_model(settings["POSE_MODEL"])
    tracker = ByteTracker(frame_rate=output.fps)
    door = LineCrossing(line_start, line_end, settings["MIN_CROSSING_FRAMES"])
    interest = InterestTracker(
        threshold_s=settings["INTEREST_THRESHOLD_SECONDS"],
        frame_period_s=STRIDE / info.fps,
    )

    with VideoWriter("outputs/entrance.mp4", output) as video:
        for frame_number, timestamp_s, frame in read_frames(video_path, START, END, STRIDE):
            prepared, scale = standardise_frame(
                draw.apply_mask(frame, mask), settings["DETECT_SIZE"]
            )
            people = detect(model, prepared, confidence=settings["CONFIDENCE"])
            people = tracker.update(people.rescale(scale))

            heads = geometry.box_anchors(people.xyxy, ratio)
            in_walkway = geometry.zone_membership(walkway, heads) >= 0
            directions, sources = pose.facing_directions(
                people.keypoints_xy, people.keypoints_conf, settings["KEYPOINT_CONFIDENCE"]
            )
            face_seen = [source == "head" for source in sources]
            facing_door = pose.facing_target(
                people.xyxy, directions, door.midpoint, settings["FACING_CONE_DEG"], ratio
            )

            interest.update(
                frame_number,
                timestamp_s,
                people.tracker_id,
                face_seen,
                in_walkway,
                facing_door,
            )
            crossed_in, _ = door.update(people.tracker_id, heads)
            entered = [
                track_id
                for track_id, crossed in zip(people.tracker_id, crossed_in)
                if crossed
            ]
            interest.mark_crossed(entered, frame_number, timestamp_s)

            annotated = frame.copy()
            draw.draw_polygons(annotated, walkway, "#00d4ff", fill_alpha=0.2)
            draw.draw_line(annotated, line_start, line_end, "#FF4081")
            for box, track_id in zip(people.xyxy, people.tracker_id):
                label = f"#{track_id} {interest.label(track_id)}"
                draw.draw_labelled_box(annotated, box, label, draw.track_color(track_id))
            counts = interest.counts()
            draw.draw_text_block(
                annotated,
                [
                    f"berminat {counts.total}: masuk {counts.entered}, lewat {counts.passed_by}"
                ],
            )
            video.write(annotated)

    with RecordWriter("outputs/interest.csv", InterestRecord) as csv_file:
        csv_file.write(interest.records())

    counts = interest.counts()
    print(f"berminat {counts.total}: masuk {counts.entered}, lewat {counts.passed_by}")
    print(f"garis pintu: masuk {door.in_count}, keluar {door.out_count}")
    ```

    `face_seen` memakai sumber arah hadap: `"head"` berarti arah dibaca dari hidung dan telinga, jadi wajahnya terlihat. Arah ke pintu diukur ke `door.midpoint`, titik tengah garis pintu.

2. Jalankan script-nya:

    ```shell
    python minat_pintu.py
    ```

    Untuk video contoh, script itu mencetak:

    ```text
    berminat 3: masuk 3, lewat 0
    garis pintu: masuk 3, keluar 0
    ```

## Membaca hasilnya

`outputs/interest.csv` berisi satu baris per orang yang berminat. Untuk video contoh, isinya:

```text
track_id,outcome,qualified_frame,qualified_time_s,crossed_frame,crossed_time_s
2,entered,5353,178.433,5524,184.133
9,entered,5560,185.333,5584,186.133
11,entered,5620,187.333,5656,188.533
```

| Kolom | Isi |
|---|---|
| `track_id` | Id orang dari tracker. |
| `outcome` | `entered` jika ia melintasi garis pintu ke dalam, `passed_by` jika tidak. |
| `qualified_frame`, `qualified_time_s` | Frame dan detik saat syarat minat terpenuhi. |
| `crossed_frame`, `crossed_time_s` | Frame dan detik saat lintasannya dihitung. Kosong untuk `passed_by`. |

Track 2 memenuhi syarat minat pada detik 178,4 dan masuk pada detik 184,1. Lintasan dihitung setelah orang itu bertahan `MIN_CROSSING_FRAMES` frame di sisi dalam, jadi `crossed_time_s` sedikit lebih lambat dari saat ia benar-benar melewati garis.

Hasil yang sudah diberikan tidak pernah turun. Orang yang tercatat `passed_by` berubah menjadi `entered` jika ia masuk kemudian, tetapi orang yang sudah `entered` tidak pernah kembali menjadi `passed_by`.

`outputs/entrance.mp4` berisi video beranotasi. Label di atas kotak setiap orang menampilkan waktu minat yang sedang berjalan, misalnya `look 0.5/2s`, lalu `INTERESTED:entered` atau `INTERESTED:passed_by` setelah syaratnya terpenuhi.

## Mengatasi masalah

### Lintasan tercatat keluar, bukan masuk

Urutan titik `ENTRANCE_LINE` terbalik. Tukar kedua titiknya, lalu jalankan lagi.

### Orang yang masuk tidak pernah melintas

`LineCrossing` hanya menghitung titik yang proyeksinya jatuh di antara kedua ujung garis. Pastikan garis pintu membentang selebar pintu, dan titik kepala orang yang masuk melewatinya. Untuk melihat titik kepala, ikuti [Sebuah rak selalu 0 kunjungan](mengukur-perhatian-ke-rak.md#sebuah-rak-selalu-0-kunjungan).

### Tidak ada orang yang berminat

Periksa ketiga syarat di video beranotasi. Jika label `look` tidak pernah muncul, salah satu syarat tidak pernah terpenuhi. Penyebab yang paling sering adalah poligon `INTEREST_POLYGON` yang tidak menutupi titik kepala orang yang lewat.

## Halaman terkait

- [Mengukur perhatian pengunjung ke rak](mengukur-perhatian-ke-rak.md) untuk kamera di dalam toko.
- [Cara kerja aturan perilaku di video](../konsep/aturan-perilaku-di-video.md) untuk alasan di balik syarat minat dan garis pintu.
- [Referensi Computer Vision](../referensi/computer-vision.md#analytics) untuk `ProximityLog`, yang mencatat kontak antara staf dan pelanggan dalam meter.
