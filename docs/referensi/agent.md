# API agent

Halaman ini mencantumkan API Python proyek hasil `zul build hexa`: state, exception, prompt, perakit agent, use case, adapter, dan fungsi composition root di controller. Urutannya mengikuti layer kode, dari `domain` sampai `interface`.

Semua path di halaman ini relatif terhadap root proyek, dan semua impor berawalan `src`. Contoh berikut mengimpor perakit agent ReAct dan use case chat:

```python
from src.application.AI.agents.react.react import build_react_agent
from src.application.usecases.chat import ChatUseCase
```

## State agent

Lokasi: `src/domain/entities/agents/react/react.py`.

### `AgentState`

Bentuk data yang dibawa graph dari satu node ke node berikutnya. State ini dipakai agent ReAct, agent human-in-the-loop, supervisor, dan subagent.

Definisinya adalah sebagai berikut:

```python title="src/domain/entities/agents/react/react.py"
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: RemainingSteps
```

| Field | Tipe | Keterangan |
|---|---|---|
| `messages` | `list[AnyMessage]` dengan reducer `add_messages` | Riwayat percakapan. Pesan yang dikembalikan node ditambahkan ke daftar. Pesan dengan `id` yang sama menggantikan versi lamanya. |
| `remaining_steps` | `RemainingSteps` | Sisa langkah sebelum `recursion_limit` tercapai. Diisi LangGraph, bukan oleh node. |

State untuk agent lain dibuat dengan menurunkan `AgentState`:

```python
class RagState(AgentState):
    documents: list[str]
```

## Exception domain

Lokasi: `src/domain/exceptions/__init__.py`. Baris impornya adalah sebagai berikut:

```python
from src.domain.exceptions import (
    DomainError,
    EmptyMessageError,
    InvalidReviewDecisionError,
    NoPendingReviewError,
    ReviewPendingError,
)
```

Setiap turunan `DomainError` yang lolos dari use case diubah menjadi respons HTTP 400 oleh handler di `src/interface/http/main.py`. Teks exception menjadi isi `detail`.

| Exception | Argumen | Pesan | Dilempar oleh |
|---|---|---|---|
| `DomainError` | Teks pesan | Ditentukan pemanggil | Tidak dilempar langsung oleh template. Kelas dasar semua pelanggaran aturan bisnis. |
| `EmptyMessageError` | Tidak ada | `Message tidak boleh kosong` | `ChatUseCase.execute`, `ReviewedChatUseCase.send_message` |
| `ReviewPendingError` | Tidak ada | `Masih ada aksi yang menunggu persetujuan. Kirim keputusannya dulu.` | `ReviewedChatUseCase.send_message` |
| `NoPendingReviewError` | Tidak ada | `Tidak ada aksi yang menunggu persetujuan di percakapan ini` | `ReviewedChatUseCase.submit_review` |
| `InvalidReviewDecisionError` | Teks pesan | Ditentukan pemanggil | `validate_decisions` |

Pesan `InvalidReviewDecisionError` dicantumkan di [Referensi format review human-in-the-loop](format-review.md).

## System prompt

Lokasi: `src/domain/templates/prompt/`. Setiap prompt adalah string Python.

| Konstanta | File | Dipakai sebagai |
|---|---|---|
| `REACT_SYSTEM_PROMPT` | `react/react_prompt_templates.py` | Nilai bawaan `system_prompt` di `build_react_agent`. |
| `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT` | `human_in_the_loop/human_in_the_loop_prompt_templates.py` | Nilai bawaan `system_prompt` di `build_human_in_the_loop_agent`. |
| `SUPERVISOR_SYSTEM_PROMPT` | `subagents/subagents_prompt_templates.py` | Nilai bawaan `system_prompt` di `build_supervisor_agent`. |
| `WEATHER_AGENT_SYSTEM_PROMPT` | `subagents/subagents_prompt_templates.py` | Prompt subagent `weather_agent`. |
| `EMAIL_AGENT_SYSTEM_PROMPT` | `subagents/subagents_prompt_templates.py` | Prompt subagent `email_agent`. |
| `_SUBAGENT_OUTPUT_RULE` | `subagents/subagents_prompt_templates.py` | Aturan penutup yang disambungkan ke akhir setiap prompt subagent. |

Isi `REACT_SYSTEM_PROMPT`:

