"""Bounded FIFO. Two Conditions share one Lock — classic
producer/consumer. close() wakes all waiters."""
from __future__ import annotations

import threading
from collections import deque
from typing import Optional


class BoundedInbox:
    def __init__(self, capacity: int = 1024) -> None:
        self._capacity  = capacity
        self._buf: deque = deque()
        self._lock      = threading.Lock()
        self._not_full  = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)
        self._closed    = False

    def put(self, item: object, timeout: Optional[float] = None) -> bool:
        with self._not_full:
            while len(self._buf) >= self._capacity and not self._closed:
                if not self._not_full.wait(timeout):
                    return False
            if self._closed:
                return False
            self._buf.append(item)
            self._not_empty.notify()
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[object]:
        with self._not_empty:
            while not self._buf and not self._closed:
                if not self._not_empty.wait(timeout):
                    return None
            if not self._buf:
                return None
            item = self._buf.popleft()
            self._not_full.notify()
            return item

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._not_full.notify_all()
            self._not_empty.notify_all()
