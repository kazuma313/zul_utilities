# {{ project_name }}

Proyek AI berarsitektur **hexagonal** (ports & adapters), dibuat dengan `zul build hexa`.

## Menjalankan

```bash
pip install -r requirements.txt
cp .env.example .env          # lalu isi OPENAI_API_KEY

# REST API (FastAPI) -> http://localhost:8000/docs
uvicorn src.interface.http.main:app --reload

# UI (Streamlit)
streamlit run src/interface/streamlit/main.py
```

## Playground

Playground adalah tempat mencoba agent sambil melihat setiap langkahnya: tool
yang dipanggil, argumennya, hasilnya, dan aksi yang menunggu persetujuan.
Tampilannya ada di halaman **Playground** dokumentasi Zul; halaman itu memanggil
endpoint `/playground/*` di aplikasi ini.

1. Pastikan `.env` berisi `PLAYGROUND_ENABLED=true`.
2. Jalankan aplikasi dengan perintah `uvicorn` di atas.
3. Buka halaman Playground di dokumentasi Zul.

Untuk mencoba fitur yang sedang kamu buat, daftarkan di
`src/interface/playground/features.py`:

```python
Feature(
    name="RAG dokumen",
    description="Agent yang mencari jawaban di dokumen internal.",
    build_agent=build_rag_agent,
    examples=("Apa isi kebijakan cuti?",),
),
```

Playground menampilkan argumen dan hasil setiap tool. Isi
`PLAYGROUND_ENABLED=false` di lingkungan produksi.

Coba endpoint chat:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"what is the weather in sf\"}"
```

Respons berisi `answer` dan `thread_id`. Kirim `thread_id` itu lagi di request berikutnya untuk melanjutkan percakapan yang sama:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"and tomorrow?\", \"thread_id\": \"<thread_id dari respons>\"}"
```

## Struktur

```text
├── data/            # dataset, seed, fixture
├── dockerfile/      # Dockerfile per environment
├── logs/            # log aplikasi (tidak di-commit)
├── notebooks/       # eksperimen & prototyping
├── src/
│   ├── domain/          # entity, exception, prompt — tanpa dependensi teknologi
│   ├── application/     # use case, AI agent (ReAct), DTO, mapper
│   ├── infrastructure/  # adapter keluar: LLM, tools, database, logging
│   ├── interface/       # adapter masuk: http (FastAPI), streamlit, cli, discord
│   └── utils/           # helper murni tanpa logika bisnis
└── test/
```

Arah dependensi selalu ke dalam:

```text
interface → application → domain
                ↑
          infrastructure
```

## Alur request chat

1. `interface/http/routers/chat.py` menerima `POST /chat`.
2. `interface/http/controllers/chat_controller.py` merakit dependensi (LLM + tools + checkpointer → agent → use case).
3. `application/usecases/chat.py` memvalidasi pesan dan memanggil agent dengan `thread_id` dan `recursion_limit`.
4. `application/AI/agents/react/react.py` menjalankan loop ReAct: `llm_call` → `tool_node` → `llm_call` → jawaban.

## Agent (LangGraph)

Agent ditulis dengan [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), mengikuti pola di [quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart):

| Bagian | Lokasi | Catatan |
|---|---|---|
| State | `src/domain/entities/agents/react/react.py` | `messages` memakai reducer `add_messages`; `remaining_steps` diisi LangGraph |
| Node & routing | `src/application/AI/agents/react/nodes/react_nodes.py` | `llm_call`, `should_continue` |
| Graph | `src/application/AI/agents/react/react.py` | `StateGraph` + `ToolNode` |
| Memory | `src/infrastructure/AI/memory/checkpointer.py` | `InMemorySaver`, percakapan per `thread_id` |

- **Memory**: `InMemorySaver` hilang saat aplikasi restart. Untuk produksi, ganti dengan checkpointer berbasis database (mis. `PostgresSaver`).
- **Batas langkah**: satu pesan dibatasi `MAX_AGENT_STEPS` (25) di `application/usecases/chat.py`. Saat langkah hampir habis, agent menutup dengan jawaban, bukan error.
- **ReAct standar**: kalau tidak butuh kustomisasi graph, `langchain.agents.create_agent` merakit loop yang sama dalam satu pemanggilan.

