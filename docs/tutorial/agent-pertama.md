# Membuat agent pertamamu

Proyek AI baru dibuat, dijalankan, lalu diberi sebuah tool buatan sendiri. Hasil akhirnya server yang menjawab pertanyaan, memanggil tool, dan mengingat percakapan.

**Sebelum mulai:** semua hal di [daftar kebutuhan tutorial](index.md) sudah siap, termasuk dokumentasi ini yang dibuka sebagai situs.

## Membuat proyek

Buka terminal di folder tempat kamu biasa menyimpan proyek, lalu jalankan:

```shell
zul build hexa --name my-agent
```

Zul menanyakan konfirmasi. Tekan Enter, lalu Zul menyalin template dan melaporkan setiap file dan folder yang dibuat:

```text
? Buat proyek 'my-agent' (hexa)? Yes
📄  File .env.example dicopy.
📄  File .gitignore dicopy.
📁  Folder data dicopy.
📁  Folder dockerfile dicopy.
📁  Folder logs dicopy.
📁  Folder notebooks dicopy.
📄  File pytest.ini dicopy.
📄  File README.md dicopy.
📄  File requirements-dev.txt dicopy.
📄  File requirements.txt dicopy.
📁  Folder src dicopy.
📁  Folder test dicopy.

✅ Proyek HEXA 'my-agent' berhasil dibuat!
```

Masuk ke folder proyek:

```shell
cd my-agent
```

Semua perintah berikutnya dijalankan dari folder ini.

## Instalasi dependency

Buat virtual environment, aktifkan, lalu install dependency proyek:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Di Windows, aktifkan environment dengan `.venv\Scripts\activate`.

## Mengisi API key

Proyek membaca pengaturannya dari file `.env`. Salin contohnya:

```shell
cp .env.example .env
```

Di Windows, gunakan `copy .env.example .env`.

Buka `.env`, lalu isi API key-mu di baris pertama:

```ini title=".env"
OPENAI_API_KEY=API_KEY
```

Ganti `API_KEY` dengan key milikmu. Biarkan baris lain apa adanya, termasuk `PLAYGROUND_ENABLED=true`. Baris itu menyalakan playground yang kita pakai sebentar lagi.

## Menjalankan server

Jalankan aplikasinya:

```shell
uvicorn src.interface.http.main:app --reload
```

Terminal menampilkan alamat server:

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Biarkan terminal ini terbuka. Buka terminal kedua untuk perintah berikutnya, lalu periksa bahwa server hidup:

```shell
curl http://localhost:8000/health
```

Server menjawab:

```json
{"status": "ok"}
```

## Berbicara dengan agent

Panel di bawah ini memakai server yang baru kamu jalankan. Tombol status di bilah panel harus bertuliskan **Terhubung**. Jika tertulis **Simulasi**, panel belum terhubung ke proyekmu dan hanya menampilkan contoh jawaban. Klik tombol itu, lalu klik **Sambungkan**.

<div class="zul-playground" data-feature="ReAct">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Klik contoh pesan **What is the weather in sf?**. Agent menjawab dengan keadaan cuaca di San Francisco. Kalimat persisnya ditentukan model, jadi bisa berbeda di tiap percobaan.

Di atas jawaban ada jejak **3 langkah**. Jejak itu menunjukkan apa yang dilakukan agent sebelum menjawab:

1. `llm_call` meminta tool `get_weather` dengan argumen `{"location": "sf"}`.
2. `tool_node` menjalankan tool itu dan mencatat hasilnya.
3. `llm_call` membaca hasil tool, lalu menulis jawaban.

Itulah satu putaran kerja agent: model meminta tool, tool dijalankan, model menjawab.

## Melanjutkan percakapan

Di panel yang sama, kirim pesan lanjutan:

```text
Should I bring an umbrella?
```

Agent menjawab berdasarkan cuaca yang tadi ia cari, tanpa kamu menyebut San Francisco lagi. Ia mengingat percakapan selama kamu belum mengklik **Percakapan baru**.

Sekarang klik **Percakapan baru**, lalu kirim pesan yang sama. Kali ini agent tidak tahu kota mana yang kamu maksud, karena percakapan baru dimulai dari kosong.

