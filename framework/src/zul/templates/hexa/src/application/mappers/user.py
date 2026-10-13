"""
Contoh mapper: mengubah data dari satu bentuk ke bentuk lain.

Gunanya:
    Mapper memisahkan bentuk data di dalam aplikasi (entity) dari bentuk
    yang dikirim keluar (DTO). Dengan begitu data sensitif, seperti hash
    password, tidak ikut terbawa ke respons.

Cara pakai:
    user = UserEntity(1, "john_doe", "john@example.com", "hashed_password")

    user_dto = UserMapper.to_dto(user)         # tanpa password_hash
    user = UserMapper.from_dto(user_dto, password_hash="hashed_password")

Menjalankan contoh di bawah:
    python -m src.application.mappers.user
"""

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Dua Bentuk Data User
# --------------------------------------------------------------------------
#
# DTO hanya membawa data yang boleh dilihat pihak luar, tanpa method
# untuk logika bisnis. Entity adalah bentuk lengkapnya di dalam
# aplikasi, di sini ia menyimpan hash password yang rahasia.
#


@dataclass
class UserDTO:
    id: int
    username: str
    email: str


class UserEntity:
    def __init__(self, id: int, username: str, email: str, password_hash: str):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash


# --------------------------------------------------------------------------
# Mapper
# --------------------------------------------------------------------------


class UserMapper:
    @staticmethod
    def to_dto(entity: UserEntity) -> UserDTO:
        """Ubah entity menjadi DTO, tanpa membawa data sensitif."""
        return UserDTO(id=entity.id, username=entity.username, email=entity.email)

    @staticmethod
    def from_dto(dto: UserDTO, password_hash: str) -> UserEntity:
        """Ubah DTO kembali menjadi entity; hash password diberikan terpisah."""
        return UserEntity(
            id=dto.id,
            username=dto.username,
            email=dto.email,
            password_hash=password_hash,
        )


if __name__ == "__main__":
    db_user = UserEntity(
        id=1,
        username="john_doe",
        email="john@example.com",
        password_hash="hashed_password123",
    )

    user_dto = UserMapper.to_dto(db_user)
    print(f"User DTO: {user_dto}")

    new_user_dto = UserDTO(id=2, username="jane_smith", email="jane@example.com")
    new_user = UserMapper.from_dto(new_user_dto, "another_hashed_password")
    print(f"User entity baru: {new_user.username}, {new_user.email}")
