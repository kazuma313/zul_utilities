# Memasang Zul lewat code assistant

Panduan ini berisi teks yang bisa kamu tempel ke code assistant (Claude Code, Cursor, atau yang lain) supaya ia memasang Zul untukmu. Assistant bertanya dulu apa yang kamu butuhkan, misalnya MCP, OCR, evaluasi retrieval, atau semuanya, lalu memasang hanya extra untuk jawabanmu. Dengan begitu, library besar seperti PyTorch tidak ikut terpasang jika kamu tidak memakainya. Pilihan extra dan ukurannya dijelaskan di [Instalasi Zul](instalasi-zul.md#memasang-per-topik).

**Sebelum mulai:** kamu butuh code assistant yang bisa menjalankan perintah di terminalmu, Python 3.11 atau lebih baru, dan Git. Assistant yang memeriksa dan memasang sisanya.

## Memakai teks ini

1. Buka code assistant di folder proyek tempat Zul akan dipakai.
2. Tempel teks dari bagian [Prompt untuk ditempel](#prompt-untuk-ditempel).
3. Jawab pertanyaan assistant. Ia memberi pilihan, dan kamu boleh memilih lebih dari satu.
4. Baca rencana yang ditunjukkan assistant: extra yang terpilih, perintah persisnya, dan perkiraan ukuran. Setujui jika sudah sesuai.
5. Tunggu laporan akhirnya. Assistant memeriksa setiap extra yang terpasang, dan melaporkan apa yang masih perlu kamu siapkan sendiri, seperti API key.

Assistant tidak boleh memasang apa pun sebelum kamu menjawab dan menyetujui rencananya. Jika ia langsung menjalankan perintah instalasi tanpa bertanya, hentikan, lalu tempel ulang teksnya.

## Prompt untuk ditempel

```text
Pasang Zul (https://github.com/kazuma313/zul_utilities) di komputerku, tetapi hanya bagian yang aku butuhkan. Jangan menjalankan perintah yang mengubah sistem sebelum aku menjawab pertanyaan di langkah 1 dan menyetujui rencana di langkah 3. Memeriksa versi di langkah 2 boleh langsung dilakukan.

Langkah 1. Tanyakan apa yang aku butuhkan.
Pakai alat tanya jawab yang kamu punya (misalnya AskUserQuestion di Claude Code). Jika tidak ada, tanyakan lewat chat. Aku boleh memilih lebih dari satu:
- MCP untuk code assistant: extra mcp
- OCR dokumen: extra ocr (Docling, jalan di komputerku, besar) dan atau extra gemini (lewat API Gemini, kecil)
- Evaluasi retrieval dan RAG dengan ragas: extra evaluation
- Vector database: extra milvus dan atau redis
- LLM, embedding, dan LangGraph: extra llm
- Dokumen dan grafik: extra converter (Markdown ke PDF dan PPTX), pdf (membaca PDF), analysis (grafik)
- Computer vision: extra vision dan tracking (gambar, video, pelacakan, tanpa model) dan atau detection (deteksi orang dengan RF-DETR, besar)
- Semuanya: extra all (sangat besar)
- Hanya dasar: perintah zul dan helper kecil, tanpa extra
Jika aku belum tahu, tanyakan apa yang ingin aku kerjakan dengan Zul, lalu usulkan pilihannya. Setelah itu tanyakan hanya yang relevan dengan pilihanku:
- OCR: Docling, Gemini, atau keduanya?
- Evaluasi retrieval: retrievernya Redis atau Milvus, dan apakah aku juga memanggil LLM untuk menjawab? Resepnya extra evaluation ditambah redis atau milvus, dan llm jika ada LLM.
- MCP: untuk code assistant yang mana: Claude Code, Cursor, VS Code, atau Claude Desktop?
- Computer vision: apakah aku butuh model deteksi orang, atau hanya menggambar dan membaca video?
- Tempat pemasangan: environment proyek ini (venv yang sudah ada atau yang baru), atau tool global untuk perintah zul? Pakai uv atau pip?
Jika aku memilih semuanya, sebutkan bahwa ukurannya sekitar 3,8 GB, lalu tanyakan bagian mana yang sebenarnya aku pakai.

Langkah 2. Periksa lingkungan (hanya membaca).
Jalankan python --version (butuh 3.11 atau lebih baru), uv --version, pip --version, dan git --version. Periksa apakah ada venv yang aktif, apakah zul sudah terpasang (zul --version), dan extra apa yang sudah ada. Jangan memasang apa pun di Python sistem tanpa venv.

Langkah 3. Usulkan rencana dan tunggu persetujuanku.
Tampilkan extra yang terpilih, perintah persisnya, dan perkiraan tambahan ruang disk dari daftar di langkah 5. Tanyakan apakah aku setuju sebelum menjalankannya.

Langkah 4. Pasang hanya yang kusetujui.
- pip di venv: pip install "zul[EXTRA1,EXTRA2] @ git+https://github.com/kazuma313/zul_utilities.git"
- uv di proyek yang dikelola uv: uv add "zul[EXTRA1,EXTRA2] @ git+https://github.com/kazuma313/zul_utilities.git"
- perintah zul global untuk MCP: uv tool install "zul[mcp] @ git+https://github.com/kazuma313/zul_utilities.git"
- hanya dasar: tulis zul tanpa kurung siku.
Ganti EXTRA1,EXTRA2 dengan extra yang kupilih, dipisah koma tanpa spasi. Jangan memasang extra yang tidak kupilih. Jika folder ini adalah checkout repository Zul, pakai uv sync --inexact. Jangan menjalankan uv sync tanpa --inexact.

Langkah 5. Periksa setiap extra yang terpasang.
Jalankan satu perintah per extra. Perintah itu mengimpor library extra tersebut dan satu modul Zul yang memakainya, dan harus selesai tanpa keluaran. Perkiraan tambahan ruang disk ada di dalam kurung.
- milvus (55 MB): python -c "import pymilvus, zul.utilities.vector_DB.milvus_helper"
- redis (6 MB): python -c "import redisvl, zul.utilities.vector_DB.redis_helper"
- converter (52 MB): python -c "import markdown, xhtml2pdf, pptx, zul.utilities.md_to_pdf"
- analysis (197 MB): python -c "import matplotlib, pandas, scipy, zul.utilities.analysis"
- pdf (14 MB): python -c "import pypdf, langchain_text_splitters, zul.utilities.script_helper.read_pdf2"
- ocr (3,4 GB): python -c "import docling, zul.utilities.OCR.docling_OCR"
- llm (27 MB): python -c "import langchain_openai, langgraph, zul.utilities.react_graph"
- gemini (23 MB): python -c "import google.genai, zul.utilities.OCR.gemini_ocr"
- vision (118 MB): python -c "import cv2, zul.computer_vision.draw"
- tracking (2 MB): python -c "import lap, zul.computer_vision.tracking"
- detection (3,4 GB): python -c "import rfdetr, zul.computer_vision.detection"
- evaluation (348 MB): python -c "import zul.adapters.ragas, zul.evaluation.judge"
- mcp (33 MB): python -c "import mcp, zul.assistant.server"
Untuk extra all, jalankan semua perintah di atas. Jalankan juga zul --version.

Langkah 6. Jika aku memilih MCP.
Jalankan zul mcp check. Hasilnya harus diawali MCP server zul siap. Lalu daftarkan servernya. Di Claude Code: claude mcp add --scope user zul -- zul mcp serve. Untuk client lain, jalankan zul mcp config NAMA_CLIENT (claude-code, cursor, vscode, atau claude-desktop), tunjukkan hasilnya kepadaku, dan tanyakan dulu sebelum menulis ke file konfigurasi.

Langkah 7. Laporkan.
Tulis apa yang terpasang, perintah yang dijalankan, hasil pemeriksaan, dan yang masih harus kusiapkan sendiri, misalnya API key di environment variable. Jangan membuat atau mengisi file .env sendiri.

Aturan: jangan menjalankan perintah di luar rencana yang kusetujui. Jika ada error, baca pesannya, jelaskan penyebabnya, dan tanyakan sebelum mencoba cara lain. Jangan memasang ulang atau menghapus paket yang sudah ada tanpa bertanya.
```

Ukuran di dalam teks adalah tambahan ruang disk dibanding instalasi dasar, diukur di Windows dengan PyTorch build CUDA 13. Cara menghitungnya ada di [Seberapa besar tiap pilihan](instalasi-zul.md#seberapa-besar-tiap-pilihan).

## Versi satu kalimat

Jika assistant-mu bisa membuka alamat web, kamu tidak perlu menempel seluruh teks. Minta ia membaca halaman ini dalam bentuk teks mentah:

```text
Pasang Zul untukku. Baca bagian "Prompt untuk ditempel" di https://raw.githubusercontent.com/kazuma313/zul_utilities/main/docs/panduan/memasang-zul-dengan-code-assistant.md, ikuti langkahnya, dan tanyakan dulu apa yang aku butuhkan sebelum memasang apa pun.
```

Periksa bahwa assistant benar-benar bertanya sebelum memasang. Versi ini bergantung pada isi alamat itu, jadi baca dulu teksnya jika kamu tidak mengenal sumbernya.

## Menambah extra kemudian

Jika Zul sudah terpasang dengan extra `mcp` dan tersambung ke code assistant, kamu tidak perlu menempel teksnya lagi. Prompt `pasang_zul` dari MCP server Zul memberi assistant instruksi yang sama:

```text
/mcp__zul__pasang_zul "saya butuh OCR dan evaluasi retrieval"
```

Argumennya opsional, dan assistant tetap bertanya untuk memastikan. Di client selain Claude Code, minta assistant memakai prompt MCP `pasang_zul`.

## Yang dikerjakan assistant

| Langkah | Assistant | Perlu persetujuanmu |
|---|---|---|
| 1 | Bertanya apa yang kamu butuhkan, dan pertanyaan lanjutan yang relevan | Kamu menjawab |
| 2 | Memeriksa versi Python, uv, pip, Git, venv, dan instalasi Zul yang sudah ada | Tidak, hanya membaca |
| 3 | Menunjukkan extra, perintah, dan ukuran | Ya |
| 4 | Memasang extra yang kamu setujui | Sudah disetujui di langkah 3 |
| 5 | Memeriksa setiap extra dengan satu perintah impor | Tidak |
| 6 | Menjalankan `zul mcp check` dan mendaftarkan server, jika kamu memilih MCP | Ya, sebelum menulis file konfigurasi |
| 7 | Melaporkan hasilnya | Tidak |

## Halaman terkait

- [Instalasi Zul](instalasi-zul.md) untuk daftar extra, ukuran, dan cara memasang sendiri.
- [Menghubungkan Zul ke code assistant](../tutorial/code-assistant.md) untuk memakai MCP setelah Zul terpasang.
- [MCP server](../referensi/mcp.md) untuk daftar prompt, termasuk `pasang_zul`.
