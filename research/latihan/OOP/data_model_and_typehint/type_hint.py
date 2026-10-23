""" 
type hint memberi tahu kalo tipe data dari suatu atribut sedang salah ini berada di editor, bukan saat program jalan.
type checker memberi tahu dengan menajalkan program. gunakan mypy dan pyright
"""

from attr import dataclass


@dataclass(frozen=True)
class Money:
    amount: int = 10 
    
    def __add__(self, other:"Money")  -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(other.amount + self.amount)


if __name__ == "__main__":
    bayar = Money(8000)
    print(bayar == Money(8000))
    result_add = bayar + Money(8000)
    print(result_add)
    