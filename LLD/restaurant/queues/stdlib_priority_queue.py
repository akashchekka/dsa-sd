"""Thread-safe blocking priority queue backed by the stdlib queue.PriorityQueue.

Same interface as CustomPriorityQueue (put / get / close) so Restaurant can use
either interchangeably. queue.PriorityQueue already handles the locking and
blocking for us; we only add:

- a (priority, seq, item) tuple so equal-priority items stay FIFO and the item
  objects are never compared, and
- a self-propagating sentinel for graceful shutdown: close() enqueues one
  _SHUTDOWN marker (lowest priority, so real orders drain first); whichever
  consumer pulls it returns None and puts it back for the next consumer.
"""
from __future__ import annotations

import itertools
import queue
from typing import Any

_SHUTDOWN = object()


class StdlibPriorityQueue:
    def __init__(self) -> None:
        self._pq: queue.PriorityQueue = queue.PriorityQueue()
        self._counter = itertools.count()          # tie-breaker => stable FIFO

    def put(self, item: Any, priority: int) -> None:
        self._pq.put((priority, next(self._counter), item))

    def get(self) -> Any | None:
        priority, seq, item = self._pq.get()
        if item is _SHUTDOWN:
            self._pq.put((priority, seq, item))    # Self Propagating Poison Pill(Sentinel) for stopping other cooks
            return None                            # drained + closed => stop signal
        return item

    def close(self) -> None:
        # float('inf') priority => the sentinel sorts after every real order,
        # so all queued orders are cooked before any consumer sees shutdown.
        self._pq.put((float("inf"), next(self._counter), _SHUTDOWN))
