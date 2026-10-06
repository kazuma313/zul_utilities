# Mengatur batas langkah

Halaman ini menunjukkan cara mengubah berapa banyak langkah yang boleh diambil agent untuk satu pesan. Batas ini mencegah agent yang terus-menerus meminta tool menghabiskan token tanpa henti.

**Sebelum mulai:** kamu tahu bahwa setiap node yang dijalankan graph dihitung sebagai satu langkah, dan satu putaran tool di agent ReAct memakai dua langkah. Lihat [Cara kerja agent ReAct](../konsep/agent-react.md).

## Mengubah batas untuk semua agent

Batas bawaan adalah 25 langkah per pesan, cukup untuk 11 putaran tool di agent ReAct. Untuk mengubahnya:

1. Buka file use case chat dan ubah nilai konstantanya:

    ```python title="src/application/usecases/chat.py"
    MAX_AGENT_STEPS = 40
    ```

2. Mulai ulang server.

Konstanta ini dipakai oleh `ChatUseCase` dan `ReviewedChatUseCase`, jadi perubahan berlaku untuk agent ReAct, human-in-the-loop, dan supervisor.

## Mengubah batas untuk satu use case

Untuk memberi satu agent batas sendiri tanpa mengubah konstanta, kirim `max_agent_steps` saat membuat use case-nya di controller:

```python title="src/interface/http/controllers/chat_controller.py"
@lru_cache
def get_chat_usecase() -> ChatUseCase:
    return ChatUseCase(get_react_agent(), max_agent_steps=40)
```

## Mengubah batas subagent

Setiap tugas yang didelegasikan ke subagent punya batasnya sendiri, terpisah dari batas supervisor. Bawaannya 15 langkah. Untuk mengubahnya, ubah konstanta berikut:

```python title="src/application/AI/agents/subagents/subagents.py"
MAX_SUBAGENT_STEPS = 20
```

## Mencoba batas lain tanpa mengubah kode

Endpoint playground menerima `max_steps` per pesan, sehingga kamu bisa melihat perilaku agent pada batas tertentu tanpa menyentuh konstanta:

```shell
curl -X POST http://localhost:8000/playground/messages \
  -H "Content-Type: application/json" \
  -d "{\"feature\": \"ReAct\", \"message\": \"What is the weather in sf?\", \"max_steps\": 3}"
```

Dengan batas 3 langkah, agent ReAct tidak sempat menyelesaikan satu putaran tool, jadi ia langsung menjawab dengan pesan penutup. Dengan batas 4, satu putaran tool muat.

## Memeriksa hasilnya

Saat langkah hampir habis, agent tidak berakhir dengan error. Ia menutup percakapan dengan jawaban berikut:

```text
Maaf, saya butuh lebih banyak langkah untuk menyelesaikan permintaan ini.
```

Jika kamu melihat jawaban itu pada permintaan yang wajar, batasnya terlalu rendah untuk tugas tersebut.

## Lihat juga

- [Cara kerja agent ReAct](../konsep/agent-react.md) untuk alasan batas ini ada dan cara agent menutup percakapan sebelum langkahnya habis.
- [API agent](../referensi/agent.md) untuk `MAX_AGENT_STEPS`, `STEPS_PER_TOOL_ROUND`, dan `STEP_LIMIT_MESSAGE`.
- [Playground API](../referensi/playground-api.md) untuk parameter `max_steps`.
