"""
REST API dengan FastAPI.

Isi folder:
    main.py        membuat aplikasi dan mendaftarkan router
    routers/       alamat endpoint (path, method, model request/response)
    controllers/   merakit dependensi dan memanggil use case

Menjalankan:
    uvicorn src.interface.http.main:app --reload
    Dokumentasi interaktif tersedia di http://localhost:8000/docs
"""
