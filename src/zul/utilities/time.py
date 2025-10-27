from time import time

# def timer_func(func):
#     # This function shows the execution time of
#     # the function object passed
#     def wrap_func(*args, **kwargs):
#         t1 = time()
#         result = func(*args, **kwargs)
#         t2 = time()
#         print(f"Function {func.__name__!r} executed in {(t2-t1):.4f}s")
#         return result

#     return wrap_func


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

