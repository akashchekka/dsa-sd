"""Per-topic daemon worker. Event for stop, Condition (in inbox) for work.

`_stop_event` not `_stop` — `Thread._stop` is a private method; shadowing it
breaks join().
"""
from __future__ import annotations

import threading

from core.topic import Topic


class TopicWorker(threading.Thread):
    _POLL = 0.1

    def __init__(self, topic: Topic) -> None:
        super().__init__(daemon=True, name=f"topic-worker-{topic.name}")
        self._topic      = topic
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()
        self._topic.inbox.close()

    def run(self) -> None:
        # Graceful drain: pull first, exit only when empty AND stopped.
        while True:
            msg = self._topic.inbox.get(timeout=self._POLL)
            if msg is not None:
                self._fanout(msg)
            elif self._stop_event.is_set():
                return

    def _fanout(self, msg) -> None:
        for sub in self._topic.get_subscribers():
            try:
                sub.consume(msg)
            except Exception as ex:
                print(f"[{self.name}] {sub} failed: {ex}")
