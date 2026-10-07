# Environment variable

Proyek hasil `zul build hexa` membaca lima environment variable: tiga untuk chat model dan dua untuk playground. File pendukungnya di root proyek adalah `.env.example`, `requirements.txt`, `requirements-dev.txt`, dan `pytest.ini`.

| Variabel | Wajib | Default | Dibaca oleh |
|---|---|---|---|
| [`OPENAI_API_KEY`](#openai_api_key) | Ya | Tidak ada | `get_llm_model()` |
| [`LLM_MODEL`](#llm_model) | Tidak | `gpt-4o-mini` | `get_llm_model()` |
| [`LLM_BASE_URL`](#llm_base_url) | Tidak | Endpoint OpenAI | `get_llm_model()` |
| [`PLAYGROUND_ENABLED`](#playground_enabled) | Tidak | Mati | `playground_enabled()` |
| [`PLAYGROUND_ORIGINS`](#playground_origins) | Tidak | `https://zulkit.my.id`, `http://127.0.0.1:8001`, dan `http://localhost:8001` | `playground_origins()` |

`get_llm_model()` ada di `src/infrastructure/AI/llm/openai.py`. `playground_enabled()` dan `playground_origins()` ada di `src/interface/playground/settings.py`.

## Cara nilai dimuat

Kedua modul di atas memanggil `load_dotenv()` dari `python-dotenv` saat diimpor. Pemanggilan itu memuat file `.env` di root proyek:

```python title="src/infrastructure/AI/llm/openai.py"
from dotenv import load_dotenv

load_dotenv()
```

Variabel yang sudah diset di shell atau di container tidak ditimpa oleh isi `.env`.

## `OPENAI_API_KEY`

API key untuk chat model.

| Sifat | Nilai |
|---|---|
| Wajib | Ya |
| Default | Tidak ada |
| Diperiksa | Setiap kali `get_llm_model()` dipanggil |

Jika variabel ini tidak ada atau kosong, `get_llm_model()` melempar `ValueError` dengan pesan berikut:

```text
OPENAI_API_KEY not found! Please set it in .env file or environment variables
```

Agent baru dirakit pada request chat pertama, bukan saat server mulai. Karena itu server tetap bisa dijalankan tanpa key: `GET /health` menjawab `200`, sedangkan endpoint chat menjawab `500`.

## `LLM_MODEL`

Nama model yang dipakai semua agent.

| Sifat | Nilai |
|---|---|
| Wajib | Tidak |
| Default | `gpt-4o-mini`, yaitu konstanta `DEFAULT_MODEL` |

Argumen `model` pada `get_llm_model(model=...)` didahulukan daripada variabel ini. Model yang dipilih harus mendukung tool calling, karena semua agent di template bergantung padanya.

## `LLM_BASE_URL`

Alamat endpoint yang kompatibel dengan OpenAI, misalnya vLLM, LiteLLM, atau Ollama.

| Sifat | Nilai |
|---|---|
| Wajib | Tidak |
| Default | Endpoint OpenAI |

Nilai kosong diperlakukan sama dengan variabel yang tidak diset. `OPENAI_API_KEY` tetap wajib ada walaupun `LLM_BASE_URL` menunjuk ke server lain.

## `PLAYGROUND_ENABLED`

Menyalakan endpoint `/playground/*`.

| Sifat | Nilai |
|---|---|
| Wajib | Tidak |
| Default | Mati |
| Nilai yang berarti menyala | `1`, `true`, `yes`, `on` |

Huruf besar dan kecil tidak dibedakan, dan spasi di awal dan akhir nilai dibuang. Nilai lain, termasuk nilai kosong, berarti mati.

Variabel ini dibaca sekali saat `src/interface/http/main.py` diimpor. Jika menyala, aplikasi mendaftarkan router playground dan memasang aturan CORS:

```python title="src/interface/http/main.py"
if playground_enabled():
    app.include_router(playground.router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=playground_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
```

Jika mati, setiap request ke `/playground/*` menjawab `404`. Endpoint playground dijelaskan di [Referensi Playground API](playground-api.md).

> [!WARNING]
> Playground menampilkan argumen dan hasil setiap tool, jadi nilai untuk lingkungan produksi adalah `PLAYGROUND_ENABLED=false`.

## `PLAYGROUND_ORIGINS`

Daftar alamat halaman yang boleh memanggil API dari browser, dipisah koma. Variabel ini hanya berpengaruh saat `PLAYGROUND_ENABLED` menyala.

| Sifat | Nilai |
|---|---|
| Wajib | Tidak |
| Default | `https://zulkit.my.id,http://127.0.0.1:8001,http://localhost:8001` |
| Format | Satu atau lebih alamat, dipisah koma |

Nilai bawaannya adalah alamat situs dokumentasi Zul: yang sudah terbit di `zulkit.my.id`, dan yang dijalankan di komputermu dengan `mkdocs serve`. Browser menganggap `127.0.0.1` dan `localhost` sebagai alamat yang berbeda, sehingga keduanya didaftarkan.

Spasi di sekitar setiap alamat dan garis miring di akhir alamat dibuang. Entri kosong dilewati. Jika tidak ada alamat yang tersisa, nilai bawaan dipakai.

Contoh berikut mengizinkan situs dokumentasi lokal dan satu alamat yang sudah dipublikasikan:

```ini title=".env"
PLAYGROUND_ORIGINS=http://127.0.0.1:8001,ALAMAT_DOKUMENTASI
```

`ALAMAT_DOKUMENTASI` adalah alamat situs dokumentasimu, misalnya `https://docs.example.com`.

Aturan CORS ini mengizinkan method `GET` dan `POST` dan header `Content-Type`.

## File `.env.example`

Template menyertakan `.env.example` sebagai titik awal file `.env`. Isinya adalah sebagai berikut:

```ini title=".env.example"
# Salin file ini menjadi .env lalu isi nilainya. Jangan commit .env.
OPENAI_API_KEY=

# Opsional
LLM_MODEL=gpt-4o-mini
# LLM_BASE_URL=https://api.openai.com/v1

# Playground: mencoba agent dari halaman dokumentasi Zul.
# Ia menampilkan argumen dan hasil setiap tool, jadi matikan di produksi.
PLAYGROUND_ENABLED=true
# Alamat halaman yang boleh memanggil API ini dari browser, dipisah koma.
# PLAYGROUND_ORIGINS=https://zulkit.my.id,http://127.0.0.1:8001,http://localhost:8001
```

File ini mengisi `PLAYGROUND_ENABLED=true`. Jadi `.env` yang disalin darinya menyalakan playground, walaupun nilai bawaan variabel itu mati. File `.env` sudah tercantum di `.gitignore` template.

## File `requirements.txt`

Dependency untuk menjalankan aplikasi. Isinya adalah sebagai berikut:

```text title="requirements.txt"
fastapi>=0.115
uvicorn[standard]>=0.30
langchain>=1.0
langchain-openai>=1.0.2
langgraph>=1.0.6
openai>=1.0
pydantic>=2.0
python-dotenv>=1.0
streamlit>=1.51
```

| Package | Dipakai untuk |
|---|---|
| `fastapi` | REST API di `src/interface/http/`. |
| `uvicorn[standard]` | Server yang menjalankan aplikasi FastAPI. |
| `langchain` | Tipe pesan, dekorator `@tool`. |
| `langchain-openai` | `ChatOpenAI` di `get_llm_model()`. |
| `langgraph` | Graph agent, checkpointer, dan `interrupt()`. |
| `openai` | Halaman utama Streamlit, yang memanggil OpenAI langsung. |
| `pydantic` | Model request dan respons. |
| `python-dotenv` | Memuat file `.env`. |
| `streamlit` | UI contoh di `src/interface/streamlit/`. |

## File `requirements-dev.txt`

Dependency aplikasi ditambah tool test. Isinya adalah sebagai berikut:

```text title="requirements-dev.txt"
-r requirements.txt
pytest>=8.0
httpx>=0.27
```

| Package | Dipakai untuk |
|---|---|
| `pytest` | Menjalankan test di folder `test/`. |
| `httpx` | Dibutuhkan `TestClient` FastAPI saat menguji endpoint. |

## File `pytest.ini`

Pengaturan pytest untuk proyek. Isinya adalah sebagai berikut:

```ini title="pytest.ini"
[pytest]
# Root proyek masuk ke sys.path supaya test bisa `from src... import ...`
pythonpath = .
testpaths = test
```

| Kunci | Nilai | Akibat |
|---|---|---|
| `pythonpath` | `.` | Root proyek masuk ke path impor, sehingga test bisa menulis `from src... import ...`. |
| `testpaths` | `test` | `pytest` tanpa argumen mencari test di folder `test/`. |

## Pengaturan lain

Pengaturan yang merupakan keputusan rancangan ditulis sebagai konstanta Python, bukan environment variable. Contohnya `MAX_AGENT_STEPS`, `TOOLS_REQUIRING_APPROVAL`, dan `SUBAGENTS`. Semuanya dicantumkan di [Referensi API agent](agent.md).

Helper di `zul.utilities` membaca environment variable miliknya sendiri. Rinciannya ada di [Referensi AI Service](ai-service.md) dan [Referensi OCR](ocr.md).

## Halaman terkait

- [Panduan: Mengatur model dan API key](../panduan/mengatur-llm.md)
- [Panduan: Menjalankan aplikasi](../panduan/menjalankan-aplikasi.md)
- [Panduan: Mencoba fitur di playground](../panduan/mencoba-di-playground.md)
- [Referensi: Playground API](playground-api.md)
- [Referensi: Struktur proyek hexa](struktur-proyek.md)
