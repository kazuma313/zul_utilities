# Struktur proyek hexa

Proyek hasil `zul build hexa` tersusun mengikuti arsitektur hexagonal: aturan bisnis di `domain`, alur kerja di `application`, teknologi di `infrastructure`, dan pintu masuk di `interface`.

Hampir setiap folder punya `__init__.py` berisi docstring tentang kegunaan folder itu, cara memakainya, dan contoh kode. Pohon di halaman ini tidak menampilkan file `__init__.py`, kecuali yang berisi kode.

## Root proyek

Pohon berikut menunjukkan isi root proyek bernama `my-app`:

```text
my-app/
├── data/
│   └── .gitkeep
├── dockerfile/
│   └── Dockerfile
├── logs/
│   └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── src/
├── test/
│   ├── conftest.py
│   └── test_chat_usecase.py
├── .env.example
├── .gitignore
├── pytest.ini
├── README.md
├── requirements.txt
└── requirements-dev.txt
```

| Path | Fungsi |
|---|---|
| `data/` | Tempat dataset, data awal, dan fixture. Kosong di template. |
| `dockerfile/Dockerfile` | Membangun image aplikasi dari `python:3.11-slim`. Image memasang `requirements.txt`, menyalin `src/`, dan menjalankan `uvicorn` di port 8000. |
| `logs/` | Tempat file log. `app.log` dibuat saat aplikasi mulai. |
| `notebooks/` | Tempat notebook eksperimen dan prototipe. Kosong di template. |
| `src/` | Seluruh kode aplikasi. Rinciannya ada di [Folder src](#folder-src). |
| `test/conftest.py` | Fixture `scripted_model`, yaitu pembuat LLM palsu untuk test. |
| `test/test_chat_usecase.py` | Empat test contoh untuk `ChatUseCase`. |
| `.env.example` | Contoh environment variable. Rinciannya ada di [Referensi environment variable](konfigurasi.md). |
| `.gitignore` | Daftar file yang tidak masuk git, termasuk `.env` dan file `*.log`. |
| `pytest.ini` | Memasukkan root proyek ke path impor dan menetapkan `test/` sebagai folder test. |
| `README.md` | Ringkasan proyek. Judulnya berisi nama proyek. |
| `requirements.txt` | Dependency untuk menjalankan aplikasi. |
| `requirements-dev.txt` | Dependency aplikasi ditambah `pytest` dan `httpx`. |

File `.gitkeep` hanya ada supaya folder kosong ikut tersalin.

## Folder src

Pohon berikut menunjukkan empat layer dan satu folder helper di dalam `src/`:

```text
src/
├── domain/
├── application/
├── infrastructure/
├── interface/
└── utils/
```

| Folder | Isi | Boleh mengimpor |
|---|---|---|
| `domain/` | Aturan bisnis: entity, state agent, exception, prompt. | Tidak ada layer lain |
| `application/` | Alur kerja: use case dan agent. | `domain` |
| `infrastructure/` | Adapter keluar: LLM, tool, memory, database. | `domain`, `application` |
| `interface/` | Adapter masuk: HTTP, playground, Streamlit, CLI, Discord. | Semua layer |
| `utils/` | Helper murni tanpa logika bisnis dan tanpa dependensi ke layer lain. Kosong di template. | Tidak ada layer lain |

Kode di proyek mengimpor dengan awalan `src`, sehingga aplikasi dan test dijalankan dari root proyek. Contoh baris impor:

```python
from src.application.usecases.chat import ChatUseCase
```

Alasan di balik arah impor ini dijelaskan di [Konsep: Perjalanan sebuah request](../konsep/alur-request.md).

## Folder domain

Pohon berikut menunjukkan isi `src/domain/`:

```text
domain/
├── entities/
│   ├── agents/
│   │   └── react/
│   │       └── react.py
│   └── react.py
├── events/
├── exceptions/
│   └── __init__.py
├── repositories/
└── templates/
    └── prompt/
        ├── human_in_the_loop/
        │   └── human_in_the_loop_prompt_templates.py
        ├── react/
        │   └── react_prompt_templates.py
        └── subagents/
            └── subagents_prompt_templates.py
```

| Path | Fungsi |
|---|---|
| `entities/` | Objek inti bisnis. Satu file per entity. |
| `entities/agents/` | State agent, yaitu bentuk data yang mengalir antar node. Satu subfolder per agent. |
| `entities/agents/react/react.py` | `AgentState`. State ini dipakai agent ReAct, human-in-the-loop, dan subagents. |
| `entities/react.py` | File cadangan bawaan template. Belum dipakai dan boleh dihapus. |
| `events/` | Tempat domain event, yaitu kejadian penting di bisnis. Kosong di template. |
| `exceptions/__init__.py` | `DomainError` dan turunannya. Setiap turunan menjadi respons HTTP 400. |
| `repositories/` | Tempat kontrak (kelas abstrak) untuk menyimpan dan mengambil data. Kosong di template. |
| `templates/prompt/react/react_prompt_templates.py` | `REACT_SYSTEM_PROMPT`. |
| `templates/prompt/human_in_the_loop/human_in_the_loop_prompt_templates.py` | `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT`. |
| `templates/prompt/subagents/subagents_prompt_templates.py` | `SUPERVISOR_SYSTEM_PROMPT`, `WEATHER_AGENT_SYSTEM_PROMPT`, `EMAIL_AGENT_SYSTEM_PROMPT`. |

## Folder application

Pohon berikut menunjukkan isi `src/application/`:

```text
application/
├── AI/
│   └── agents/
│       ├── react/
│       │   ├── react.py
│       │   └── nodes/
│       │       └── react_nodes.py
│       ├── human_in_the_loop/
│       │   ├── human_in_the_loop.py
│       │   └── nodes/
│       │       └── human_in_the_loop_nodes.py
│       └── subagents/
│           └── subagents.py
├── dto/
│   └── user.py
├── mappers/
│   └── user.py
├── prompts/
├── services/
└── usecases/
    ├── chat.py
    └── reviewed_chat.py
```

| Path | Fungsi |
|---|---|
| `AI/agents/react/react.py` | `build_react_agent`, perakit graph agent ReAct. |
| `AI/agents/react/nodes/react_nodes.py` | `make_llm_call`, `should_continue`, `STEPS_PER_TOOL_ROUND`, `STEP_LIMIT_MESSAGE`. |
| `AI/agents/human_in_the_loop/human_in_the_loop.py` | `build_human_in_the_loop_agent`, perakit graph agent dengan langkah persetujuan. |
| `AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py` | Node `human_review`, node `tool_node`, dan pembuat payload review. |
| `AI/agents/subagents/subagents.py` | `SubagentSpec`, `build_subagent_tool`, `build_supervisor_agent`, `MAX_SUBAGENT_STEPS`. |
| `usecases/chat.py` | `ChatUseCase` dan `MAX_AGENT_STEPS`. |
| `usecases/reviewed_chat.py` | `ReviewedChatUseCase`, `ChatTurn`, dan `validate_decisions`. |
| `dto/user.py` | Contoh DTO Pydantic (`UserDTO`). Belum dipakai agent. |
| `mappers/user.py` | Contoh mapper entity ke DTO (`UserMapper`). Belum dipakai agent. |
| `prompts/` | Tempat fungsi yang merakit prompt dari data saat runtime. Kosong di template. |
| `services/` | Tempat koordinasi beberapa use case. Kosong di template. |

Setiap fungsi, kelas, dan konstanta di folder ini dijelaskan di [Referensi API agent](agent.md).

## Folder infrastructure

Pohon berikut menunjukkan isi `src/infrastructure/`:

```text
infrastructure/
├── AI/
│   ├── llm/
│   │   └── openai.py
│   ├── memory/
│   │   └── checkpointer.py
│   └── tools/
│       ├── email_tool.py
│       └── weather_tool.py
├── connections/
├── database/
├── external/
└── logging_config.py
```

| Path | Fungsi |
|---|---|
| `AI/llm/openai.py` | `get_llm_model`, pembuat chat model untuk OpenAI atau endpoint yang kompatibel dengan OpenAI. |
| `AI/memory/checkpointer.py` | `get_checkpointer`, pembuat penyimpan percakapan (`InMemorySaver`). |
| `AI/tools/weather_tool.py` | Tool contoh `get_weather` yang membaca data. Isinya placeholder dengan jawaban tetap. |
| `AI/tools/email_tool.py` | Tool contoh `send_email` yang punya efek ke dunia luar. Isinya placeholder: email hanya dicatat ke log. |
| `connections/` | Tempat koneksi yang dipakai bersama, misalnya pool database. Kosong di template. |
| `database/` | Tempat implementasi repository. Kosong di template. |
| `external/` | Tempat client API pihak ketiga. Kosong di template. |
| `logging_config.py` | `setup_logging(log_level)`. Memasang log ke console dan ke `logs/app.log` dengan level bawaan `INFO`. |

## Folder interface

Pohon berikut menunjukkan isi `src/interface/`:

```text
interface/
├── http/
│   ├── main.py
│   ├── controllers/
│   │   ├── chat_controller.py
│   │   ├── hitl_controller.py
│   │   ├── playground_controller.py
│   │   └── subagents_controller.py
│   └── routers/
│       ├── chat.py
│       ├── hitl.py
│       ├── playground.py
│       └── subagents.py
├── playground/
│   ├── features.py
│   ├── runner.py
│   └── settings.py
├── streamlit/
│   ├── main.py
│   ├── components/
│   └── pages/
│       ├── chat_with_search.py
│       ├── chat_with_user_feedback.py
│       ├── file_Q&A.py
│       ├── langchain_prompt_template.py
│       └── langchain_quickstart.py
├── cli/
└── discord/
```

### http

| Path | Fungsi |
|---|---|
| `http/main.py` | Membuat aplikasi FastAPI, memanggil `setup_logging()`, mendaftarkan router, memasang handler `DomainError`, dan menyediakan `GET /health`. Router playground dan aturan CORS hanya dipasang jika `PLAYGROUND_ENABLED` bernilai benar. |
| `http/routers/chat.py` | `POST /chat`. |
| `http/routers/hitl.py` | `POST /hitl/chat` dan `POST /hitl/review`. |
| `http/routers/subagents.py` | `POST /subagents/chat`. |
| `http/routers/playground.py` | `GET /playground/features`, `POST /playground/messages`, `POST /playground/resume`. |
| `http/controllers/chat_controller.py` | Model `ChatRequest` dan `ChatResponse`, perakit `get_react_agent` dan `get_chat_usecase`, dan handler `chat`. |
| `http/controllers/hitl_controller.py` | Model request dan respons review, konstanta `TOOLS` dan `TOOLS_REQUIRING_APPROVAL`, perakit `get_human_in_the_loop_agent` dan `get_reviewed_chat_usecase`, dan handler `chat` dan `review`. |
| `http/controllers/subagents_controller.py` | Konstanta `SUBAGENTS`, perakit `get_supervisor_agent` dan `get_subagents_chat_usecase`. |
| `http/controllers/playground_controller.py` | Model request dan respons playground, dan handler yang mengubah jejak langkah agent menjadi JSON. |

Endpoint dijelaskan di [Referensi HTTP API](http-api.md) dan [Referensi Playground API](playground-api.md).

### playground

| Path | Fungsi |
|---|---|
| `playground/features.py` | `Feature`, daftar `FEATURES`, dan `find_feature`. Daftar ini menentukan agent yang bisa dicoba di playground. |
| `playground/runner.py` | Menjalankan agent dan mencatat setiap langkahnya. Tidak bergantung pada HTTP. |
| `playground/settings.py` | `playground_enabled()` dan `playground_origins()`, yang membaca `PLAYGROUND_ENABLED` dan `PLAYGROUND_ORIGINS`. |

### streamlit

| Path | Fungsi |
|---|---|
| `streamlit/main.py` | Halaman utama: chatbot contoh yang memanggil OpenAI langsung, bukan agent proyek. API key diisi user di sidebar. |
| `streamlit/pages/chat_with_search.py` | Kerangka UI chat dengan pencarian web. Belum memanggil LLM. |
| `streamlit/pages/chat_with_user_feedback.py` | Kerangka UI chat dengan tombol feedback. Belum memanggil LLM. |
| `streamlit/pages/file_Q&A.py` | Kerangka UI tanya jawab atas file yang diunggah. Belum memanggil LLM. |
| `streamlit/pages/langchain_prompt_template.py` | Kerangka form satu pertanyaan. Fungsi `generate_response` masih kosong. |
| `streamlit/pages/langchain_quickstart.py` | Kerangka form satu pertanyaan. Fungsi `generate_response` masih kosong. |
| `streamlit/components/` | Tempat potongan UI yang dipakai ulang. Kosong di template. |

Setiap file `.py` di `streamlit/pages/` menjadi satu halaman di sidebar Streamlit.

### cli dan discord

| Path | Fungsi |
|---|---|
| `cli/` | Tempat perintah command line yang memanggil use case. Kosong di template; docstring-nya berisi contoh. |
| `discord/` | Tempat bot Discord yang memanggil use case. Kosong di template; docstring-nya berisi contoh. |

## Folder test

| Path | Fungsi |
|---|---|
| `test/conftest.py` | Kelas `FakeToolCallingModel` dan fixture `scripted_model`. Model palsu ini menjawab sesuai naskah, dan mencatat pesan yang diterimanya di `received` dan tool yang diberikan agent di `bound_tools`. |
| `test/test_chat_usecase.py` | Empat test contoh: jawaban langsung, pemanggilan tool, percakapan yang berlanjut, dan penolakan pesan kosong. |

Alasan test memakai model palsu dijelaskan di [Konsep: Menguji tanpa LLM asli](../konsep/pengujian.md).

## Lokasi untuk kode baru

Tabel berikut memetakan jenis kode ke lokasinya:

| Yang ditambah | Lokasi | Panduan |
|---|---|---|
| Tool | `src/infrastructure/AI/tools/`, lalu didaftarkan di controller agent yang memakainya | [Menambah tool](../panduan/menambah-tool.md) |
| Tool yang butuh persetujuan | `TOOLS` dan `TOOLS_REQUIRING_APPROVAL` di `hitl_controller.py` | [Mewajibkan persetujuan untuk sebuah tool](../panduan/mewajibkan-persetujuan.md) |
| Subagent | `SUBAGENTS` di `subagents_controller.py`, prompt di `domain/templates/prompt/subagents/` | [Menambah subagent](../panduan/menambah-subagent.md) |
| Node graph | `src/application/AI/agents/NAMA/nodes/` | [Menambah node ke graph](../panduan/menambah-node.md) |
| Agent baru | `src/application/AI/agents/NAMA/`, state di `domain/entities/agents/NAMA/`, prompt di `domain/templates/prompt/NAMA/` | Tidak ada |
| System prompt | `src/domain/templates/prompt/` | [Mengubah system prompt](../panduan/mengubah-system-prompt.md) |
| Aksi bisnis | `src/application/usecases/` | Tidak ada |
| Entity atau aturan bisnis | `src/domain/entities/` | Tidak ada |
| Error bisnis | `src/domain/exceptions/` | Tidak ada |
| Endpoint | `src/interface/http/routers/` dan `controllers/`, lalu didaftarkan di `main.py` | [Menambah endpoint](../panduan/menambah-endpoint.md) |
| Fitur playground | `FEATURES` di `src/interface/playground/features.py` | [Mencoba fitur di playground](../panduan/mencoba-di-playground.md) |
| Provider LLM lain | `src/infrastructure/AI/llm/` | [Mengatur model dan API key](../panduan/mengatur-llm.md) |
| Penyimpanan percakapan lain | `src/infrastructure/AI/memory/` | [Menyimpan percakapan di database](../panduan/menyimpan-percakapan.md) |
| Akses database | Kontrak di `domain/repositories/`, implementasi di `infrastructure/database/` | Tidak ada |

`NAMA` adalah nama agent yang kamu buat, misalnya `rag`.

## Halaman terkait

- [Referensi: Perintah zul](cli.md)
- [Referensi: API agent](agent.md)
- [Referensi: Environment variable](konfigurasi.md)
- [Konsep: Arsitektur hexagonal](../konsep/arsitektur-hexagonal.md)
- [Konsep: Perjalanan sebuah request](../konsep/alur-request.md)
