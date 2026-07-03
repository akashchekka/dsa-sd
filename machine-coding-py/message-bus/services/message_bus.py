"""In-memory pub/sub message bus.

Public API:
    subscribe(topic, subscriber)
    unsubscribe(topic, subscriber)
    publish(topic, payload) -> Message
    shutdown()

Topics are created lazily on first subscribe/publish. Delivery is asynchronous
(handled by each topic's worker thread), so publish() returns immediately.
"""
from __future__ import annotations

import threading

from interfaces.subscriber import Subscriber
from models.message import Message
from services.topic import Topic


class MessageBus:
    def __init__(self, topic_capacity: int = 0) -> None:
        """topic_capacity: max queued messages per topic (0 = unbounded).

        When bounded, publish() applies backpressure (see publish()).
        """
        self._topics: dict[str, Topic] = {}
        self._lock = threading.Lock()
        self._closed = False
        self._topic_capacity = topic_capacity

    def _get_or_create_topic(self, name: str) -> Topic:
        if self._closed:
            raise RuntimeError("MessageBus is shut down")
        # Fast path: dict.get is atomic, so avoid locking when the topic exists.
        topic = self._topics.get(name)
        if topic is not None:
            return topic

        with self._lock:
            if self._closed:
                raise RuntimeError("MessageBus is shut down")
            topic = self._topics.get(name)  # re-check under lock
            if topic is None:
                topic = Topic(name, capacity=self._topic_capacity)
                self._topics[name] = topic
            return topic

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._get_or_create_topic(topic).add_subscriber(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        existing = self._topics.get(topic)
        if existing is not None:
            existing.remove_subscriber(subscriber)

    def publish(
        self,
        topic: str,
        payload: object,
        block: bool = True,
        timeout: float | None = None,
    ) -> Message:
        if self._closed:
            raise RuntimeError("MessageBus is shut down")
        message = Message(topic=topic, payload=payload)
        self._get_or_create_topic(topic).publish(message, block=block, timeout=timeout)
        return message

    def shutdown(self, timeout: float = 5.0) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            topics = list(self._topics.values())

        for topic in topics:            # signal every worker to drain and stop
            topic.shutdown()
        for topic in topics:            # then wait for them to finish
            topic.join(timeout)

    def __enter__(self) -> "MessageBus":
        return self

    def __exit__(self, *_exc) -> None:
        self.shutdown()
