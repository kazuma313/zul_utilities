# Format review human-in-the-loop

Agent human-in-the-loop bertukar dua bentuk data dengan manusia: payload `pending_review` yang berisi aksi yang menunggu persetujuan, dan daftar keputusan yang menjawabnya. Halaman ini mencantumkan bentuk keduanya, aturan validasinya, dan pesan error-nya.

Kedua bentuk mengikuti format human-in-the-loop LangChain (`action_requests`, `review_configs`, `decisions`).

## Payload `pending_review`

Payload ini dibuat oleh `build_review_request` di `src/application/AI/agents/human_in_the_loop/nodes/human_in_the_loop_nodes.py`. Payload yang sama muncul di tiga tempat:

| Tempat | Cara membacanya |
|---|---|
| Respons `POST /hitl/chat` dan `POST /hitl/review` | Field `pending_review` |
| `ReviewedChatUseCase` | `ChatTurn.pending_review` |
| Agent dipanggil langsung | `result["__interrupt__"][0].value` |

Isi payload:

| Field | Tipe | Keterangan |
|---|---|---|
| `action_requests` | array | Aksi yang menunggu keputusan. Satu item per tool call yang butuh persetujuan. |
| `action_requests[].name` | string | Nama tool. |
| `action_requests[].args` | objek | Argumen yang diusulkan model. |
| `action_requests[].description` | string | Teks tetap berbentuk ``Tool `NAMA` menunggu persetujuan``. |
| `review_configs` | array | Pengaturan review. Satu item per aksi, dalam urutan yang sama dengan `action_requests`. |
| `review_configs[].action_name` | string | Nama tool, sama dengan `name` pada aksi yang bersangkutan. |
| `review_configs[].allowed_decisions` | array string | Selalu `["approve", "edit", "reject"]`, yaitu konstanta `ALLOWED_DECISIONS`. |

Aturan pembentukan payload:

- Hanya tool call yang namanya ada di `tools_requiring_approval` yang masuk ke `action_requests`. Tool call lain di giliran yang sama tidak dicantumkan.
- Urutan `action_requests` mengikuti urutan tool call di pesan model.
- Payload hanya berisi data yang bisa diubah menjadi JSON.

Contoh payload untuk satu aksi `send_email`:

```json
{
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
```

## Daftar keputusan

Keputusan dikirim sebagai daftar: satu keputusan per item `action_requests`, dalam urutan yang sama. Keputusan pertama berlaku untuk aksi pertama, dan seterusnya.

Tempat daftar itu dikirim bergantung pada cara agent dipanggil:

| Cara memanggil | Bentuk |
|---|---|
| `POST /hitl/review` | Field `decisions` di body, bersama `thread_id` |
| `ReviewedChatUseCase` | Argumen `decisions` pada `submit_review(decisions, thread_id)` |
| Agent dipanggil langsung | `Command(resume={"decisions": [...]})` |

Contoh body `POST /hitl/review` untuk payload berisi dua aksi:

```json
{
  "thread_id": "THREAD_ID",
  "decisions": [
    {"type": "reject", "message": "Not this one"},
    {"type": "approve"}
  ]
}
```

`THREAD_ID` adalah nilai `thread_id` dari respons yang berisi `pending_review`.

Setiap keputusan adalah objek dengan field berikut:

| Field | Tipe | Dipakai oleh | Keterangan |
|---|---|---|---|
| `type` | `"approve"`, `"edit"`, atau `"reject"` | Semua | Jenis keputusan. Wajib. |
| `edited_action` | objek | `edit` | Aksi pengganti. Wajib untuk `edit`. |
| `edited_action.name` | string | `edit` | Nama tool yang dijalankan. Biasanya sama dengan nama aslinya. |
| `edited_action.args` | objek | `edit` | Seluruh argumen tool setelah diubah, bukan hanya yang berubah. |
| `message` | string | `reject` | Alasan penolakan. Opsional. |

Field yang bukan milik jenis keputusannya diabaikan. Misalnya, `message` pada keputusan `approve` tidak berpengaruh.

### `approve`

Menjalankan tool dengan nama dan argumen yang diusulkan model.

Bentuknya adalah sebagai berikut:

```json
{"type": "approve"}
```

### `edit`

Menjalankan tool dengan nama dan argumen dari `edited_action`. Tool call di pesan model diganti dengan versi yang diubah, sehingga riwayat percakapan mencatat argumen yang sungguh dijalankan.

Bentuknya adalah sebagai berikut:

```json
{
  "type": "edit",
  "edited_action": {
    "name": "send_email",
    "args": {
      "to": "alice@example.com",
      "subject": "Meeting moved",
      "body": "The meeting is at 11."
    }
  }
}
```

Jika `edited_action.name` bukan nama tool milik agent, tool tidak dijalankan dan model menerima hasil tool berstatus `error` yang menyebut daftar tool yang tersedia.

> [!NOTE]
> Validasi keputusan tidak mencocokkan `edited_action.args` dengan skema tool. Argumen yang tidak sesuai skema baru ketahuan saat tool dijalankan: tool tidak berjalan, model menerima hasil tool berstatus `error` yang menyebut field bermasalah, dan aksi itu tidak lagi menunggu keputusan.

### `reject`

Membatalkan tool. Tool tidak dijalankan, dan model menerima hasil tool berstatus `error` yang berisi alasan penolakan.

