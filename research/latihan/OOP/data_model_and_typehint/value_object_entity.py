""" 
terkadang suatu atribut bisa terdapat 2 value yang berbeda dengan object yang sama. 
maka perlu di bedakan object uang mutable dan imutable:
imutable (value order -> object yang identitasnya adalah nilai): money, orderline
mutable(entity -> memiliki identitas tetap): order
"""

from dataclasses import dataclass, field
from enum import Enum


class OrderStatus(Enum):
    DRAFT = "draft"
    PAID = "paid"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class Money:
    amount: int = 10 
    
    def __add__(self, other:"Money")  -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(other.amount + self.amount)
    
    

@dataclass(frozen=True)
class OrderLine:
    nama: str
    harga: Money
    qty: int

    def __post_init__(self) -> None:
        if self.qty < 1:
            raise ValueError("qty minimal 1")

    @property
    def subtotal(self) -> Money:
        return Money(self.harga.amount * self.qty)
    
@dataclass(eq=False)
class Order:
    id: str
    pelanggan: str
    lines: list[OrderLine] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def total(self) -> Money:
        hasil = Money(0)
        for line in self.lines:
            hasil = hasil + line.subtotal
        return hasil

andi = Order("A-001", "Andi")
andi.lines.append(OrderLine("kopi susu", Money(18000), 2))
andi.lines.append(OrderLine("roti bakar", Money(15000), 1))
print(andi.total)                        # Money(amount=51000)
print(andi == Order("A-001", "Andi"))    # True, id sama
print(andi == Order("A-002", "Andi"))    # False

