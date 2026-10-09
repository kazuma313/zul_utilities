# Mengubah perilaku library pihak ketiga

Zul memakai library seperti OpenCV, ultralytics, dan pymilvus lewat satu lapisan: `src/zul/adapters/`. Setiap library hanya diimpor di satu file adapter. Jika kamu atau kolaboratormu perlu mengubah perilaku sebuah library untuk kebutuhan proyek, perubahannya ditulis di adapter itu, bukan di dalam paket library yang ter-install.

Panduan ini untuk orang yang mengubah Zul sendiri. Alasan di balik lapisan ini ada di [Lapisan adapter](../konsep/lapisan-adapter.md).

**Sebelum mulai:** kamu butuh Zul dari source, dengan cara di [Berkontribusi](berkontribusi.md#menyiapkan-lingkungan).

Jangan mengubah file di dalam `.venv/Lib/site-packages/`. Perubahan di sana hilang saat paket di-install ulang, dan tidak pernah sampai ke kolaborator.

## Memilih cara mengubah

Pakai cara pertama yang cukup untuk kebutuhanmu:

| Cara | Kapan dipakai | Yang berubah |
|---|---|---|
| [Lewat parameter](#mengubah-lewat-parameter) | Library-nya sudah menyediakan pilihan untuk perilaku itu. | Pemanggilan di adapter. |
| [Kelas turunan di adapter](#mengubah-lewat-kelas-turunan) | Perubahan kecil di satu atau dua method sebuah kelas. | File adapter. |
| [Salinan di `_vendor`](#menyalin-kode-library-ke-zul) | Perubahan besar, tetapi hanya di satu atau dua file library. | Salinan file itu di Zul. |
| [Fork library](#memakai-fork-library) | Perubahan menyebar di banyak file library. | Repository fork dan versi yang dikunci. |

Ketiga cara pertama hidup di repository Zul, jadi kolaborator mendapat perubahan yang sama begitu mereka memakai versi Zul yang sama.

## Mencari adapter sebuah library

1. Cari file adapter untuk library itu di `src/zul/adapters/`. Nama file mengikuti nama library, misalnya `opencv.py` untuk OpenCV dan `ultralytics.py` untuk ultralytics.

2. Pastikan library itu memang ditangani di file tersebut. Daftar lengkapnya ada di `ADAPTERS` di `tests/test_architecture.py`:

    ```python
    ADAPTERS = {
        "opencv": {"cv2"},
        "ultralytics": {"ultralytics"},
        "yaml": {"yaml"},
        ...
    }
    ```

3. Cari fungsi adapter yang dipanggil modul Zul. Misalnya, `ByteTracker` di `zul/computer_vision/detection.py` memanggil `create_tracker` dan `track` dari `zul/adapters/ultralytics.py`.

## Mengubah lewat parameter

Jika library sudah punya pilihan untuk perilaku yang kamu butuhkan, teruskan pilihan itu dari adapter, lalu dari modul Zul yang memakainya.

Contohnya, ambang `ByteTracker` diteruskan ke `create_tracker` di adapter, lalu ke `BYTETracker` milik ultralytics. Untuk membuka pilihan baru, tambahkan parameter dengan nilai bawaan yang sama dengan perilaku sekarang, supaya kode yang sudah ada tidak berubah hasilnya.

## Mengubah lewat kelas turunan

Untuk mengubah sebagian kecil perilaku sebuah kelas library, turunkan kelas itu di adapter. Contoh berikut mengubah cara tracker mencocokkan deteksi dengan track, dengan menurunkan method `get_dists` milik `BYTETracker`:

1. Buka `src/zul/adapters/ultralytics.py` dan cari kelas `ZulBYTETracker`. Kelas ini sudah menjadi turunan `BYTETracker`, dan semua tracker Zul dibuat dari kelas ini.

2. Tambahkan method yang ingin diubah:

    ```python
    class ZulBYTETracker(BYTETracker):
        """BYTETracker milik ultralytics, dengan Zul sebagai kelas turunannya."""

        def get_dists(self, tracks, detections):
            dists = super().get_dists(tracks, detections)
            # perubahan khusus proyek, misalnya bobot jarak yang berbeda
            return dists
    ```

3. Tulis test yang membuktikan perilaku barunya, misalnya di `tests/test_computer_vision.py`, dengan deteksi buatan.

4. Jalankan test arsitektur dan test modul itu:

    ```shell
    uv run pytest tests/test_architecture.py tests/test_computer_vision.py
    ```

Kelas turunan tetap memakai kode library yang ter-install, jadi ia ikut rusak jika method induknya berubah di versi library berikutnya. Karena itu Zul mengunci versi library yang bagian internalnya dipakai, misalnya `ultralytics>=8.4.120,<8.5`. Test `test_ultralytics_internals_used_by_the_adapter_still_exist` gagal lebih dulu jika method yang dipakai hilang.

## Menyalin kode library ke Zul

Jika perubahannya terlalu besar untuk kelas turunan, salin file library yang perlu diubah ke `src/zul/adapters/_vendor/`:

1. Buat folder untuk library itu, misalnya `src/zul/adapters/_vendor/bytetrack/`.

2. Salin file yang perlu diubah ke folder itu, beserta file lisensi asli library-nya sebagai `LICENSE`. Test `test_vendored_libraries_keep_their_license` gagal jika file lisensi tidak ada.

3. Tulis di bagian atas setiap file salinan: dari library dan versi mana file itu berasal, dan apa yang diubah.

4. Ubah adapter supaya memakai salinan itu, bukan modul library-nya.

Salinan tidak ikut diperbarui saat library-nya diperbarui. Perbaikan dari versi library yang lebih baru harus kamu salin sendiri.

## Memakai fork library

Jika perubahannya menyebar di banyak file library:

1. Fork repository library itu di GitHub, misalnya ke `kazuma313/ultralytics`.

2. Buat perubahanmu di fork, lalu beri tag yang menyebut versi asal dan versi perubahanmu, misalnya `v8.4.120-zul.1`.

3. Arahkan dependency ke tag itu di `pyproject.toml`:

    ```toml
    [tool.uv.sources]
    ultralytics = { git = "https://github.com/kazuma313/ultralytics", tag = "v8.4.120-zul.1" }
    ```

4. Jalankan `uv lock`, lalu commit `pyproject.toml` dan `uv.lock` bersama. Kolaborator mendapat fork yang sama saat menjalankan `uv sync`.

Paket di PyPI tidak boleh bergantung pada URL git. Jika Zul nanti diterbitkan ke PyPI, fork-nya juga harus diterbitkan dengan nama lain. Usahakan juga perubahanmu diajukan ke library aslinya, supaya fork bisa ditinggalkan.

## Menambah library baru

Untuk memakai library yang belum dipakai Zul:

1. Buat file adapter baru di `src/zul/adapters/`, dinamai sesuai library-nya. Hanya file ini yang mengimpor library itu.

2. Tulis fungsi adapter yang menerima dan mengembalikan tipe Python biasa atau array NumPy, bukan objek library.

3. Tambahkan satu baris ke `ADAPTERS` di `tests/test_architecture.py`, berisi nama adapter dan nama paket teratas yang diimpornya.

4. Tambahkan library ke extra yang sesuai di `pyproject.toml`, lalu tambahkan adapter itu ke `EXTRA_MODULES` di `tests/test_dependencies.py`.

5. Jalankan semua test:

    ```shell
    uv run pytest tests
    ```

`test_third_party_libraries_are_imported_only_in_adapters` gagal jika modul Zul lain mengimpor library itu langsung, dan pesannya menyebut modul serta library-nya.

## Memeriksa lisensi

Mengubah kode library, lewat kelas turunan, salinan, atau fork, berarti membuat turunan dari kode itu. Periksa lisensinya sebelum perubahan dibagikan:

- ultralytics berlisensi AGPL-3.0. Kode turunan yang dibagikan, atau dijalankan sebagai layanan yang dipakai orang lewat jaringan, wajib dibuka dengan lisensi AGPL juga.
- Library berlisensi MIT, BSD, atau Apache 2.0 membolehkan perubahan, asalkan pemberitahuan lisensinya tetap disertakan.

## Halaman terkait

- [Lapisan adapter](../konsep/lapisan-adapter.md) untuk alasan di balik aturan ini dan daftar library yang dipakai langsung.
- [Berkontribusi](berkontribusi.md) untuk menjalankan test dan mengirim perubahan.
