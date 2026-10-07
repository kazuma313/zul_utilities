# Playground API

Endpoint `/playground/*` menjalankan sebuah fitur dan mengembalikan jawaban agent beserta setiap langkahnya. Panel Playground di dokumentasi ini memanggil endpoint tersebut.

Endpoint ini hanya terdaftar jika `PLAYGROUND_ENABLED` bernilai benar. Rinciannya ada di [Environment variable](konfigurasi.md). Saat playground mati, ketiga path di halaman ini menjawab `404`.

| Method | Path | Kegunaan |
|---|---|---|
| `GET` | `/playground/features` | Daftar fitur yang bisa dicoba. |
| `POST` | `/playground/messages` | Mengirim pesan ke sebuah fitur. |
| `POST` | `/playground/resume` | Melanjutkan fitur yang berhenti menunggu keputusan. |

Kode sumber: `src/interface/http/routers/playground.py` dan `src/interface/http/controllers/playground_controller.py`.

## GET /playground/features

Mengembalikan fitur yang terdaftar di `src/interface/playground/features.py`, dalam urutan yang sama.

Respons `200` berupa array. Setiap item berisi:

| Field | Tipe | Keterangan |
|---|---|---|
| `name` | string | Nama fitur. Dipakai sebagai nilai `feature` di endpoint lain. |
| `description` | string | Keterangan singkat. |
| `examples` | array of string | Contoh pesan siap kirim. |

**Contoh:**

```shell
curl http://localhost:8000/playground/features
```

```json
[
  {
    "name": "ReAct",
    "description": "Agent dasar dengan tool cuaca. Sama dengan `POST /chat`.",
    "examples": ["What is the weather in sf?"]
  }
]
```

## POST /playground/messages

Mengirim satu pesan user ke sebuah fitur dan menjalankan agent sampai ia menjawab, berhenti menunggu keputusan, atau gagal.

Body request:

| Field | Tipe | Wajib | Default | Keterangan |
|---|---|---|---|---|
| `feature` | string | Ya | | Nama fitur. |
| `message` | string | Ya | | Pesan user. Minimal satu karakter. |
| `thread_id` | string | Tidak | Dibuat server | Id percakapan. Kosongkan untuk percakapan baru. |
| `max_steps` | integer | Tidak | `25` | Batas langkah graph untuk pesan ini. Antara `1` dan `200`. |

