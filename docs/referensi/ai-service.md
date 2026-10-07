# AI Service

`AIService` membungkus `ChatOpenAI` dan `OpenAIEmbeddings` dari LangChain dengan konfigurasi yang divalidasi Pydantic. Konfigurasi bisa datang dari file YAML atau JSON, dari environment variable, atau dirakit langsung di kode.

Baris berikut mengimpor kelas-kelasnya:

```python
from zul.utilities.embedding_service import (
    AIConfig,
    AIService,
    ChatResponse,
    EmbedResponse,
    EmbeddingConfig,
    LLMConfig,
    ServiceConfig,
)
```

Modul ini membutuhkan extra `llm` (`langchain-openai`).

## Urutan prioritas nilai

Setiap nilai konfigurasi diambil dari sumber pertama yang menyediakannya:

| Urutan | Sumber | Contoh |
|---|---|---|
| Pertama | Environment variable | `LLM_MODEL` |
| Kedua | Nilai di file config atau argumen konstruktor | `llm.model` |
| Ketiga | Nilai bawaan field | Lihat tabel tiap model |

Environment variable dibaca setiap kali sebuah model config dibuat, juga saat model itu dirakit langsung di kode. `LLMConfig(api_key="...")` tetap memakai nilai `LLM_API_KEY` jika variabel itu diset.

## `LLMConfig`

Pengaturan chat model. Di file config, isinya berada di bawah kunci `llm`.

| Field | Tipe | Default | Environment variable | Keterangan |
|---|---|---|---|---|
| `base_url` | `str` | Alamat server internal | `LLM_BASE_URL` | Endpoint chat model yang kompatibel dengan OpenAI. |
| `api_key` | `SecretStr` | `""` | `LLM_API_KEY` | API key. Wajib diisi lewat file atau environment. |
| `model` | `str` | `"qwen2-32B-Instruct-resolved"` | `LLM_MODEL` | Nama model. |
| `temperature` | `float` | `0.1` | `LLM_TEMPERATURE` | Keacakan keluaran, antara 0.0 dan 2.0. |
| `max_tokens` | `int` | `2048` | `LLM_MAX_TOKENS` | Batas token jawaban, lebih dari 0. |
| `timeout` | `int` | `30` | `LLM_TIMEOUT` | Batas waktu request dalam detik, lebih dari 0. |

**Melempar:** `pydantic.ValidationError`, turunan `ValueError`, jika sebuah nilai di luar batas atau jika `api_key` kosong atau berupa placeholder. Nilai yang dianggap placeholder: `""`, `"your-llm-api-key"`, `"change-me"`, dan `"YOUR_KEY_HERE"`. Pesannya memuat `LLM API key is missing or is a placeholder.`

`api_key` bertipe `SecretStr`, jadi nilainya tidak ikut tercetak saat objek config di-print. Teks aslinya didapat dengan `api_key.get_secret_value()`.

## `EmbeddingConfig`

Pengaturan model embedding. Di file config, isinya berada di bawah kunci `embedding`.

| Field | Tipe | Default | Environment variable | Keterangan |
|---|---|---|---|---|
| `base_url` | `str` | `""` | `EMBEDDING_BASE_URL` | Endpoint model embedding. |
| `api_key` | `SecretStr` | `""` | `EMBEDDING_API_KEY` | API key. Wajib diisi jika bagian `embedding` ada. |
| `model` | `str` | `"Qwen3-Embedding-4B"` | `EMBEDDING_MODEL` | Nama model embedding. |
| `timeout` | `int` | `30` | `EMBEDDING_TIMEOUT` | Batas waktu request dalam detik, lebih dari 0. |

**Melempar:** `pydantic.ValidationError` jika `api_key` kosong atau berupa placeholder. Nilai yang dianggap placeholder: `""`, `"your-embedding-api-key"`, `"change-me"`, dan `"YOUR_KEY_HERE"`. Pesannya memuat `Embedding API key is missing or is a placeholder.`

## `ServiceConfig`

Pengaturan perilaku service. Di file config, isinya berada di bawah kunci `service`.

