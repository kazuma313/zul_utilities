# 📖 Cara Pakai `folder_migrator`

Panduan praktis memindahkan folder besar dari satu tempat ke tempat lain — aman, bisa dilanjut kalau berhenti, dan tahan crash. Baca dari atas ke bawah; 5 menit selesai.

> **Ringkasnya:** isi `config.yaml` → jalankan `python main.py` → selesai. Kalau berhenti, jalankan lagi perintah yang sama, otomatis lanjut.

---

## 1. Sekali setup

```bash
# Masuk ke folder tool
cd research/tools/folder_migrator

# Install (butuh Python 3.11+). PyYAML hanya perlu kalau pakai config .yaml
pip install -r requirements.txt
```

Cek berhasil:

```bash
python main.py --help
```

---

## 2. Langkah pakai (3 langkah)

### Langkah 1 — Edit `config.yaml`

Buka `config.yaml`, isi minimal **dua baris** ini:

```yaml
source: "E:/data/foto_lama"        # folder ASAL (isinya akan dipindah)
destination: "E:/backup/foto"      # folder TUJUAN (dibuat otomatis kalau belum ada)
```

> 💡 **Windows:** pakai garis miring depan `/` (bukan `\`), contoh `E:/data/foto`. Lebih aman di YAML.

### Langkah 2 — Jalankan

```bash
python main.py
```

atau kalau file config-nya beda nama/lokasi:

```bash
python main.py --config C:/konfig/migrasi.yaml
```

### Langkah 3 — Lihat hasil

Selama jalan kamu akan lihat baris progress:

```text
Processed: 12345 | moved: 12315 | current: 2024/img123.png
```

Setelah selesai:

```text
Migration finished: 498765 moved, 27 skipped, 3 failed
```

Selesai. Isi `source` sudah pindah ke `destination`. ✅

---

## 3. Kalau proses berhenti (mati listrik / CTRL+C / error)

**Tidak perlu mulai ulang dari nol.** Cukup jalankan lagi perintah yang sama:

```bash
python main.py
```

Program membaca file `checkpoint.json` dan **lanjut dari posisi terakhir** — file yang sudah pindah tidak diulang. Kalau migrasi sudah benar-benar selesai dan kamu ingin mulai fresh untuk tugas baru, hapus `checkpoint.json` dulu.

---

## 4. Semua pengaturan di `config.yaml`

| Pengaturan | Arti | Default |
|------------|------|---------|
| `source` | Folder asal (wajib, harus sudah ada) | — |
| `destination` | Folder tujuan (wajib) | — |
| `include` | Regex file yang **boleh** dipindah | `[".*"]` (semua) |
| `exclude` | Regex file/folder yang **dilewati** | kosong |
| `follow_symlink` | Ikuti symbolic link? | `false` |
| `overwrite` | Timpa file yang sudah ada di tujuan? | `false` (dilewati) |
| `workers` | Jumlah proses paralel (makin besar makin cepat, sampai batas disk) | `4` |
| `checkpoint_path` | Lokasi file resume | `checkpoint.json` |
| `log_path` | Lokasi file log | `logs/move_folder.log` |
| `checkpoint_every` | Simpan progress tiap N file | `500` |

---

## 5. Contoh skenario umum

**a. Pindahkan semua, tapi lewati file/folder sampah**

```yaml
source: "E:/project_lama"
destination: "D:/arsip/project_lama"
exclude:
  - "__pycache__"
  - "node_modules"
  - "\\.venv"
  - "\\.DS_Store"
  - "\\.git$"
```

**b. Pindahkan HANYA gambar**

```yaml
include:
  - "\\.(jpg|jpeg|png|gif|webp)$"
```

**c. Timpa file yang sudah ada di tujuan**

```yaml
overwrite: true
```

**d. Lebih cepat untuk jutaan file (SSD/NVMe)**

```yaml
workers: 8
```

> ℹ️ Aturan main regex: sebuah file dipindah kalau **cocok salah satu `include`** DAN **tidak cocok `exclude` mana pun**. Folder yang cocok `exclude` tidak akan dimasuki sama sekali.

---

## 6. Membaca log

Semua kejadian tersimpan di `logs/move_folder.log` (dan tampil di layar):

```text
2026-07-28 09:12:01 | INFO     | Starting migration: E:/data/src -> D:/backup
2026-07-28 09:12:03 | WARNING  | Skipped documents/old.tmp (destination exists)
2026-07-28 09:12:07 | ERROR    | Failed 2024/locked.png: [Errno 13] Permission denied
2026-07-28 09:14:55 | INFO     | Migration finished: 498765 moved, 27 skipped, 3 failed
```

Arti level: **INFO** = jalan normal · **WARNING** = ada yang dilewati (mis. file sudah ada / ter-exclude) · **ERROR** = satu file gagal (proses tetap lanjut, tidak crash).

> Mau lihat setiap file yang berhasil dipindah? Detail per-file ada di level `DEBUG` (sengaja disembunyikan agar log tetap rapi saat jutaan file).

---

## 7. Pakai dari kode Python (opsional)

```python
from folder_migrator import FolderMover

FolderMover.from_config_file("config.yaml").run()
```

---

## 8. Troubleshooting cepat

| Pesan / Gejala | Penyebab & solusi |
|----------------|-------------------|
| `Configuration error: 'source' directory does not exist` | Path `source` salah/typo. Pastikan folder ada & pakai `/`. |
| `'destination' must not be ... inside 'source'` | Folder tujuan tidak boleh berada di dalam folder asal. Pilih lokasi terpisah. |
| `PyYAML is required for YAML configs` | Jalankan `pip install -r requirements.txt`, atau pakai config `.json`. |
| Banyak baris `WARNING ... destination exists` | File sudah ada di tujuan & `overwrite: false`. Set `overwrite: true` bila ingin menimpa. |
| Ada `ERROR Permission denied` | File sedang dipakai/terkunci. Tutup aplikasi terkait lalu jalankan ulang (resume otomatis). |
| Ingin mulai benar-benar dari awal | Hapus `checkpoint.json` sebelum menjalankan. |

---

## 9. Tips aman

- **Coba dulu di folder kecil** sebelum migrasi besar, untuk memastikan pola `include`/`exclude` sudah benar.
- **`overwrite: false`** (default) aman — file di tujuan tidak akan tertimpa.
- Ini operasi **MOVE**, bukan copy: setelah berhasil, file hilang dari `source`. Kalau ingin tetap ada salinannya, backup dulu.

---

Butuh detail arsitektur, alasan desain, atau mekanisme resume secara teknis? Lihat **`README.md`** di folder yang sama.