```python title="src/domain/templates/prompt/react/react_prompt_templates.py"
REACT_SYSTEM_PROMPT = """\
You are a helpful AI assistant.

Think step by step. When a tool can give you facts you do not have, call it
instead of guessing. Once you have enough information, answer the user directly
and concisely, in the same language the user used.
"""
```

Isi `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT`:

```python title="src/domain/templates/prompt/human_in_the_loop/human_in_the_loop_prompt_templates.py"
HUMAN_IN_THE_LOOP_SYSTEM_PROMPT = """\
You are a helpful AI assistant.

Think step by step. When a tool can give you facts or perform an action the user
asked for, call it instead of guessing.

Some actions are reviewed by a human before they run. If a tool result says the
user rejected the action, do not call that tool again with the same arguments:
explain what was not done and ask the user how they want to proceed.

Answer concisely, in the same language the user used.
"""
```

Isi `SUPERVISOR_SYSTEM_PROMPT` dan `_SUBAGENT_OUTPUT_RULE`:

```python title="src/domain/templates/prompt/subagents/subagents_prompt_templates.py"
SUPERVISOR_SYSTEM_PROMPT = """\
You are a supervisor that coordinates specialized subagents.

Each tool you have is one subagent. Break the user's request into tasks, delegate
each task to the subagent whose description matches it, then combine their results
into one answer. A subagent only sees the query you give it, not this conversation,
so write each query as a complete, self-contained instruction.

Answer concisely, in the same language the user used.
"""

_SUBAGENT_OUTPUT_RULE = """
Your final message is the only thing the supervisor sees. Put every result it
needs (facts, confirmations, anything that failed) in that final message.
"""
```

## Agent ReAct

Lokasi: `src/application/AI/agents/react/`.

### `build_react_agent(llm, tools, system_prompt, checkpointer)`

Merakit graph agent ReAct dengan dua node, `llm_call` dan `tool_node`. File: `react.py`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `llm` | `BaseChatModel` | Wajib | Chat model yang mendukung tool calling. |
| `tools` | `Sequence[BaseTool]` | Wajib | Tool yang boleh dipanggil agent. Boleh kosong. |
| `system_prompt` | `str` | `REACT_SYSTEM_PROMPT` | Instruksi sistem untuk agent. |
| `checkpointer` | `BaseCheckpointSaver` atau `None` | `None` | Penyimpan state per thread. Jika diisi, setiap `invoke` wajib menyertakan `thread_id`. |

**Mengembalikan:** graph ter-compile. Graph dipanggil dengan `.invoke({"messages": [...]}, config)` dan mengembalikan state akhir; jawaban agent adalah pesan terakhir di `messages`.

**Melempar:** tidak ada saat merakit. Saat dipanggil, graph yang punya checkpointer melempar `ValueError` jika `config` tidak berisi `thread_id`.

Contoh berikut merakit agent tanpa memory lalu memanggilnya:

```python
from src.application.AI.agents.react.react import build_react_agent
from src.infrastructure.AI.llm.openai import get_llm_model
from src.infrastructure.AI.tools.weather_tool import get_weather

agent = build_react_agent(llm=get_llm_model(), tools=[get_weather])
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in sf?"}]},
    {"recursion_limit": 25},
)

print(result["messages"][-1].text)
```

Contoh berikut merakit agent dengan memory dan memanggilnya dua kali di thread yang sama:

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = build_react_agent(llm=llm, tools=tools, checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "user-42"}}

