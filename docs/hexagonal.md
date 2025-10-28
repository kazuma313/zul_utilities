# 🏛️ Hexagonal Architecture - Panduan Lengkap untuk Pemula

## 📖 Apa itu Hexagonal Architecture?

**Hexagonal Architecture** (disebut juga **Ports and Adapters**) adalah cara mengorganisir kode aplikasi kita agar:
- **Business logic** (logika bisnis) terpisah dari teknologi
- Mudah diubah dan di-test
- Tidak bergantung pada database, framework, atau API tertentu

### 🤔 Analogi Sederhana: Rumah dengan Banyak Pintu

Bayangkan aplikasi kita adalah sebuah **rumah** (domain/business logic):

```
          🚪 Pintu Depan (HTTP API)
               ↓
    ┌─────────────────────────┐
    │                         │
    │    🏠 RUMAH (DOMAIN)    │ ← Inti aplikasi kita
    │   Business Logic        │
    │                         │
    └─────────────────────────┘
         ↓              ↓
   🚪 Pintu Samping   🚪 Pintu Belakang
   (CLI)             (Database)
```

**Konsep Utama:**
- **Rumah (Domain)** = Business logic kita (aturan bisnis, entitas)
- **Pintu-pintu (Ports)** = Interface/kontrak untuk masuk/keluar
- **Kunci Pintu (Adapters)** = Implementasi konkret (PostgreSQL, FastAPI, dll)

**Kenapa berbentuk Hexagon (Segi Enam)?**
Bukan karena harus 6 sisi, tapi untuk menunjukkan bahwa aplikasi bisa punya **banyak pintu masuk dan keluar** dari berbagai arah!

---

## ❓ Mengapa Menggunakan Hexagonal Architecture?

### 🔴 **Masalah Tanpa Hexagonal Architecture**

Bayangkan kita bikin aplikasi toko online dengan cara biasa:

```python
# ❌ Kode campur aduk (tanpa hexagonal)
from fastapi import FastAPI
from sqlalchemy import create_engine

app = FastAPI()

@app.post("/order")
def create_order(item: str, qty: int):
    # Business logic CAMPUR dengan teknologi!
    
    # 1. Validasi (business logic)
    if qty <= 0:
        return {"error": "Quantity harus positif"}
    
    # 2. Hitung harga (business logic)
    price = qty * 10000
    
    # 3. Simpan ke database (teknologi - PostgreSQL)
    engine = create_engine("postgresql://...")
    engine.execute(f"INSERT INTO orders VALUES ('{item}', {qty}, {price})")
    
    # 4. Kirim email (teknologi - SMTP)
    send_email_via_smtp("order@toko.com", f"Order baru: {item}")
    
    return {"success": True, "total": price}
```

**🚨 Masalahnya:**
1. ❌ **Sulit di-test** - Harus punya database dan email server untuk testing
2. ❌ **Sulit diubah** - Mau ganti dari PostgreSQL ke MongoDB? Harus ubah semua kode!
3. ❌ **Kode berantakan** - Business logic (hitung harga) campur dengan database
4. ❌ **Sulit dikembangkan tim** - Semua orang harus nunggu setup database

### ✅ **Solusi: Dengan Hexagonal Architecture**

```
Kita pisahkan menjadi:
┌─────────────────────────────────────────┐
│  INTERFACE (Pintu Masuk)                │
│  - FastAPI Controller                    │
│  - CLI Command                           │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  APPLICATION (Use Cases)                 │
│  - CreateOrderUseCase                    │
│  - SendOrderNotification                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  DOMAIN (Business Logic) 🏠              │
│  - Order Entity                          │
│  - Hitung total harga                    │
│  - Validasi quantity                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  INFRASTRUCTURE (Pintu Keluar)           │
│  - PostgreSQLRepository                  │
│  - EmailService                          │
└─────────────────────────────────────────┘
```