Respons `200`: sebuah [giliran](#bentuk-giliran).

**Contoh:**

```shell
curl -X POST http://localhost:8000/playground/messages \
  -H "Content-Type: application/json" \
  -d "{\"feature\": \"ReAct\", \"message\": \"What is the weather in sf?\"}"
```

## POST /playground/resume

Melanjutkan fitur yang berhenti di `interrupt()`. Untuk agent human-in-the-loop, nilai yang dikirim adalah keputusan review.

Body request:

| Field | Tipe | Wajib | Default | Keterangan |
|---|---|---|---|---|
| `feature` | string | Ya | | Nama fitur yang sedang menunggu. |
| `thread_id` | string | Ya | | `thread_id` dari giliran yang berisi `pending_review`. |
| `value` | apa saja | Ya | | Nilai yang menjadi hasil `interrupt()`. Untuk review: `{"decisions": [...]}`. |
| `max_steps` | integer | Tidak | `25` | Batas langkah graph. Antara `1` dan `200`. |

Jika `pending_review` berisi `action_requests`, isi `value.decisions` diperiksa sebelum agent dilanjutkan, dengan aturan di [Format review](format-review.md). Untuk bentuk `pending_review` yang lain, `value` diteruskan apa adanya.

Respons `200`: sebuah [giliran](#bentuk-giliran).

**Contoh:**

```shell
curl -X POST http://localhost:8000/playground/resume \
  -H "Content-Type: application/json" \
  -d "{\"feature\": \"Human-in-the-loop\", \"thread_id\": \"THREAD_ID\", \"value\": {\"decisions\": [{\"type\": \"approve\"}]}}"
```

`THREAD_ID` adalah nilai `thread_id` dari giliran sebelumnya.

## Bentuk giliran

Kedua endpoint `POST` mengembalikan bentuk yang sama.

| Field | Tipe | Keterangan |
|---|---|---|
| `thread_id` | string | Id percakapan. Nilai yang sama dikirim lagi untuk melanjutkan percakapan. Id buatan server diawali `playground-`. |
| `answer` | string atau `null` | Teks jawaban agent. `null` jika agent menunggu keputusan atau gagal. |
| `pending_review` | apa saja atau `null` | Nilai yang diberikan agent ke `interrupt()`. `null` jika agent tidak sedang menunggu. |
| `error` | object atau `null` | Error yang menghentikan agent: `type` (nama kelas exception) dan `message`. |
| `seconds` | number | Lama giliran ini, dalam detik. |
| `steps` | array | Langkah yang selesai dijalankan, berurutan. |

Paling banyak satu dari `answer`, `pending_review`, dan `error` yang terisi.

Setiap item `steps`:

| Field | Tipe | Keterangan |
|---|---|---|
| `node` | string | Nama node graph yang selesai dijalankan. |
| `depth` | integer | `0` untuk graph utama. `1` atau lebih untuk graph yang dipanggil dari dalam sebuah tool, misalnya subagent. |
| `events` | array | Kejadian yang dihasilkan node itu. Kosong jika node tidak menghasilkan pesan. |

Setiap item `events`:

| Field | Tipe | Keterangan |
|---|---|---|
| `type` | string | `tool_call`, `tool_result`, atau `text`. |
| `name` | string atau `null` | Nama tool. Terisi untuk `tool_call` dan `tool_result`. |
| `args` | object atau `null` | Argumen tool. Terisi untuk `tool_call`. |
| `content` | string atau `null` | Hasil tool untuk `tool_result`, atau teks model untuk `text`. |
| `failed` | boolean | `true` jika hasil tool berstatus error, termasuk aksi yang ditolak saat review. |

**Contoh giliran agent ReAct yang memakai satu tool:**

```json
{
  "thread_id": "playground-3f9a1c2e",
  "answer": "It's sunny in San Francisco.",
  "pending_review": null,
  "error": null,
  "seconds": 1.204,
  "steps": [
    {
      "node": "llm_call",
      "depth": 0,
      "events": [
        {"type": "tool_call", "name": "get_weather", "args": {"location": "sf"}, "content": null, "failed": false}
      ]
    },
    {
      "node": "tool_node",
      "depth": 0,
      "events": [
        {"type": "tool_result", "name": "get_weather", "args": null, "content": "It's sunny in San Francisco, but you better look out if you're a Gemini 😈.", "failed": false}
      ]
    },
    {
      "node": "llm_call",
      "depth": 0,
      "events": [
        {"type": "text", "name": null, "args": null, "content": "It's sunny in San Francisco.", "failed": false}
      ]
    }
  ]
}
```

## Kode status

| Status | Kapan | Bentuk body |
|---|---|---|
| `200` | Giliran selesai dijalankan. Termasuk saat agent gagal di tengah jalan; kegagalannya ada di field `error`. | Giliran |
| `400` | `message` hanya berisi spasi; pesan baru dikirim ke thread yang masih menunggu keputusan; `resume` dipanggil pada thread yang tidak menunggu; keputusan review salah bentuk. | `{"detail": "pesan"}` |
| `404` | `feature` tidak terdaftar, atau playground mati. | `{"detail": "pesan"}` |
| `422` | Body tidak sesuai tabel di atas, misalnya `feature` tidak dikirim. | `{"detail": [daftar kesalahan per field]}` |
| `503` | Fitur tidak bisa dirakit, misalnya `OPENAI_API_KEY` belum diisi. `detail` memuat alasannya. | `{"detail": "pesan"}` |

## Akses dari browser

Aplikasi hanya mengizinkan request browser dari alamat yang terdaftar di `PLAYGROUND_ORIGINS`. Bawaannya `http://127.0.0.1:8001` dan `http://localhost:8001`. Method yang diizinkan adalah `GET` dan `POST`, dengan header `Content-Type`.

Aturan ini berlaku untuk seluruh aplikasi selama playground menyala, bukan hanya untuk path `/playground/*`. Request yang tidak berasal dari browser, misalnya curl, tidak terpengaruh.

## Fungsi Python di balik endpoint

Endpoint ini adalah pembungkus tipis untuk modul `src/interface/playground/runner.py`.

| Fungsi | Kegunaan |
|---|---|
| `send_message(agent, message, thread_id, max_steps=25)` | Mengirim pesan user dan mengembalikan `Turn`. |
| `submit_review(agent, decisions, thread_id, max_steps=25)` | Melanjutkan agent dengan daftar keputusan review. |
| `resume(agent, value, thread_id, max_steps=25)` | Melanjutkan agent dengan nilai apa pun. |
| `pending_review_of(agent, thread_id)` | Mengembalikan nilai `interrupt()` yang sedang menunggu di sebuah thread, atau `None`. |

`Turn` berisi `steps`, `pending_review`, `error`, `seconds`, dan properti `answer`. Setiap `Step` berisi `node`, `messages` (pesan LangChain yang dihasilkan node), dan `depth`.

Daftar fitur dibentuk dari `Feature` di `src/interface/playground/features.py`:

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `name` | `str` | Wajib | Nama fitur. |
| `description` | `str` | Wajib | Keterangan singkat. |
| `build_agent` | fungsi tanpa argumen | Wajib | Mengembalikan graph ter-compile. Dipanggil saat fitur dipakai. |
| `examples` | `tuple[str, ...]` | `()` | Contoh pesan. |

`find_feature(name)` mengembalikan `Feature` dengan nama itu, atau melempar `KeyError` yang menyebut nama-nama yang tersedia.
