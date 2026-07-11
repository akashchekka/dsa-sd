from __future__ import annotations

import heapq
import itertools
import threading
from typing import Any

class CustomPriorityQueue:
    def __init__(self) -> None:
        self._heap: list[tuple[int, int, Any]] = []
        self._counter = itertools.count()          # tie-breaker => stable FIFO
        self._cond = threading.Condition()
        self._closed = False

    def put(self, item: Any, priority: int) -> None:
        with self._cond:
            if self._closed:
                raise RuntimeError("Queue is closed")
            heapq.heappush(self._heap, (priority, next(self._counter), item))
            self._cond.notify()                    # wake one waiting consumer

    def get(self) -> Any | None:
        with self._cond:
            while not self._heap:
                if self._closed:
                    return None                    # drained + closed => stop signal
                self._cond.wait()
            _, _, item = heapq.heappop(self._heap)
            return item

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify_all()                # wake every blocked consumer
