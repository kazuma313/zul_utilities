# Menambah tool

Tool baru memberi agent kemampuan mengambil data atau melakukan aksi yang sebelumnya tidak bisa.

**Sebelum mulai:** kamu punya proyek hasil `zul build hexa` yang berjalan. Contoh di halaman ini menambah tool pengambil status pesanan ke agent ReAct.

## Langkah-langkah

1. Buat file tool di `src/infrastructure/AI/tools/`. Tool adalah fungsi dengan dekorator `@tool`:

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

2. Kembalikan teks yang bisa dibaca model di setiap cabang, termasuk saat data tidak ditemukan. Model memakai teks itu untuk menyusun jawabannya.

3. Berikan tool ke agent di controller yang merakitnya. Untuk agent ReAct, impor tool-nya dan ubah `get_react_agent`:

    ```python title="src/interface/http/controllers/chat_controller.py"
    from src.infrastructure.AI.tools.order_tool import get_order_status
    from src.infrastructure.AI.tools.weather_tool import get_weather


    @lru_cache
    def get_react_agent():
        """Agent ReAct yang dilayani `POST /chat` dan dicoba di playground."""
        return build_react_agent(
            llm=get_llm_model(),
            tools=[get_weather, get_order_status],
            checkpointer=get_checkpointer(),
        )
    ```

4. Mulai ulang server. Dengan `--reload`, server memulai ulang sendiri saat file disimpan.

Kamu tidak perlu mengubah prompt. Nama, deskripsi, dan skema argumen setiap tool dikirim ke model secara otomatis.

## Mendaftarkan tool ke agent lain

Tempat mendaftarkan tool berbeda untuk setiap agent di template:

| Agent | Tempat mendaftarkan |
|---|---|
| ReAct | Argumen `tools` di `get_react_agent`, file `chat_controller.py` |
| Human-in-the-loop | Konstanta `TOOLS` di `hitl_controller.py`. Tool yang berisiko dibahas di [Mewajibkan persetujuan untuk sebuah tool](mewajibkan-persetujuan.md). |
| Subagents | Field `tools` pada `SubagentSpec` di `subagents_controller.py`. Rinciannya ada di [Menambah subagent](menambah-subagent.md). |

## Menulis deskripsi yang dipahami model

Model memilih tool hanya dari nama fungsi, docstring, dan skema argumennya. Deskripsi yang kabur membuat tool jarang dipakai, atau dipakai di saat yang salah.

- Awali docstring dengan kata kerja yang menyebut hasilnya: "Get the current status of a customer order."
- Jelaskan setiap argumen di bagian `Args`, dengan contoh nilai jika formatnya tidak jelas.
- Beri nama argumen yang bermakna: `order_id`, bukan `id` atau `x`.
- Pakai type hint yang tepat. `location: str` dan `limit: int` menghasilkan skema yang berbeda.
- Tulis dalam bahasa yang paling dikuasai modelmu. Untuk sebagian besar model, itu bahasa Inggris.

## Menangani kegagalan di dalam tool

Jika fungsi tool melempar exception, request berhenti dan client menerima HTTP 500. Tangani kegagalan yang bisa diperkirakan di dalam tool, lalu kembalikan sebagai teks:

```python title="src/infrastructure/AI/tools/order_tool.py"
@tool
def get_order_status(order_id: str) -> str:
    """Get the current status of a customer order."""
    try:
        order = order_api.fetch(order_id)
    except OrderApiTimeout:
        return "The order service did not respond. Ask the user to try again later."

    return f"Order {order_id} is {order.status}"
```

Di contoh ini `order_api` dan `OrderApiTimeout` mewakili client layanan pesananmu sendiri. Dengan mengembalikan teks, model bisa menjelaskan masalahnya ke user.

## Memeriksa hasilnya

Tool bisa dipanggil langsung, tanpa agent dan tanpa model. Kirim argumennya sebagai dict ke `invoke`:

```python
from src.infrastructure.AI.tools.order_tool import get_order_status

print(get_order_status.invoke({"order_id": "ORD-1042"}))
```

Keluarannya:

```text
Order ORD-1042 is shipped
```

Untuk melihat agent memakai tool itu, kirim pesan lewat panel di bawah ini, lalu lihat jejaknya:

<div class="zul-playground" data-feature="ReAct" data-examples="What is the status of order ORD-1042?">
Panel Playground hanya tampil di situs dokumentasi, <a href="https://zulkit.my.id/">zulkit.my.id</a>.
</div>

## Halaman terkait

- [Cara kerja agent ReAct](../konsep/agent-react.md) untuk apa yang terjadi saat model meminta tool, termasuk saat argumennya salah.
- [Menguji agent](menguji-agent.md) untuk menguji pemanggilan tool dengan model palsu.
- [API agent](../referensi/agent.md) untuk parameter `build_react_agent`.