agent.invoke({"messages": [{"role": "user", "content": "Saya Bob"}]}, config)
agent.invoke({"messages": [{"role": "user", "content": "Siapa saya?"}]}, config)
```

### `make_llm_call(model_with_tools, system_prompt, steps_per_tool_round)`

Membuat node `llm_call`. File: `nodes/react_nodes.py`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `model_with_tools` | Chat model hasil `llm.bind_tools(tools)` | Wajib | Model yang sudah diberi daftar tool. |
| `system_prompt` | `str` | Wajib | Instruksi sistem yang ditaruh di depan percakapan pada setiap pemanggilan. |
| `steps_per_tool_round` | `int` | `STEPS_PER_TOOL_ROUND` (`2`) | Jumlah langkah graph dari `llm_call` ini sampai `llm_call` berikutnya ketika ada tool call. |

**Mengembalikan:** fungsi node `llm_call(state: AgentState) -> dict`.

Node `llm_call` memanggil model dengan system prompt diikuti `state["messages"]`, lalu mengembalikan `{"messages": [response]}`. Jika respons berisi tool call dan `state["remaining_steps"] <= steps_per_tool_round`, respons diganti dengan `AIMessage` berisi `STEP_LIMIT_MESSAGE` tanpa tool call.

### `should_continue(state)`

Memilih langkah setelah `llm_call`. File: `nodes/react_nodes.py`.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `state` | `AgentState` | State graph saat ini. |

**Mengembalikan:** `"tool_node"` jika pesan terakhir berisi tool call, atau `END` jika tidak.

### Konstanta agent ReAct

| Nama | File | Nilai | Keterangan |
|---|---|---|---|
| `STEPS_PER_TOOL_ROUND` | `nodes/react_nodes.py` | `2` | Satu putaran tool melewati dua node: `tool_node` lalu `llm_call`. |
| `STEP_LIMIT_MESSAGE` | `nodes/react_nodes.py` | `"Maaf, saya butuh lebih banyak langkah untuk menyelesaikan permintaan ini."` | Jawaban penutup saat langkah hampir habis. |

## Agent human-in-the-loop

Lokasi: `src/application/AI/agents/human_in_the_loop/`.

### `build_human_in_the_loop_agent(llm, tools, tools_requiring_approval, checkpointer, system_prompt)`

Merakit graph agent dengan tiga node: `llm_call`, `human_review`, dan `tool_node`. File: `human_in_the_loop.py`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `llm` | `BaseChatModel` | Wajib | Chat model yang mendukung tool calling. |
| `tools` | `Sequence[BaseTool]` | Wajib | Semua tool yang boleh dipanggil agent. |
| `tools_requiring_approval` | `Collection[str]` | Wajib | Nama tool yang harus disetujui manusia sebelum dijalankan. |
| `checkpointer` | `BaseCheckpointSaver` | Wajib | Penyimpan state per thread. `interrupt()` tidak bisa berjalan tanpanya. |
| `system_prompt` | `str` | `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT` | Instruksi sistem untuk agent. |

**Mengembalikan:** graph ter-compile. Setiap `invoke` wajib menyertakan `config` berisi `{"configurable": {"thread_id": ...}}`. Jika graph berhenti menunggu keputusan, hasil `invoke` berisi kunci `"__interrupt__"`.

**Melempar:** `ValueError` jika `tools_requiring_approval` berisi nama yang tidak ada di `tools`. Pesannya berbentuk `tools_requiring_approval berisi tool tak dikenal: ['NAMA']`.

Contoh berikut merakit agent, memanggilnya, lalu melanjutkannya dengan keputusan:

```python
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

agent = build_human_in_the_loop_agent(
    llm=llm,
    tools=[get_weather, send_email],
    tools_requiring_approval={"send_email"},
    checkpointer=InMemorySaver(),
)
config = {"configurable": {"thread_id": "t1"}}

result = agent.invoke({"messages": [HumanMessage(content="email alice")]}, config)
if "__interrupt__" in result:
    print(result["__interrupt__"][0].value)
    result = agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config)
