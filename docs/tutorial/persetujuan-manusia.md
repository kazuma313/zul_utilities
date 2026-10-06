# Meminta persetujuan manusia

Di tutorial ini kita memakai agent yang berhenti sebelum mengirim email dan menunggu keputusan kita. Kita mencoba ketiga keputusan yang tersedia, lalu mewajibkan persetujuan untuk tool lain.

Di akhir tutorial kamu tahu cara membuat agent yang tidak menjalankan aksi berisiko tanpa dilihat manusia.

**Sebelum mulai:** selesaikan [Membuat agent pertamamu](agent-pertama.md). Server dari tutorial itu harus masih berjalan.

## Melihat agent berhenti

Proyekmu sudah membawa agent kedua, yang punya dua tool: `get_weather` dan `send_email`. Tool `send_email` ditandai butuh persetujuan.

Panel di bawah ini memakai agent itu. Tombol status di bilah panel harus bertuliskan **Terhubung**. Jika tertulis **Simulasi**, panel belum terhubung ke proyekmu dan hanya menampilkan contoh jawaban. Klik tombol itu, lalu klik **Sambungkan**.

<div class="zul-playground" data-feature="Human-in-the-loop">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

Klik contoh pesan **Kirim email ke alice@example.com: rapat besok jam 10**.

Kali ini agent tidak menjawab. Panel menampilkan tulisan "Agent berhenti dan menunggu keputusanmu", diikuti form berjudul **Aksi 1: send_email**. Di form itu terlihat argumen yang disusun model: alamat tujuan, subjek, dan isi email.

Lihat jejak di atas form. Hanya ada satu langkah: `llm_call` meminta tool `send_email`. Tool-nya belum dijalankan, jadi belum ada email yang terkirim.

## Menyetujui aksi

Di form, biarkan pilihan **Setujui**, lalu klik **Kirim keputusan**.

Agent melanjutkan dan menjawab bahwa email sudah dikirim. Lihat jejak **3 langkah** yang baru:

1. `human_review` meneruskan permintaan tool `send_email` dengan argumen yang sama.
2. `tool_node` menjalankan tool dan mencatat hasilnya, yaitu teks yang diawali `Email sent to alice@example.com`.
3. `llm_call` membaca hasil itu, lalu menjawab.

Tool `send_email` di template belum mengirim email sungguhan. Ia hanya mencatat pemanggilannya ke log, jadi kamu aman mencobanya berkali-kali.

## Menolak aksi

Klik **Percakapan baru**, lalu klik contoh pesan yang sama. Agent berhenti lagi.

Kali ini pilih **Tolak**. Di kotak **Alasan penolakan**, tulis:

```text
Alamatnya salah. Tanyakan alamat yang benar ke user.
```

Klik **Kirim keputusan**. Agent menjawab bahwa email tidak dikirim dan menanyakan alamat yang benar.

Lihat jejaknya. Di langkah `human_review` ada baris merah bertuliskan "tool gagal atau ditolak", dan isinya adalah alasan yang kamu tulis. Tidak ada langkah `tool_node`: tool-nya tidak pernah dijalankan. Model membaca alasanmu sebagai hasil tool, sehingga ia bisa menjelaskannya ke user.

## Mengubah aksi sebelum dijalankan

Klik **Percakapan baru**, lalu klik contoh pesan sekali lagi.

Pilih **Ubah**. Kotak **Argumen** sekarang bisa disunting. Ganti nilai `subject` dengan teks lain, misalnya:

```json
{
  "to": "alice@example.com",
  "subject": "Rapat diundur",
  "body": "Rapat besok jam 10."
}
```

Nilai `to` dan `body` milikmu mengikuti yang ditulis model, jadi cukup ubah `subject`-nya. Klik **Kirim keputusan**.

Lihat jejaknya. Langkah `human_review` menampilkan argumen yang sudah kamu ubah, dan hasil di `tool_node` memuat subjek baru itu. Tool dijalankan dengan argumen darimu, bukan dari model.

## Mewajibkan persetujuan untuk tool lain

Tool `get_weather` sekarang berjalan tanpa persetujuan. Kita ubah supaya ia juga butuh persetujuan.

Buka `src/interface/http/controllers/hitl_controller.py` dan cari baris berikut:

```python title="src/interface/http/controllers/hitl_controller.py"
TOOLS_REQUIRING_APPROVAL = {send_email.name}
```

Tambahkan nama tool cuaca ke himpunan itu:

```python title="src/interface/http/controllers/hitl_controller.py"
TOOLS_REQUIRING_APPROVAL = {send_email.name, get_weather.name}
```

Simpan file. Server memulai ulang sendiri.

Kembali ke panel, klik **Percakapan baru**, lalu kirim:

```text
What is the weather in sf?
```

Agent berhenti, dan form menampilkan **Aksi 1: get_weather**. Setujui, lalu agent menjawab seperti biasa.

Sebelum lanjut, kembalikan baris tadi ke bentuk semula, karena tool yang hanya membaca data tidak perlu disetujui:

```python title="src/interface/http/controllers/hitl_controller.py"
TOOLS_REQUIRING_APPROVAL = {send_email.name}
```

## Yang sudah kamu kerjakan

Kamu sudah:

- Melihat agent berhenti sebelum menjalankan tool yang butuh persetujuan.
- Menyetujui, menolak, dan mengubah sebuah aksi, lalu melihat akibat tiap keputusan di langkah agent.
- Menentukan tool mana yang butuh persetujuan lewat `TOOLS_REQUIRING_APPROVAL`.

Lanjutkan ke [Membangun tim agent](tim-agent.md).

Jika kamu ingin tahu lebih dalam:

- [Cara kerja human-in-the-loop](../konsep/human-in-the-loop.md) menjelaskan bagaimana agent bisa berhenti dan dilanjutkan.
- [Mewajibkan persetujuan untuk sebuah tool](../panduan/mewajibkan-persetujuan.md) memuat langkah untuk tool buatanmu sendiri dan cara memanggilnya lewat API.
- [Format review](../referensi/format-review.md) mencantumkan bentuk setiap keputusan.
