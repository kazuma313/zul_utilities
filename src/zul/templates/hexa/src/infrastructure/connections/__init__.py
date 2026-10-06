"""
Koneksi yang dipakai bersama oleh beberapa adapter.

Gunanya:
    Membuat koneksi sekali lalu memakainya ulang: pool database, client
    Redis, client Milvus. Adapter di `database/` dan `external/` mengambil
    koneksi dari sini, bukan membuat sendiri.

Contoh:
    # infrastructure/connections/postgres.py
    from functools import lru_cache
    from psycopg_pool import ConnectionPool

    @lru_cache
    def get_pool() -> ConnectionPool:
        return ConnectionPool(os.environ["DATABASE_URL"])
"""
