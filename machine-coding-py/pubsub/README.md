# PubSub — Production-Grade In-Memory Bus

An in-memory publish/subscribe bus designed to be **interview-pitchable in 5 minutes** without skipping the parts that matter under pressure: thread safety, back-pressure, clean shutdown, and per-topic isolation.

## Run

```pwsh
cd machine-coding-py/pubsub_production
python __main__.py
```

## File layout

```
pubsub_production/
├── README.md
├── __init__.py
├── __main__.py                       # 3 demos: isolation, topic isolation, clean shutdown
├── core/
│   ├── bounded_inbox.py              # Condition × 2 (not_full / not_empty), one Lock
│   ├── topic.py                      # name + inbox + subscriber set
│   └── dispatcher.py                 # one worker per topic; deliver / shutdown
├── interfaces/
│   └── subscriber.py                 # Subscriber.consume(message)
├── models/
│   └── message.py                    # frozen dataclass; auto id + utc timestamp
├── services/
│   └── message_bus.py                # public API + DCL on topic dict + lifecycle
└── workers/
    └── topic_worker.py               # daemon thread; Event-driven shutdown
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Per-topic worker** | One thread per topic | Slow subscribers on topic A don't stall topic B. Simpler than a thread pool and preserves per-topic ordering. |
| **Topic registry** | Double-checked locking on `dict` | Hot path (topic exists) is lock-free — `dict.get` is atomic under the GIL. Lock only on first creation. |
| **Topic-set lock** | `Lock`, not `RLock` | No re-entrance in any critical section. `Lock` is faster and surfaces re-entry bugs immediately. |
| **Inbox** | Hand-rolled `BoundedInbox` on `threading.Condition` | Showcases the producer-consumer primitive properly — `queue.Queue` hides the same machinery. Also gives us a `close()` that wakes every waiter. |
| **Shutdown** | `threading.Event` per worker | One-shot, broadcast "stop" signal — textbook `Event` use. |
| **Back-pressure** | `BoundedInbox.put()` blocks when full | Slow consumers naturally throttle publishers instead of unbounded queue growth. |
| **Message** | Frozen dataclass with auto id/timestamp | Safe to fan out by reference — no defensive copies. |
| **Subscriber failure** | `try/except` around each `consume` | One bad subscriber can't poison the rest of the fan-out. |

## How `Lock`, `Condition`, and `Event` are used

This is what an interviewer is most likely to probe. Each primitive has exactly one job here:

| Primitive | Where | Why this one |
|---|---|---|
| **`threading.Lock`** | `Topic._subscribers` | Guards a `set`. No reentrance. `Lock` is faster than `RLock` and would deadlock loudly if anyone ever introduced reentrance — surfaces bugs, doesn't hide them. |
| **`threading.Condition`** | `BoundedInbox._not_full` / `_not_empty` | Predicate-based waiting that flips repeatedly: "has space" / "has items." Two Conditions share **one Lock** so producers and consumers can wait on different predicates without racing each other. Always loop with `while`, never `if` — guards against spurious wakeups *and* the case where multiple waiters wake but only one slot opened. |
| **`threading.Event`** | `TopicWorker._stop_event` | A single "shutdown requested" boolean that flips once and never flips back. Sticky, broadcast — every worker that checks `is_set()` sees it. Combined with `BoundedInbox.close()` to unblock any in-flight `get()`. |

The combo `Event` (stop latch) + `Condition` (work signal) is the canonical "stoppable worker" pattern.

## Trade-offs and what's intentionally out of scope

| Topic | Why it's out for this size |
|---|---|
| **Retry / DLQ** | Adds policy. Drop-in `RetryingSubscriber` wrapper — feature, not architecture. |
| **Wildcards (`news.*` / `news.#`)** | Turns the topic registry into a trie. Out of scope for "in-memory bus." |
| **Exactly-once / persistence** | Requires a write-ahead log + ack protocol. That's Kafka, not an in-memory bus. |
| **Worker pool per topic** | A pool would parallelize but reorder. One worker per topic preserves ordering. |
| **Async/await** | Thread-based design. An `asyncio` version is its own implementation; mixing is worse than either pure version. |
| **Sync delivery** | Removed — slow subscribers blocking publishers is rarely what you want and is one line to add back (`for s in topic.get_subscribers(): s.consume(m)`). |

## Extending it (small, additive changes)

| Add… | Touch |
|---|---|
| **Drop-oldest back-pressure** | Tweak `BoundedInbox.put` to pop-then-append when full |
| **Retries** | Decorator `RetryingSubscriber(inner, attempts=3)` |
| **Metrics** | `MetricsSubscriber` wrapper, or counters on `Topic` |
| **Priority** | Swap `deque` → `heapq` in `BoundedInbox` |
| **Filtering** | `FilteredSubscriber(inner, predicate)` |

## What the demo proves

The `__main__.py` exercises three guarantees and prints proof of each:

1. **Slow subscriber isolation** — `publish()` returns immediately; slow handler runs on its own worker.
2. **Topic isolation** — a blocking worker on topic A doesn't delay topic B's delivery.
3. **Clean shutdown** — workers drain in-flight messages, then exit; post-shutdown publishes are rejected (no silent loss).
