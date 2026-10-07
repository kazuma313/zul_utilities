# Membangun tim agent

Agent ketiga di proyekmu adalah supervisor yang membagi pekerjaan ke agent spesialis. Tutorial ini memakai supervisor itu, lalu menambahkan satu spesialis baru ke timnya. Hasil akhirnya supervisor dengan tiga subagent, salah satunya buatanmu.

**Sebelum mulai:** tutorial [Membuat agent pertamamu](agent-pertama.md) sudah selesai, karena tool `get_order_status` dari tutorial itu dipakai di sini, dan server-nya masih berjalan.

## Melihat supervisor mendelegasikan

Supervisor di proyekmu punya dua subagent: `weather_agent` untuk cuaca dan `email_agent` untuk email. Supervisor sendiri tidak punya tool cuaca atau email. Yang ia punya adalah kedua subagent itu.

Panel di bawah ini memakai supervisor itu. Tombol status di bilah panel harus bertuliskan **Terhubung**. Jika tertulis **Simulasi**, panel belum terhubung ke proyekmu dan hanya menampilkan contoh jawaban. Klik tombol itu, lalu klik **Sambungkan**.

<div class="zul-playground" data-feature="Subagents">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Klik contoh pesan **Cek cuaca di sf, lalu email hasilnya ke alice@example.com**.

Supervisor menjawab dengan rangkuman: cuaca di San Francisco, dan keterangan bahwa email sudah dikirim.

Sekarang lihat jejaknya. Sebagian langkah menjorok ke kanan. Langkah yang menjorok adalah pekerjaan subagent; langkah yang rata kiri adalah pekerjaan supervisor. Urutannya kira-kira begini:

1. `llm_call` milik supervisor meminta tool `weather_agent` dengan satu argumen `query`.
2. Menjorok: `weather_agent` bekerja dengan caranya sendiri. Ia meminta `get_weather`, menerima hasilnya, lalu menjawab.
3. `tool_node` milik supervisor mencatat jawaban akhir `weather_agent` sebagai hasil tool.
4. Supervisor mengulangi pola yang sama untuk `email_agent`.
5. `llm_call` milik supervisor merangkum kedua hasil menjadi jawaban.

Perhatikan langkah ketiga. Supervisor hanya menerima satu teks dari subagent, yaitu jawaban akhirnya. Langkah-langkah subagent yang menjorok tidak pernah sampai ke supervisor.

## Menulis prompt untuk subagent baru

Kita tambahkan subagent ketiga yang mengurus pesanan. Subagent butuh tiga hal: tool, prompt, dan pendaftaran. Tool-nya sudah ada dari tutorial pertama, jadi kita mulai dari prompt.

Buka `src/domain/templates/prompt/subagents/subagents_prompt_templates.py` dan tambahkan di akhir file:

```python title="src/domain/templates/prompt/subagents/subagents_prompt_templates.py"
ORDER_AGENT_SYSTEM_PROMPT = """\
You are an order specialist. Use your tools to look up order status.
Do not guess order information.
""" + _SUBAGENT_OUTPUT_RULE
```

Bagian `_SUBAGENT_OUTPUT_RULE` sudah ada di file itu. Isinya meminta subagent menaruh semua hasil kerjanya di jawaban akhir, karena hanya jawaban akhir yang sampai ke supervisor.

## Mendaftarkan subagent

Buka `src/interface/http/controllers/subagents_controller.py`. Di bagian impor, tambahkan prompt dan tool pesanan:

```python title="src/interface/http/controllers/subagents_controller.py"
from src.domain.templates.prompt.subagents.subagents_prompt_templates import (
    EMAIL_AGENT_SYSTEM_PROMPT,
    ORDER_AGENT_SYSTEM_PROMPT,
    WEATHER_AGENT_SYSTEM_PROMPT,
)
from src.infrastructure.AI.tools.order_tool import get_order_status
```

Lalu tambahkan satu `SubagentSpec` ke daftar `SUBAGENTS`, setelah `email_agent`:

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

Simpan kedua file. Server memulai ulang sendiri.

## Mencoba subagent baru

Kembali ke panel, klik **Percakapan baru**, lalu kirim:

```text
What is the status of order ORD-1042?
```

Supervisor menjawab bahwa pesanan itu sudah dikirim. Lihat jejaknya: `llm_call` milik supervisor meminta tool `order_agent`, dan di bawahnya, menjorok, `order_agent` meminta `get_order_status`.

Kita tidak mengubah prompt supervisor. Supervisor memilih `order_agent` karena `description` yang kita tulis menyebut tugasnya dengan jelas.

Sekarang coba permintaan yang melibatkan dua subagent:

```text
Check order ORD-1043 and tell me the weather in sf.
```

Di langkahnya terlihat supervisor memanggil `order_agent` dan `weather_agent`, lalu menggabungkan kedua jawaban.

## Yang sudah kamu kerjakan

Kamu sudah:

- Melihat supervisor membagi satu permintaan ke dua subagent.
- Membaca jejak bertingkat: langkah supervisor dan langkah subagent di dalamnya.
- Menambah subagent baru dengan tiga bagian: tool, prompt, dan `SubagentSpec`.

Ketiga tutorial selesai. Proyekmu sekarang punya tiga agent yang kamu pahami cara kerjanya dan kamu tahu cara mengubahnya.

> [!WARNING]
> `email_agent` menjalankan `send_email` tanpa persetujuan manusia. Di template tool itu baru mencatat ke log, tetapi setelah kamu menyambungkannya ke layanan email sungguhan, setiap tugas yang didelegasikan ke `email_agent` langsung terkirim.

Dari sini, pakai dokumentasi sesuai kebutuhan:

- [Cara kerja subagents](../konsep/subagents.md) menjelaskan kapan pola ini cocok dan apa batasannya.
- [Menambah subagent](../panduan/menambah-subagent.md) memuat pedoman menulis nama dan deskripsi subagent.
- [Mencoba fitur di playground](../panduan/mencoba-di-playground.md) menunjukkan cara mendaftarkan agent buatanmu sendiri ke panel ini.
- [Panduan](../panduan/index.md) memuat tugas lain, seperti menyimpan percakapan di database dan menguji agent.
