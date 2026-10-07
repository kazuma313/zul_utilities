# Memanggil LLM dan embedding

`AIService` memanggil chat model dan model embedding yang kompatibel dengan OpenAI. Pengaturannya ditulis sekali, di file config atau environment variable, lalu `chat()` dan `embed()` dipanggil dari script, notebook, atau pipeline data.

**Sebelum mulai:** kamu butuh Zul yang sudah terpasang ([Memasang Zul](memasang-zul.md)), alamat endpoint yang kompatibel dengan OpenAI, dan API key-nya. `AIService` membutuhkan extra `llm`:

```shell
pip install "zul[llm] @ git+https://github.com/kazuma313/zul_utilities.git"
```

## Membuat service dari file config

1. Tulis file config di folder proyek:

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
      log_level: "INFO"
    ```

    File JSON dengan struktur yang sama juga diterima. Format dipilih dari ekstensi file.

2. Simpan API key di environment, bukan di file:

    ```shell
    export LLM_API_KEY=API_KEY
    export EMBEDDING_API_KEY=API_KEY
    ```

    Ganti `API_KEY` dengan key-mu. Di PowerShell, pakai `$env:LLM_API_KEY = "API_KEY"`.

3. Buat service dari file itu:

    ```python
    from zul.utilities.embedding_service import AIService

    service = AIService.from_file("config.yaml")
    ```

> [!NOTE]
> Tulis `base_url` secara eksplisit. Nilai bawaan `llm.base_url` menunjuk ke server internal, bukan ke OpenAI.

## Membuat service dari environment

Di container atau CI, kamu bisa melewati file config dan membaca semuanya dari environment.

1. Set pengaturan LLM di environment. `LLM_API_KEY` wajib ada:

    ```shell
    export LLM_BASE_URL=https://api.openai.com/v1
    export LLM_MODEL=gpt-4o-mini
    export LLM_API_KEY=API_KEY
    ```

2. Jika kamu butuh embedding, set juga pengaturannya. Embedding aktif hanya jika `EMBEDDING_API_KEY` diset:

    ```shell
    export EMBEDDING_BASE_URL=https://api.openai.com/v1
    export EMBEDDING_MODEL=text-embedding-3-small
    export EMBEDDING_API_KEY=API_KEY
    ```

3. Buat service tanpa file:

    ```python
    from zul.utilities.embedding_service import AIService

    service = AIService.from_env()
    ```

    Tanpa `EMBEDDING_API_KEY`, service hanya bisa `chat()`.

## Mengirim prompt ke LLM

1. Panggil `chat` dengan satu prompt:

    ```python
    response = service.chat("Apa ibu kota Indonesia?")
    ```

2. Baca jawabannya dari objek `ChatResponse` yang dikembalikan:

    ```python
    print(response.content)         # teks jawaban
    print(response.model)           # model yang menjawab
    print(response.finish_reason)   # misalnya "stop" atau "length"
    print(response.usage)           # jumlah token, jika API mengembalikannya
    ```

3. Tangani kegagalan. Jika request gagal, `chat` melempar `RuntimeError` yang memuat penyebabnya:

    ```python
    try:
        response = service.chat("Apa ibu kota Indonesia?")
    except RuntimeError as error:
        print(f"LLM tidak bisa dihubungi: {error}")
    ```

## Membuat embedding

1. Periksa apakah embedding tersedia di service ini:

    ```python
    if not service.is_embedding_enabled():
        raise SystemExit("Embedding belum dikonfigurasi")
    ```

2. Ubah satu teks menjadi vektor dengan `embed`:

    ```python
    response = service.embed("Jakarta adalah ibu kota Indonesia.")

    print(response.dimensions)   # panjang vektor
    print(response.vector[:3])   # tiga angka pertama
    ```

    `embed` melempar `ValueError` jika embedding tidak dikonfigurasi, dan `RuntimeError` jika request gagal.

## Menimpa nilai config lewat environment

Setiap nilai diambil dari sumber pertama yang menyediakannya: environment variable, lalu file config, lalu nilai bawaan. Karena itu satu file config bisa dipakai di semua environment.

1. Set variabel untuk nilai yang ingin kamu timpa, misalnya nama model:

    ```shell
    export LLM_MODEL=gpt-4o
    ```

2. Buat service dari file yang sama:

    ```python
    service = AIService.from_file("config.yaml")
    print(service.config.llm.model)
    ```

    Kode itu mencetak nilai dari environment, bukan dari file:

    ```text
    gpt-4o
    ```

    Daftar variabel yang dikenali ada di [Referensi AI Service](../referensi/ai-service.md).

## Memeriksa hasilnya

Untuk memastikan config terbaca dengan benar tanpa memanggil model, cetak ringkasannya. `safe_summary` mengganti setiap API key dengan `***`, jadi keluarannya aman untuk log:

```python
import json

print(json.dumps(service.config.safe_summary(), indent=2))
```

Untuk `config.yaml` di halaman ini, tanpa variabel penimpa seperti `LLM_MODEL`, kode itu mencetak:

```text
{
  "llm": {
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 2048,
    "timeout": 30,
    "api_key": "***"
  },
  "embedding": {
    "base_url": "https://api.openai.com/v1",
    "model": "text-embedding-3-small",
    "timeout": 30,
    "api_key": "***"
  },
  "service": {
    "enable_embedding": true,
    "log_level": "INFO"
  }
}
```

Lalu kirim satu prompt pendek dengan `service.chat("Halo")` dan pastikan `response.content` berisi jawaban.

## Halaman terkait

- [Referensi AI Service](../referensi/ai-service.md) untuk semua kunci config, environment variable, dan error.
- [Mengatur model dan API key](mengatur-llm.md) jika kamu ingin mengatur LLM untuk agent di proyek hasil `zul build hexa`, bukan untuk script.
- [Menyimpan dan mencari vektor di Milvus](memakai-milvus.md) untuk menyimpan vektor hasil `embed`.
