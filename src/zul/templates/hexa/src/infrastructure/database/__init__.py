"""
Implementasi repository: cara data disimpan dan diambil sungguhan.

Gunanya:
    Kontrak repository didefinisikan di `src/domain/repositories/`.
    Implementasinya (PostgreSQL, MongoDB, Milvus, ...) ada di sini, jadi
    mengganti database tidak mengubah domain maupun use case.

Contoh:
    # infrastructure/database/postgres_order_repository.py
    class PostgresOrderRepository(OrderRepository):
        def __init__(self, pool) -> None:
            self._pool = pool

        def find(self, order_id: str) -> Order:
            row = self._pool.execute("SELECT ... WHERE id = %s", [order_id]).fetchone()
            return Order(id=row["id"], total=row["total"], status=row["status"])
"""
