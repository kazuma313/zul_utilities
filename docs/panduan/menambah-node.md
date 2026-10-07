# Menambah node ke graph

Langkah baru disisipkan ke graph agent ReAct sebagai node. Contohnya node yang mencatat setiap permintaan tool ke log sebelum tool dijalankan.

**Sebelum mulai:** kamu mengenal bentuk graph ReAct: `llm_call`, lalu `tool_node`, lalu kembali ke `llm_call`. Penjelasannya ada di [Cara kerja agent ReAct](../konsep/agent-react.md).

## Langkah-langkah

1. Tulis node di file node agent ReAct. Node adalah fungsi yang menerima state dan mengembalikan perubahan untuk state itu. Node yang hanya mengamati mengembalikan dict kosong:

    ```python title="src/application/AI/agents/react/nodes/react_nodes.py"
    import logging

    logger = logging.getLogger(__name__)


    def log_tool_calls(state: AgentState) -> dict:
        """Catat setiap permintaan tool sebelum tool dijalankan."""
        for tool_call in state["messages"][-1].tool_calls:
            logger.info("tool=%s args=%s", tool_call["name"], tool_call["args"])

        return {}
    ```

2. Di file yang sama, ubah `should_continue` supaya mengarah ke node baru:

    ```python title="src/application/AI/agents/react/nodes/react_nodes.py"
    def should_continue(state: AgentState) -> Literal["log_tool_calls", END]:
        """Pilih langkah berikutnya: catat tool call, atau selesai."""
        last_message = state["messages"][-1]

        if last_message.tool_calls:
            return "log_tool_calls"

        return END
    ```

3. Di file yang sama, naikkan `STEPS_PER_TOOL_ROUND` dari `2` menjadi `3`, karena satu putaran tool sekarang melewati tiga node:

    ```python title="src/application/AI/agents/react/nodes/react_nodes.py"
    STEPS_PER_TOOL_ROUND = 3
    ```

4. Daftarkan node dan sambungannya di perakit graph. Impor `log_tool_calls`, tambahkan node-nya, lalu ganti tujuan sambungan bersyarat:

    ```python title="src/application/AI/agents/react/react.py"
    agent_builder.add_node("llm_call", make_llm_call(model_with_tools, system_prompt))
    agent_builder.add_node("log_tool_calls", log_tool_calls)
    agent_builder.add_node("tool_node", ToolNode(tools))

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call", should_continue, ["log_tool_calls", END]
    )
    agent_builder.add_edge("log_tool_calls", "tool_node")
    agent_builder.add_edge("tool_node", "llm_call")
    ```

> [!WARNING]
> Jangan melewatkan langkah 3. Jika putaran tool bertambah panjang tetapi `STEPS_PER_TOOL_ROUND` tidak dinaikkan, agent yang kehabisan langkah berakhir dengan `GraphRecursionError`, bukan dengan jawaban penutup.

## Menambah data ke state

Node yang perlu menyimpan data selain pesan membutuhkan field baru di state. Turunkan `AgentState`, lalu pakai kelas turunannya saat membuat `StateGraph`:

```python
class RagState(AgentState):
    documents: list[str]
```

Node kemudian mengembalikan perubahan untuk field itu, misalnya `{"documents": hasil_pencarian}`.

## Memeriksa hasilnya

Kirim pesan yang memicu tool lewat panel di bawah ini, lalu lihat jejaknya. Node baru muncul di antara `llm_call` dan `tool_node`, dengan keterangan "meneruskan tanpa perubahan":

<div class="zul-playground" data-feature="ReAct">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Terminal server juga menampilkan baris log dari node itu, misalnya `tool=get_weather args={'location': 'sf'}`.

## Halaman terkait

- [Mengatur batas langkah](mengatur-batas-langkah.md) untuk hubungan antara jumlah node dan batas langkah.
- [API agent](../referensi/agent.md) untuk `AgentState`, `make_llm_call`, dan `should_continue`.