**🎯 Keuntungan:**
1. ✅ **Mudah di-test** - Test business logic tanpa database!
2. ✅ **Mudah diubah** - Ganti PostgreSQL ke MongoDB? Tinggal ganti 1 file!
3. ✅ **Kode rapi** - Setiap layer punya tanggung jawab jelas
4. ✅ **Tim bisa kerja paralel** - Developer A bikin API, Developer B bikin business logic

---

## 🏗️ Cara Menggunakan Hexagonal Architecture

### 📐 **4 Layer Utama**

```
┌─────────────────────────────────────────────────┐
│  1. INTERFACE (Delivery/Driving Adapters)       │
│     Cara user berinteraksi dengan aplikasi      │
│     - HTTP/REST API (FastAPI, Flask)            │
│     - CLI (Command Line)                        │
│     - GraphQL                                   │
│     - WebSocket                                 │
└────────────────────┬────────────────────────────┘
                     ↓ (memanggil)
┌─────────────────────────────────────────────────┐
│  2. APPLICATION (Use Cases)                     │
│     Apa yang bisa dilakukan aplikasi            │
│     - CreateOrderUseCase                        │
│     - GetOrderUseCase                           │
│     - UpdateOrderUseCase                        │
│     - DeleteOrderUseCase                        │
└────────────────────┬────────────────────────────┘
                     ↓ (menggunakan)
┌─────────────────────────────────────────────────┐
│  3. DOMAIN (Business Logic) 🏠 INTI APLIKASI    │
│     Aturan bisnis & data penting                │
│     - Order (entity)                            │
│     - Product (entity)                          │
│     - Hitung diskon                             │
│     - Validasi stok                             │
│     - Repository Interface (kontrak)            │
└────────────────────┬────────────────────────────┘
                     ↑ (diimplementasi oleh)
┌─────────────────────────────────────────────────┐
│  4. INFRASTRUCTURE (Driven Adapters)            │
│     Implementasi teknologi eksternal            │
│     - PostgreSQLRepository                      │
│     - MongoDBRepository                         │
│     - EmailService (SMTP)                       │
│     - PaymentGateway (Midtrans)                 │
└─────────────────────────────────────────────────┘
```

---

## 💡 Contoh Lengkap: Aplikasi Toko Online

### **1️⃣ DOMAIN Layer** (Inti Bisnis - Yang Paling Penting!)

```python
# domain/entities/order.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order:
    """Entity Order - Objek bisnis utama"""
    id: str
    product_name: str
    quantity: int
    price_per_item: int
    created_at: datetime
    
    def calculate_total(self) -> int:
        """Business logic: Hitung total harga"""
        return self.quantity * self.price_per_item
    
    def apply_discount(self, percentage: int) -> int:
        """Business logic: Hitung diskon"""
        total = self.calculate_total()
        discount = total * percentage / 100
        return total - discount
    
    def validate(self) -> bool:
        """Business logic: Validasi order"""
        if self.quantity <= 0:
            raise ValueError("Quantity harus lebih dari 0")
        if self.price_per_item <= 0:
            raise ValueError("Harga harus lebih dari 0")
        return True
```

```python
# domain/repositories/order_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.order import Order

class OrderRepository(ABC):
    """PORT (Interface) - Kontrak untuk simpan/ambil Order"""
    
    @abstractmethod
    def save(self, order: Order) -> Order:
        """Simpan order ke database"""
        pass
    
    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Cari order by ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Order]:
        """Ambil semua order"""
        pass
```

**🔑 Poin Penting Domain:**
- ✅ **Tidak ada import** dari FastAPI, SQLAlchemy, atau teknologi lain!
- ✅ **Pure Python** - hanya business logic
- ✅ **Mudah di-test** - tidak butuh database untuk test `calculate_total()`

---

### **2️⃣ APPLICATION Layer** (Use Cases)

