"""
Entity: objek inti bisnis yang punya identitas dan aturan sendiri.

Gunanya:
    Menyimpan data dan aturan yang tetap benar apa pun teknologinya.
    Entity tidak boleh import FastAPI, SQLAlchemy, atau library lain di
    luar Python murni (pengecualian: state agent di `agents/`, yang
    memang bentuk data milik LangGraph).

Contoh:
    # domain/entities/order.py
    @dataclass
    class Order:
        id: str
        total: int
        status: str = "pending"

        def pay(self) -> None:
            if self.status != "pending":
                raise OrderAlreadyPaidError(self.id)
            self.status = "paid"
"""
