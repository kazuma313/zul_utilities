# Baseline tech requirement — skills pptx_claude, pptx_research, resaerch_poster, mind_map

Dokumen ini untuk manusia, bukan untuk model. Isinya: berapa besar model yang dibutuhkan, framework apa saja yang bisa dipakai, dan apa syarat minimum mesin yang menjalankan skill.

## Prinsip: dua mesin yang terpisah

Setiap skill di folder ini dibagi dua bagian yang boleh berjalan di komputer berbeda.

**Mesin eksekusi** menjalankan script Python (dan Node untuk pptx_claude). Ia yang mengukur teks, menyusun layout, menggambar SVG, mengisi template dan menulis file. Bagian ini deterministik, tidak butuh GPU, tidak butuh internet, dan tidak pernah melempar exception — hasilnya selalu `{"ok": ...}`.

**Model bahasa** hanya menulis *spec*: satu outline pendek (mind_map) atau satu objek JSON (tiga skill lainnya). Model tidak pernah menulis HTML, CSS, pptxgenjs, python-pptx atau kode gambar apa pun. Konsekuensinya penting untuk dipahami: kualitas visual tidak bergantung pada ukuran model. Model 8B dan model 200B menghasilkan poster yang sama rapinya; yang berbeda adalah kualitas *isi* — pemilihan cabang, ringkasan kalimat, angka yang dipilih untuk disorot.

Karena itu pertanyaan "berapa billion" sebenarnya adalah pertanyaan "seberapa rumit spec yang harus ditulis", dan jawabannya berbeda per skill.

## Baseline mesin eksekusi

| Skill | Wajib | Opsional | Catatan |
|---|---|---|---|
| `mind_map` | Python 3.9+ (stdlib saja) | browser Chromium-family untuk PNG/PDF; `pillow` untuk crop presisi; `pypdf`/poppler untuk sumber PDF; `cairosvg` sebagai pengganti browser | SVG, HTML, MD, MMD, JSON tidak butuh apa pun selain Python |
| `resaerch_poster` | Python 3.9+ (stdlib saja) | — | HTML tidak butuh browser; **PDF dan PNG butuh** Edge / Chrome / Chromium |
| `pptx_research` | Python 3.9+, `python-pptx` (diuji 1.0.2) | — | `assets/template.pptx` 6 MB harus ikut disalin |
| `pptx_claude` | Python 3.9+, Node.js 18+ (diuji v22), `npm install` di folder skill (`pptxgenjs` ^4) | `sharp`, `react-icons` untuk ikon | satu-satunya skill yang butuh Node |
| `youtube_transcript` | Python 3.9+, `youtube-transcript-api` (diuji 1.2.4), akses jaringan ke youtube.com | `yt-dlp` (diuji 2026.8.19) untuk durasi, kategori, tag, dan bab; tanpa itu hanya judul dan channel | Tidak memakai model. YouTube memblokir IP sementara setelah sekitar 30 permintaan dalam beberapa menit; dengan `SUPADATA_API_KEY` (gratis 100 transcript per bulan) skrip beralih ke layanan itu selama blokir |
| `contextual_retrieval` | Python 3.9+ (stdlib saja) | model chat lokal lewat Ollama untuk kalimat konteks; `nomic-embed-text` untuk `--embed`; PyYAML untuk header YAML | `--no-llm` membuat chunk dengan header dari kode saja, tanpa model |

Python diuji pada 3.10 dan 3.11; 3.9 adalah batas bawah dari sintaks yang dipakai. RAM 2 GB cukup, disk sekitar 100 MB per skill termasuk font, template dan `node_modules`. Windows, Linux dan macOS sama saja — deteksi browser sudah mencakup lokasi Edge bawaan Windows, dan `POSTER_BROWSER` dipakai kalau path-nya tidak standar.

Mesin ini **tidak perlu GPU sama sekali**. Pola yang masuk akal untuk PC-mu: model berjalan di GPU lewat Ollama, script berjalan di CPU yang sama atau di server lain, berkomunikasi lewat HTTP.

