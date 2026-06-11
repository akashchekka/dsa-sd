"""In-memory Pub/Sub. Topic -> list of subscriptions. Publishing fans out
to all subscribers across whichever channel each subscribed with, each
guarded by the configured retry policy.

For production:
  * Replace dict with a durable store (DB / Kafka).
  * Each (topic, channel) gets its own queue + worker pool.
  * Add dead-letter queue for messages that exhaust retries."""
from __future__ import annotations

import asyncio
import itertools
import threading
from datetime import datetime, timezone

from interfaces.notification_channel import INotificationChannel
from interfaces.retry_policy         import IRetryPolicy
from models.notification             import Notification
from models.subscription             import Channel, Subscription


class NotificationService:
    def __init__(self, channels: list[INotificationChannel], retry: IRetryPolicy) -> None:
        self._channels: dict[Channel, INotificationChannel] = {c.kind: c for c in channels}
        self._retry    = retry
        self._subs:    dict[str, list[Subscription]] = {}
        self._lock     = threading.Lock()
        self._seq      = itertools.count(1)

    def subscribe(self, s: Subscription) -> None:
        with self._lock:
            self._subs.setdefault(s.topic, []).append(s)

    async def publish(self, topic: str, body: str) -> None:
        note = Notification(
            id=f"N-{next(self._seq):05d}",
            topic=topic, body=body,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            snapshot = list(self._subs.get(topic, ()))

        async def deliver(sub: Subscription) -> None:
            ch = self._channels.get(sub.channel)
            if ch is None:
                return
            ok = await self._retry.execute(lambda: ch.send(sub.address, note))
            if not ok:
                print(f"  DLQ: failed to deliver {note.id} to {sub.user_id} via {sub.channel.value}")

        await asyncio.gather(*(deliver(s) for s in snapshot))
