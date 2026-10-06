# Mewajibkan persetujuan untuk sebuah tool

Halaman ini menunjukkan cara membuat agent berhenti dan menunggu keputusan manusia sebelum menjalankan sebuah tool. Lakukan ini untuk tool yang efeknya tidak bisa dibatalkan: mengirim email, menghapus data, melakukan pembayaran.

**Sebelum mulai:** tool-nya sudah ditulis. Lihat [Menambah tool](menambah-tool.md). Contoh di halaman ini memakai tool bernama `delete_order`.

## Langkah-langkah

Persetujuan disediakan oleh agent human-in-the-loop, yang dirakit di `src/interface/http/controllers/hitl_controller.py`.

1. Impor tool-mu di controller itu, lalu tambahkan ke daftar `TOOLS`:

    ```python title="src/interface/http/controllers/hitl_controller.py"
    TOOLS = [get_weather, send_email, delete_order]
    ```

2. Tambahkan nama tool ke `TOOLS_REQUIRING_APPROVAL`:

    ```python title="src/interface/http/controllers/hitl_controller.py"
    TOOLS_REQUIRING_APPROVAL = {send_email.name, delete_order.name}
    ```

3. Mulai ulang server.

Jika himpunan itu berisi nama yang bukan salah satu isi `TOOLS`, perakit agent melempar `ValueError` saat agent dirakit. Salah ketik nama tool ketahuan pada pesan pertama, bukan saat tool itu diam-diam berjalan tanpa persetujuan.

## Memeriksa hasilnya

Minta agent menjalankan tool itu lewat panel berikut. Agent harus berhenti dan menampilkan form keputusan:

<div class="zul-playground" data-feature="Human-in-the-loop">
Panel Playground tampil saat halaman ini dibuka sebagai situs dokumentasi (<code>uv run mkdocs serve</code>).
</div>

## Mengirim keputusan lewat API

Client sungguhan memakai dua endpoint. Pertama, kirim pesan ke `POST /hitl/chat`:

```shell
curl -X POST http://localhost:8000/hitl/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Send an email to alice@example.com saying the meeting is at 10\"}"
```

Jika agent ingin menjalankan tool yang butuh persetujuan, `answer` kosong dan `pending_review` berisi aksinya:

```json
{
  "thread_id": "5d0f8c2e4b7a4f0e9a1c3b6d8e2f4a70",
  "answer": null,
  "pending_review": {
    "action_requests": [
      {
        "name": "send_email",
        "args": {
          "to": "alice@example.com",
          "subject": "Meeting",
          "body": "The meeting is at 10."
        },
        "description": "Tool `send_email` menunggu persetujuan"
      }
    ],
    "review_configs": [
      {"action_name": "send_email", "allowed_decisions": ["approve", "edit", "reject"]}
    ]
  }
}
```

Tampilkan aksi itu ke manusia, lalu kirim keputusannya ke `POST /hitl/review` dengan `thread_id` yang sama:

```shell
curl -X POST http://localhost:8000/hitl/review \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"THREAD_ID\", \"decisions\": [{\"type\": \"approve\"}]}"
```

Ganti `THREAD_ID` dengan nilai dari respons pertama. Kirim satu keputusan untuk setiap aksi di `action_requests`, dalam urutan yang sama.

Setelah keputusan dikirim, periksa lagi `pending_review` di responsnya. Satu pesan bisa memicu lebih dari satu review.

## Memakai dari kode Python

Untuk memakai agent ini di luar REST API, misalnya dari bot, pakai `ReviewedChatUseCase`:

```python
from src.interface.http.controllers.hitl_controller import get_reviewed_chat_usecase

usecase = get_reviewed_chat_usecase()

turn = usecase.send_message("Email alice@example.com: the meeting is at 10", thread_id="t1")

if turn.pending_review:
    for action in turn.pending_review["action_requests"]:
        print(action["name"], action["args"])

    turn = usecase.submit_review([{"type": "approve"}], thread_id="t1")

print(turn.answer)
```

## Membatasi review ke sebagian pemanggilan

Persetujuan ditentukan per nama tool, bukan per isi argumen. Untuk aturan seperti "hanya email ke luar perusahaan yang direview", ubah penyaringan `calls_to_review` di fungsi `make_human_review`, file `src/application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py`.

> [!WARNING]
> Template tidak memeriksa siapa yang mengirim keputusan. Siapa pun yang mengetahui `thread_id` bisa menyetujui aksinya. Tambahkan autentikasi dan pemeriksaan hak di depan `POST /hitl/review` sebelum memakainya di produksi.

## Lihat juga

- [Format review](../referensi/format-review.md) untuk bentuk lengkap `pending_review` dan ketiga jenis keputusan.
- [Cara kerja human-in-the-loop](../konsep/human-in-the-loop.md) untuk aturan yang harus dijaga saat mengubah agent ini.
- [Menyimpan percakapan di database](menyimpan-percakapan.md), karena review yang menunggu hilang saat server dimulai ulang jika percakapan masih disimpan di memori.