## Baseline model

Angka token di bawah ini diukur dari file yang ada di repo ini (1 token ≈ 3,6 karakter untuk teks campuran Indonesia–Inggris).

| Skill | Yang ditulis model | Output | Prompt sistem | Minimum realistis | Nyaman | Tanpa model |
|---|---|---|---|---|---|---|
| `mind_map` | outline berindentasi | 200–400 tok | ~1.750 tok | **3–4B** (topik), 7–8B (artikel) | 8B | ya — `--no-llm` |
| `pptx_research` | JSON slide, urutan diatur script | ~1.800 tok | ~2.050 tok | **7–8B** | 14B | tidak |
| `pptx_claude` | JSON slide, 20 layout dipilih sendiri | 600–1.800 tok | ~1.800 tok | **7–8B** | 14B | tidak |
| `resaerch_poster` | JSON section + angka + chart | ~1.000 tok | ~2.350 tok | **8B** (pakai JSON Schema) | 14B+ | tidak |

Urutan kesulitan itu bukan tebakan kasar: mind_map paling ringan karena outline berindentasi adalah format terstruktur paling sederhana yang ada dan parser-nya memperbaiki hampir semua kesalahan bentuk; poster paling berat karena model harus memilih tipe section, memasukkan angka yang konsisten dengan teks, dan menjaga panjang tiap field.

**Qwen3 8B (Q4_K_M) adalah titik aman untuk keempat skill.** Itu yang dijadikan target saat prompt dan schema ditulis. Di bawah itu: 4B masih baik untuk mind_map dan bisa dipakai untuk pptx sederhana dengan schema, tetapi sering menulis kalimat penuh alih-alih frasa. Di bawah 3B tidak direkomendasikan untuk skill JSON — bukan karena file gagal dibuat (normalizer akan memperbaikinya), tetapi karena isinya jadi generik.

Anggaran memori untuk model, kuantisasi Q4_K_M, plus context:

| Ukuran | VRAM | Kecepatan wajar | Cocok untuk |
|---|---|---|---|
| 3–4B | ~3 GB | 30–60 tok/s GPU, 8–15 tok/s CPU | mind_map, draft |
| 7–8B | ~6 GB | 25–45 tok/s GPU | semua skill (baseline) |
| 12–14B | ~9–10 GB | 15–30 tok/s GPU | poster dan deck panjang |
| 24–32B | ~16–20 GB | 8–20 tok/s GPU | kalau VRAM tersedia |

Kuantisasi: Q4_K_M cukup untuk mind_map; untuk skill berbasis JSON, Q5_K_M atau Q6 terasa lebih stabil pada nama field dan tanda kutip, terutama tanpa constrained decoding. Jangan turun ke Q3 untuk skill JSON.

Context window: minimum 8k, **16k yang direkomendasikan** (itu default `--num-ctx` di runner). Hitungannya sederhana — prompt sistem 2k + materi sumber sampai 12.000 karakter ≈ 3,3k + draft + output. Kalau memakai model reasoning dengan thinking aktif, siapkan 32k karena blok `<think>` bisa dua sampai tiga kali panjang jawabannya; kalau context terbatas, matikan thinking (`--think off`) dan naikkan `--max-tokens` saja.

Keluarga model yang wajar dicoba selain Qwen3: Llama 3.1 8B, Gemma 3 12B, Phi-4 14B, Mistral Small 3 24B, dan MoE seperti Qwen3 30B-A3B kalau RAM besar tetapi GPU kecil. Yang penting bukan mereknya, tetapi tiga hal: mengikuti instruksi format, mendukung structured output, dan menulis bahasa Indonesia yang wajar kalau materinya berbahasa Indonesia.

## Framework yang bisa dipakai

**Penyedia model.** Semua runner (`generate_deck.py`, `generate_poster.py`, `generate_mindmap.py`) hanya bicara dua dialek HTTP, jadi praktis semua server lokal bisa dipakai.

