# Konsep

Cara kerja setiap bagian Zul dan alasan di balik rancangannya.

| Halaman | Pertanyaan yang dijawab |
|---|---|
| [Arsitektur hexagonal](arsitektur-hexagonal.md) | Kenapa proyek dibagi menjadi domain, application, infrastructure, dan interface, dan ke mana arah dependensinya? |
| [Perjalanan sebuah request](alur-request.md) | Apa yang terjadi sejak request HTTP masuk sampai jawaban agent keluar, dan di mana komponennya dirakit? |
| [Cara kerja agent ReAct](agent-react.md) | Bagaimana putaran model dan tool berjalan, dan bagaimana agent berhenti sebelum kehabisan langkah? |
| [Cara kerja human-in-the-loop](human-in-the-loop.md) | Bagaimana agent berhenti menunggu keputusan lalu dilanjutkan, dan aturan apa yang muncul dari cara kerja itu? |
| [Cara kerja subagents](subagents.md) | Bagaimana supervisor mendelegasikan pekerjaan, dan kapan pola ini cocok? |
| [Memory dan thread](memory.md) | Apa yang disimpan checkpointer, dan apa arti `thread_id`? |
| [Menguji tanpa LLM asli](pengujian.md) | Apa yang dibuktikan test dengan model palsu, dan apa yang tetap harus diuji dengan model sungguhan? |
| [Cara situs dokumentasi diterbitkan](penerbitan-dokumentasi.md) | Kenapa workflow penerbitan mengunci semua versi dan memeriksa hasilnya berlapis, dan apa yang tetap tidak dijamin? |
| [Model lokal untuk skill belajar](model-lokal-untuk-skill-belajar.md) | Model Ollama mana yang paling cocok untuk skill silabus dan materi belajar, dan kesalahan apa yang tidak tertangkap oleh kode? |
| [Cara kerja Computer Vision](cara-kerja-computer-vision.md) | Kenapa satu orang diwakili satu titik, kenapa garis menunggu beberapa frame, dan kenapa grace berbeda dari batas kredit? |
| [Lapisan adapter](lapisan-adapter.md) | Kenapa Zul hanya memakai library pihak ketiga lewat `zul/adapters`, dan library mana yang tetap dipakai langsung? |
| [Hexagonal dari nol](../hexagonal.md) | Seperti apa arsitektur hexagonal dijelaskan dari awal, dengan contoh aplikasi toko online? |

## Halaman terkait

- [Panduan](../panduan/index.md) untuk langkah mengerjakan sebuah tugas.
- [Referensi](../referensi/index.md) untuk parameter dan bentuk data.