Bentuknya adalah sebagai berikut:

```json
{"type": "reject", "message": "Wrong recipient. Ask the user for the correct address."}
```

Jika `message` tidak dikirim atau kosong, model menerima teks bawaan `REJECTED_BY_USER_MESSAGE`:

```text
User rejected this action. It was not executed.
```

## Akibat keputusan pada graph

Tabel berikut merangkum apa yang terjadi setelah keputusan diterapkan:

| Keadaan | Akibat |
|---|---|
| Ada tool call yang disetujui atau diubah | Graph lanjut ke `tool_node`, yang menjalankan tool call yang belum punya hasil. |
| Semua tool call di giliran itu ditolak | Graph kembali ke `llm_call` tanpa menjalankan tool apa pun. |
| Ada tool call yang tidak butuh persetujuan di giliran yang sama | Tool call itu tetap dijalankan, walaupun aksi lain ditolak. |
| Model meminta aksi lain yang butuh persetujuan setelah dilanjutkan | Graph berhenti lagi dan `pending_review` terisi dengan payload baru. |

## Aturan validasi

Keputusan diperiksa di dua tempat sebelum graph dilanjutkan. Model Pydantic `ReviewRequest` di `hitl_controller.py` memeriksa bentuk body HTTP dan menghasilkan HTTP 422. Fungsi `validate_decisions` di `src/application/usecases/reviewed_chat.py` memeriksa kecocokan keputusan dengan aksi yang menunggu dan melempar `InvalidReviewDecisionError`, yang menjadi HTTP 400.

| Keadaan | Lewat `POST /hitl/review` | Lewat `submit_review` |
|---|---|---|
| Tidak ada aksi yang menunggu di thread itu | `400` | `NoPendingReviewError` |
| `decisions` kosong | `422` | `InvalidReviewDecisionError` |
| Jumlah keputusan tidak sama dengan jumlah aksi | `400` | `InvalidReviewDecisionError` |
| `type` bukan `approve`, `edit`, atau `reject` | `422` | `InvalidReviewDecisionError` |
| Keputusan bukan objek | `422` | `InvalidReviewDecisionError` |
| `edit` tanpa `edited_action` | `400` | `InvalidReviewDecisionError` |
| `edited_action` tanpa `name` berupa teks atau tanpa `args` berupa objek | `422` | `InvalidReviewDecisionError` |

`submit_review` memeriksa dengan urutan berikut dan berhenti di kesalahan pertama: keberadaan aksi yang menunggu, jumlah keputusan, lalu setiap keputusan sesuai urutannya (jenis, kemudian `edited_action`).

Keputusan yang ditolak validasi tidak mengubah state percakapan. Aksi tetap menunggu, dan keputusan yang benar bisa dikirim sesudahnya.

## Pesan error

Tabel berikut mencantumkan teks setiap exception. Lewat REST API, teks ini menjadi isi `detail` pada respons `400`.

| Exception | Pesan |
|---|---|
| `NoPendingReviewError` | `Tidak ada aksi yang menunggu persetujuan di percakapan ini` |
| `ReviewPendingError` | `Masih ada aksi yang menunggu persetujuan. Kirim keputusannya dulu.` |
| `InvalidReviewDecisionError` | `Butuh 2 keputusan (satu per aksi), diterima 1` |
| `InvalidReviewDecisionError` | `Jenis keputusan 'postpone' tidak dikenal. Pilihan: ['approve', 'edit', 'reject']` |
| `InvalidReviewDecisionError` | `Keputusan 'edit' wajib menyertakan 'edited_action'` |
| `InvalidReviewDecisionError` | `'edited_action' harus berisi 'name' (teks) dan 'args' (objek)` |

Angka dan jenis keputusan di dalam pesan mengikuti nilai yang dikirim. Untuk keputusan yang bukan objek, jenis yang tercetak adalah `None`.

`ReviewPendingError` dilempar oleh `send_message`, bukan oleh `submit_review`: pesan baru ditolak selama thread masih punya aksi yang menunggu.

## Aksi tanpa keputusan

Node `human_review` punya aturan cadangan untuk agent yang dilanjutkan langsung dengan `Command(resume=...)`, tanpa melewati `validate_decisions`:

| Keadaan | Akibat |
|---|---|
| Keputusan lebih sedikit daripada aksi | Aksi yang tidak mendapat keputusan diperlakukan sebagai ditolak, memakai konstanta `NO_DECISION`. |
| Keputusan lebih banyak daripada aksi | Keputusan yang berlebih diabaikan. |

Hasil tool untuk aksi tanpa keputusan berstatus `error` dan berisi teks berikut:

```text
No decision was given for this action. It was not executed.
```

Lewat `ReviewedChatUseCase` dan `POST /hitl/review`, keadaan ini tidak terjadi karena jumlah keputusan sudah diperiksa lebih dulu.

## Lihat juga

- [Referensi: HTTP API](http-api.md)
- [Referensi: API agent](agent.md)
- [Konsep: Cara kerja human-in-the-loop](../konsep/human-in-the-loop.md)
- [Panduan: Mewajibkan persetujuan untuk sebuah tool](../panduan/mewajibkan-persetujuan.md)
- [Tutorial: Meminta persetujuan manusia](../tutorial/persetujuan-manusia.md)