## Memberi agent tool baru

Agent kita baru bisa mengecek cuaca. Kita tambahkan tool kedua yang mengambil status pesanan.

Buat file baru dengan isi berikut:

```python title="src/infrastructure/AI/tools/order_tool.py"
from langchain.tools import tool


@tool
def get_order_status(order_id: str) -> str:
    """Get the current status of a customer order.

    Args:
        order_id: The order number, for example "ORD-1042"
    """
    orders = {"ORD-1042": "shipped", "ORD-1043": "processing"}
    status = orders.get(order_id)

    if status is None:
        return f"No order found with id {order_id}"

    return f"Order {order_id} is {status}"
```

Sekarang kita berikan tool itu ke agent. Buka `src/interface/http/controllers/chat_controller.py` dan cari baris impor berikut:

```python title="src/interface/http/controllers/chat_controller.py"
from src.infrastructure.AI.tools.weather_tool import tools
```

Ganti baris itu dengan dua baris ini:

```python title="src/interface/http/controllers/chat_controller.py"
from src.infrastructure.AI.tools.order_tool import get_order_status
from src.infrastructure.AI.tools.weather_tool import get_weather
```

Di file yang sama, cari fungsi `get_react_agent` dan ubah argumen `tools`:

```python title="src/interface/http/controllers/chat_controller.py"
@lru_cache
def get_react_agent():
    """Agent ReAct yang dilayani `POST /chat` dan dicoba di playground."""
    return build_react_agent(
        llm=get_llm_model(),
        tools=[get_weather, get_order_status],
        checkpointer=get_checkpointer(),
    )
```

Simpan kedua file. Karena server berjalan dengan `--reload`, ia memulai ulang sendiri. Terminal pertama menampilkan:

```text
INFO:     Application startup complete.
```

## Mencoba tool baru

Kembali ke panel playground di atas, klik **Percakapan baru**, lalu kirim:

```text
What is the status of order ORD-1042?
```

Agent menjawab bahwa pesanan itu sudah dikirim. Lihat jejaknya: kali ini `llm_call` meminta tool `get_order_status` dengan argumen `{"order_id": "ORD-1042"}`.

Kita tidak mengubah prompt agent sama sekali. Agent tahu kapan memakai tool baru dari nama fungsi dan docstring yang kita tulis.

## Memanggil API tanpa playground

Playground berbicara dengan agent yang sama dengan yang dilayani endpoint `POST /chat`. Client sungguhan, misalnya aplikasi web, memanggil endpoint itu. Coba dari terminal kedua:

```shell
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the status of order ORD-1043?\"}"
```

Respons berisi jawaban dan `thread_id` percakapan:

```json
{
  "answer": "Order ORD-1043 is currently processing.",
  "thread_id": "5d0f8c2e4b7a4f0e9a1c3b6d8e2f4a70"
}
```

## Menjalankan test

Proyek membawa contoh test yang berjalan tanpa API key, karena model di dalam test diganti model palsu. Di terminal kedua, jalankan:

```shell
pytest
```

Baris terakhir keluarannya:

```text
4 passed
```

## Yang sudah kamu kerjakan

Kamu sudah:

- Membuat proyek dengan `zul build hexa` dan menjalankannya.
- Berbicara dengan agent lewat playground dan lewat `POST /chat`.
- Melihat langkah agent: model meminta tool, tool dijalankan, model menjawab.
- Menulis tool baru dan memberikannya ke agent.

Lanjutkan ke [Meminta persetujuan manusia](persetujuan-manusia.md), tempat agent yang sama belajar berhenti sebelum melakukan aksi yang berisiko.

Jika kamu ingin tahu lebih dalam tentang yang baru kamu lihat:

- [Cara kerja agent ReAct](../konsep/agent-react.md) menjelaskan putaran model dan tool.
- [Menambah tool](../panduan/menambah-tool.md) memuat pedoman menulis tool yang dipahami model.
- [Struktur proyek](../referensi/struktur-proyek.md) menjelaskan isi setiap folder.
