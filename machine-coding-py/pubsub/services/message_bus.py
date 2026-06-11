"""Thread-safe bus. DCL on topic dict; delegates delivery to Dispatcher."""
from __future__ import annotations

import threading

from core.dispatcher       import Dispatcher
from core.topic            import Topic
from interfaces.subscriber import Subscriber
from models.message        import Message


class InMemoryMessageBus:
    def __init__(self) -> None:
        self._dispatcher = Dispatcher()
        self._topics: dict[str, Topic] = {}
        self._lock = threading.Lock()
        self._closed = False

    def _get_or_create_topic(self, name: str) -> Topic:
        topic = self._topics.get(name)                       # lock-free fast path
        if topic is not None:
            return topic
        with self._lock:
            if self._closed:
                raise RuntimeError("MessageBus is shut down")
            topic = self._topics.get(name)
            if topic is not None:
                return topic
            topic = Topic(name)
            self._topics[name] = topic
            self._dispatcher.register(topic)
            return topic

    def subscribe(self, topic_name: str, subscriber: Subscriber) -> None:
        self._get_or_create_topic(topic_name).add_subscriber(subscriber)

    def unsubscribe(self, topic_name: str, subscriber: Subscriber) -> None:
        topic = self._topics.get(topic_name)
        if topic is not None:
            topic.remove_subscriber(subscriber)

    def publish(self, topic_name: str, payload: object) -> Message:
        if self._closed:
            raise RuntimeError("MessageBus is shut down")
        topic = self._get_or_create_topic(topic_name)
        msg   = Message(payload=payload, topic=topic_name)
        self._dispatcher.deliver(topic, msg)
        return msg

    def shutdown(self, timeout: float = 5.0) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._dispatcher.shutdown(timeout=timeout)

    def __enter__(self) -> "InMemoryMessageBus":
        return self

    def __exit__(self, *_exc) -> None:
        self.shutdown()
