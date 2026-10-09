# Panduan

Setiap panduan berisi langkah untuk menyelesaikan satu tugas dengan Zul.

## Memulai

| Tugas | Panduan |
|---|---|
| Instalasi perintah `zul` dan library-nya | [Instalasi Zul](instalasi-zul.md) |
| Membuat proyek dari template | [Membuat proyek baru](membuat-proyek.md) |
| Mengisi API key, mengganti model, memakai endpoint sendiri | [Mengatur model dan API key](mengatur-llm.md) |
| Menjalankan server untuk pengembangan atau di container | [Menjalankan aplikasi](menjalankan-aplikasi.md) |

## Agent

| Tugas | Panduan |
|---|---|
| Memberi agent kemampuan baru | [Menambah tool](menambah-tool.md) |
| Mengubah peran dan gaya agent | [Mengubah system prompt](mengubah-system-prompt.md) |
| Menyisipkan langkah di graph agent | [Menambah node ke graph](menambah-node.md) |
| Membatasi berapa lama agent boleh bekerja | [Mengatur batas langkah](mengatur-batas-langkah.md) |
| Membuat percakapan bertahan setelah server berhenti | [Menyimpan percakapan di database](menyimpan-percakapan.md) |
| Membuat agent menunggu persetujuan sebelum sebuah aksi | [Mewajibkan persetujuan untuk sebuah tool](mewajibkan-persetujuan.md) |
| Menambah spesialis ke supervisor | [Menambah subagent](menambah-subagent.md) |
| Menyediakan fitur baru lewat REST API | [Menambah endpoint](menambah-endpoint.md) |
| Mencoba agent yang sedang kamu buat | [Mencoba fitur di playground](mencoba-di-playground.md) |
| Menulis test tanpa memanggil LLM asli | [Menguji agent](menguji-agent.md) |

## Utilities

Alat bantu yang kamu panggil langsung dari kode atau terminal: helper dari paket `zul`, dan script di `research/agentic/algorithms/utilities/` yang bekerja tanpa model AI.

| Tugas | Panduan |
|---|---|
| Menyimpan dan mencari vektor di Milvus | [Milvus](memakai-milvus.md) |
| Menyimpan dan mencari vektor di Redis | [Redis](memakai-redis.md) |
| Mengubah PDF atau gambar menjadi teks | [OCR](membaca-dokumen-ocr.md) |
| Memanggil LLM dan model embedding dengan konfigurasi tervalidasi | [LLM dan embedding](memanggil-llm-dan-embedding.md) |
| Mengubah Markdown menjadi PDF atau PPTX | [Markdown ke PDF dan PPTX](mengonversi-markdown.md) |
| Membandingkan hasil pengukuran dalam grafik | [Grafik perbandingan](membuat-grafik.md) |
| Memakai logger, pengukur waktu, dan helper lain | [Helper kecil](memakai-helper.md) |
| Mengambil transcript dan metadata video YouTube, tanpa model AI | [Mengambil transcript YouTube](mengambil-transcript-youtube.md) |
| Mengambil harga token crypto beserta EMA, Stochastic, dan volume, tanpa model AI | [Mengambil snapshot harga crypto](mengambil-snapshot-crypto.md) |
| Menggambar candlestick chart token crypto beserta indikatornya, tanpa model AI | [Membuat candlestick chart crypto](membuat-chart-crypto.md) |

## Skill

Kemampuan yang di dalamnya ada model AI yang bekerja, dengan model lokal lewat Ollama atau model lain. Kodenya ada di `research/agentic/algorithms/skills/`.

| Tugas | Panduan |
|---|---|
| Mengubah topik, catatan, atau dokumen menjadi mind map, juga dengan model lokal | [Membuat mind map](membuat-mindmap.md) |
| Membuat silabus dan materi belajar dari topik, PDF, gambar, atau dokumen, dengan model lokal | [Membuat silabus dan materi belajar](membuat-silabus-dan-materi.md) |
| Memotong dokumen menjadi chunk berkonteks untuk vector database, dengan model lokal | [Menyiapkan dokumen untuk RAG](menyiapkan-dokumen-untuk-rag.md) |

## Computer Vision

Fungsi-fungsi kecil di `zul.computer_vision` untuk video, yang kamu rangkai sendiri sesuai kebutuhan.

| Tugas | Panduan |
|---|---|
| Mendeteksi orang di video dan memberi id yang sama di setiap frame | [Mendeteksi dan melacak orang](mendeteksi-dan-melacak-orang.md) |
| Menulis teks di sudut frame, menggambar kotak, bentuk, kerangka, jejak gerak, dan heatmap | [Menggambar di frame](menggambar-di-frame.md) |
| Menghitung orang yang melintasi garis, dan orang di dalam poligon | [Menghitung dengan garis dan poligon](menghitung-dengan-garis-dan-poligon.md) |
| Mengukur lama setiap orang di zona, atau lama sebuah kondisi benar | [Mengukur durasi per orang](mengukur-durasi.md) |
| Membaca ke mana orang menghadap, dan jarak antar orang dalam meter | [Membaca arah hadap dan jarak](membaca-arah-hadap-dan-jarak.md) |
| Menghitamkan area sebelum deteksi, atau mengaburkan wajah dan badan | [Menghitamkan dan menyamarkan area](menghitamkan-dan-menyamarkan-area.md) |

## Proyek Zul

| Tugas | Panduan |
|---|---|
| Menerbitkan situs dokumentasi dan menyambungkan playground-nya | [Menerbitkan dokumentasi](menerbitkan-dokumentasi.md) |
| Menambah tulisan bertanggal ke blog, beserta gambar dan file-nya | [Menulis tulisan blog](menulis-blog.md) |
| Mengubah Zul sendiri: kode, test, atau dokumentasi | [Berkontribusi](berkontribusi.md) |
| Mengubah perilaku OpenCV, RF-DETR, atau library lain untuk kebutuhan proyek | [Mengubah perilaku library pihak ketiga](mengubah-perilaku-library.md) |