| Runtime | Cara memanggil | Structured output |
|---|---|---|
| Ollama | default; model dipilih otomatis (lihat *Model bawaan per skill*) | `format: <schema>` — pakai `--think auto` karena `think=false` merusak `format` di sebagian versi |
| LM Studio | `--api openai --base-url http://localhost:1234/v1` | `response_format: json_schema` |
| llama.cpp server | `--api openai --base-url http://localhost:8080/v1` | json_schema / GBNF grammar |
| vLLM | `--api openai --base-url http://host:8000/v1` | guided JSON; pilihan terbaik untuk banyak pengguna sekaligus |
| TGI, Jan, KoboldCpp, text-generation-webui, LiteLLM proxy, OpenRouter, API cloud | sama, `--api openai --base-url ...` | tergantung server |

Schema tanpa `$ref` sudah disediakan di `assets/*.schema.json` supaya bisa dipakai langsung oleh Ollama maupun endpoint OpenAI-compatible.

**Orkestrasi agent.** Setiap skill menyediakan satu tool LangChain opsional: `create_mind_map`, `create_research_poster`, `create_research_pptx`, `create_pptx_js`. Yang dibutuhkan hanya `langchain-core` (≥ 0.3), bukan seluruh LangChain, sehingga bisa dipasang di LangGraph, `deepagents`, atau dipakai sebagai fungsi Python biasa.

Karena intinya cuma fungsi `(str) -> str`, framework lain juga jalan tanpa perubahan: CrewAI, AutoGen, Semantic Kernel, atau loop function-calling buatan sendiri tinggal memanggil `build_mindmap()` / `build_poster()` / `build_deck()`. Untuk layanan, bungkus dengan FastAPI dan kembalikan URL file — `UPLOAD_HOOK` dan `PPTX_PUBLIC_URL` memang disiapkan untuk itu (MinIO, S3, folder statis). Untuk n8n atau Zapier, panggil endpoint FastAPI tadi. Untuk MCP, bungkus fungsi yang sama sebagai satu tool server.

Tanpa framework apa pun juga sah: `python scripts/build_mindmap.py map.md -o map.png` di terminal, atau lewat cron.

## Tiga tingkat setup

**Minimum yang benar-benar jalan.** Python 3.9, tanpa GPU, tanpa model. Untuk mind_map pakai `--no-llm` (outline dibuat dengan aturan) lalu edit file `.md`-nya; untuk tiga skill lain, tulis JSON-nya sendiri atau minta model cloud menuliskannya lalu jalankan script secara lokal. Output: SVG dan HTML untuk mind_map dan poster, .pptx untuk kedua skill deck. Ini yang saya sarankan sebagai *bare minimum* kalau modelmu di bawah 4B.

**Setup yang disarankan untuk PC-mu.** Qwen3 8B Q4_K_M di Ollama, context 16k, thinking dimatikan untuk kecepatan, GPU 6–8 GB, plus Edge yang sudah ada di Windows untuk PNG/PDF. Node 22 sudah terpasang, jadi pptx_claude tinggal `npm install`. Ini menjalankan keempat skill end-to-end.

**Kalau mau hasil isi yang lebih baik.** Model 14B (atau 30B-A3B) dengan context 32k dan structured output aktif, khusus untuk poster dan deck panjang. Sisanya tidak berubah — mesin eksekusinya identik.

## Apa yang rusak lebih dulu saat model terlalu kecil

Urutannya cukup konsisten, dan berguna untuk mendiagnosis: pertama model menulis kalimat penuh alih-alih frasa (map jadi berat, warning `text too long -> note`); lalu cabang tidak seimbang, satu cabang enam anak, sisanya satu; lalu ia mengabaikan batas jumlah (`9 branches -> 8` muncul di warning); lalu untuk skill JSON, nama field salah (diperbaiki normalizer, tetapi muncul di `AUTO-FIXED`); baru paling akhir JSON-nya benar-benar rusak — dan itu pun biasanya karena terpotong `--max-tokens`, bukan karena modelnya kecil.

