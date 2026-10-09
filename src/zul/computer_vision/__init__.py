"""
Computer vision untuk analisis perilaku orang di video, misalnya CCTV toko.

Gunanya:
    Modul-modul yang dipisahkan dari proyek analitik video toko
    (research/computer_vision), supaya bisa dipakai di proyek lain. Setiap
    nilai masuk lewat argumen, jadi tidak ada pengaturan global.

Modul dan extra yang dibutuhkan:
    geometry    titik jangkar, zona, arah                      tanpa extra
    pose        arah kepala dan badan dari keypoint COCO-17     tanpa extra
    crossing    lintasan masuk dan keluar sebuah garis          tanpa extra
    analytics   kunjungan, perhatian, kontak, minat             tanpa extra
    config      config scene dari YAML dan validasinya          tanpa extra
    report      CSV per kejadian                                tanpa extra
    draw        anotasi frame dan masker area                   zul[vision]
    video       membaca, menulis, dan mengukur kecepatan        zul[vision]
    detection   model YOLO, YOLO-World, pose, dan ByteTrack     zul[yolo]
    weights     mengunduh bobot model ke folder proyek          zul[yolo]

Cara pakai:
    from zul.computer_vision import analytics, geometry, pose

Paket ini tidak mengimpor modul apa pun saat diimpor, jadi modul yang
butuh OpenCV atau ultralytics hanya dimuat ketika benar-benar dipakai.
"""
