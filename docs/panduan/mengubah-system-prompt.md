# Mengubah system prompt

System prompt menentukan peran, batasan, dan gaya jawaban agent.

**Sebelum mulai:** kamu punya proyek hasil `zul build hexa`.

## Mengubah prompt bawaan

Setiap agent punya prompt bawaan di `src/domain/templates/prompt/`. Tabel berikut menunjukkan file dan nama konstantanya:

| Agent | File | Konstanta |
|---|---|---|
| ReAct | `react/react_prompt_templates.py` | `REACT_SYSTEM_PROMPT` |
| Human-in-the-loop | `human_in_the_loop/human_in_the_loop_prompt_templates.py` | `HUMAN_IN_THE_LOOP_SYSTEM_PROMPT` |
| Supervisor | `subagents/subagents_prompt_templates.py` | `SUPERVISOR_SYSTEM_PROMPT` |
| Subagent cuaca dan email | `subagents/subagents_prompt_templates.py` | `WEATHER_AGENT_SYSTEM_PROMPT`, `EMAIL_AGENT_SYSTEM_PROMPT` |

Untuk mengubah perilaku sebuah agent di semua pemanggilan:

1. Buka file prompt-nya. Contoh berikut adalah prompt agent ReAct:

    ```python title="src/domain/templates/prompt/react/react_prompt_templates.py"
    REACT_SYSTEM_PROMPT = """\
    You are a helpful AI assistant.

    Think step by step. When a tool can give you facts you do not have, call it
    instead of guessing. Once you have enough information, answer the user directly
    and concisely, in the same language the user used.
    """
    ```

2. Sunting teksnya. Sebutkan peran agent, kapan ia harus memakai tool, dan bahasa serta gaya jawabannya.

3. Mulai ulang server.

Perubahan langsung berlaku, termasuk untuk percakapan yang sudah berjalan. System prompt tidak disimpan di riwayat percakapan; node `llm_call` menambahkannya di depan pada setiap pemanggilan model.

## Memakai prompt lain untuk satu agent

Jika kamu merakit lebih dari satu agent dan masing-masing butuh prompt sendiri, kirim prompt-nya lewat parameter `system_prompt`:

```python
agent = build_react_agent(
    llm=get_llm_model(),
    tools=tools,
    system_prompt=SUPPORT_AGENT_PROMPT,
    checkpointer=get_checkpointer(),
)
```

Di contoh ini `SUPPORT_AGENT_PROMPT` adalah konstanta teks yang kamu tulis sendiri di folder `src/domain/templates/prompt/`. Parameter yang sama tersedia di `build_human_in_the_loop_agent` dan `build_supervisor_agent`.

## Menjaga aturan khusus tiap prompt

Dua prompt bawaan memuat aturan yang dibutuhkan agent-nya. Pertahankan aturan itu saat kamu menyunting:

- Prompt human-in-the-loop meminta model tidak mengulang tool yang ditolak user. Tanpa aturan itu, model cenderung meminta tool yang sama lagi.
- Setiap prompt subagent ditutup dengan `_SUBAGENT_OUTPUT_RULE`, yang meminta subagent menaruh semua hasil di jawaban akhirnya. Supervisor hanya menerima jawaban akhir itu.

## Memeriksa hasilnya

Kirim pesan lewat panel di bawah ini dan perhatikan apakah gaya jawabannya mengikuti prompt barumu:

<div class="zul-playground" data-feature="ReAct">
Panel Playground hanya tampil di situs dokumentasi, <a href="https://zulkit.my.id/">zulkit.my.id</a>.
</div>

## Halaman terkait

- [API agent](../referensi/agent.md) untuk parameter `system_prompt` di setiap perakit agent.
- [Cara kerja subagents](../konsep/subagents.md) untuk alasan di balik `_SUBAGENT_OUTPUT_RULE`.
