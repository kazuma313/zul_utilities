"""
Router: daftar alamat endpoint.

Gunanya:
    Router hanya menentukan path, method, dan model request/response, lalu
    meneruskan ke controller. Logika tidak ditaruh di sini.

Contoh router baru:
    # interface/http/routers/orders.py
    router = APIRouter(prefix="/orders", tags=["orders"])

    @router.get("/{order_id}", response_model=OrderResponse)
    def show(order_id: str, usecase: GetOrderUseCase = Depends(get_order_usecase)):
        return orders_controller.show(order_id, usecase)

    Daftarkan di `main.py`: `app.include_router(orders.router)`.
"""
