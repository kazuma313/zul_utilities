# Menyimpan percakapan di database

Penyimpan percakapan bawaan bisa diganti dengan PostgreSQL, sehingga percakapan bertahan setelah server berhenti dan bisa dibagi antar proses.

**Sebelum mulai:** kamu punya database PostgreSQL yang bisa dihubungi dari aplikasi, beserta alamat koneksinya.

## Kenapa perlu diganti

Template memakai `InMemorySaver`, yang menyimpan percakapan di memori proses. Itu cocok untuk pengembangan, tetapi punya tiga akibat:

- Percakapan hilang saat server berhenti atau dimulai ulang.
- Percakapan tidak dibagi antar proses. Dengan beberapa worker, pesan berikutnya bisa mendarat di worker yang tidak punya percakapannya.
- Aksi human-in-the-loop yang sedang menunggu keputusan ikut hilang bersama percakapannya.

## Langkah-langkah

Contoh ini mengikuti [dokumentasi LangGraph tentang memory](https://docs.langchain.com/oss/python/langgraph/add-memory).

1. Pasang paket checkpointer PostgreSQL dan tambahkan keduanya ke `requirements.txt`:

    ```shell
    pip install -U "psycopg[binary,pool]" langgraph-checkpoint-postgres
    ```

2. Buat checkpointer dari alamat database, lalu berikan ke perakit agent:

    ```python
    from langgraph.checkpoint.postgres import PostgresSaver

    DB_URI = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=disable"

    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        agent = build_react_agent(llm=llm, tools=tools, checkpointer=checkpointer)
        ...
    ```

    Ganti `USER`, `PASSWORD`, `HOST`, dan `DATABASE` dengan nilai milikmu. Baca alamat itu dari environment variable; jangan menulis password di kode.

3. Panggil `checkpointer.setup()` sekali. Method itu membuat tabel yang dibutuhkan checkpointer.

Checkpointer hanya hidup di dalam blok `with`. Di aplikasi FastAPI, buka blok itu saat aplikasi mulai dan tutup saat berhenti, lalu berikan checkpointer-nya ke fungsi perakit agent di controller. Fungsi yang sekarang membuat checkpointer adalah `get_checkpointer()` di `src/infrastructure/AI/memory/checkpointer.py`.

## Memeriksa hasilnya

1. Kirim pesan dan catat `thread_id` dari responsnya:

    ```shell
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"Saya Bob\"}"
    ```

2. Hentikan server, lalu jalankan lagi.

3. Lanjutkan percakapan dengan `thread_id` tadi:

    ```shell
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"Siapa nama saya?\", \"thread_id\": \"THREAD_ID\"}"
    ```

    Ganti `THREAD_ID` dengan nilai dari langkah pertama. Jika checkpointer database bekerja, agent masih menyebut nama Bob.

## Melihat isi percakapan yang tersimpan

Saat debugging, baca state sebuah thread dengan `get_state`:

```python
snapshot = agent.get_state({"configurable": {"thread_id": "user-42"}})

for message in snapshot.values["messages"]:
    print(type(message).__name__, message.content)
```

Untuk thread yang belum pernah dipakai, `snapshot.values` berupa dict kosong.

## Halaman terkait

- [Memory dan thread](../konsep/memory.md) untuk cara kerja checkpointer, pilihan `thread_id`, dan batasan yang tetap ada setelah pindah ke database.
- [API agent](../referensi/agent.md) untuk `get_checkpointer` dan parameter `checkpointer` di setiap perakit agent.