```python
# application/usecases/create_order.py
from datetime import datetime
from domain.entities.order import Order
from domain.repositories.order_repository import OrderRepository

class CreateOrderUseCase:
    """Use Case: Buat order baru"""
    
    def __init__(self, order_repository: OrderRepository):
        # Dependency Injection - terima interface, bukan implementasi!
        self.order_repository = order_repository
    
    def execute(self, product_name: str, quantity: int, price: int) -> Order:
        """Jalankan use case"""
        
        # 1. Buat entity Order
        order = Order(
            id=self._generate_id(),
            product_name=product_name,
            quantity=quantity,
            price_per_item=price,
            created_at=datetime.now()
        )
        
        # 2. Validasi (business logic)
        order.validate()
        
        # 3. Simpan menggunakan repository (interface)
        saved_order = self.order_repository.save(order)
        
        # 4. Return
        return saved_order
    
    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

**🔑 Poin Penting Application:**
- ✅ **Hanya depend pada Domain** (import dari domain/)
- ✅ **Terima interface**, bukan implementasi konkret
- ✅ **Satu use case = satu aksi bisnis**

---

### **3️⃣ INFRASTRUCTURE Layer** (Implementasi Teknologi)

```python
# infrastructure/database/postgresql_order_repository.py
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, Session
from domain.entities.order import Order
from domain.repositories.order_repository import OrderRepository

Base = declarative_base()

class OrderModel(Base):
    """ORM Model untuk PostgreSQL"""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True)
    product_name = Column(String)
    quantity = Column(Integer)
    price_per_item = Column(Integer)
    created_at = Column(DateTime)