```

> [!NOTE]
> Di aplikasi, agent ini dipanggil lewat `ReviewedChatUseCase`, yang memvalidasi keputusan sebelum graph dilanjutkan.

### `STEPS_PER_TOOL_ROUND` (human-in-the-loop)

Konstanta di `human_in_the_loop.py` bernilai `3`. Satu putaran tool di graph ini melewati tiga node: `human_review`, `tool_node`, lalu `llm_call`. Nilai ini diberikan ke `make_llm_call` sebagai `steps_per_tool_round`.

### `should_continue(state)` (human-in-the-loop)

Memilih langkah setelah `llm_call`. File: `nodes/human_in_the_loop_nodes.py`.

**Mengembalikan:** `"human_review"` jika pesan terakhir berisi tool call, atau `END` jika tidak.

### `build_review_request(tool_calls)`

Membuat payload review yang ditampilkan ke manusia. File: `nodes/human_in_the_loop_nodes.py`.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `tool_calls` | `Sequence[ToolCall]` | Tool call yang butuh persetujuan. |

**Mengembalikan:** `dict` berisi `action_requests` dan `review_configs`. Bentuknya dijelaskan di [Referensi format review human-in-the-loop](format-review.md).

### `make_human_review(tools_requiring_approval)`

Membuat node `human_review`. File: `nodes/human_in_the_loop_nodes.py`.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `tools_requiring_approval` | `Collection[str]` | Nama tool yang wajib disetujui manusia. Tool lain langsung diteruskan ke `tool_node`. |

**Mengembalikan:** fungsi node `human_review(state: AgentState) -> Command`.

Perilaku node `human_review`:

- Jika tidak ada tool call yang butuh persetujuan, node mengembalikan `Command(goto="tool_node")` tanpa berhenti.
- Jika ada, node memanggil `interrupt()` dengan hasil `build_review_request`. Graph berhenti sampai dilanjutkan dengan `Command(resume={"decisions": [...]})`.
- Setelah dilanjutkan, node memasangkan keputusan dengan tool call yang direview menurut urutannya. Tool call yang tidak butuh review diperlakukan sebagai `APPROVE`. Tool call yang butuh review tetapi tidak mendapat keputusan diperlakukan sebagai `NO_DECISION`.
- Node mengembalikan `Command` yang memperbarui `messages` dan menuju `"tool_node"` jika masih ada tool call yang berjalan, atau `"llm_call"` jika semuanya ditolak.

### `unanswered_tool_calls(messages)`

Mengembalikan tool call di `AIMessage` terakhir yang belum punya `ToolMessage`. File: `nodes/human_in_the_loop_nodes.py`.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `messages` | `Sequence[AnyMessage]` | Riwayat pesan dari state. |

**Mengembalikan:** `list[ToolCall]`.

### `make_tool_node(tools)`

Membuat node `tool_node` yang hanya menjalankan tool call yang lolos review. File: `nodes/human_in_the_loop_nodes.py`.

| Parameter | Tipe | Keterangan |
|---|---|---|
| `tools` | `Sequence[BaseTool]` | Tool yang bisa dijalankan. |

**Mengembalikan:** fungsi node `tool_node(state: AgentState) -> dict`.

Node ini menjalankan setiap hasil `unanswered_tool_calls` dan mengembalikan `ToolMessage`-nya. Jika nama tool tidak dikenal, node mengembalikan `ToolMessage` berstatus `error` dengan isi berbentuk berikut:

```text
Error: NAMA_TOOL is not a valid tool, try one of ['get_weather', 'send_email'].
```

`NAMA_TOOL` adalah nama yang diminta model.

Jika argumen tidak sesuai skema tool, node mengembalikan `ToolMessage` berstatus `error` yang menyebut field bermasalah, dengan isi berbentuk berikut:

```text
Error: invalid arguments for send_email. subject: Field required; body: Field required
```

Exception lain yang dilempar fungsi tool diteruskan ke pemanggil.

### Konstanta agent human-in-the-loop

| Nama | File | Nilai |
|---|---|---|
| `STEPS_PER_TOOL_ROUND` | `human_in_the_loop.py` | `3` |
| `ALLOWED_DECISIONS` | `nodes/human_in_the_loop_nodes.py` | `["approve", "edit", "reject"]` |
| `REJECTED_BY_USER_MESSAGE` | `nodes/human_in_the_loop_nodes.py` | `"User rejected this action. It was not executed."` |
| `APPROVE` | `nodes/human_in_the_loop_nodes.py` | `{"type": "approve"}` |
| `NO_DECISION` | `nodes/human_in_the_loop_nodes.py` | `{"type": "reject", "message": "No decision was given for this action. It was not executed."}` |

## Subagents

Lokasi: `src/application/AI/agents/subagents/subagents.py`.

### `MAX_SUBAGENT_STEPS`

Konstanta bernilai `15`. Nilai ini menjadi `recursion_limit` untuk satu tugas subagent, terpisah dari batas langkah supervisor.

### `SubagentSpec`

Definisi satu subagent. Kelas ini adalah dataclass yang tidak bisa diubah setelah dibuat (`frozen=True`).

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | Wajib | Nama tool yang dilihat supervisor. Harus unik di antara subagent. |
| `description` | `str` | Wajib | Deskripsi tool yang dilihat supervisor. |
| `system_prompt` | `str` | Wajib | Instruksi sistem untuk subagent. |
| `tools` | `Sequence[BaseTool]` | Wajib | Tool milik subagent. |
| `llm` | `BaseChatModel` atau `None` | `None` | Model khusus subagent ini. `None` berarti memakai model supervisor. |

Contoh berikut mendefinisikan subagent cuaca:

```python
from src.application.AI.agents.subagents.subagents import SubagentSpec

