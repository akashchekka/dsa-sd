"""A topic: owns its subscribers, an inbox queue, and one worker thread.

One worker per topic gives two useful guarantees:
  * publishers never block on slow subscribers (delivery is async), and
  * messages on the same topic are delivered in FIFO order.
Topics are independent, so a slow subscriber on one topic cannot stall another.
"""
from __future__ import annotations

import queue
import threading

from interfaces.subscriber import Subscriber
from models.message import Message


# Sentinel pushed onto the queue to tell the worker to stop.
_SHUTDOWN = object()


class Topic:
    def __init__(self, name: str, capacity: int = 0) -> None:
        """capacity: max queued messages (0 = unbounded). A bounded queue lets
        publishers apply backpressure instead of growing memory without limit.
        """
        self._name = name
        self._subscribers: set[Subscriber] = set()
        self._lock = threading.Lock()
        self._inbox: queue.Queue = queue.Queue(maxsize=capacity)
        self._worker = threading.Thread(
            target=self._run, name=f"topic-{name}", daemon=True
        )
        self._worker.start()

    def add_subscriber(self, subscriber: Subscriber) -> None:
        with self._lock:
            self._subscribers.add(subscriber)

    def remove_subscriber(self, subscriber: Subscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, message: Message, block: bool = True, timeout: float | None = None) -> None:
        # On an unbounded queue this never blocks or raises. On a bounded queue,
        # block=True waits for space (backpressure); block=False raises queue.Full.
        self._inbox.put(message, block=block, timeout=timeout)

    def _run(self) -> None:
        while True:
            item = self._inbox.get()
            if item is _SHUTDOWN:
                return
            self._deliver(item)

    def _deliver(self, message: Message) -> None:
        # Snapshot under the lock so subscribe/unsubscribe can run concurrently.
        with self._lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            try:
                subscriber.on_message(message)
            except Exception as exc:  # isolate: one bad subscriber can't break others
                print(f"[topic-{self._name}] subscriber {subscriber!r} failed: {exc}")

    def shutdown(self) -> None:
        self._inbox.put(_SHUTDOWN)

    def join(self, timeout: float | None = None) -> None:
        self._worker.join(timeout)