| Field | Tipe | Default | Environment variable | Keterangan |
|---|---|---|---|---|
| `enable_embedding` | `bool` | `True` | `SERVICE_ENABLE_EMBEDDING` | Jika `False`, client embedding tidak dibuat walau bagian `embedding` ada. |
| `log_level` | `str` | `"INFO"` | `SERVICE_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, atau `CRITICAL`. Huruf besar-kecil bebas, disimpan dalam huruf besar. |

`SERVICE_ENABLE_EMBEDDING` dibaca sebagai `True` untuk `1`, `true`, atau `yes` (huruf besar-kecil bebas). Nilai lain dibaca sebagai `False`.

**Melempar:** `pydantic.ValidationError` dengan pesan yang memuat `Invalid log_level 'NILAI'.` jika `log_level` tidak dikenal.

## `AIConfig`

Akar konfigurasi. Model ini memuat ketiga model di atas sebagai field bersarang.

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `llm` | `LLMConfig` | `LLMConfig()` | Pengaturan chat model. Tanpa bagian `llm`, semua nilainya diambil dari environment dan nilai bawaan. |
| `embedding` | `EmbeddingConfig` atau `None` | `None` | Pengaturan embedding. `None` berarti embedding tidak dikonfigurasi. |
| `service` | `ServiceConfig` | `ServiceConfig()` | Pengaturan perilaku service. |

Contoh berikut menunjukkan file config dengan ketiga bagian:

```yaml title="config.yaml"
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 2048
  timeout: 30

embedding:
  base_url: "https://api.openai.com/v1"
  model: "text-embedding-3-small"

service:
  enable_embedding: true
  log_level: "INFO"
```

### `AIConfig.from_file(path="config.yaml")`

Memuat konfigurasi dari file YAML atau JSON. Format dipilih dari ekstensi file: `.yaml` dan `.yml` dibaca sebagai YAML, `.json` sebagai JSON. File YAML yang kosong dibaca sebagai konfigurasi kosong.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `path` | `str` atau `Path` | `"config.yaml"` | Path ke file config. |

**Mengembalikan:** `AIConfig`.

**Melempar:**

- `FileNotFoundError` dengan pesan `Config file not found: 'FILE'` jika file tidak ada.
- `ValueError` dengan pesan `Unsupported config file format: 'EKSTENSI'` jika ekstensinya bukan `.yaml`, `.yml`, atau `.json`.
- `pydantic.ValidationError`, turunan `ValueError`, jika isi file tidak lolos validasi.

### `AIConfig.from_env()`

Merakit konfigurasi dari environment variable saja. Bagian `embedding` dibuat hanya jika `EMBEDDING_API_KEY` diset. Tanpa itu, `embedding` bernilai `None`.

**Mengembalikan:** `AIConfig`.

**Melempar:** `pydantic.ValidationError` jika `LLM_API_KEY` tidak diset atau berupa placeholder.

### `safe_summary()`

Mengembalikan seluruh konfigurasi sebagai `dict` dengan setiap API key diganti `"***"`.

**Mengembalikan:** `dict` dengan kunci `llm`, `embedding`, dan `service`. Nilai `embedding` adalah `None` jika embedding tidak dikonfigurasi.

Contoh berikut mencetak konfigurasi tanpa membocorkan API key:

```python
import json

print(json.dumps(service.config.safe_summary(), indent=2))
```

## `ChatResponse`

Nilai kembalian `AIService.chat`. Model Pydantic.

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `content` | `str` | Wajib | Teks jawaban model. |
| `model` | `str` | Wajib | Nama model yang menjawab. |
| `finish_reason` | `str` atau `None` | `None` | Alasan model berhenti, misalnya `stop` atau `length`. |
| `usage` | `dict[str, int]` atau `None` | `None` | Jumlah token: `prompt_tokens`, `completion_tokens`, `total_tokens`. `None` jika API tidak mengembalikannya. |

## `EmbedResponse`

Nilai kembalian `AIService.embed`. Model Pydantic.

| Field | Tipe | Default | Keterangan |
|---|---|---|---|
| `vector` | `list[float]` | Wajib | Vektor embedding. |
| `dimensions` | `int` | Wajib | Panjang vektor, sama dengan `len(vector)`. |
| `model` | `str` | Wajib | Model embedding yang dipakai. |

## `AIService(config)`

Membuat service dari sebuah `AIConfig`.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `config` | `AIConfig` | Wajib | Konfigurasi yang sudah divalidasi. |

Saat dibuat, service memanggil `logging.basicConfig` dengan level `service.log_level`, lalu mencatat ringkasan config dari `safe_summary()` pada level `INFO`. Client LLM dan client embedding baru dibuat saat `chat()` atau `embed()` pertama kali dipanggil, lalu dipakai ulang.

**Atribut:**

| Atribut | Tipe | Keterangan |
|---|---|---|
| `config` | `AIConfig` | Konfigurasi yang dipakai service. |

Contoh berikut merakit konfigurasi di kode, misalnya untuk test:

```python
from zul.utilities.embedding_service import AIConfig, AIService, LLMConfig

