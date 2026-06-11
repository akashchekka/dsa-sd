"""A named channel: subscriber set + bounded inbox."""
from __future__ import annotations

import threading

from core.bounded_inbox    import BoundedInbox
from interfaces.subscriber import Subscriber


class Topic:
    def __init__(self, name: str, inbox_capacity: int = 1024) -> None:
        self.name  = name
        self.inbox = BoundedInbox(capacity=inbox_capacity)
        self._subscribers: set[Subscriber] = set()
        self._lock = threading.Lock()

    def add_subscriber(self, sub: Subscriber) -> None:
        with self._lock:
            self._subscribers.add(sub)

    def remove_subscriber(self, sub: Subscriber) -> None:
        with self._lock:
            self._subscribers.discard(sub)

    def get_subscribers(self) -> list[Subscriber]:
        with self._lock:
            return list(self._subscribers)
