---
hide:
  - navigation
  - toc
---

<div class="zul-wide" markdown>

<div class="zul-hero" markdown>

<div class="zul-hero__text" markdown>

# Proyek AI yang rapi dari satu perintah

Zul membuat kerangka proyek AI berarsitektur hexagonal: agent LangGraph, REST API, memory, dan test sudah di dalamnya. Zul juga membawa helper untuk vector database, OCR, dan pemanggilan LLM.

<div class="zul-actions" markdown>

[Tutorial pertama](tutorial/agent-pertama.md)
[Panduan](panduan/index.md)

</div>

```shell
zul build hexa --name my-agent
```

</div>

<div class="zul-hero__art">
<svg class="zul-stack" viewBox="0 0 470 466" role="img" aria-labelledby="zul-stack-title zul-stack-desc">
  <title id="zul-stack-title">Empat lapisan proyek hasil zul build hexa</title>
  <desc id="zul-stack-desc">Lapisan interface, application, domain, dan infrastructure bertumpuk. Request POST /chat masuk lewat interface, dan infrastructure memanggil LLM.</desc>
  <path class="zs-wire" d="M 102 125 H 112 Q 124 125 134 131 L 216.0 185.2"/>
  <path class="zs-wire" d="M 380.5 343.8 L 430 418 V 432"/>
  <g class="zs-pill">
    <rect x="6" y="112" width="96" height="26" rx="13"/>
    <text x="54" y="129">POST /chat</text>
  </g>
  <g class="zs-pill">
    <rect x="400" y="432" width="60" height="26" rx="13"/>
    <text x="430" y="449">LLM</text>
  </g>
  <!-- Jalur titik ditulis di atribut path milik animateMotion, bukan lewat <mpath>. Navigasi instan Material menulis ulang setiap atribut href di halaman baru, dan href pada <mpath> tidak bisa ditulis ulang, sehingga pindah ke beranda gagal. -->
  <circle class="zs-dot" r="4.5">
    <animateMotion dur="2.6s" repeatCount="indefinite" begin="1.2s" keyPoints="0;1" keyTimes="0;1" calcMode="linear" path="M 102 125 H 112 Q 124 125 134 131 L 216.0 185.2"/>
  </circle>
  <circle class="zs-dot zs-dot--out" r="4.5">
    <animateMotion dur="2.6s" repeatCount="indefinite" begin="2.5s" keyPoints="0;1" keyTimes="0;1" calcMode="linear" path="M 380.5 343.8 L 430 418 V 432"/>
  </circle>
  <g class="zs-drop" style="--zs-delay:0.00s">
    <g class="zs-float zs-float--3">
      <g class="zs-layer zs-layer--infrastructure">
        <polygon class="zs-left" points="125.5,321.0 290.0,416.0 290.0,376.0 125.5,281.0"/>
        <polygon class="zs-right" points="454.5,321.0 290.0,416.0 290.0,376.0 454.5,281.0"/>
        <polygon class="zs-top" points="290.0,186.0 454.5,281.0 290.0,376.0 125.5,281.0"/>
        <text class="zs-name" transform="matrix(0.8660 0.5 0 1 125.5 281.0)" x="12" y="24.5">infrastructure</text>
        <text class="zs-note" transform="matrix(0.8660 -0.5 0 1 290.0 376.0)" x="12" y="24.0">LLM · database · tool</text>
      </g>
    </g>
  </g>
  <g class="zs-drop" style="--zs-delay:0.12s">
    <g class="zs-float zs-float--2">
      <g class="zs-layer zs-layer--domain">
        <polygon class="zs-left" points="125.5,265.0 290.0,360.0 290.0,320.0 125.5,225.0"/>
        <polygon class="zs-right" points="454.5,265.0 290.0,360.0 290.0,320.0 454.5,225.0"/>
        <polygon class="zs-top" points="290.0,130.0 454.5,225.0 290.0,320.0 125.5,225.0"/>
        <text class="zs-name" transform="matrix(0.8660 0.5 0 1 125.5 225.0)" x="12" y="24.5">domain</text>
        <text class="zs-note" transform="matrix(0.8660 -0.5 0 1 290.0 320.0)" x="12" y="24.0">entitas · aturan bisnis</text>
      </g>
    </g>
  </g>
  <g class="zs-drop" style="--zs-delay:0.24s">
    <g class="zs-float zs-float--1">
      <g class="zs-layer zs-layer--application">
        <polygon class="zs-left" points="125.5,209.0 290.0,304.0 290.0,264.0 125.5,169.0"/>
        <polygon class="zs-right" points="454.5,209.0 290.0,304.0 290.0,264.0 454.5,169.0"/>
        <polygon class="zs-top" points="290.0,74.0 454.5,169.0 290.0,264.0 125.5,169.0"/>
        <text class="zs-name" transform="matrix(0.8660 0.5 0 1 125.5 169.0)" x="12" y="24.5">application</text>
        <text class="zs-note" transform="matrix(0.8660 -0.5 0 1 290.0 264.0)" x="12" y="24.0">use case · agent</text>
      </g>
    </g>
  </g>
  <g class="zs-drop" style="--zs-delay:0.36s">
    <g class="zs-float zs-float--0">
      <g class="zs-layer zs-layer--interface">
        <polygon class="zs-left" points="125.5,153.0 290.0,248.0 290.0,208.0 125.5,113.0"/>
        <polygon class="zs-right" points="454.5,153.0 290.0,248.0 290.0,208.0 454.5,113.0"/>
        <polygon class="zs-top" points="290.0,18.0 454.5,113.0 290.0,208.0 125.5,113.0"/>
        <text class="zs-name" transform="matrix(0.8660 0.5 0 1 125.5 113.0)" x="12" y="24.5">interface</text>
        <text class="zs-note" transform="matrix(0.8660 -0.5 0 1 290.0 208.0)" x="12" y="24.0">HTTP · CLI · Streamlit</text>
        <text class="zs-project" transform="matrix(0.8660 0.5 -0.8660 0.5 237.3 105.4)">my-agent/</text>
      </g>
    </g>
  </g>
</svg>
</div>

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
| Computer Vision | Deteksi dan tracking, teks di sudut frame, garis dan poligon penghitung, timer, arah hadap, jarak, blur | [Mendeteksi dan melacak orang](panduan/mendeteksi-dan-melacak-orang.md) |

</div>
