""" 
dataclass pada python membantu agar tidak menulis tamplate dunder sehingga tidak terjadi kesalahan tulisan.
yang sudah dihandle sama dataclass adalah __init__, __eq__, __repr__.

dengan melakukan frozen=True, maka dataclass ini imutable. yang artinya tidak bisa di ganti setelah didefinisikan
"""

from attr import dataclass


@dataclass(frozen=True)
class Money:
    amount: int = 10 
    
    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return other.amount + self.amount


if __name__ == "__main__":
    bayar = Money(8000)
    print(bayar == Money(8000))
    print(bayar + Money(8000))