class PostgreSQLOrderRepository(OrderRepository):
    """ADAPTER - Implementasi OrderRepository untuk PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
    
    def save(self, order: Order) -> Order:
        """Simpan ke PostgreSQL"""
        with Session(self.engine) as session:
            order_model = OrderModel(
                id=order.id,
                product_name=order.product_name,
                quantity=order.quantity,
                price_per_item=order.price_per_item,
                created_at=order.created_at
            )
            session.add(order_model)
            session.commit()
        return order
    
    def find_by_id(self, order_id: str) -> Optional[Order]:
        """Cari dari PostgreSQL"""
        with Session(self.engine) as session:
            order_model = session.query(OrderModel).filter(
                OrderModel.id == order_id
            ).first()
            
            if not order_model:
                return None
            
            # Convert ORM model ke Domain entity
            return Order(
                id=order_model.id,
                product_name=order_model.product_name,
                quantity=order_model.quantity,
                price_per_item=order_model.price_per_item,
                created_at=order_model.created_at
            )
    
    def find_all(self) -> List[Order]:
        """Ambil semua dari PostgreSQL"""
        with Session(self.engine) as session:
            order_models = session.query(OrderModel).all()
            return [
                Order(
                    id=om.id,
                    product_name=om.product_name,
                    quantity=om.quantity,
                    price_per_item=om.price_per_item,
                    created_at=om.created_at
                )
                for om in order_models
            ]
```

**💡 Mau ganti ke MongoDB? Bikin adapter baru!**

```python
# infrastructure/database/mongodb_order_repository.py
from pymongo import MongoClient
from domain.repositories.order_repository import OrderRepository

class MongoDBOrderRepository(OrderRepository):
    """ADAPTER - Implementasi OrderRepository untuk MongoDB"""
    
    def __init__(self, connection_string: str):
        self.client = MongoClient(connection_string)
        self.db = self.client.orders_db
        self.collection = self.db.orders
    
    def save(self, order: Order) -> Order:
        """Simpan ke MongoDB"""
        self.collection.insert_one({
            "id": order.id,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "price_per_item": order.price_per_item,
            "created_at": order.created_at
        })
        return order
    
    # ... implementasi lainnya
```

**🔑 Poin Penting Infrastructure:**
- ✅ **Implementasi interface** dari Domain
- ✅ **Semua teknologi** (database, API eksternal, email) ada di sini
- ✅ **Ganti teknologi mudah** - tinggal ganti adapter!

---

### **4️⃣ INTERFACE Layer** (API/CLI)

```python
# interface/http/order_controller.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from application.usecases.create_order import CreateOrderUseCase
from infrastructure.database.postgresql_order_repository import PostgreSQLOrderRepository

app = FastAPI()

# Setup dependency (bisa pakai Dependency Injection framework)
order_repository = PostgreSQLOrderRepository("postgresql://localhost/orders")
create_order_use_case = CreateOrderUseCase(order_repository)

class CreateOrderRequest(BaseModel):
    product_name: str
    quantity: int
    price: int

@app.post("/orders")
def create_order(request: CreateOrderRequest):
    """HTTP Endpoint untuk buat order"""
    try:
        # Panggil use case
        order = create_order_use_case.execute(
            product_name=request.product_name,
            quantity=request.quantity,
            price=request.price
        )
        
        # Return response
        return {
            "id": order.id,
            "product": order.product_name,
            "quantity": order.quantity,
            "total": order.calculate_total()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**CLI Alternative:**

```python
# interface/cli/order_cli.py
import click
from application.usecases.create_order import CreateOrderUseCase
from infrastructure.database.postgresql_order_repository import PostgreSQLOrderRepository

order_repository = PostgreSQLOrderRepository("postgresql://localhost/orders")
create_order_use_case = CreateOrderUseCase(order_repository)

@click.command()
@click.option('--product', prompt='Nama produk')
@click.option('--quantity', prompt='Jumlah', type=int)
@click.option('--price', prompt='Harga', type=int)
def create_order_cli(product: str, quantity: int, price: int):
    """CLI Command untuk buat order"""
    order = create_order_use_case.execute(product, quantity, price)
    click.echo(f"✅ Order berhasil dibuat! ID: {order.id}")
    click.echo(f"Total: Rp {order.calculate_total():,}")
```

**🔑 Poin Penting Interface:**
- ✅ **Hanya handle request/response** - tidak ada business logic!
- ✅ **Panggil use case** untuk eksekusi bisnis
- ✅ **Bisa punya banyak interface** (HTTP, CLI, GraphQL) untuk use case yang sama

---

## 🧪 Testing Jadi Mudah!

### Test Domain (Tanpa Database!)

```python
# test/domain/test_order.py
from domain.entities.order import Order
from datetime import datetime

def test_calculate_total():
    """Test business logic tanpa database!"""
    order = Order(
        id="1",
        product_name="Laptop",
        quantity=2,
        price_per_item=5000000,
        created_at=datetime.now()
    )
    
    assert order.calculate_total() == 10000000  # 2 x 5 juta

def test_apply_discount():
    order = Order(
        id="1",
        product_name="Laptop",
        quantity=2,
        price_per_item=5000000,
        created_at=datetime.now()
    )
    
    # Diskon 10%
    final_price = order.apply_discount(10)
    assert final_price == 9000000  # 10 juta - 10%
```

### Test Use Case dengan Mock

```python
# test/application/test_create_order.py
from unittest.mock import Mock
from application.usecases.create_order import CreateOrderUseCase

def test_create_order():
    """Test use case dengan mock repository"""
    # Mock repository (fake, bukan database beneran)
    mock_repo = Mock()
    mock_repo.save.return_value = Mock(id="123")
    
    # Test use case
    use_case = CreateOrderUseCase(mock_repo)
    order = use_case.execute("Laptop", 2, 5000000)
    
    # Verify
    assert mock_repo.save.called
    assert order is not None
```

---

## 📊 Struktur Folder yang Benar

```
src/
├── domain/                          # 🏠 INTI (Paling Penting!)
│   ├── entities/                    # Objek bisnis
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   ├── value_objects/               # Konsep immutable
│   │   ├── email.py
│   │   └── money.py
│   ├── services/                    # Logic bisnis kompleks
│   │   └── pricing_service.py
│   └── repositories/                # Interface (kontrak)
│       ├── order_repository.py
│       └── product_repository.py
│
├── application/                     # 🎯 Use Cases
│   ├── usecases/
│   │   ├── create_order.py
│   │   ├── get_order.py
│   │   └── update_order.py
│   ├── dto/                         # Data transfer objects
│   │   ├── order_dto.py
│   │   └── product_dto.py
│   └── services/                    # Application services
│       └── order_service.py
│
├── infrastructure/                  # 🔧 Implementasi Teknologi
│   ├── database/
│   │   ├── postgresql_order_repository.py
│   │   └── mongodb_product_repository.py
│   ├── external/
│   │   ├── midtrans_payment.py
│   │   └── smtp_email_service.py
│   └── ai/
│       └── openai_service.py
│
└── interface/                       # 🌐 API/CLI
    ├── http/
    │   ├── order_controller.py
    │   └── product_controller.py
    └── cli/
        └── order_cli.py
```

---

## 🎯 Aturan Emas Hexagonal Architecture

### ✅ **BOLEH:**

```
interface → application → domain
              ↓
         infrastructure
```

1. ✅ Interface boleh import Application
2. ✅ Application boleh import Domain
3. ✅ Infrastructure boleh import Domain (untuk implement interface)
4. ✅ Infrastructure boleh import Application (untuk implement ports)

### ❌ **TIDAK BOLEH:**

1. ❌ Domain **TIDAK BOLEH** import Application
2. ❌ Domain **TIDAK BOLEH** import Infrastructure
3. ❌ Domain **TIDAK BOLEH** import Interface
4. ❌ Application **TIDAK BOLEH** import Infrastructure
5. ❌ Application **TIDAK BOLEH** import Interface

**Contoh Salah:**

```python
# ❌ SALAH! Domain tidak boleh import SQLAlchemy
# domain/entities/order.py
from sqlalchemy import Column, Integer  # ❌ TIDAK BOLEH!

class Order:
    id = Column(Integer)  # ❌ TIDAK BOLEH!
```

**Contoh Benar:**

```python
# ✅ BENAR! Domain pure Python
# domain/entities/order.py
from dataclasses import dataclass

@dataclass
class Order:  # ✅ Pure Python!
    id: str
    quantity: int
```

---

## 🚀 Langkah-langkah Implementasi

### **Step 1: Mulai dari Domain (INTI)**

1. Identifikasi objek bisnis (Entity)
   - Order
   - Product
   - User

2. Tulis business logic
   - Validasi
   - Perhitungan
   - Aturan bisnis

3. Buat interface repository
   - Kontrak untuk save/find data

### **Step 2: Buat Use Cases (Application)**

1. Identifikasi aksi user
   - Create order
   - Cancel order
   - Get order

2. Implementasi use case
   - Panggil domain entity
   - Gunakan repository interface

### **Step 3: Implementasi Teknologi (Infrastructure)**

1. Pilih database (PostgreSQL/MongoDB/dll)
2. Implementasi repository interface
3. Setup connection
4. Implementasi external services

### **Step 4: Buat Interface (API/CLI)**

1. Pilih delivery mechanism (FastAPI/Flask/CLI)
2. Buat controller/handler
3. Panggil use case
4. Return response

---

## 💡 Tips untuk Pemula

### 1. **Mulai Sederhana**
Jangan langsung kompleks! Mulai dengan 1 entity, 1 use case, 1 endpoint.

### 2. **Domain Dulu, Teknologi Kemudian**
Pikirkan business logic dulu, baru teknologi (database, API, dll).

### 3. **Test Business Logic Tanpa Database**
Ini keuntungan terbesar! Test tanpa setup database.

### 4. **Jangan Takut Refactor**
Ganti PostgreSQL ke MongoDB? Tinggal ganti 1 file di infrastructure!

### 5. **Konsisten dengan Aturan**
Domain tidak boleh tahu tentang FastAPI, SQLAlchemy, atau teknologi lain!

---

## 📚 Kesimpulan

**Hexagonal Architecture = Pisahkan Business Logic dari Teknologi**

- **Domain** = Aturan bisnis (inti aplikasi) 🏠
- **Application** = Apa yang bisa dilakukan aplikasi 🎯
- **Infrastructure** = Implementasi teknologi (database, email, dll) 🔧
- **Interface** = Cara user akses aplikasi (API, CLI, dll) 🌐

**Keuntungan:**
- ✅ Mudah di-test
- ✅ Mudah diubah
- ✅ Kode rapi dan terorganisir
- ✅ Tim bisa kerja paralel
- ✅ Independent dari framework/database

**Ingat:** Domain adalah RAJA! Semua layer lain melayani domain! 👑