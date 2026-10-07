---
hide:
  - navigation
  - toc
---

<div class="zul-wide" markdown>

<div class="zul-hero" markdown>

<div class="zul-hero__text" markdown>

# Bangun proyek AI yang rapi sejak perintah pertama

Zul membuat kerangka proyek AI berarsitektur hexagonal dengan satu perintah: agent LangGraph, REST API, memory, dan test sudah di dalamnya. Zul juga membawa helper untuk vector database, OCR, dan pemanggilan LLM.

<div class="zul-actions" markdown>

[Tutorial pertama](tutorial/agent-pertama.md)
[Playground](playground.md)

</div>

Proyek baru dibuat dengan satu perintah:

```shell
zul build hexa --name my-agent
```

</div>

<div class="zul-hero__demo" markdown>

<div class="zul-playground" data-feature="Human-in-the-loop" data-simulate data-autoplay="Kirim email ke alice@example.com: rapat besok jam 10">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Panel ini menampilkan simulasi agent human-in-the-loop dari template. Agent itu berhenti sebelum mengirim email dan menunggu keputusan manusia.

</div>

</div>

## Peta dokumentasi

Dokumentasi ini dibagi menjadi empat bagian, menurut kebutuhan pembaca: belajar atau bekerja, langkah atau pengetahuan.

<div class="zul-map" markdown>

| | Saat belajar | Saat bekerja |
|---|---|---|
| **Butuh langkah** | [Tutorial](tutorial/index.md)<br>Pelajaran dari awal sampai ada agent yang berjalan di komputermu. | [Panduan](panduan/index.md)<br>Resep untuk satu tugas: menambah tool, memakai Milvus, menerbitkan dokumentasi. |
| **Butuh pengetahuan** | [Konsep](konsep/index.md)<br>Alasan di balik rancangannya: kenapa strukturnya begini, bagaimana agent bisa berhenti menunggu. | [Referensi](referensi/index.md)<br>Fakta untuk dicari cepat: opsi perintah, bentuk request, parameter, nilai bawaan. |

</div>

## Yang ada di dalam Zul

| Bagian | Isi | Halaman pertama |
|---|---|---|
| CLI | `zul build hexa`, `zul install milvus-helper`, `zul install redis-helper` | [Perintah zul](referensi/cli.md) |
| Template proyek | Agent ReAct, human-in-the-loop, subagents, REST API, memory, test, playground | [Membuat agent pertamamu](tutorial/agent-pertama.md) |
| Vector database | `MilvusHelper`, `RedisHelper`, `RedisVectorDB` | [Milvus](panduan/memakai-milvus.md), [Redis](panduan/memakai-redis.md) |
| OCR | `DoclingVLMConverter`, OCR dengan Gemini | [Mengubah dokumen menjadi teks](panduan/membaca-dokumen-ocr.md) |
| LLM dan embedding | `AIService` | [Memanggil LLM dan embedding](panduan/memanggil-llm-dan-embedding.md) |
| Dokumen | Markdown ke PDF dan PPTX | [Mengubah Markdown menjadi PDF dan PPTX](panduan/mengonversi-markdown.md) |
| Analisis | `ChartGenerator` dengan uji statistik | [Membuat grafik perbandingan](panduan/membuat-grafik.md) |

> [!NOTE]
> Contoh perintah di dokumentasi ini memakai sintaks shell Unix. Di Windows, perintah `zul`, `uv`, `pip`, dan `pytest` sama persis. Yang berbeda hanya perintah sistem seperti `cp`, dan perbedaannya disebut di tempatnya.

</div>
