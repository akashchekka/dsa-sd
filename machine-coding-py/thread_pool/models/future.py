"""A minimal Future: a handle to a result that will be produced later by a
worker thread. The caller blocks on result() until the worker sets the outcome.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

class Future:
    def __init__(self) -> None:
        self._done = threading.Event()
        self._result: Any = None
        self._exception: Optional[BaseException] = None

    def set_result(self, value: Any) -> None:
        self._result = value
        self._done.set()

    def set_exception(self, exc: BaseException) -> None:
        self._exception = exc
        self._done.set()

    def result(self, timeout: Optional[float] = None) -> Any:
        # Event.wait() returns True if the flag was set, False if it timed out.
        finished = self._done.wait(timeout)
        if not finished:
            raise TimeoutError("result not ready")
        if self._exception is not None:
            raise self._exception
        return self._result