Artinya: warning yang keluar di terminal adalah alat ukur yang cukup baik. Kalau `AUTO-FIXED` selalu kosong, ukuran modelmu sudah memadai. Kalau isinya panjang di setiap run, naikkan satu tingkat ukuran model atau perketat prompt (`--depth 2`, minta maksimal 6 kata per baris).

## Hasil uji langsung dengan model lokal (3 Oktober 2026)

Bagian di atas ditulis sebelum skill dicoba dengan model sungguhan. Bagian ini berisi hasil pengukurannya: Ollama 0.32.6, Ryzen 7 5800HS, RAM 23 GB, RTX 3060 Laptop 6 GB. Untuk mengulanginya dengan model lain, jalankan `python evals/small_model_check.py NAMA_MODEL` dari folder ini.

| Yang diuji | `gemma3:4b` | `qwen3:4b` | `qwen3:8b` |
|---|---|---|---|
| Memilih skill yang tepat dari 11 deskripsi | 11 dari 11, 3 detik per permintaan | 11 dari 11, 10-19 detik | 11 dari 11, 5-6 detik |
| Memanggil tool (`math_calculator`, `create_docx`, `create_mind_map`, `web_search`, `view_image`, `dispatch_research_subagents`, `generate_chart`, `create_xlsx`) | 8 dari 8, 3-8 detik | 7 dari 8 (`create_docx` gagal sebelum pembaca JSON diperbaiki), 11-457 detik | 6 dari 6 (dua terakhir belum diuji), 12-117 detik |
| `pptx_research` lewat `generate_deck.py` | berhasil, 9-12 detik | berhasil, 302 detik | berhasil, 275 detik |
| `resaerch_poster` lewat `generate_poster.py` | berhasil, 16-17 detik | berhasil, 594 detik | berhasil, 159 detik |
| `pptx_claude` lewat `generate_deck.py` | berhasil, 9 detik | berhasil, 611 detik | lihat perbandingan di bawah |
| `mind_map` lewat `generate_mindmap.py` | 16 dari 16, 8-98 detik | topik berhasil, 159-224 detik | berhasil, 87-389 detik |

Kolom `qwen3:8b` diukur saat GPU NVIDIA sedang tidak aktif, jadi model berjalan di CPU (sekitar 4 token per detik). Waktunya tidak bisa dibandingkan dengan dua kolom lain, yang diukur di GPU.

`chart`, `xlsx`, dan `pptx_claude` baru bisa diuji setelah `seaborn` dipasang di environment ini dan `npm install pptxgenjs` dijalankan di folder `pptx_claude`.

Lima hal yang ternyata menentukan, dan tidak ada di perkiraan awal:

