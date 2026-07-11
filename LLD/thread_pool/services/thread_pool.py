"""Fixed-size thread pool.

N worker threads share one task queue. submit() enqueues a callable and returns
a Future; an idle worker picks it up, runs it, and stores the result/exception
on the Future. shutdown() puts one sentinel per worker so each drains remaining
tasks (FIFO) and then exits cleanly.
"""
from __future__ import annotations

import queue
import threading
from typing import Callable

from models.future import Future

# Sentinel enqueued to tell a worker to stop.
_SHUTDOWN = object()


class ThreadPool:
    def __init__(self, num_workers: int = 4, capacity: int = 0) -> None:
        """num_workers: number of worker threads.
        capacity: max queued tasks (0 = unbounded). Bounded => submit() applies
        backpressure by blocking when full.
        """
        if num_workers < 1:
            raise ValueError("num_workers must be >= 1")

        self._tasks: queue.Queue = queue.Queue(maxsize=capacity)
        self._lock = threading.Lock()
        self._closed = False
        self._workers = [
            threading.Thread(target=self._worker, name=f"worker-{i}", daemon=True)
            for i in range(num_workers)
        ]
        for w in self._workers:
            w.start()

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        with self._lock:
            if self._closed:
                raise RuntimeError("ThreadPool is shut down")
        future = Future()
        self._tasks.put((future, fn, args, kwargs))
        return future

    def _worker(self) -> None:
        while True:
            item = self._tasks.get()
            if item is _SHUTDOWN:
                return
            future, fn, args, kwargs = item
            try:
                future.set_result(fn(*args, **kwargs))
            except Exception as exc:  # a failed task must not kill the worker
                future.set_exception(exc)

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True

        for _ in self._workers:      # one sentinel per worker
            self._tasks.put(_SHUTDOWN)
        if wait:
            for w in self._workers:
                w.join()

    def __enter__(self) -> "ThreadPool":
        return self

    def __exit__(self, *_exc) -> None:
        self.shutdown()
