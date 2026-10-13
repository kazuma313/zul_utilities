"""
Layer Interface: pintu masuk ke aplikasi.

Gunanya:
    Menerjemahkan permintaan dari luar (HTTP, UI, CLI, bot) menjadi
    pemanggilan use case, lalu menerjemahkan hasilnya kembali. Di sinilah
    adapter infrastructure disambungkan ke use case (composition root).

Isi folder:
    http/        REST API dengan FastAPI
    playground/  mencoba agent dari halaman dokumentasi Zul
    streamlit/   UI chat dengan Streamlit
    cli/         perintah command line
    discord/     bot Discord

Aturan dependensi:
    Boleh import dari semua layer. Tidak ada layer lain yang import dari sini.
"""
