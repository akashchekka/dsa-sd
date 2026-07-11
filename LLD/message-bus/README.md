# In-Memory Pub/Sub Message Bus

A small, thread-safe publish/subscribe message bus. Publishers send messages to
named **topics**; **subscribers** receive every message on the topics they
subscribe to. Sized for a 45–50 minute machine-coding interview.

## Design

```
Publisher ──publish(topic, payload)──▶ MessageBus ──▶ Topic ──▶ [inbox queue] ──▶ worker thread ──▶ Subscriber.on_message()
```

- **`MessageBus`** — public API and topic registry. Creates topics lazily and
  routes each publish to the right topic. Thread-safe via a lock with a
  lock-free fast path for the common "topic already exists" case.
- **`Topic`** — owns its subscribers, an inbox `Queue`, and a single worker
  thread that drains the queue and delivers to each subscriber.
- **`Message`** — immutable envelope (`topic`, `payload`, `id`, `timestamp`).
- **`Subscriber`** — ABC with one method, `on_message(message)`.

### Key decisions

| Concern | Approach |
| --- | --- |
| Publisher blocking | **Async delivery** — publish just enqueues, so a slow subscriber never blocks the publisher. |
| Backpressure | Optional **bounded queue per topic** (`topic_capacity`). When full, publish either blocks (backpressure) or fails fast with `queue.Full`. |
| Ordering | **One worker per topic** → FIFO order per topic. |
| Topic isolation | Independent workers → a slow subscriber on one topic can't stall another. |
| Subscriber isolation | `on_message` exceptions are caught per subscriber; one bad subscriber can't break others. |
| Thread safety | Lock around the topic registry and each topic's subscriber set. |
| Shutdown | Sentinel enqueued per topic; workers drain, then are joined. |

## Run

```bash
cd machine-coding-py/message-bus
python __main__.py
```

## Usage

```python
from services.message_bus import MessageBus
from interfaces.subscriber import Subscriber
from models.message import Message


class Logger(Subscriber):
    def on_message(self, message: Message) -> None:
        print(message.payload)


with MessageBus() as bus:
    bus.subscribe("orders", Logger())
    bus.publish("orders", {"id": 42})
    # ... work ...
# bus shuts down cleanly on context exit
```

### Backpressure

```python
# Bound each topic's inbox to 1000 queued messages.
bus = MessageBus(topic_capacity=1000)

bus.publish("jobs", payload)                 # blocks if full (backpressure)
bus.publish("jobs", payload, block=False)    # raises queue.Full if full (fail-fast)
```

## Design patterns

| Pattern | Where | Why it works |
|---|---|---|
| **Observer / Publish–Subscribe** | `MessageBus` ↔ `Subscriber` per `Topic` | Publishers know only the topic name, not who listens; subscribers register and drop out freely — decoupling producers from an unknown, changing set of consumers. |
| **Producer–Consumer** | topic inbox `Queue` + worker thread | The queue buffers bursts and hands work to a worker, so a slow subscriber never blocks the publisher and delivery stays FIFO per topic. |
| **Poison pill (sentinel)** | shutdown enqueues a sentinel per topic | A worker blocked on `queue.get()` can't be stopped by a flag; an in-band sentinel guarantees it wakes, drains remaining messages, and exits cleanly. |

## Concepts

### The worker thread (producer/consumer)

Each `Topic` runs one background **worker thread** in a loop:

```
while True:
    message = inbox.get()   # blocks until a message is available
    if message is SHUTDOWN: # sentinel → stop
        return
    deliver(message)        # call every subscriber's on_message()
```

This is the classic **producer/consumer** pattern. Publishers are *producers*:
they only drop a message into the topic's inbox and return. The worker is the
*consumer*: it pulls messages off one at a time and delivers them. Decoupling
the two means a publisher never waits for a subscriber to finish.

**Delivery.** For each message the worker takes a snapshot of the current
subscriber set (under a short lock so `subscribe`/`unsubscribe` can run
concurrently), then calls `on_message` on each one. Every call is wrapped in
`try/except`, so a subscriber that throws is logged and skipped instead of
killing the worker or starving the other subscribers.

