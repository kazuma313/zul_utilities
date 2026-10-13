"""
Analitik video CCTV yang dibangun dari blok `zul.computer_vision`.

Gunanya:
    Boilerplate aplikasi: config per kamera, deteksi dan pelacakan orang,
    garis dan zona penghitung, lama kunjungan, perhatian ke rak, kontak
    antar orang, video beranotasi, dan CSV. Salin folder proyek ini untuk
    memulai aplikasi computer vision baru, lalu ubah config dan aturannya.

Modul:
    settings    config dasar, config kamera, dan geometri scene
    detector    RF-DETR, atau detektor lain dengan bentuk yang sama
    analytics   aturan per frame dan ringkasan akhir
    render      overlay di setiap frame
    pipeline    perulangan frame dan semua keluarannya
    cli         perintah `cctv run` dan `cctv check`

Cara pakai:
    cctv check configs/entrance.yaml
    cctv run configs/entrance.yaml --mode both
"""
