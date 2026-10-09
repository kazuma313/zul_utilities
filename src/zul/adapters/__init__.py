"""
Lapisan adapter: satu-satunya tempat Zul mengimpor library pihak ketiga.

Gunanya:
    Library seperti OpenCV, RF-DETR, atau pymilvus adalah lapisan induk.
    Modul Zul lain adalah lapisan anak: mereka merangkai fungsi dari adapter
    menjadi alat yang siap dipakai, dan tidak pernah mengimpor library itu
    sendiri. Jika sebuah library perlu diubah, diganti, atau dikunci ke
    versi tertentu, yang berubah hanya satu file di folder ini.

Aturan adapter:
    - Satu file per library, dinamai sesuai library-nya, misalnya opencv.py.
    - Fungsi adapter menerima dan mengembalikan tipe Python biasa atau
      array NumPy, bukan objek library, kecuali disebut di docstring-nya.
    - Perilaku library yang perlu diubah ditulis sebagai kelas turunan di
      sini, bukan dengan mengubah file library yang ter-install.
    - Adapter hanya mengimpor library-nya, NumPy, dan adapter lain, tidak
      pernah modul Zul di luar folder ini.

Aturan ini diperiksa oleh tests/test_architecture.py. Library yang memang
dipakai langsung di luar adapter, misalnya NumPy sebagai tipe data, tercatat
di daftar EMBEDDED di test itu beserta alasannya.

Paket ini tidak mengimpor adapter apa pun saat diimpor, jadi library berat
hanya dimuat ketika adapter-nya benar-benar dipakai.
"""
