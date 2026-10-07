# HTTP API

Proyek hasil `zul build hexa` menyediakan REST API yang dibuat dengan FastAPI. Aplikasinya adalah objek `app` di `src/interface/http/main.py`.

Semua body request dan respons memakai JSON. Contoh di halaman ini memakai alamat `http://localhost:8000`, yaitu alamat server saat dijalankan di komputermu.

| Method | Path | Kegunaan |
|---|---|---|
| `GET` | [`/health`](#get-health) | Memeriksa bahwa server hidup. |
| `POST` | [`/chat`](#post-chat) | Mengirim pesan ke agent ReAct. |
| `POST` | [`/hitl/chat`](#post-hitlchat) | Mengirim pesan ke agent human-in-the-loop. |
| `POST` | [`/hitl/review`](#post-hitlreview) | Mengirim keputusan untuk aksi yang menunggu persetujuan. |
| `POST` | [`/subagents/chat`](#post-subagentschat) | Mengirim pesan ke supervisor, yang mendelegasikan pekerjaan ke subagent. |

Jika `PLAYGROUND_ENABLED` bernilai benar, aplikasi juga mendaftarkan endpoint `/playground/*`, yang dijelaskan di [Referensi Playground API](playground-api.md).

FastAPI menyediakan dokumentasi interaktif di `/docs` dan skema OpenAPI di `/openapi.json`.

## Kode status

Tabel berikut berlaku untuk semua endpoint di halaman ini:

| Status | Kapan | Bentuk body |
|---|---|---|
| `200` | Request berhasil. | Sesuai endpoint. |
| `400` | Aturan bisnis dilanggar, yaitu use case melempar turunan `DomainError`. | `{"detail": "PESAN"}` |
| `422` | Body tidak sesuai model request, misalnya field wajib tidak ada. | `{"detail": [DAFTAR_KESALAHAN]}` |
| `500` | Kegagalan yang tidak ditangani. | Teks `Internal Server Error` |

`PESAN` adalah teks exception. `DAFTAR_KESALAHAN` berisi satu objek per field yang salah.

Status `400` dihasilkan oleh satu handler di `main.py`, yang mengubah setiap `DomainError` menjadi respons berikut:

```python title="src/interface/http/main.py"
@app.exception_handler(DomainError)
def handle_domain_error(_request: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(error)})
```

Contoh body `400` saat `message` hanya berisi spasi:

```json
{"detail": "Message tidak boleh kosong"}
```

Contoh body `422` saat `message` tidak dikirim:

```json
{
  "detail": [
    {"type": "missing", "loc": ["body", "message"], "msg": "Field required", "input": {}}
  ]
}
```

Status `500` muncul dalam keadaan berikut:

- `OPENAI_API_KEY` belum diisi. Agent dirakit pada request chat pertama, dan `get_llm_model()` melempar `ValueError` saat itu.
- LLM tidak bisa dihubungi.
- Fungsi sebuah tool melempar exception.

## GET /health

Memeriksa bahwa server hidup. Endpoint ini tidak merakit agent dan tidak memanggil LLM, sehingga tetap menjawab walaupun `OPENAI_API_KEY` belum diisi.

Contoh request:

```shell
curl http://localhost:8000/health
```

Respons `200`:

```json
{"status": "ok"}
```

## POST /chat

Mengirim satu pesan ke agent ReAct dan mengembalikan jawabannya.

Body request (`ChatRequest`):

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `message` | string | Ya | Pesan user. Minimal satu karakter. |
| `thread_id` | string atau `null` | Tidak | ID percakapan. Jika kosong atau tidak dikirim, server membuat ID baru. |

Respons `200` (`ChatResponse`):

| Field | Tipe | Keterangan |
|---|---|---|
| `answer` | string | Jawaban agent. |
| `thread_id` | string | ID percakapan. ID yang dibuat server berupa 32 karakter heksadesimal. |

Kode status:

| Status | Kapan | Isi `detail` |
|---|---|---|
| `200` | Agent menjawab. | Tidak ada |
| `400` | `message` hanya berisi spasi. | `Message tidak boleh kosong` |
| `422` | `message` tidak dikirim, berupa string kosong, atau bukan string. | Daftar kesalahan per field |
| `500` | Rinciannya ada di [Kode status](#kode-status). | Tidak ada |

Jika agent kehabisan langkah, respons tetap `200` dan `answer` berisi `Maaf, saya butuh lebih banyak langkah untuk menyelesaikan permintaan ini.`

Contoh request untuk memulai percakapan baru:

```shell
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the weather in sf?\"}"
```

Contoh respons:

```json
{
  "answer": "It's sunny in San Francisco.",
  "thread_id": "5d0f8c2e4b7a4f0e9a1c3b6d8e2f4a70"
}
```

Contoh request untuk melanjutkan percakapan yang sama:

```shell
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"And tomorrow?\", \"thread_id\": \"THREAD_ID\"}"
```

`THREAD_ID` adalah nilai `thread_id` dari respons sebelumnya.

## POST /hitl/chat

Mengirim satu pesan ke agent human-in-the-loop. Agent menjawab, atau berhenti karena ada aksi yang menunggu persetujuan.

Body request (`ReviewedChatRequest`) sama dengan body [`POST /chat`](#post-chat):

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `message` | string | Ya | Pesan user. Minimal satu karakter. |
| `thread_id` | string atau `null` | Tidak | ID percakapan. Jika kosong atau tidak dikirim, server membuat ID baru. |

Respons `200` (`ReviewedChatResponse`):

| Field | Tipe | Keterangan |
|---|---|---|
| `thread_id` | string | ID percakapan. Wajib dikirim ke `POST /hitl/review` jika `pending_review` terisi. |
| `answer` | string atau `null` | Jawaban agent. Terisi jika agent selesai menjawab. |
| `pending_review` | objek atau `null` | Aksi yang menunggu keputusan. Terisi jika agent berhenti. |

Tepat satu dari `answer` dan `pending_review` terisi. Isi `pending_review` dijelaskan di [Referensi format review human-in-the-loop](format-review.md).

Kode status:

| Status | Kapan | Isi `detail` |
|---|---|---|
| `200` | Agent menjawab, atau berhenti menunggu keputusan. | Tidak ada |
| `400` | `message` hanya berisi spasi. | `Message tidak boleh kosong` |
| `400` | Thread itu masih punya aksi yang menunggu keputusan. | `Masih ada aksi yang menunggu persetujuan. Kirim keputusannya dulu.` |
| `422` | `message` tidak dikirim, berupa string kosong, atau bukan string. | Daftar kesalahan per field |
| `500` | Rinciannya ada di [Kode status](#kode-status). | Tidak ada |

Contoh request yang meminta agent mengirim email:

```shell
curl -X POST http://localhost:8000/hitl/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Send an email to alice@example.com saying the meeting is at 10\"}"
```

Contoh respons saat agent berhenti menunggu keputusan:

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

## POST /hitl/review

Mengirim keputusan untuk aksi yang menunggu, lalu melanjutkan agent dari titik berhentinya.

Body request (`ReviewRequest`):

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `thread_id` | string | Ya | `thread_id` dari respons yang berisi `pending_review`. |
| `decisions` | array | Ya | Satu keputusan per item `pending_review.action_requests`, dalam urutan yang sama. Minimal satu item. |

Setiap item `decisions` (`ReviewDecision`):

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `type` | `"approve"`, `"edit"`, atau `"reject"` | Ya | Jenis keputusan. |
| `edited_action` | objek atau `null` | Untuk `edit` | Aksi pengganti. Berisi `name` (string) dan `args` (objek); keduanya wajib. |
| `message` | string atau `null` | Tidak | Alasan penolakan untuk `reject`. |

Akibat setiap jenis keputusan dijelaskan di [Referensi format review human-in-the-loop](format-review.md).

Respons `200` sama bentuknya dengan respons [`POST /hitl/chat`](#post-hitlchat). Jika agent kemudian meminta aksi lain yang juga butuh persetujuan, `pending_review` terisi lagi.

Kode status:

| Status | Kapan | Isi `detail` |
|---|---|---|
| `200` | Agent dilanjutkan. | Tidak ada |
| `400` | Tidak ada aksi yang menunggu di thread itu, termasuk saat `thread_id` tidak dikenal. | `Tidak ada aksi yang menunggu persetujuan di percakapan ini` |
| `400` | Jumlah keputusan tidak sama dengan jumlah aksi. | `Butuh 1 keputusan (satu per aksi), diterima 2` |
| `400` | Keputusan `edit` tanpa `edited_action`. | `Keputusan 'edit' wajib menyertakan 'edited_action'` |
| `422` | `thread_id` tidak dikirim, `decisions` kosong, `type` bukan salah satu dari tiga nilai, atau `edited_action` tidak berisi `name` dan `args`. | Daftar kesalahan per field |
| `500` | Rinciannya ada di [Kode status](#kode-status). | Tidak ada |

Angka pada pesan jumlah keputusan mengikuti keadaan sebenarnya. Keputusan yang ditolak dengan `400` atau `422` tidak mengubah apa pun: aksi tetap menunggu dan keputusan bisa dikirim ulang.

Contoh request yang menyetujui satu aksi:

```shell
curl -X POST http://localhost:8000/hitl/review \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"THREAD_ID\", \"decisions\": [{\"type\": \"approve\"}]}"
```

`THREAD_ID` adalah nilai `thread_id` dari respons `POST /hitl/chat`.

Contoh respons setelah agent menjalankan tool dan menjawab:

```json
{
  "thread_id": "5d0f8c2e4b7a4f0e9a1c3b6d8e2f4a70",
  "answer": "I've sent the email to alice@example.com.",
  "pending_review": null
}
```

## POST /subagents/chat

Mengirim satu pesan ke supervisor, yang mendelegasikan pekerjaan ke subagent lalu merangkum hasilnya.

Endpoint ini memakai model request, model respons, dan handler yang sama dengan [`POST /chat`](#post-chat). Body request, bentuk respons, dan kode statusnya sama; yang berbeda hanya agent yang menjawab.

Contoh request yang melibatkan dua subagent:

```shell
curl -X POST http://localhost:8000/subagents/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Check the weather in sf and email it to alice@example.com\"}"
```

Contoh respons:

```json
{
  "answer": "It's sunny in San Francisco. I've emailed the forecast to alice@example.com.",
  "thread_id": "5d0f8c2e4b7a4f0e9a1c3b6d8e2f4a70"
}
```

> [!NOTE]
> Subagent `email_agent` menjalankan `send_email` tanpa langkah persetujuan. Endpoint ini tidak pernah mengembalikan `pending_review`.

## Halaman terkait

- [Referensi: Format review human-in-the-loop](format-review.md)
- [Referensi: Playground API](playground-api.md)
- [Referensi: API agent](agent.md)
- [Referensi: Environment variable](konfigurasi.md)
- [Panduan: Menjalankan aplikasi](../panduan/menjalankan-aplikasi.md)
- [Panduan: Menambah endpoint](../panduan/menambah-endpoint.md)
- [Konsep: Perjalanan sebuah request](../konsep/alur-request.md)