**Why one worker per topic.** A single worker processing a queue in order gives
**FIFO delivery per topic** for free. Separate workers keep topics independent —
a slow subscriber on topic `a` can't stall topic `b`.

### `queue.Queue` and `threading.Condition`

The inbox is a `queue.Queue`. It handles all the thread-safety for us, but it's
worth knowing what it does under the hood, because interviewers ask.

#### `wait()` and `notify()` operate on threads

A **condition variable** lets a thread sleep efficiently until some state
changes, instead of busy-looping and burning CPU.

- `wait()` puts the **calling thread** to sleep. It does three things
  atomically: release the lock, sleep, then re-acquire the lock on wakeup before
  returning. Releasing the lock while asleep is essential — otherwise no other
  thread could change the state this thread is waiting for, and you would
  deadlock.
- `notify()` wakes **one** sleeping thread; `notify_all()` wakes all of them.
  Notifying does not run the thread immediately — it only marks it *runnable*.
  The woken thread must still re-acquire the lock (which the notifier holds
  until it leaves its `with` block) before it can continue.
- Both `wait()` and `notify()` require holding the associated lock, which is why
  they always run inside a `with condition:` block.

#### One shared mutex, three waiting rooms

`threading.Condition` is a lock plus a "waiting room." `queue.Queue` creates
**three** conditions that all share the **same** underlying mutex:

- `not_empty` — consumers wait here when the queue is empty.
- `not_full` — producers wait here when a bounded queue is full.
- `all_tasks_done` — `join()` waits here until every item is processed.

Because the three conditions share one lock, holding any one of them is the same
as holding the single mutex. That is why `put()` can enter under `not_full` yet
legally notify `not_empty`: they are backed by the identical lock object.

#### The producer/consumer handshake

Each side waits on its own condition and notifies the *other* side:

| Method  | Enters under (may wait) | Notifies (wakes the other side) |
|---------|-------------------------|---------------------------------|
| `put`   | `not_full`              | `not_empty`                     |
| `get`   | `not_empty`             | `not_full`                      |

- `put` on a full bounded queue waits on `not_full` for a slot; after adding an
  item it calls `not_empty.notify()` to wake a waiting consumer.
- `get` on an empty queue waits on `not_empty` for an item; after removing one
  it calls `not_full.notify()` to wake a waiting producer.

Our worker's `inbox.get()` blocks on `not_empty` when there is nothing to do;
a publisher's `put()` wakes it. This is the efficient blocking hand-off, and we
get it without writing a single lock or sleep loop ourselves.

#### Always re-check the condition in a `while` loop

Queue waits look like this, never a plain `if`:

```python
while not self._qsize():
    self.not_empty.wait()
```

Returning from `wait()` only means the thread was *woken*, not that its
condition is now true. It must re-check, because:

- another consumer may have grabbed the item first,
- `notify_all()` may have woken several threads for one item, or
- the runtime may produce a *spurious wakeup* with no `notify()` at all.

So the golden rule of condition variables is: **wake → re-acquire lock →
re-check the condition → sleep again if still unsatisfied.**

### Backpressure

**Backpressure** is a slow consumer pushing back on a fast producer so the
system doesn't accumulate unbounded work.

With an **unbounded** queue, if publishers outpace the subscriber, the inbox
grows forever until the process runs out of memory. A **bounded** queue
(`topic_capacity=N`) caps how much can pile up and forces a decision when it's
full:

- **Block (default):** `publish(...)` waits for the worker to free a slot. The
  producer is *slowed to the consumer's rate* — this is backpressure.
- **Fail-fast:** `publish(..., block=False)` raises `queue.Full` immediately, so
  the caller can shed load, retry later, or drop the message.

Other real-world policies (not implemented here, good to mention): drop-oldest,
drop-newest, or spill to disk.

## Complexity

- `publish` — O(1) enqueue (non-blocking on an unbounded queue).
- Delivery — O(S) per message, where S = subscribers on that topic.
- `subscribe` / `unsubscribe` — O(1).

## Possible extensions (talking points)

- Consumer groups (queue semantics: one subscriber per group gets each message).
- Bounded queues + backpressure or drop policy.
- Retries / dead-letter queue for failing subscribers.
- Wildcard / hierarchical topics (`orders.*`).
- Persistence and at-least-once delivery.
