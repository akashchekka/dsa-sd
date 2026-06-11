"""
=============================================================================
 NotificationService — entry point
=============================================================================
 Run:  python -m notification_service   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

import asyncio

from models.subscription                 import Channel, Subscription
from services.notification_service       import NotificationService
from strategies.channels                 import EmailChannel, PushChannel, SmsChannel
from strategies.exponential_backoff_retry import ExponentialBackoffRetry


async def _demo() -> None:
    svc = NotificationService(
        channels=[EmailChannel(), SmsChannel(), PushChannel()],
        retry=ExponentialBackoffRetry(max_attempts=3),
    )

    svc.subscribe(Subscription("u1", "deals", Channel.EMAIL, "alice@example.com"))
    svc.subscribe(Subscription("u2", "deals", Channel.SMS,   "+15551234567"))
    svc.subscribe(Subscription("u3", "deals", Channel.PUSH,  "device-token-abc"))

    await svc.publish("deals", "50% off everything today only!")


def main() -> None:
    asyncio.run(_demo())


if __name__ == "__main__":
    main()