1. **`gemma3:4b` adalah pilihan tercepat untuk semua skill yang diuji.** Model ini muat seluruhnya di GPU 6 GB (2,9 GB) dan tidak punya mode berpikir, jadi satu slide deck selesai dalam 12 detik. Angka "7-8B minimum" di tabel atas terlalu hati-hati untuk skill yang spec-nya diperbaiki script.
2. **`gemma3` tidak punya tool calling di Ollama.** Server menolak permintaan yang membawa tool. Jalan keluarnya: kirim skema argumen tool sebagai `format`, lalu model menjawab dengan satu objek JSON yang bentuknya dijaga server. Dengan cara itu `gemma3:4b` memanggil keenam tool dengan benar. Agent yang memakai model ini harus memanggil tool dengan cara tersebut, bukan lewat `bind_tools`.
3. **`qwen3:4b` menalar dulu setiap kali menjawab teks bebas.** Dengan `think=false`, penalarannya masuk ke jawaban ("Okay, let's see. The user wants ...") dan uji teks bebas gagal. Dengan penalaran menyala uji-uji itu berhasil, tetapi jauh lebih lambat dari `gemma3:4b`. `small_model_check.py` dan `generate_mindmap.py` mendeteksi hal ini sendiri. Jawaban berupa JSON berskema adalah pengecualian: lihat temuan 7 di bagian perbandingan.
4. **Argumen berupa JSON di dalam string mudah rusak.** `qwen3:4b` dan `qwen3:8b` masing-masing sekali menulis JSON `create_docx` dengan tanda kutip nyasar di akhir. `docx`, `xlsx`, dan `chart` sekarang membaca JSON itu dengan `_loads_lenient`, yang mengambil nilai JSON pertama yang utuh.
5. **Empat skill ber-`scripts/` saling menimpa modul.** `mind_map`, `pptx_research`, `pptx_claude`, dan `resaerch_poster` sama-sama punya `langchain_tool.py`, `font_metrics.py`, atau `spec_normalizer.py`. Dimuat dalam satu proses, skill kedua mengimpor modul milik skill pertama: `pptx_research` gagal diimpor, dan tool `resaerch_poster` diam-diam menjadi `None`. File `*_skill.py` keempat skill sekarang memuat script-nya secara terpisah, dan keempat tool muncul bersamaan.

Untuk server Ollama di laptop dengan dua GPU: secara bawaan Ollama memilih GPU terintegrasi (lewat Vulkan), sekitar 6 token per detik untuk model 8B. Jalankan dengan `OLLAMA_VULKAN=0` supaya GPU NVIDIA yang dipakai, lalu periksa kolom `PROCESSOR` di `ollama ps`.

## Perbandingan isi hasil: 4B, 8B, dan Claude (3 Oktober 2026)

Tabel di atas hanya mencatat apakah file jadi. Uji ini membandingkan isinya. `python evals/compare_models.py gemma3:4b qwen3:4b qwen3:8b` memberi tiap model materi dan permintaan yang sama untuk 12 kasus, lalu menulis `evals/comparison/index.html`: hasil tiap skill berdampingan, dengan argumen atau spec yang ditulis model. Kolom terakhir dibangun dari spec yang ditulis Claude (`evals/comparison/claude/`) dengan script yang sama. Catatan per kasus ada di `evals/comparison/notes.json`.

| Kasus | `gemma3:4b` | `qwen3:4b` | `qwen3:8b` | Claude |
|---|---|---|---|---|
| Mind map dari dokumen | angka lengkap, satu butir salah cabang | angka benar, satu temuan tidak masuk | ringkas, rincian 54/31/15 hilang | lengkap |
| `create_mind_map` | isi benar, nama file tidak diisi | benar, 16 menit | benar, beberapa baris terlalu panjang | benar |
| Poster | angka benar, bagian Rekomendasi tidak ditulis | 8 bagian, angka benar | 8 bagian, angka benar | 7 bagian, angka benar |
| Slide `pptx_claude` | 6 slide, satu angka salah pasang | 7 slide, angka benar | 8 slide, angka benar | 8 slide, angka benar |
| Slide `pptx_research` | 9 slide, satu grafik dibuang karena angkanya karangan | 10 slide, dua grafik berlabel salah | 10 slide, satu kalimat salah pasang angka | 10 slide |
| `create_docx` | menulis Markdown; jadi setelah tool diperbaiki | benar pada percobaan pertama, 14 menit | JSON kurang satu kurung; jadi setelah tool diperbaiki | benar |
| `create_xlsx` | baris tanpa kunci; jadi setelah tool diperbaiki, isi lemah | satu sheet hilang; lengkap setelah tool diperbaiki | benar, satu judul kolom salah | benar |
| `generate_chart` | benar, tanpa judul | benar, label sumbu berbahasa Inggris | benar | benar |
| Kalkulator, web search, gambar, subagent | benar | benar, 3-6 menit per panggilan | benar | benar |

