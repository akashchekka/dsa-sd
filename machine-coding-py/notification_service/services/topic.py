from __future__ import annotations

from queue import Queue
import threading

from interfaces.notification_channel import INotificationChannel
from interfaces.retry_policy import IRetryPolicy
from models.notification import Notification
from models.subscription import Channel, Subscription

_SHUTDOWN = object()

class Topic:
    def __init__(self, name: str, channels: dict[Channel, INotificationChannel], retry: IRetryPolicy, capacity: int = 0) -> None:
        self._name = name
        self._channels = channels
        self._retry = retry
        self._subscriptions: set[Subscription] = set()
        self._lock = threading.Lock()
        self._inbox: Queue = Queue(maxsize=capacity)
        self._worker = threading.Thread(
            target=self._run, name=f"topic-{name}", daemon=True
        )
        self._worker.start()

    def add_subscription(self, subscription: Subscription) -> None:
        with self._lock:
            self._subscriptions.add(subscription)

    def remove_subscription(self, subscription: Subscription) -> None:
        with self._lock:
            self._subscriptions.discard(subscription)

    def publish(self, notification: Notification, block: bool = True, timeout: float | None = None) -> None:
        self._inbox.put(notification, block=block, timeout=timeout)

    def _run(self) -> None:
        while True:
            item = self._inbox.get()
            if item is _SHUTDOWN:
                return
            self._deliver(item)

    def _deliver(self, notification: Notification) -> None:
        # Snapshot under the lock so subscribe/unsubscribe can run concurrently.
        with self._lock:
            subscriptions = list(self._subscriptions)

        for sub in subscriptions:
            channel = self._channels.get(sub.channel)
            if channel is None:
                continue
            try:
                ok = self._retry.execute(lambda: channel.send(sub.address, notification))
            except Exception as exc:  # isolate: one bad delivery can't break others
                ok = False
                print(f"[topic-{self._name}] delivery to {sub.user_id} raised: {exc}")
            if not ok:
                print(
                    f"[topic-{self._name}] DLQ: failed to deliver {notification.id} "
                    f"to {sub.user_id} via {sub.channel.value}"
                )

    def shutdown(self) -> None:
        self._inbox.put(_SHUTDOWN)

    def join(self, timeout: float | None = None) -> None:
        self._worker.join(timeout)
