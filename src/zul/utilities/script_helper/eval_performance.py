"""
Decorator pengukur waktu eksekusi.

Gunanya:
    Mengukur berapa lama sebuah fungsi berjalan, misalnya untuk
    membandingkan latency pencarian di Milvus dan Redis.

Cara pakai:
    from zul.utilities.script_helper.eval_performance import TimerDecorator, timer_func

    @timer_func                      # cukup cetak durasi tiap pemanggilan
    def ingest(): ...

    @TimerDecorator                  # simpan histori untuk dianalisis
    def search(query): ...

    for query in queries:
        search(query)

    search.get_average_time()        # rata-rata dalam detik
    search.get_all_times()           # daftar semua durasi
    search.reset_times()

Contoh:
    Mengukur QPS (query per second) sebuah vector database. Durasi satu
    query belum menggambarkan throughput, jadi langkahnya:

    1. Siapkan query vector.
    2. Jalankan ribuan query secara paralel (multi-thread atau async).
    3. Bagi total query dengan total waktu, hasilnya QPS.
    4. Analisis juga distribusi latency-nya (rata-rata, P95, P99).

    Milvus (asumsi sudah connect dan collection-nya sudah ada):

        import time
        from concurrent.futures import ThreadPoolExecutor

        import numpy as np
        from pymilvus import Collection

        collection = Collection("doc_vectors")

        def query():
            q_vec = np.random.random((1, 768)).tolist()
            _ = collection.search(q_vec, "embedding", params={"ef": 32}, limit=5)

        n_queries = 1000
        n_workers = 10

        start = time.time()
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            executor.map(lambda _: query(), range(n_queries))
        end = time.time()

        qps = n_queries / (end - start)
        print(f"Throughput: {qps:.2f} QPS")

    Redis: uji paralelnya sama persis, hanya fungsi query() yang berbeda.

        r = redis.Redis(host="localhost", port=6379)

        def query():
            q_vec = np.random.random(768).astype(np.float32).tobytes()
            _ = r.execute_command(
                "FT.SEARCH", "doc_idx",
                "*=>[KNN 5 @embedding $vec]",
                "PARAMS", "2", "vec", q_vec,
                "SORTBY", "__embedding_score",
                "DIALECT", "2",
            )
"""

from functools import update_wrapper, wraps
from time import perf_counter

# --------------------------------------------------------------------------
# Timer Sekali Cetak
# --------------------------------------------------------------------------


def timer_func(func):
    """Decorator: print durasi eksekusi fungsi setiap kali dipanggil."""

    @wraps(func)
    def wrap_func(*args, **kwargs):
        t1 = perf_counter()
        result = func(*args, **kwargs)
        t2 = perf_counter()
        print(f"Function {func.__name__!r} executed in {(t2-t1):.4f}s")
        return result

    return wrap_func


# --------------------------------------------------------------------------
# Timer dengan Histori
# --------------------------------------------------------------------------
#
# Decorator ini berbentuk kelas supaya durasi setiap pemanggilan
# dapat disimpan di objeknya. Histori itu yang dipakai untuk
# mencari rata-rata setelah fungsi dipanggil berkali-kali.
#


class TimerDecorator:
    """
    Decorator yang menyimpan histori waktu eksekusi fungsi.

    Contoh:
        @TimerDecorator
        def search(query): ...

        search("a"); search("b")
        search.get_average_time()
    """

    def __init__(self, func):
        self.func = func
        self.times = []
        self.total_time = 0
        self.call_count = 0
        # Salin __name__, __doc__, dsb. dari fungsi asli
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        t1 = perf_counter()
        result = self.func(*args, **kwargs)
        t2 = perf_counter()
        execution_time = t2 - t1

        # Store timing data
        self.times.append(execution_time)
        self.total_time += execution_time
        self.call_count += 1

        print(f"Function {self.func.__name__!r} executed in {execution_time:.4f}s")
        return result

    def get_last_time(self):
        return self.times[-1] if self.times else None

    def get_all_times(self):
        return self.times.copy()

    def get_average_time(self):
        return self.total_time / self.call_count if self.call_count > 0 else 0

    def reset_times(self):
        self.times = []
        self.total_time = 0
        self.call_count = 0
