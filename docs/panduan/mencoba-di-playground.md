# Mencoba fitur di playground

Panel Playground di dokumentasi ini menjalankan agent yang sedang kamu buat, sebelum endpoint dan test-nya selesai. Panel menampilkan setiap langkah agent: tool yang diminta, argumennya, hasilnya, dan aksi yang menunggu keputusan.

**Sebelum mulai:** kamu punya proyek hasil `zul build hexa`.

## Menyalakan playground

1. Di file `.env` proyekmu, pastikan baris berikut ada:

    ```ini title=".env"
    PLAYGROUND_ENABLED=true
    ```

    File `.env.example` sudah memuat baris itu, jadi proyek yang `.env`-nya disalin dari contoh sudah siap.

2. Jalankan aplikasinya dari root proyek:

    ```shell
    uvicorn src.interface.http.main:app --reload
    ```

3. Buka halaman [Playground](../playground.md). Tombol status di bilah panel bertuliskan **Terhubung** saat panel memakai proyekmu. Jika tertulis **Simulasi**, klik tombol itu, lalu klik **Sambungkan**.

## Mendaftarkan fiturmu

Panel menampilkan fitur yang terdaftar di `src/interface/playground/features.py`. Untuk menambah fitur:

1. Tulis fungsi tanpa argumen yang mengembalikan agent-mu. Rakit dengan checkpointer supaya percakapan bisa berlanjut, dan pakai `lru_cache` supaya agent dibuat sekali saja:

    ```python title="src/interface/playground/features.py"
    from functools import lru_cache

    from src.application.AI.agents.react.react import build_react_agent
    from src.infrastructure.AI.llm.openai import get_llm_model
    from src.infrastructure.AI.memory.checkpointer import get_checkpointer
    from src.infrastructure.AI.tools.order_tool import get_order_status


    @lru_cache
    def build_order_agent():
        return build_react_agent(
            llm=get_llm_model(),
            tools=[get_order_status],
            system_prompt="You answer questions about customer orders.",
            checkpointer=get_checkpointer(),
        )
    ```

2. Tambahkan satu `Feature` ke daftar `FEATURES` di file yang sama. Taruh di paling atas selama fitur itu masih kamu kerjakan, karena fitur pertama terpilih saat halaman dibuka:

    ```python title="src/interface/playground/features.py"
    FEATURES = [
        Feature(
            name="Pesanan",
            description="Agent yang menjawab pertanyaan tentang pesanan.",
            build_agent=build_order_agent,
            examples=("What is the status of order ORD-1042?",),
        ),
        ...
    ]
    ```

3. Simpan file, tunggu server memulai ulang, lalu muat ulang halaman Playground. Fiturmu muncul di daftar pilihan.

Isi `examples` tampil sebagai tombol pesan siap kirim. Fungsi `build_agent` baru dipanggil saat fiturnya dipakai, jadi fitur yang belum bisa dirakit tidak mengganggu fitur lain. Panel menampilkan alasannya saat kamu mengirim pesan ke fitur itu.

## Menaruh panel di halaman dokumentasi lain

Panel bisa ditaruh di halaman Markdown mana pun di situs ini. Tulis satu `div` dengan nama fiturnya:

```html
<div class="zul-playground" data-feature="Pesanan"></div>
```

Tabel berikut menjelaskan atributnya:

| Atribut | Kegunaan |
|---|---|
| `data-feature` | Nama fitur yang dipakai panel. Tanpa atribut ini, panel menampilkan pilihan semua fitur. |
| `data-examples` | Contoh pesan, dipisah tanda `|`. Tanpa atribut ini, panel memakai `examples` dari `features.py`. |

## Memakai mesin playground tanpa browser

Jejak langkah yang sama bisa dibaca dari skrip atau notebook, lewat modul `runner`:

```python
from src.interface.playground.features import find_feature
from src.interface.playground.runner import send_message

agent = find_feature("ReAct").build_agent()
turn = send_message(agent, "What is the weather in sf?", thread_id="coba-1")

for step in turn.steps:
    print("  " * step.depth, step.node, step.messages)

print(turn.answer)
```

## Mengizinkan alamat dokumentasi lain

Browser hanya boleh memanggil API-mu dari alamat yang diizinkan. Bawaannya adalah situs ini, `https://zulkit.my.id`, dan alamat `mkdocs serve`: `http://127.0.0.1:8001` dan `http://localhost:8001`. Jika dokumentasimu dibuka dari alamat lain, daftarkan alamat itu di `.env`, dipisah koma:

```ini title=".env"
PLAYGROUND_ORIGINS=http://127.0.0.1:8001,https://ALAMAT_DOKUMENTASI
```

Ganti `ALAMAT_DOKUMENTASI` dengan alamat situsmu, tanpa path di belakangnya. Jika API-mu sendiri berjalan di alamat selain `http://localhost:8000`, klik tombol status di panel, isi **Alamat API proyekmu**, lalu klik **Sambungkan**.

> [!WARNING]
> Playground menampilkan argumen dan hasil setiap tool, dan bisa menjalankan aksi agent. Isi `PLAYGROUND_ENABLED=false` di lingkungan produksi.

## Halaman terkait

- [Playground API](../referensi/playground-api.md) untuk endpoint yang dipanggil panel, termasuk bentuk jejak langkahnya.
- [Environment variable](../referensi/konfigurasi.md) untuk `PLAYGROUND_ENABLED` dan `PLAYGROUND_ORIGINS`.
- [Menguji agent](menguji-agent.md), langkah berikutnya setelah fiturmu berjalan di playground.