weather_agent = SubagentSpec(
    name="weather_agent",
    description="Look up current weather for a location.",
    system_prompt="You are a weather specialist.",
    tools=[get_weather],
)
```

### `build_subagent_tool(spec, default_llm)`

Merakit satu subagent sebagai agent ReAct tanpa checkpointer, lalu membungkusnya menjadi tool untuk supervisor.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `spec` | `SubagentSpec` | Wajib | Definisi subagent. |
| `default_llm` | `BaseChatModel` | Wajib | Model yang dipakai jika `spec.llm` bernilai `None`. |

**Mengembalikan:** `BaseTool` bernama `spec.name` dengan deskripsi `spec.description`. Tool ini menerima satu argumen, `query` (`str`), memanggil subagent dengan `recursion_limit` sebesar `MAX_SUBAGENT_STEPS`, dan mengembalikan teks pesan terakhir subagent.

### `build_supervisor_agent(llm, subagents, system_prompt, checkpointer)`

Merakit supervisor: agent ReAct yang setiap tool-nya adalah satu subagent.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `llm` | `BaseChatModel` | Wajib | Chat model supervisor, dan model subagent yang tidak punya model sendiri. |
| `subagents` | `Sequence[SubagentSpec]` | Wajib | Definisi subagent yang tersedia. |
| `system_prompt` | `str` | `SUPERVISOR_SYSTEM_PROMPT` | Instruksi sistem untuk supervisor. |
| `checkpointer` | `BaseCheckpointSaver` atau `None` | `None` | Penyimpan percakapan supervisor per `thread_id`. |

**Mengembalikan:** graph ter-compile yang dipanggil sama seperti hasil `build_react_agent`, sehingga bisa diberikan ke `ChatUseCase`.

**Melempar:** `ValueError` jika ada nama subagent yang sama. Pesannya berbentuk `Nama subagent harus unik, duplikat: ['NAMA']`.

Contoh berikut merakit supervisor dengan satu subagent dan memanggilnya lewat use case:

```python
from langgraph.checkpoint.memory import InMemorySaver

from src.application.AI.agents.subagents.subagents import build_supervisor_agent
from src.application.usecases.chat import ChatUseCase

supervisor = build_supervisor_agent(
    llm=llm,
    subagents=[weather_agent],
    checkpointer=InMemorySaver(),
)

answer = ChatUseCase(supervisor).execute("cuaca di sf?", thread_id="t1")
```

## Use case chat

Lokasi: `src/application/usecases/chat.py`.

### `MAX_AGENT_STEPS`

Konstanta bernilai `25`. Nilai ini adalah jumlah langkah graph paling banyak untuk satu pesan, dan menjadi nilai bawaan `max_agent_steps` di kedua use case.

### `ChatAgent`

Protocol yang menggambarkan agent yang diterima `ChatUseCase`: objek apa pun yang punya method `invoke(input, config=None)` dan mengembalikan `dict` berisi `messages`. Graph ter-compile dari LangGraph memenuhi protocol ini.

### `ChatUseCase(agent, max_agent_steps)`

Menjalankan satu giliran percakapan dengan agent. Dipakai untuk agent ReAct dan supervisor.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `agent` | `ChatAgent` | Wajib | Agent yang dipanggil. |
| `max_agent_steps` | `int` | `MAX_AGENT_STEPS` (`25`) | Nilai `recursion_limit` untuk setiap pemanggilan agent. |

### `ChatUseCase.execute(message, thread_id)`

Mengirim pesan user ke agent dan mengembalikan jawaban akhirnya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `message` | `str` | Wajib | Pesan dari user. |
| `thread_id` | `str` | Wajib | ID percakapan. Pesan dengan `thread_id` yang sama melanjutkan percakapan sebelumnya jika agent memakai checkpointer. |

**Mengembalikan:** `str`, yaitu teks pesan terakhir agent.

**Melempar:** `EmptyMessageError` jika `message` kosong atau hanya berisi spasi. Agent tidak dipanggil dalam keadaan itu.

Use case memanggil agent dengan `config` berisi `recursion_limit` dan `thread_id`.

Contoh berikut memasang batas 40 langkah, lalu mengirim satu pesan:

```python
from src.application.usecases.chat import ChatUseCase

