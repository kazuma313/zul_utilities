# Menambah subagent

Halaman ini menunjukkan cara menambah agent spesialis ke supervisor, sehingga supervisor bisa mendelegasikan satu bidang pekerjaan baru. Contohnya menambah subagent yang menangani pesanan.

**Sebelum mulai:** tool untuk subagent itu sudah ditulis. Lihat [Menambah tool](menambah-tool.md). Contoh ini memakai tool `get_order_status`.

## Langkah-langkah

1. Tulis system prompt subagent di file prompt subagents. Tutup prompt-nya dengan `_SUBAGENT_OUTPUT_RULE`:

    ```python title="src/domain/templates/prompt/subagents/subagents_prompt_templates.py"
    ORDER_AGENT_SYSTEM_PROMPT = """\
    You are an order specialist. Use your tools to look up order status.
    Do not guess order information.
    """ + _SUBAGENT_OUTPUT_RULE
    ```

2. Di controller subagents, impor prompt dan tool-nya:

    ```python title="src/interface/http/controllers/subagents_controller.py"
    from src.domain.templates.prompt.subagents.subagents_prompt_templates import (
        EMAIL_AGENT_SYSTEM_PROMPT,
        ORDER_AGENT_SYSTEM_PROMPT,
        WEATHER_AGENT_SYSTEM_PROMPT,
    )
    from src.infrastructure.AI.tools.order_tool import get_order_status
    ```

3. Tambahkan `SubagentSpec` ke daftar `SUBAGENTS` di file yang sama:

    ```python title="src/interface/http/controllers/subagents_controller.py"
    SubagentSpec(
        name="order_agent",
        description=(
            "Look up the status of customer orders. "
            "Give it one or more order ids; it returns the status of each."
        ),
        system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
        tools=[get_order_status],
    ),
    ```

4. Mulai ulang server.

Prompt supervisor tidak perlu diubah. Nama subagent harus unik; jika dua `SubagentSpec` punya `name` yang sama, perakit supervisor melempar `ValueError`.

## Menulis nama dan deskripsi

Supervisor memilih subagent hanya dari `name` dan `description`. Ia tidak melihat prompt maupun tool milik subagent. Deskripsi yang baik menjawab tiga pertanyaan:

| Pertanyaan | Contoh |
|---|---|
| Tugas apa yang ditangani? | "Look up the status of customer orders." |
| Masukan apa yang dibutuhkan? | "Give it one or more order ids;" |
| Apa yang dikembalikan? | "it returns the status of each." |

Beri nama yang menyebut bidangnya, misalnya `order_agent`, bukan `agent_2`.

## Memberi subagent model sendiri

Secara bawaan, semua subagent memakai model yang sama dengan supervisor. Untuk memberi satu subagent model lain, misalnya model yang lebih murah untuk tugas sederhana, isi field `llm`:

```python title="src/interface/http/controllers/subagents_controller.py"
SubagentSpec(
    name="weather_agent",
    description="Look up current weather for one or more locations.",
    system_prompt=WEATHER_AGENT_SYSTEM_PROMPT,
    tools=[get_weather],
    llm=get_llm_model(model="gpt-4o-mini"),
)
```

## Memeriksa hasilnya

Kirim permintaan yang termasuk bidang subagent barumu lewat panel berikut, lalu lihat jejaknya. Langkah subagent tampil menjorok di bawah permintaan supervisor:

<div class="zul-playground" data-feature="Subagents" data-examples="What is the status of order ORD-1042?">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Client sungguhan memanggil `POST /subagents/chat`, dengan bentuk request dan respons yang sama seperti `POST /chat`:

```shell
curl -X POST http://localhost:8000/subagents/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the status of order ORD-1042?\"}"
```

## Lihat juga

- [Cara kerja subagents](../konsep/subagents.md) untuk kapan pola ini cocok, dan kenapa subagent tidak punya memory.
- [API agent](../referensi/agent.md) untuk field `SubagentSpec` dan parameter `build_supervisor_agent`.
- [Mengatur batas langkah](mengatur-batas-langkah.md) untuk batas langkah tiap tugas subagent.