Poster dan slide deck model lokal di tabel ini adalah hasil setelah perbaikan di bawah. Waktu di halaman perbandingan tidak bisa dibandingkan dengan tabel waktu di atas: `gemma3:4b` dan `qwen3:8b` diukur saat GPU dipakai bersama aplikasi lain, dan `qwen3:4b` diukur di GPU terintegrasi.

Kesalahan yang baru terlihat setelah isinya dibaca, dan perbaikannya:

1. **Model kecil menyalin contoh di prompt.** Radar chart berisi 5, 7, 3 muncul di proposal `gemma3:4b` dan `qwen3:8b` karena angka itu ada di contoh prompt. Angka contoh di ketiga prompt lite sekarang berupa `<number>`, dan `generate_*.py` membuang grafik yang angkanya tidak ada di materi sumber (`from_source`).
2. **Field yang wajib diisi dengan karangan.** Penyaji "Dr. Andi Rahman", email, dan situs yang tidak pernah diberikan. Prompt sekarang melarangnya, dan `drop_invented` serta `drop_invented_contacts` mengosongkan nama dan kontak yang tidak ada di teks pengguna.
3. **Model berhenti di batas bawah skema.** Diminta 8 slide, `gemma3:4b` menulis 3, karena `minItems` skema adalah 3. Batas bawah sekarang mengikuti `--slides`, dan slide pengisi setelah kesimpulan dipotong.
4. **Argumen tool tidak selalu berbentuk JSON yang diminta.** `create_docx` sekarang membaca dokumen yang ditulis sebagai Markdown, `create_xlsx` membaca baris `{"harga", "54"}`, dan ketiga pembaca JSON menutup kurung yang tertinggal.
5. **Skill sendiri merusak angka yang benar.** Poster memotong "Rp 310.000" menjadi "Rp 310.00", dan donat menghitung ulang 54 dan 31 menjadi 63,5% dan 36,5% ketika satu kategori tidak ditulis. Nilai sekarang dipotong per kata, dan sisa persen ditambahkan sebagai "Lainnya".
6. **Judul bahasa Inggris dari contoh prompt** ("Research Overview", "Age range") diterjemahkan oleh `build_poster.py` untuk poster berbahasa Indonesia, dan oleh `pptx_research/scripts/generate_deck.py` untuk proposal. "Language: the same language as the topic" terlalu samar untuk model kecil: `qwen3:4b` menulis seluruh slide dalam bahasa Inggris. Untuk topik berbahasa Indonesia, ketiga `generate_*.py` sekarang menyebut bahasanya.
7. **Penalaran menghabiskan jatah jawaban.** Dengan penalaran menyala, `qwen3:4b` menyusun seluruh slide di dalam penalarannya (sampai menghitung huruf judul), memakai habis 8.192 token, dan mengembalikan jawaban kosong: dua kali, 61 menit, gagal. Karena server hanya mengizinkan JSON yang sesuai skema, penalaran tidak dibutuhkan: `--think auto` sekarang meminta tanpa penalaran lebih dulu, dan `generate_mindmap.py` meminta outline sebagai JSON berskema untuk model yang terdeteksi hanya bisa menjawab setelah menalar. Hasilnya: proposal 225 detik, slide 100 detik, poster 176 detik, mind map dari dokumen 72 detik.
8. **JSON yang ditutup terlalu cepat kehilangan data tanpa pesan.** `qwen3:4b` menulis `{"Alasan":[...]}"Tren":[...]}`; pembaca JSON mengambil objek pertama, dan sheet kedua hilang. `create_xlsx` sekarang menyambung kembali kedua sheet.

Yang tidak bisa diperbaiki script: angka yang benar tetapi dipasangkan salah. Kedua model lokal pernah menulis "paylater naik dari 12%", padahal 12% adalah angka live streaming. Untuk hasil yang dipakai orang lain, periksa angkanya terhadap sumber, atau pakai model yang lebih besar.

Setelah memperbaiki skill, `python evals/compare_models.py NAMA_MODEL --replay` membangun ulang dari jawaban yang sudah disimpan tanpa memanggil model. Uji perbaikannya ada di `evals/test_small_model_repairs.py`.

