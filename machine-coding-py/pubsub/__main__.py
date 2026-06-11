"""
=============================================================================
 PubSub Production — demo entry point
=============================================================================
 Run:  python __main__.py   (from machine-coding-py/pubsub_production/)
=============================================================================
"""
from __future__ import annotations

import time

from interfaces.subscriber  import Subscriber
from models.message          import Message
from services.message_bus    import InMemoryMessageBus


class PrintSubscriber(Subscriber):
    def __init__(self, name: str) -> None:
        self._name = name

    def consume(self, message: Message) -> None:
        print(f"  [{self._name}] got {message.payload!r} on '{message.topic}'")

    def __repr__(self) -> str:
        return f"<{self._name}>"


class SlowSubscriber(Subscriber):
    def __init__(self, name: str, delay: float) -> None:
        self._name  = name
        self._delay = delay

    def consume(self, message: Message) -> None:
        time.sleep(self._delay)
        print(f"  [{self._name}] (slow) finished {message.payload!r}")

    def __repr__(self) -> str:
        return f"<{self._name}>"


def demo_isolation() -> None:
    print("\n--- demo 1: slow subscriber doesn't block fast ---")
    with InMemoryMessageBus() as bus:
        bus.subscribe("orders", SlowSubscriber("slow", delay=0.2))
        bus.subscribe("orders", PrintSubscriber("fast"))

        t0 = time.perf_counter()
        for i in range(3):
            bus.publish("orders", f"order-{i}")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"  publish loop returned in {elapsed_ms:.1f} ms")
        time.sleep(0.8)


def demo_topic_isolation() -> None:
    print("\n--- demo 2: per-topic workers — topics are independent ---")
    with InMemoryMessageBus() as bus:
        bus.subscribe("a", SlowSubscriber("a-slow", delay=0.3))
        bus.subscribe("b", PrintSubscriber("b-fast"))

        bus.publish("a", "blocking-payload")     # tied up on topic a's worker
        bus.publish("b", "should arrive first")  # topic b sails through
        time.sleep(0.5)


def demo_clean_shutdown() -> None:
    print("\n--- demo 3: clean shutdown via Event (no thread leaks) ---")
    bus = InMemoryMessageBus()
    bus.subscribe("metrics", PrintSubscriber("M"))
    for i in range(3):
        bus.publish("metrics", f"sample-{i}")
    bus.shutdown()
    print("  bus shut down cleanly; workers joined")

    try:
        bus.publish("metrics", "after-shutdown")
    except RuntimeError as ex:
        print(f"  publish after shutdown rejected: {ex}")


def main() -> None:
    demo_isolation()
    demo_topic_isolation()
    demo_clean_shutdown()


if __name__ == "__main__":
    main()

