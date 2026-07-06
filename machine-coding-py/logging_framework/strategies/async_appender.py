"""Decorator: wraps any ILogAppender and pushes writes off the hot path.
One background daemon thread drains the
Overflow strategy: drop oldest then add (configurable in real impl)."""
from __future__ import annotations

from queue import Full, Empty, Queue
import threading
import traceback

from interfaces.log_appender import ILogAppender
from models.log_event        import LogEvent

class AsyncAppender(ILogAppender):
    _SENTINEL = object()

    def __init__(self, inner: ILogAppender, capacity: int = 1024) -> None:
        self._inner  = inner
        self._queue:Queue[LogEvent] =Queue(maxsize=capacity)
        self._worker = threading.Thread(target=self._drain, daemon=True)
        self._worker.start()

    def append(self, event: LogEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except Full:
            # Overflow strategy: drop oldest, then add.
            try:    self._queue.get_nowait()
            except Empty: pass
            try:    self._queue.put_nowait(event)
            except Full:  pass

    def _drain(self) -> None:
        while True:
            event = self._queue.get()
            if event is self._SENTINEL:
                return
            try:
                self._inner.append(event)
            except Exception:                          # never let a sink kill the worker
                traceback.print_exc()

    def close(self, timeout: float = 2.0) -> None:
        try:    self._queue.put_nowait(self._SENTINEL)
        except Full:
            try:    self._queue.get_nowait()
            except Empty: pass
            self._queue.put_nowait(self._SENTINEL)
        self._worker.join(timeout=timeout)

    def __enter__(self) -> "AsyncAppender":
        return self
    
    def __exit__(self, *exc: object) -> None:
        self.close()
