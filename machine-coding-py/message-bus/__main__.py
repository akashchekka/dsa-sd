"""Demo entry point.

Run from the message-bus folder:
    python __main__.py
"""
from __future__ import annotations

import queue
import time

from interfaces.subscriber import Subscriber
from models.message import Message
from services.message_bus import MessageBus


class PrintSubscriber(Subscriber):
    def __init__(self, name: str) -> None:
        self._name = name

    def on_message(self, message: Message) -> None:
        print(f"  [{self._name}] received {message.payload!r} on '{message.topic}'")

    def __repr__(self) -> str:
        return f"<{self._name}>"


class SlowSubscriber(Subscriber):
    def __init__(self, name: str, delay: float) -> None:
        self._name = name
        self._delay = delay

    def on_message(self, message: Message) -> None:
        time.sleep(self._delay)
        print(f"  [{self._name}] (slow) finished {message.payload!r}")

    def __repr__(self) -> str:
        return f"<{self._name}>"


class FlakySubscriber(Subscriber):
    def on_message(self, message: Message) -> None:
        raise RuntimeError("boom")

    def __repr__(self) -> str:
        return "<flaky>"


def demo_fanout() -> None:
    print("\n--- demo 1: fan-out to multiple subscribers ---")
    with MessageBus() as bus:
        bus.subscribe("orders", PrintSubscriber("email"))
        bus.subscribe("orders", PrintSubscriber("audit"))
        bus.publish("orders", "order-42")
        time.sleep(0.1)


def demo_async_publish() -> None:
    print("\n--- demo 2: publish is async, slow subscriber doesn't block ---")
    with MessageBus() as bus:
        bus.subscribe("orders", SlowSubscriber("slow", delay=0.2))
        start = time.perf_counter()
        for i in range(3):
            bus.publish("orders", f"order-{i}")
        print(f"  publish loop returned in {(time.perf_counter() - start) * 1000:.1f} ms")
        time.sleep(0.8)


def demo_topic_isolation() -> None:
    print("\n--- demo 3: topics are independent ---")
    with MessageBus() as bus:
        bus.subscribe("a", SlowSubscriber("a-slow", delay=0.3))
        bus.subscribe("b", PrintSubscriber("b-fast"))
        bus.publish("a", "blocking-payload")
        bus.publish("b", "should-arrive-first")
        time.sleep(0.5)


def demo_subscriber_isolation() -> None:
    print("\n--- demo 4: a failing subscriber can't break others ---")
    with MessageBus() as bus:
        bus.subscribe("events", FlakySubscriber())
        bus.subscribe("events", PrintSubscriber("healthy"))
        bus.publish("events", "ping")
        time.sleep(0.1)


def demo_unsubscribe_and_shutdown() -> None:
    print("\n--- demo 5: unsubscribe and rejecting publish after shutdown ---")
    bus = MessageBus()
    sub = PrintSubscriber("temp")
    bus.subscribe("news", sub)
    bus.publish("news", "first")
    time.sleep(0.1)
    bus.unsubscribe("news", sub)
    bus.publish("news", "second (no subscribers)")
    time.sleep(0.1)
    bus.shutdown()
    try:
        bus.publish("news", "after-shutdown")
    except RuntimeError as exc:
        print(f"  publish after shutdown rejected: {exc}")


def demo_backpressure() -> None:
    print("\n--- demo 6: bounded topic applies backpressure (fail-fast) ---")
    # capacity=1 + a slow subscriber means the inbox fills quickly.
    with MessageBus(topic_capacity=1) as bus:
        bus.subscribe("jobs", SlowSubscriber("worker", delay=0.3))
        accepted, rejected = 0, 0
        for i in range(5):
            try:
                bus.publish("jobs", f"job-{i}", block=False)  # fail-fast when full
                accepted += 1
            except queue.Full:
                rejected += 1
        print(f"  accepted={accepted}, rejected(queue full)={rejected}")
        time.sleep(1.0)


def main() -> None:
    demo_fanout()
    demo_async_publish()
    demo_topic_isolation()
    demo_subscriber_isolation()
    demo_unsubscribe_and_shutdown()
    demo_backpressure()


if __name__ == "__main__":
    main()
