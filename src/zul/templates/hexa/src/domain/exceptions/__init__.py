"""
Error khusus domain: pelanggaran aturan bisnis.

Gunanya:
    Memberi nama pada setiap aturan bisnis yang dilanggar, supaya pemanggil
    bisa menangani kasusnya satu per satu dan tidak menebak dari
    `Exception` umum.

Cara pakai:
    Lempar dari use case atau entity saat aturan bisnis dilanggar. Semua
    turunan `DomainError` otomatis menjadi respons HTTP 400 lewat handler
    di `src/interface/http/main.py`, jadi controller tidak perlu try/except.

Contoh menambah error baru:
    class OrderAlreadyPaidError(DomainError):
        def __init__(self, order_id: str) -> None:
            super().__init__(f"Order {order_id} sudah dibayar")

Contoh melemparnya:
    if not message.strip():
        raise EmptyMessageError()
"""

# --------------------------------------------------------------------------
# Error Dasar
# --------------------------------------------------------------------------
#
# Semua error domain diturunkan dari kelas ini. Layer interface cukup
# menangkap DomainError sekali untuk mengubah seluruh pelanggaran
# aturan bisnis menjadi respons yang dimengerti oleh client.
#


class DomainError(Exception):
    """Base class untuk semua pelanggaran aturan bisnis."""


# --------------------------------------------------------------------------
# Error Percakapan
# --------------------------------------------------------------------------


class EmptyMessageError(DomainError):
    """Pesan chat dari user kosong."""

    def __init__(self) -> None:
        super().__init__("Message tidak boleh kosong")


# --------------------------------------------------------------------------
# Error Review (Human-in-the-loop)
# --------------------------------------------------------------------------


class ReviewPendingError(DomainError):
    """Percakapan sedang menunggu keputusan manusia; pesan baru belum boleh."""

    def __init__(self) -> None:
        super().__init__(
            "Masih ada aksi yang menunggu persetujuan. Kirim keputusannya dulu."
        )


class NoPendingReviewError(DomainError):
    """Keputusan dikirim padahal tidak ada aksi yang menunggu persetujuan."""

    def __init__(self) -> None:
        super().__init__("Tidak ada aksi yang menunggu persetujuan di percakapan ini")


class InvalidReviewDecisionError(DomainError):
    """Keputusan review tidak cocok dengan aksi yang sedang menunggu."""
