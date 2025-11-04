"""
Apa itu Value Object?

Objek yang diidentifikasi dari nilainya, bukan ID
Tidak berubah (immutable)
Dipakai untuk mewakili konsep domain

contoh:

# domain/value_objects/money.py
@dataclass(frozen=True)
class Money:
    /"/"/"Value Object untuk uang/"/"/"
    amount: int  # dalam rupiah
    currency: str = "IDR"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount tidak boleh negatif")
        if self.currency not in ["IDR", "USD"]:
            raise ValueError("Currency tidak didukung")

    def add(self, other: 'Money') -> 'Money':
        /"/"/"Tambah uang/"/"/"
        if self.currency != other.currency:
            raise ValueError("Currency harus sama")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: int) -> 'Money':
        /"/"/"Kalikan uang/"/"/"
        return Money(self.amount * factor, self.currency)

    def format(self) -> str:
        /"/"/"Format uang untuk display/"/"/"
        if self.currency == "IDR":
            return f"Rp {self.amount:,}"
        return f"${self.amount:,}"

# Penggunaan:
price = Money(50000, "IDR")
total = price.multiply(3)  # Rp 150.000
"""
