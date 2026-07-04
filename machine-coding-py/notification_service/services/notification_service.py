from __future__ import annotations

import itertools
import threading
from datetime import datetime, timezone

from interfaces.notification_channel import INotificationChannel
from interfaces.retry_policy         import IRetryPolicy
from models.notification             import Notification
from models.subscription             import Channel, Subscription
from services.topic                  import Topic


class NotificationService:
    def __init__(self, channels: list[INotificationChannel], retry: IRetryPolicy, topic_capacity: int = 0) -> None:
        self._channels: dict[Channel, INotificationChannel] = {c.kind: c for c in channels}
        self._retry            = retry
        self._topics: dict[str, Topic] = {}
        self._lock             = threading.Lock()
        self._closed           = False
        self._topic_capacity   = topic_capacity
        self._seq              = itertools.count(1)

    def _get_or_create_topic(self, name: str) -> Topic:
        if self._closed:
            raise RuntimeError("NotificationService is shut down")
        # Fast path: dict.get is atomic, so avoid locking when the topic exists.
        topic = self._topics.get(name)
        if topic is not None:
            return topic

        with self._lock:
            if self._closed:
                raise RuntimeError("NotificationService is shut down")
            topic = self._topics.get(name)  # re-check under lock
            if topic is None:
                topic = Topic(name, self._channels, self._retry, capacity=self._topic_capacity)
                self._topics[name] = topic
            return topic

    def subscribe(self, subscription: Subscription) -> None:
        self._get_or_create_topic(subscription.topic).add_subscription(subscription)

    def unsubscribe(self, subscription: Subscription) -> None:
        existing = self._topics.get(subscription.topic)
        if existing is not None:
            existing.remove_subscription(subscription)

    def publish(
        self,
        topic: str,
        body: str,
        block: bool = True,
        timeout: float | None = None,
    ) -> Notification:
        if self._closed:
            raise RuntimeError("NotificationService is shut down")
        with self._lock:
            seq = next(self._seq)
        note = Notification(id=f"N-{seq:05d}", topic=topic, body=body, created_at=datetime.now(timezone.utc))
        self._get_or_create_topic(topic).publish(note, block=block, timeout=timeout)
        return note

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

    def __enter__(self) -> "NotificationService":
        return self

    def __exit__(self, *_exc) -> None:
        self.shutdown()