usecase = ChatUseCase(agent, max_agent_steps=40)
answer = usecase.execute("cuaca di sf?", thread_id="user-42")
```

## Use case chat dengan review

Lokasi: `src/application/usecases/reviewed_chat.py`.

### `INTERRUPT_KEY`

Konstanta bernilai `"__interrupt__"`, yaitu kunci di hasil `invoke` yang berisi payload interrupt.

### `ReviewableAgent`

Protocol yang menggambarkan agent yang diterima `ReviewedChatUseCase`: objek yang punya method `invoke(input, config=None)` dan `get_state(config)`. Graph ter-compile dengan checkpointer memenuhi protocol ini.

### `ChatTurn`

Hasil satu giliran percakapan. Kelas ini adalah dataclass yang tidak bisa diubah setelah dibuat (`frozen=True`). Tepat satu field terisi.

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `answer` | `str` atau `None` | `None` | Jawaban agent, jika agent selesai menjawab. |
| `pending_review` | `dict` atau `None` | `None` | Payload review, jika agent berhenti menunggu keputusan. |

### `validate_decisions(decisions, pending_review)`

Memeriksa apakah daftar keputusan cocok dengan aksi yang menunggu review. Fungsi ini berdiri di tingkat modul karena dipakai juga oleh playground.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `decisions` | `Sequence[dict]` | Wajib | Keputusan dari manusia. |
| `pending_review` | `dict` | Wajib | Payload review yang sedang menunggu, berisi `action_requests`. |

**Mengembalikan:** `None` jika semua keputusan valid.

**Melempar:** `InvalidReviewDecisionError` jika jumlah, jenis, atau isi keputusan tidak sesuai. Aturan dan pesannya dicantumkan di [Referensi format review human-in-the-loop](format-review.md).

### `ReviewedChatUseCase(agent, max_agent_steps)`

Menjalankan percakapan yang bisa berhenti menunggu keputusan manusia.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `agent` | `ReviewableAgent` | Wajib | Agent yang dirakit dengan checkpointer. |
| `max_agent_steps` | `int` | `MAX_AGENT_STEPS` (`25`) | Nilai `recursion_limit` untuk setiap pemanggilan agent. |

### `ReviewedChatUseCase.send_message(message, thread_id)`

Mengirim pesan user ke agent.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `message` | `str` | Wajib | Pesan dari user. |
| `thread_id` | `str` | Wajib | ID percakapan. |

**Mengembalikan:** `ChatTurn`.

**Melempar:** `EmptyMessageError` jika `message` kosong atau hanya berisi spasi. `ReviewPendingError` jika thread itu masih menunggu keputusan review.

### `ReviewedChatUseCase.submit_review(decisions, thread_id)`

Melanjutkan agent dengan keputusan manusia, satu keputusan per aksi yang direview dan dalam urutan yang sama.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `decisions` | `Sequence[dict]` | Wajib | Daftar keputusan. |
| `thread_id` | `str` | Wajib | ID percakapan yang sedang menunggu. |

**Mengembalikan:** `ChatTurn`. Jika agent kemudian meminta aksi lain yang butuh persetujuan, `pending_review` terisi lagi.

**Melempar:** `NoPendingReviewError` jika thread itu tidak sedang menunggu review. `InvalidReviewDecisionError` jika keputusan tidak cocok dengan aksi yang menunggu. Dalam kedua keadaan itu agent tidak dilanjutkan.

Contoh berikut mengirim pesan, lalu menyetujui aksi yang menunggu:

```python
from src.application.usecases.reviewed_chat import ReviewedChatUseCase

usecase = ReviewedChatUseCase(agent)

turn = usecase.send_message("email alice: rapat jam 10", thread_id="t1")
if turn.pending_review:
    print(turn.pending_review["action_requests"])
    turn = usecase.submit_review([{"type": "approve"}], thread_id="t1")

print(turn.answer)
```

## Adapter infrastructure

Lokasi: `src/infrastructure/AI/`.

### `get_llm_model(temperature, model)`

Membuat chat model `ChatOpenAI`. File: `llm/openai.py`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `temperature` | `float` | `0.0` | Temperature model. |
| `model` | `str` atau `None` | `None` | Nama model. `None` berarti memakai `LLM_MODEL`, lalu `DEFAULT_MODEL`. |

**Mengembalikan:** `ChatOpenAI`. Alamat endpoint diambil dari `LLM_BASE_URL` jika diisi.

**Melempar:** `ValueError` jika `OPENAI_API_KEY` belum diisi.

Contoh berikut membuat model bawaan, model dengan nama tertentu, dan model dengan temperature lain:

```python
from src.infrastructure.AI.llm.openai import get_llm_model

