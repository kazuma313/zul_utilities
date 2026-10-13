# Boilerplate computer vision CCTV

Aplikasi analitik video CCTV yang dibangun dari blok `zul.computer_vision`. Satu pipeline dipakai untuk semua kamera; yang membedakan kamera hanya config-nya. Salin folder ini untuk memulai proyek computer vision baru.

Untuk setiap kamera, aplikasi ini menghitung:

| Hasil | Dari | Contoh pertanyaan |
|---|---|---|
| Lintasan garis, masuk dan keluar | `LINES` | Berapa orang masuk toko? |
| Kunjungan zona dan lamanya | `ZONES` | Berapa orang berhenti di depan toko minimal 2 detik? |
| Perhatian: lama menghadap target zona | `ZONES` dan keypoint pose | Rak mana yang paling lama diperhatikan? |
| Kontak: dua orang berdekatan | `PROXIMITY_METRES` | Berapa kali pengunjung didekati orang lain? |

Esensinya berasal dari proyek CCTV toko sepatu di `research/computer_vision`, yang memakai YOLO. Boilerplate ini memakai RF-DETR (Apache 2.0) dan ByteTrack milik Zul, sehingga tidak ada dependency berlisensi AGPL.

## Struktur

| Path | Isi |
|---|---|
| `configs/base.yaml` | Pengaturan yang sama untuk semua kamera: model, pelacakan, aturan, warna. |
| `configs/entrance.yaml`, `configs/interior.yaml` | Contoh config kamera: video sumber, zona, garis, dan area yang diabaikan. |
| `src/cctv/settings.py` | Memuat dan memeriksa config. Salah ketik dan tipe yang salah ketahuan sebelum model dimuat. |
| `src/cctv/detector.py` | RF-DETR lewat `zul.computer_vision.detection`. |
| `src/cctv/analytics.py` | Aturan per frame: garis, zona, perhatian, kontak, dan ringkasan akhir. Tanpa IO, jadi mudah diuji. |
| `src/cctv/render.py` | Overlay di setiap frame. |
| `src/cctv/pipeline.py` | Perulangan frame dan semua keluarannya. |
| `src/cctv/cli.py` | Perintah `cctv run` dan `cctv check`. |
| `tests/` | Test dengan video sintetis dan detektor palsu, tanpa model dan tanpa GPU. |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.cpu.yml` | Menjalankan di server, dengan atau tanpa GPU. |

## Memulai proyek baru

1. Salin folder ini ke lokasi proyekmu, lalu install:

    ```bash
    uv venv
    uv pip install -e ".[dev]"
    ```

    Perintah itu meng-install Zul dengan extra `detection` dari GitHub, termasuk PyTorch. Di Windows, PyTorch dari PyPI hanya berjalan di CPU.

2. Taruh video di `videos/`, lalu salin `configs/entrance.yaml` menjadi config kameramu. Ubah `SOURCE_VIDEO_PATH`, zona, dan garisnya dalam koordinat piksel video itu.

3. Periksa config-nya tanpa memuat model:

    ```bash
    cctv check configs/kamera.yaml
    ```

    Keluarannya menyebut zona, garis, dan pengaturan yang ditimpa, serta apakah file videonya ada.

4. Proses sebagian kecil video dulu:

    ```bash
    cctv run configs/kamera.yaml --mode both --start 0 --end 300 --stride 3
    ```

    Bobot RF-DETR diunduh ke cache saat pertama dipakai, sekitar 164 MB.

## Menjalankan

| Mode | Hasil |
|---|---|
| `--mode live` | Jendela pratinjau saja; tekan `q` atau Esc untuk berhenti. |
| `--mode save` | Video beranotasi, CSV, dan ringkasan, tanpa jendela. |
| `--mode both` | Pratinjau dan file. |

`--stride N` memproses setiap frame ke-N, dan video hasilnya ditulis dengan fps dibagi N, sehingga durasinya sama dengan sumber. `--start` dan `--end` memilih rentang frame.

Keluaran ditulis ke `outputs/<kamera>/`:

| File | Isi |
|---|---|
| `annotated.mp4` | Video beranotasi (mode `save` dan `both`). |
| `crossings.csv` | Setiap lintasan garis: frame, waktu, id track, garis, arah. |
| `visits.csv` | Setiap kunjungan zona, dengan waktu masuk dan keluar. |
| `attention.csv` | Setiap rentang menghadap target zona, dengan lama aktifnya. |
| `contacts.csv` | Setiap kontak antar orang, jika `PROXIMITY_METRES` lebih dari 0. |
| `summary.json` | Angka akhir per garis dan per zona. |

Dengan Docker, mode `save` dipakai karena container tidak punya layar:

```bash
docker compose run --rm cctv run configs/interior.yaml --mode save
```

## Mengubah aturan

- **Ambang dan warna:** ubah `configs/base.yaml`, atau timpa di config kamera lewat bagian `settings:`.
- **Aturan baru:** tambahkan ke `SceneAnalytics.update` di `analytics.py`, dengan blok dari `zul.computer_vision`, misalnya `ConditionTimer` untuk kondisi yang perlu diukur lamanya. Fungsi yang tersedia ada di [referensi computer vision](https://zulkit.my.id/referensi/computer-vision/).
- **Model lain:** buat kelas dengan `__call__(frame) -> Detections`, lalu berikan ke `run` sebagai pengganti `load_detector`.

## Test

```bash
uv run pytest
```

Di dalam repository Zul, jalankan dari root repository dengan `uv run pytest framework/project/computer_vision`.
