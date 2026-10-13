# Memulai proyek computer vision dari boilerplate

Boilerplate di `framework/project/computer_vision` adalah aplikasi analitik CCTV yang sudah jadi: membaca video, mendeteksi dan melacak orang, menghitung lintasan garis, kunjungan zona, perhatian ke rak, dan kontak antar orang, lalu menulis video beranotasi, CSV, dan ringkasan. Panduan ini memakai boilerplate itu sebagai awal proyek baru untuk kameramu sendiri.

Semua aturannya dirangkai dari blok `zul.computer_vision` yang dijelaskan di panduan Computer Vision lainnya. Jika yang kamu butuhkan hanya satu blok, misalnya garis penghitung, panduan [Menghitung dengan garis dan poligon](menghitung-dengan-garis-dan-poligon.md) lebih cocok.

**Sebelum mulai:** kamu butuh Python 3.11 atau lebih baru, [uv](https://github.com/astral-sh/uv), Git, dan satu file video dari kameramu.

## Menyalin boilerplate

1. Salin folder `framework/project/computer_vision` dari repository Zul ke folder proyekmu, misalnya `cctv-toko`.

2. Install dari dalam folder itu:

    ```shell
    cd cctv-toko
    uv venv
    uv pip install -e ".[dev]"
    ```

    Perintah itu meng-install Zul dengan extra `detection` dari GitHub, termasuk PyTorch, dan mendaftarkan perintah `cctv`. Di Windows, PyTorch dari PyPI hanya berjalan di CPU.

3. Pastikan test-nya lulus:

    ```shell
    uv run pytest
    ```

    Test memakai video sintetis dan detektor palsu, jadi tidak butuh model atau GPU.

## Menulis config kamera

Setiap kamera punya satu file di `configs/`. `configs/base.yaml` berisi pengaturan yang sama untuk semua kamera, misalnya ambang deteksi dan warna.

1. Taruh videomu di `videos/`, lalu salin `configs/entrance.yaml` menjadi config kameramu, misalnya `configs/kasir.yaml`.

2. Ambil satu frame untuk mencari koordinat zona dan garis:

    ```python
    from zul.computer_vision.video import read_frames, save_image

    _, _, frame = next(read_frames("videos/kasir.mp4", start=300))
    save_image("outputs/frame-kasir.png", frame)
    ```

    Buka gambar itu di editor gambar mana pun yang menampilkan posisi kursor, lalu catat titik-titik sudut zona dalam piksel.

3. Isi config kamera:

    ```yaml title="configs/kasir.yaml"
    SOURCE_VIDEO_PATH: videos/kasir.mp4

    IGNORE_POLYGONS: []

    ZONES:
      - name: antrean
        polygon: [[120, 300], [480, 300], [480, 700], [120, 700]]

    LINES:
      - name: keluar
        start: [900, 650]
        end: [1250, 650]

    settings:
      DWELL_THRESHOLD_S: 5.0
    ```

    `ZONES` dan `LINES` boleh kosong. Kunci di bagian `settings:` menimpa nilai yang sama di `configs/base.yaml`.

4. Periksa config-nya tanpa memuat model:

    ```shell
    uv run cctv check configs/kasir.yaml
    ```

    Keluarannya menyebut zona, garis, dan pengaturan yang ditimpa, serta apakah file videonya ada:

    ```text
    {
      "kamera": "kasir",
      "video": "videos/kasir.mp4",
      "video_ada": true,
      "zona": [
        "antrean"
      ],
      "garis": [
        "keluar"
      ],
      "area_diabaikan": 0,
      "pengaturan_ditimpa": [
        "DWELL_THRESHOLD_S"
      ]
    }
    ```

    Salah ketik di nama pengaturan, tipe yang salah, atau poligon dengan kurang dari tiga titik dilaporkan di sini, dengan kode keluar 2.

## Menjalankan

Proses sebagian kecil video dulu untuk memeriksa letak zona dan garis:

```shell
uv run cctv run configs/kasir.yaml --mode both --start 0 --end 300 --stride 3
```

Saat pertama dijalankan, bobot RF-DETR diunduh ke cache, sekitar 164 MB. `--mode both` membuka jendela pratinjau sekaligus menulis file; tekan `q` untuk berhenti lebih awal. Setelah letaknya benar, proses seluruh video dengan `--mode save`.

Hasilnya ada di `outputs/kasir/`:

| File | Isi |
|---|---|
| `annotated.mp4` | Video beranotasi. |
| `crossings.csv` | Setiap lintasan garis: frame, waktu, id track, garis, dan arah. |
| `visits.csv` | Setiap kunjungan zona, dengan waktu masuk dan keluar. |
| `attention.csv` | Setiap rentang menghadap target zona. |
| `contacts.csv` | Setiap kontak antar orang, jika `PROXIMITY_METRES` lebih dari 0. |
| `summary.json` | Angka akhir per garis dan per zona. |

## Menambah aturan

Aturan per frame ada di `SceneAnalytics.update` di `src/cctv/analytics.py`. Untuk aturan baru, rangkai blok yang sudah ada, misalnya `ConditionTimer` untuk mengukur lama sebuah kondisi benar:

1. Buat timer-nya di `SceneAnalytics.__init__`.
2. Hitung kondisinya untuk setiap orang di `update`, lalu panggil `timer.update(...)`.
3. Tambahkan catatan yang selesai ke `Finished`, dan tulis ke CSV baru di `pipeline.py`.
4. Tulis test-nya di `tests/test_analytics.py` dengan deteksi buatan, seperti test yang sudah ada.

Daftar blok yang tersedia ada di [referensi Computer Vision](../referensi/computer-vision.md).

## Menjalankan di server

Di server tanpa layar, pakai Docker dengan mode `save`:

```shell
docker compose run --rm cctv run configs/kasir.yaml --mode save
```

`docker-compose.yml` memakai GPU NVIDIA dan butuh NVIDIA Container Toolkit di server. Untuk server tanpa GPU, pakai `docker compose -f docker-compose.cpu.yml` dengan perintah yang sama, dan tambahkan `--stride` karena prosesnya jauh lebih lambat.

## Meminta code assistant memakainya

Jika code assistant-mu tersambung ke [MCP server Zul](../tutorial/code-assistant.md), ia bisa membaca boilerplate ini dengan tool `list_projects` dan `read_project`. Contoh permintaan:

```text
Buat aplikasi penghitung pengunjung di depan kasir. Tiru boilerplate computer_vision dari Zul.
```

## Halaman terkait

- [Mendeteksi dan melacak orang](mendeteksi-dan-melacak-orang.md)
- [Mengukur durasi per orang](mengukur-durasi.md)
- [Referensi: MCP server](../referensi/mcp.md), untuk `list_projects` dan `read_project`
