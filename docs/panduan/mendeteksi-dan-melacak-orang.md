# Mendeteksi dan melacak orang

Fungsi lain di `zul.computer_vision` menerima kotak, keypoint, dan id track. Halaman ini membuat ketiganya dari video: membaca frame, mendeteksi orang dengan model YOLO, memberi id yang sama untuk orang yang sama di setiap frame, lalu menulis video beranotasi.

**Sebelum mulai:** kamu butuh:

- Python 3.11 atau lebih baru.
- File video, misalnya mp4 dari CCTV.
- GPU NVIDIA, sangat disarankan. Di CPU, deteksi jauh lebih lambat.

## Menyiapkan model

1. Install Zul dengan extra `yolo`. Extra ini sudah termasuk extra `vision` untuk OpenCV:

    ```shell
    pip install "zul[yolo] @ git+https://github.com/kazuma313/zul_utilities.git"
    ```

    Extra `yolo` meng-install ultralytics, yang ikut meng-install PyTorch. Di Windows, PyTorch dari PyPI hanya berjalan di CPU. Untuk GPU NVIDIA, install PyTorch versi CUDA dulu dengan perintah dari [pytorch.org](https://pytorch.org/get-started/locally/), lalu jalankan perintah di atas.

2. Pastikan PyTorch melihat GPU-mu:

    ```shell
    python -c "import torch; print(torch.cuda.is_available())"
    ```

    Perintah itu mencetak `True` jika GPU bisa dipakai.

3. Unduh bobot model ke folder `models`:

    ```python
    from zul.computer_vision.weights import fetch

    print(fetch("models/yolo11m-pose.pt"))
    ```

    Hasilnya `(True, ...)` dengan keterangan `diunduh` dan ukuran file, sekitar 42 MB. Jika file sudah ada, keterangannya `ada` dan tidak ada yang diunduh. Tanpa `fetch`, ultralytics mengunduh bobot ke folder tempat kamu menjalankan script, dan mengunduhnya lagi saat kamu pindah folder.

## Mendeteksi dan melacak orang di video

1. Simpan script berikut sebagai `lacak_orang.py`:

    ```python title="lacak_orang.py"
    from zul.computer_vision import draw, geometry
    from zul.computer_vision.detection import (
        ByteTracker,
        detect,
        load_model,
        standardise_frame,
    )
    from zul.computer_vision.video import FpsMeter, VideoInfo, VideoWriter, read_frames

    VIDEO = "videos/toko.mp4"
    START, END, STRIDE = 0, 900, 3

    info = VideoInfo.from_path(VIDEO)
    output = info.slice(START, END, STRIDE)
    model = load_model("models/yolo11m-pose.pt")
    tracker = ByteTracker(frame_rate=output.fps)
    trace = draw.TrackTrace(length=30)
    meter = FpsMeter()
    seen = set()

    with VideoWriter("outputs/lacak_orang.mp4", output) as video:
        for frame_number, timestamp_s, frame in read_frames(VIDEO, START, END, STRIDE):
            meter.start()
            prepared, scale = standardise_frame(frame)
            people = detect(model, prepared, confidence=0.2).rescale(scale)
            people = tracker.update(people)
            seen.update(people.tracker_id.tolist())

            annotated = frame.copy()
            trace.update(geometry.foot_points(people.xyxy), people.tracker_id)
            draw.draw_traces(annotated, trace)
            for box, track_id in zip(people.xyxy, people.tracker_id):
                colour = draw.track_color(track_id)
                draw.draw_labelled_box(annotated, box, f"#{track_id}", colour)
            meter.stop()
            lines = [f"{len(people)} orang di frame", f"{len(seen)} id sejauh ini"]
            draw.draw_corner_text(annotated, lines)
            draw.draw_corner_text(
                annotated, [f"{meter.fps:.1f} fps"], corner=draw.Corner.TOP_RIGHT
            )
            video.write(annotated)

    print(f"{video.frames} frame, {len(seen)} id track, {meter.fps:.1f} fps")
    ```

    Ganti `VIDEO` dengan path videomu. `START`, `END`, dan `STRIDE` memilih frame 0 sampai 900, satu dari setiap tiga frame. Untuk seluruh video, isi `END = None`.

2. Jalankan script-nya:

    ```shell
    python lacak_orang.py
    ```

    Script itu mencetak jumlah frame yang diproses, jumlah id track berbeda, dan kecepatan rata-rata 30 frame terakhir. Untuk video toko 1280×720 di RTX 3060 Laptop, hasilnya:

    ```text
    300 frame, 19 id track, 45.0 fps
    ```

3. Buka `outputs/lacak_orang.mp4`. Setiap orang punya kotak dan id dengan warna yang tetap, jejak gerak kakinya, dan jumlah orang di kiri atas.

Setiap frame melewati langkah yang sama:

| Langkah | Fungsi | Gunanya |
|---|---|---|
| Membaca frame | `read_frames` | Frame demi frame, beserta nomor frame asli dan detiknya dari awal video. |
| Ukuran input | `standardise_frame`, `Detections.rescale` | Memperkecil frame ke 640 piksel untuk model, lalu mengembalikan koordinatnya ke ukuran asli. |
| Deteksi | `detect` | Kotak orang, dan keypoint jika modelnya model pose. |
| Tracking | `ByteTracker.update` | Id yang sama untuk orang yang sama di setiap frame. Deteksi yang belum dikonfirmasi dibuang. |
| Menulis video | `VideoWriter` | Video hasil dengan FPS dibagi `STRIDE`, jadi durasinya sama dengan video sumber. |

Hasil `tracker.update` adalah `Detections`, wadah array NumPy: `people.xyxy`, `people.confidence`, `people.tracker_id`, dan untuk model pose, `people.keypoints_xy` serta `people.keypoints_conf`. Semua array sejajar per baris, dan `people[mask]` memotong semuanya sekaligus.

Jumlah id track bisa lebih besar dari jumlah orang sebenarnya. Orang yang lama tertutup orang lain bisa kembali dengan id baru.

## Memilih model

`load_model` memuat tiga jenis model:

| Model | Hasil | Kapan dipakai |
|---|---|---|
| Model pose, misalnya `yolo11m-pose.pt` | Kotak orang dan 17 keypoint per orang. | Saat kamu butuh [arah hadap](membaca-arah-hadap-dan-jarak.md) atau kerangka pose. |
| Model deteksi biasa, misalnya `yolo11m.pt` | Kotak untuk 80 kelas COCO. | Saat kamu hanya butuh kotak. Isi `classes=[0]` di `detect` untuk orang saja. |
| YOLO-World, misalnya `yolov8l-worldv2.pt` | Kotak untuk kelas yang kamu tulis sebagai teks. | Saat kelasnya tidak ada di COCO. Panggil `load_model(path, prompts=["person"])`. |

YOLO-World butuh paket CLIP dari ultralytics. Tanpa paket itu, `load_model` berhenti dengan `ImportError` berisi perintah instalasinya.

## Mempercepat proses

- **Lewati frame.** `STRIDE = 3` memproses satu dari setiap tiga frame. Nilai yang lebih besar mempercepat proses, tetapi track lebih mudah tertukar saat orang bergerak cepat.
- **Pertahankan ukuran input 640.** `standardise_frame` memperkecil frame ke ukuran latih model. Pada video 1280×720, langkah ini menaikkan kecepatan dari 8,3 menjadi 13,9 frame per detik, dengan hitungan yang sama.
- **Hitamkan area yang tidak diukur.** Lihat [Menghitamkan dan menyamarkan area](menghitamkan-dan-menyamarkan-area.md).

## Menyimpan pengaturan di YAML

Untuk memakai script yang sama di beberapa kamera, simpan pengaturannya di YAML. `load_scene` menggabungkan file dasar dengan file per kamera, dan `validate_settings` memeriksa nama dan tipenya terhadap dataclass sebelum model dimuat:

```yaml title="base.yaml"
settings:
  POSE_MODEL: models/yolo11m-pose.pt
  CONFIDENCE: 0.20
  STRIDE: 3
```

```yaml title="pintu.yaml"
VIDEO: videos/pintu.mp4
settings:
  CONFIDENCE: 0.25
```

```python
from dataclasses import dataclass

from zul.computer_vision.config import load_scene, validate_settings


@dataclass(frozen=True)
class Settings:
    POSE_MODEL: str
    CONFIDENCE: float
    STRIDE: int


scene = load_scene("base.yaml", "pintu.yaml")
settings = validate_settings(scene["settings"], Settings)
print(scene["VIDEO"], settings, scene["overrides"])
```

Script itu mencetak:

```text
videos/pintu.mp4 {'POSE_MODEL': 'models/yolo11m-pose.pt', 'CONFIDENCE': 0.25, 'STRIDE': 3} ['CONFIDENCE']
```

`overrides` berisi pengaturan dasar yang ditimpa file kamera. Nama yang salah ketik, pengaturan yang belum diisi, atau tipe yang salah menghentikan script dengan `ConfigError`, misalnya `settings: kunci tidak dikenal: CONFIDENSE (maksudnya CONFIDENCE?)`.

## Mengatasi masalah

### FileNotFoundError: video tidak bisa dibuka

Path video dibaca relatif terhadap folder tempat kamu menjalankan script. Jalankan script dari folder proyek, atau tulis path lengkapnya.

### Prosesnya sangat lambat

Periksa langkah 2 di [Menyiapkan model](#menyiapkan-model). Jika `torch.cuda.is_available()` mencetak `False`, model berjalan di CPU.

## Halaman terkait

- [Menggambar di frame](menggambar-di-frame.md) untuk fungsi gambar lainnya.
- [Menghitung dengan garis dan poligon](menghitung-dengan-garis-dan-poligon.md) untuk menghitung orang dari hasil deteksi.
- [Referensi Computer Vision](../referensi/computer-vision.md#detection) untuk semua parameter deteksi, tracking, dan video.