## Model bawaan per skill

Skrip yang memanggil model lokal memilih modelnya sendiri, jadi `--model` tidak perlu ditulis. Tiap skrip memakai model pertama dari daftarnya yang sudah ada di server, dan mencetak model yang dipakai. Urutannya diambil dari perbandingan isi di atas.

| Skill | Urutan pilihan | Alasan |
|---|---|---|
| `mind_map` (`generate_mindmap.py`) | `gemma3:4b`, `qwen3:8b`, `qwen3:4b` | `gemma3:4b` menggambar 16 dari 16 peta uji dan menjaga rincian dokumen; `qwen3:8b` menghilangkan rincian. |
| `pptx_claude`, `pptx_research` (`generate_deck.py`) | `qwen3:8b`, `gemma3:4b`, `qwen3:4b` | `qwen3:8b` menulis slide paling lengkap dengan angka benar; `gemma3:4b` beberapa kali lebih cepat dan muat di GPU yang lebih kecil. |
| `resaerch_poster` (`generate_poster.py`) | `qwen3:8b`, `gemma3:4b`, `qwen3:4b` | Sama dengan slide. |

Jika tidak ada satu pun model di daftar, skrip memakai model chat pertama yang terpasang. `--model NAMA_MODEL` memilih model untuk satu perintah, dan variabel lingkungan `SKILL_MODEL` memilih satu model untuk semua skill.

Skill lain tidak memanggil model sendiri; modelnya ditentukan aplikasi agent yang memakainya:

| Kebutuhan agent | Model yang disarankan | Catatan |
|---|---|---|
| Memilih skill dan memanggil tool (`docx`, `xlsx`, `chart`, `calculator`, `web_search`, `subagent_research`, `youtube_transcript`, `crypto_snapshot`) | `qwen3:8b` | Tool calling bawaan jalan dengan penalaran mati. `gemma3:4b` juga bisa, tetapi lewat JSON berskema karena Ollama tidak memberinya tool calling. |
| Membaca gambar (`image`) | `gemma3:4b` | Model teks seperti `qwen3` tidak bisa membaca gambar. Isi `VISION_MODEL_ID`; tanpa itu tool memakai `GENERAL_MODEL_ID`. |

`youtube_transcript` dan `crypto_snapshot` tidak butuh model sama sekali. Skrip dan fungsi Python-nya bisa dipakai langsung dari terminal atau kode; model hanya dibutuhkan jika keduanya dipakai sebagai tool di agent.

## Ringkasnya

Mesin: Python 3.9+ untuk semuanya, tambah `python-pptx` untuk satu skill, Node 18+ untuk satu skill lagi, browser Chromium-family untuk PNG/PDF. Tidak ada GPU yang dibutuhkan di sisi ini.

Model: menurut hasil uji di atas, `gemma3:4b` sudah menjalankan `mind_map`, `pptx_research`, `resaerch_poster`, pemilihan skill, dan pemanggilan tool, asalkan tool dipanggil lewat JSON berskema. Di perbandingan isi, `qwen3:8b` lebih lengkap dan lebih jarang salah daripada `gemma3:4b`; `qwen3:4b` menulis argumen tool lebih rapi daripada `gemma3:4b` tetapi butuh 3 sampai 16 menit per panggilan karena menalar, dan ketiganya masih bisa memasangkan angka dengan hal yang salah, jadi angka di hasil model lokal perlu dicek terhadap sumbernya. 8B tetap pilihan jika agent-mu bergantung pada tool calling bawaan model. 14B kalau mau isi poster lebih tajam, dan 0B tetap menghasilkan file lewat jalur `--no-llm` atau JSON yang ditulis tangan.

Framework: apa pun yang bisa bicara HTTP ala Ollama atau ala OpenAI untuk sisi model, dan apa pun yang bisa memanggil fungsi Python untuk sisi orkestrasi.
