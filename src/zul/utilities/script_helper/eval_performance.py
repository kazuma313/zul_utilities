from time import time

def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f"Function {func.__name__!r} executed in {(t2-t1):.4f}s")
        return result

    return wrap_func


class TimerDecorator:
    def __init__(self, func):
        self.func = func
        self.times = []
        self.total_time = 0
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        t1 = time()
        result = self.func(*args, **kwargs)
        t2 = time()
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



## Dari babang GPT
# import time
# import numpy as np
# from pymilvus import Collection
# from concurrent.futures import ThreadPoolExecutor

# # asumsi sudah connect ke milvus & ada collection
# collection = Collection("doc_vectors")

# def query():
#     q_vec = np.random.random((1, 768)).tolist()
#     _ = collection.search(q_vec, "embedding", params={"ef": 32}, limit=5)

# # uji parallel query
# n_queries = 1000
# n_workers = 10

# start = time.time()
# with ThreadPoolExecutor(max_workers=n_workers) as executor:
#     executor.map(lambda _: query(), range(n_queries))
# end = time.time()

# qps = n_queries / (end - start)
# print(f"Throughput: {qps:.2f} QPS")



# r = redis.Redis(host="localhost", port=6379)

# def query():
#     q_vec = np.random.random(768).astype(np.float32).tobytes()
#     _ = r.execute_command(
#         "FT.SEARCH", "doc_idx",
#         f"*=>[KNN 5 @embedding $vec]",
#         "PARAMS", "2", "vec", q_vec,
#         "SORTBY", "__embedding_score",
#         "DIALECT", "2"
#     )

# # uji parallel query
# n_queries = 1000
# n_workers = 10

# start = time.time()
# with ThreadPoolExecutor(max_workers=n_workers) as executor:
#     executor.map(lambda _: query(), range(n_queries))
# end = time.time()

# qps = n_queries / (end - start)
# print(f"Throughput: {qps:.2f} QPS")



# # Siapkan query vector.

# # 1. Jalankan ribuan query secara paralel (multi-thread/async).
# # 2. Hitung total query ÷ total waktu → dapat QPS.
# # 3. Analisis juga distribusi latency (avg, P95, P99).