Tiga template agent tersedia di `src/application/AI/agents/`:

| Template | Folder | Endpoint | Kapan dipakai |
|---|---|---|---|
| ReAct | `react/` | `POST /chat` | Satu agent dengan beberapa tool |
| Human-in-the-loop | `human_in_the_loop/` | `POST /hitl/chat`, `POST /hitl/review` | Ada tool yang harus disetujui manusia sebelum jalan |
| Subagents | `subagents/` | `POST /subagents/chat` | Beberapa domain berbeda, masing-masing ditangani agent spesialis |

### Human-in-the-loop

Mengikuti [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts). Tool yang namanya ada di `TOOLS_REQUIRING_APPROVAL` (`interface/http/controllers/hitl_controller.py`) tidak langsung dijalankan: node `human_review` memanggil `interrupt()`, graph berhenti, dan state disimpan checkpointer sampai keputusan datang.

```bash
# 1. Agent ingin mengirim email -> respons berisi pending_review, bukan answer
curl -X POST http://localhost:8000/hitl/chat -H "Content-Type: application/json" -d "{\"message\": \"email alice@example.com: rapat jam 10\"}"

# 2. Kirim keputusan, satu per aksi di pending_review.action_requests
curl -X POST http://localhost:8000/hitl/review -H "Content-Type: application/json" -d "{\"thread_id\": \"<thread_id>\", \"decisions\": [{\"type\": \"approve\"}]}"
```

| Keputusan | Bentuk | Akibat |
|---|---|---|
| `approve` | `{"type": "approve"}` | Tool jalan dengan argumen asli |
| `edit` | `{"type": "edit", "edited_action": {"name": "send_email", "args": {...}}}` | Tool jalan dengan argumen yang diubah |
| `reject` | `{"type": "reject", "message": "alasan"}` | Tool tidak jalan; alasannya diteruskan ke LLM |

Yang perlu diingat saat mengubah template ini:

- Wajib ada checkpointer dan `thread_id`; tanpa keduanya `interrupt()` tidak bisa dilanjutkan.
- Saat di-resume, node `human_review` jalan lagi dari awal. Jangan taruh side effect sebelum `interrupt()`.
- Keputusan divalidasi di use case sebelum resume. Nilai resume ikut tersimpan di checkpoint, jadi error di dalam node setelah `interrupt()` akan terulang di setiap percobaan resume berikutnya.
- Selama ada review yang menunggu, pesan baru di thread itu ditolak, supaya tidak ada tool call tanpa jawaban di riwayat percakapan.

### Subagents

Mengikuti pola [subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) (tool per agent): supervisor adalah agent ReAct yang tool-nya adalah subagent. Daftar subagent ada di `SUBAGENTS` (`interface/http/controllers/subagents_controller.py`).

```python
SubagentSpec(
    name="weather_agent",                       # nama tool yang dilihat supervisor
    description="Look up current weather ...",   # kapan supervisor memakainya
    system_prompt=WEATHER_AGENT_SYSTEM_PROMPT,
    tools=[get_weather],
    llm=None,                                    # opsional: model khusus subagent ini
)
```

- Supervisor memilih subagent hanya dari `name` dan `description`, jadi keduanya harus jelas.
- Subagent tidak punya memory dan hanya melihat query dari supervisor. Riwayat percakapan disimpan supervisor.
- Supervisor hanya menerima pesan terakhir subagent, jadi prompt subagent harus meminta semua hasil ditaruh di jawaban akhir.

## Menambah fitur

| Yang ditambah | Lokasi |
|---|---|
| Tool baru untuk agent | `src/infrastructure/AI/tools/`, lalu daftarkan di controller agent yang memakainya |
| Tool yang butuh persetujuan manusia | Tambahkan namanya ke `TOOLS_REQUIRING_APPROVAL` di `hitl_controller.py` |
| Subagent baru | Tambahkan `SubagentSpec` ke `SUBAGENTS` di `subagents_controller.py` |
| Provider LLM lain | `src/infrastructure/AI/llm/` (kembalikan chat model LangChain) |
| Aksi bisnis baru | `src/application/usecases/` |
| Aturan / entity bisnis | `src/domain/` |
| Endpoint baru | `src/interface/http/routers/` + `controllers/` |
