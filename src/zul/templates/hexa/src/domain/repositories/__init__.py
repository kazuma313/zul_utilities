"""
Apa itu Repository Interface?

Kontrak (abstract) untuk simpan/ambil data
Hanya definisi, bukan implementasi
Implementasinya ada di Infrastructure layer

✅ Domain tidak perlu tahu database apa yang dipakai
✅ Mudah ganti database (PostgreSQL → MongoDB)
✅ Mudah di-test dengan mock
✅ Dependency Inversion Principle
"""