config = AIConfig(llm=LLMConfig(api_key="API_KEY", base_url="https://HOST/v1"))
service = AIService(config)
```

`API_KEY` adalah key endpoint dan `HOST` alamat servernya.

### `AIService.from_file(path="config.yaml")`

Membuat service dari file config YAML atau JSON.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `path` | `str` atau `Path` | `"config.yaml"` | Path ke file config. |

**Mengembalikan:** `AIService`.

**Melempar:** sama dengan [`AIConfig.from_file`](#aiconfigfrom_filepathconfigyaml).

### `AIService.from_env()`

Membuat service dari environment variable saja, tanpa file config.

**Mengembalikan:** `AIService`.

**Melempar:** sama dengan [`AIConfig.from_env`](#aiconfigfrom_env).

### `chat(prompt)`

Mengirim satu prompt ke LLM dan mengembalikan jawabannya.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `prompt` | `str` | Wajib | Pertanyaan atau instruksi untuk model. |

**Mengembalikan:** [`ChatResponse`](#chatresponse). Jika API tidak menyebut nama model, `model` diisi `llm.model` dari config.

**Melempar:** `RuntimeError` dengan pesan `Chat request failed: ...` jika pemanggilan gagal karena alasan apa pun.

### `embed(text)`

Mengubah satu teks menjadi vektor embedding.

| Parameter | Tipe | Default | Keterangan |
|---|---|---|---|
| `text` | `str` | Wajib | Teks yang diubah menjadi vektor. |

**Mengembalikan:** [`EmbedResponse`](#embedresponse).

**Melempar:**

- `ValueError` dengan pesan yang diawali `Embedding is not available.` jika `service.enable_embedding` bernilai `False` atau bagian `embedding` tidak ada.
- `RuntimeError` dengan pesan `Embedding request failed: ...` jika pemanggilan gagal.

### `is_embedding_enabled()`

Memeriksa apakah client embedding tersedia.

**Mengembalikan:** `bool`. `True` jika `service.enable_embedding` bernilai `True` dan bagian `embedding` dikonfigurasi.

## Environment variable

| Variabel | Menimpa | Tipe |
|---|---|---|
| `LLM_BASE_URL` | `llm.base_url` | teks |
| `LLM_API_KEY` | `llm.api_key` | teks |
| `LLM_MODEL` | `llm.model` | teks |
| `LLM_TEMPERATURE` | `llm.temperature` | bilangan pecahan |
| `LLM_MAX_TOKENS` | `llm.max_tokens` | bilangan bulat |
| `LLM_TIMEOUT` | `llm.timeout` | bilangan bulat |
| `EMBEDDING_BASE_URL` | `embedding.base_url` | teks |
| `EMBEDDING_API_KEY` | `embedding.api_key` | teks |
| `EMBEDDING_MODEL` | `embedding.model` | teks |
| `EMBEDDING_TIMEOUT` | `embedding.timeout` | bilangan bulat |
| `SERVICE_ENABLE_EMBEDDING` | `service.enable_embedding` | `1`, `true`, atau `yes` untuk `True` |
| `SERVICE_LOG_LEVEL` | `service.log_level` | nama level log |

Variabel `EMBEDDING_*` hanya berpengaruh jika bagian `embedding` dibuat, yaitu saat file config memuat kunci `embedding` atau saat `from_env` menemukan `EMBEDDING_API_KEY`.

## Halaman terkait

- [Memanggil LLM dan embedding](../panduan/memanggil-llm-dan-embedding.md) untuk langkah pemakaian.
- [Helper kecil](helper.md) untuk `AIService` versi ringkas di `zul.utilities.script_helper.ai_models`.
- [Environment variable](konfigurasi.md) untuk variabel yang dipakai proyek hasil `zul build hexa`.
