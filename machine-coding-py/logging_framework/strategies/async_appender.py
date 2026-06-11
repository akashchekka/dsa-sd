"""Decorator: wraps any ILogAppender and pushes writes off the hot path.
One background daemon thread drains the queue.
Overflow strategy: drop oldest then add (configurable in real impl)."""
from __future__ import annotations

import queue
import threading
import traceback
from datetime import datetime, timezone

from interfaces.log_appender import ILogAppender
from models.log_event        import LogEvent
from models.log_level        import LogLevel


class AsyncAppender(ILogAppender):
    _SENTINEL: LogEvent = LogEvent(datetime.min.replace(tzinfo=timezone.utc),
                                   LogLevel.DEBUG, "_", "_", None)

    def __init__(self, inner: ILogAppender, capacity: int = 1024) -> None:
        self._inner  = inner
        self._queue: queue.Queue[LogEvent] = queue.Queue(maxsize=capacity)
        self._worker = threading.Thread(target=self._drain, daemon=True)
        self._worker.start()

    def append(self, event: LogEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            # Overflow strategy: drop oldest, then add.
            try:    self._queue.get_nowait()
            except queue.Empty: pass
            try:    self._queue.put_nowait(event)
            except queue.Full:  pass

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
        except queue.Full:
            try:    self._queue.get_nowait()
            except queue.Empty: pass
            self._queue.put_nowait(self._SENTINEL)
        self._worker.join(timeout=timeout)

    def __enter__(self) -> "AsyncAppender": return self
    def __exit__(self, *exc: object) -> None: self.close()