llm = get_llm_model()
llm = get_llm_model(model="gpt-4o")
llm = get_llm_model(temperature=0.7)
```

Konstanta `DEFAULT_MODEL` di file yang sama bernilai `"gpt-4o-mini"`. Environment variable yang dibaca fungsi ini dijelaskan di [Referensi environment variable](konfigurasi.md).

### `get_checkpointer()`

Mengembalikan `InMemorySaver` baru. File: `memory/checkpointer.py`. Fungsi ini tidak punya parameter, dan setiap pemanggilan menghasilkan objek yang berbeda.

`InMemorySaver` menyimpan percakapan di memori proses: isinya hilang saat aplikasi dimulai ulang dan tidak terbagi antar worker.

### Tool contoh

| Tool | File | Argumen | Mengembalikan |
|---|---|---|---|
| `get_weather` | `tools/weather_tool.py` | `location: str` | Teks cuaca. Jawabannya tetap: cerah untuk `sf` atau `san francisco`, tidak diketahui untuk lokasi lain. |
| `send_email` | `tools/email_tool.py` | `to: str`, `subject: str`, `body: str` | Teks konfirmasi yang menyebut alamat tujuan dan subjek. Email hanya dicatat ke log, belum dikirim. |

Setiap file juga mengekspor daftar `tools` berisi tool di file itu: `[get_weather]` dan `[send_email]`.

## Composition root di controller

Lokasi: `src/interface/http/controllers/`. Fungsi di bagian ini menyambungkan adapter infrastructure ke agent dan use case. Semuanya berdekorator `@lru_cache`: objeknya dibuat pada pemanggilan pertama, lalu dipakai ulang oleh semua request.

### `get_react_agent()`

Mengembalikan agent ReAct yang dilayani `POST /chat` dan dicoba di playground. File: `chat_controller.py`.

Isinya adalah sebagai berikut:

```python title="src/interface/http/controllers/chat_controller.py"
@lru_cache
def get_react_agent():
    """Agent ReAct yang dilayani `POST /chat` dan dicoba di playground."""
    return build_react_agent(
        llm=get_llm_model(),
        tools=tools,
        checkpointer=get_checkpointer(),
    )
