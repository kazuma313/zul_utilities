"""
DTO (Data Transfer Object): bentuk data yang melintas antar layer.

Gunanya:
    Memisahkan bentuk data yang diterima atau dikirim keluar dari entity
    domain, sehingga perubahan API tidak ikut mengubah aturan bisnis.
    DTO hanya membawa data dan validasinya, tanpa logika bisnis.

Cara pakai:
    Buat satu file per konsep, misal `order.py` berisi `OrderDTO`.
    Lihat `user.py` untuk contoh DTO Pydantic dengan validasi.

Contoh:
    from src.application.dto.user import UserDTO

    user = UserDTO(first_name="John", lastName="Doe", age=31)
    user.model_dump()   # {'first_name': 'John', 'last_name': 'Doe', 'age': 31}
"""
