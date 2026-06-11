"""Owns one daemon worker per topic. Bus calls register() at topic creation
and shutdown() at teardown."""
from __future__ import annotations

from core.topic           import Topic
from workers.topic_worker import TopicWorker


class Dispatcher:
    def __init__(self) -> None:
        self._workers: list[TopicWorker] = []

    def register(self, topic: Topic) -> None:
        worker = TopicWorker(topic)
        self._workers.append(worker)
        worker.start()

    def deliver(self, topic: Topic, message) -> None:
        topic.inbox.put(message)   # blocks when inbox is full

    def shutdown(self, timeout: float = 5.0) -> None:
        for w in self._workers: w.stop()
        for w in self._workers: w.join(timeout=timeout)
