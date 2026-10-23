from dataclasses import dataclass, field
from enum import Enum

class OrderStatus(Enum):
    DRAFT = "draft"
    PAID = "paid"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class Money:
    amount: int

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("amount tidak boleh negatif")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

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

class OrderMember(Order):
    @property
    def total(self) -> Money:
        return Money(super().total.amount * 90 // 100)
    

class OrderPromo(Order):
    @property
    def total(self) -> Money:
        return Money(super().total.amount - 5000)
    
    
class OrederMemberPromo(OrderMember, OrderPromo):
    pass