```

`tools` di sini adalah daftar yang diimpor dari `src/infrastructure/AI/tools/weather_tool.py`.

### `get_chat_usecase()`

Mengembalikan `ChatUseCase(get_react_agent())`. File: `chat_controller.py`. Router `POST /chat` memintanya lewat `Depends`.

### `get_human_in_the_loop_agent()`

Mengembalikan agent human-in-the-loop yang dilayani `POST /hitl/*` dan dicoba di playground. File: `hitl_controller.py`.

Agent dirakit dari dua konstanta di file yang sama:

```python title="src/interface/http/controllers/hitl_controller.py"
TOOLS = [get_weather, send_email]

TOOLS_REQUIRING_APPROVAL = {send_email.name}


@lru_cache
def get_human_in_the_loop_agent():
    """Agent yang dilayani `POST /hitl/*` dan dicoba di playground."""
    return build_human_in_the_loop_agent(
        llm=get_llm_model(),
        tools=TOOLS,
        tools_requiring_approval=TOOLS_REQUIRING_APPROVAL,
        checkpointer=get_checkpointer(),
    )
```

### `get_reviewed_chat_usecase()`

Mengembalikan `ReviewedChatUseCase(get_human_in_the_loop_agent())`. File: `hitl_controller.py`. Router `POST /hitl/chat` dan `POST /hitl/review` memintanya lewat `Depends`.

### `get_supervisor_agent()`

Mengembalikan supervisor yang dilayani `POST /subagents/chat` dan dicoba di playground. File: `subagents_controller.py`.

Supervisor dirakit dari konstanta `SUBAGENTS` di file yang sama:

```python title="src/interface/http/controllers/subagents_controller.py"
@lru_cache
def get_supervisor_agent():
    """Supervisor yang dilayani `POST /subagents/chat` dan dicoba di playground."""
    return build_supervisor_agent(
        llm=get_llm_model(),
        subagents=SUBAGENTS,
        checkpointer=get_checkpointer(),
    )
```

`SUBAGENTS` berisi dua `SubagentSpec`:

| `name` | `tools` | `system_prompt` |
|---|---|---|
| `weather_agent` | `[get_weather]` | `WEATHER_AGENT_SYSTEM_PROMPT` |
| `email_agent` | `[send_email]` | `EMAIL_AGENT_SYSTEM_PROMPT` |

### `get_subagents_chat_usecase()`

Mengembalikan `ChatUseCase(get_supervisor_agent())`. File: `subagents_controller.py`. Router `POST /subagents/chat` memintanya lewat `Depends`.

### Handler dan model request

Setiap controller juga berisi model Pydantic dan fungsi handler yang dipanggil router:

| Controller | Model | Handler |
|---|---|---|
| `chat_controller.py` | `ChatRequest`, `ChatResponse` | `chat(request, usecase)` |
| `hitl_controller.py` | `ReviewedChatRequest`, `EditedAction`, `ReviewDecision`, `ReviewRequest`, `ReviewedChatResponse` | `chat(request, usecase)`, `review(request, usecase)` |
| `subagents_controller.py` | Memakai `ChatRequest` dan `ChatResponse` | Memakai `chat_controller.chat` |

Handler `chat` memakai `thread_id` dari request, atau membuat ID baru dengan `uuid4().hex` jika kosong. Field setiap model dicantumkan di [Referensi HTTP API](http-api.md).

## Ringkasan konstanta

Tabel berikut mengumpulkan semua konstanta di halaman ini. Path relatif terhadap `src/`.

| Nama | File | Nilai |
|---|---|---|
| `MAX_AGENT_STEPS` | `application/usecases/chat.py` | `25` |
| `STEPS_PER_TOOL_ROUND` | `application/AI/agents/react/nodes/react_nodes.py` | `2` |
| `STEPS_PER_TOOL_ROUND` | `application/AI/agents/human_in_the_loop/human_in_the_loop.py` | `3` |
| `STEP_LIMIT_MESSAGE` | `application/AI/agents/react/nodes/react_nodes.py` | Teks jawaban penutup saat langkah hampir habis |
| `MAX_SUBAGENT_STEPS` | `application/AI/agents/subagents/subagents.py` | `15` |
| `ALLOWED_DECISIONS` | `application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py` | `["approve", "edit", "reject"]` |
| `REJECTED_BY_USER_MESSAGE` | `application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py` | Teks hasil tool saat aksi ditolak tanpa alasan |
| `APPROVE` | `application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py` | `{"type": "approve"}` |
| `NO_DECISION` | `application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py` | Keputusan `reject` untuk aksi tanpa keputusan |
| `INTERRUPT_KEY` | `application/usecases/reviewed_chat.py` | `"__interrupt__"` |
| `DEFAULT_MODEL` | `infrastructure/AI/llm/openai.py` | `"gpt-4o-mini"` |
| `TOOLS` | `interface/http/controllers/hitl_controller.py` | `[get_weather, send_email]` |
| `TOOLS_REQUIRING_APPROVAL` | `interface/http/controllers/hitl_controller.py` | `{"send_email"}` |
| `SUBAGENTS` | `interface/http/controllers/subagents_controller.py` | `weather_agent`, `email_agent` |
| `REACT_SYSTEM_PROMPT` | `domain/templates/prompt/react/react_prompt_templates.py` | System prompt agent ReAct |
| `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT` | `domain/templates/prompt/human_in_the_loop/human_in_the_loop_prompt_templates.py` | System prompt agent human-in-the-loop |
| `SUPERVISOR_SYSTEM_PROMPT` | `domain/templates/prompt/subagents/subagents_prompt_templates.py` | System prompt supervisor |
| `WEATHER_AGENT_SYSTEM_PROMPT` | `domain/templates/prompt/subagents/subagents_prompt_templates.py` | System prompt `weather_agent` |
| `EMAIL_AGENT_SYSTEM_PROMPT` | `domain/templates/prompt/subagents/subagents_prompt_templates.py` | System prompt `email_agent` |

## Lihat juga

- [Referensi: Format review human-in-the-loop](format-review.md)
- [Referensi: HTTP API](http-api.md)
- [Referensi: Struktur proyek hexa](struktur-proyek.md)
- [Konsep: Cara kerja agent ReAct](../konsep/agent-react.md)
- [Konsep: Cara kerja human-in-the-loop](../konsep/human-in-the-loop.md)
- [Konsep: Cara kerja subagents](../konsep/subagents.md)
- [Konsep: Memory dan thread](../konsep/memory.md)
- [Panduan: Mengatur batas langkah](../panduan/mengatur-batas-langkah.md)
