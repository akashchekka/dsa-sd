# Machine Coding — Multithreading (Python)

> **Ordered by interview ROI.** Master problems 1–5 to clear 80% of concurrency rounds at Google, Uber, Amazon, Meta.

---

## Table of Contents

- [Prerequisites: Primitives Cheat Sheet](#prerequisites-primitives-cheat-sheet)
- [Python Concurrency Reality: GIL, Threads, Async, Processes](#python-concurrency-reality-gil-threads-async-processes)
- [Folder Structure](#folder-structure)
- [1. Lock + Race Condition](#1-lock--race-condition)
- [2. Producer-Consumer / Bounded Buffer](#2-producer-consumer--bounded-buffer)
- [3. Blocking Queue (from Scratch)](#3-blocking-queue-from-scratch)
- [4. Rate Limiter — Token Bucket](#4-rate-limiter--token-bucket)
- [5. Thread Pool from Scratch](#5-thread-pool-from-scratch)
- [6. Deadlock — 4 Conditions + Fixes](#6-deadlock--4-conditions--fixes)
- [7. Reader-Writer Lock](#7-reader-writer-lock)
- [8. Thread-Safe LRU Cache](#8-thread-safe-lru-cache)
- [9. Dining Philosophers](#9-dining-philosophers)
- [10. Rate Limiter — Sliding Window](#10-rate-limiter--sliding-window)
- [11. Print In Order](#11-print-in-order)
- [12. Print FooBar Alternately](#12-print-foobar-alternately)
- [13. Scheduled Task Executor](#13-scheduled-task-executor)
- [Testing Concurrent Code](#testing-concurrent-code)
- [Interview Delivery Tips](#interview-delivery-tips)

---

## Prerequisites: Primitives Cheat Sheet

Before coding, know these 6 tools:

```
Primitive            | What It Does                           | When to Use
---------------------|----------------------------------------|----------------------------
threading.Lock()     | Only 1 thread at a time                | Protect shared data
threading.RLock()    | Same thread can re-acquire             | Methods calling each other
threading.Condition()| wait() + notify() on a lock            | "Wait until X is true"
threading.Semaphore()| Allow N threads at once                | Connection pools, throttling
threading.Event()    | Simple boolean flag threads wait on    | "Go!" signal
queue.Queue()        | Thread-safe FIFO with blocking         | Don't reinvent this in prod
```

**Three rules you MUST follow:**

1. **Always use `with` for locks** — never manual `acquire()`/`release()` unless you need timeout
2. **Always `while` (not `if`) with `condition.wait()`** — spurious wakeups
3. **Keep critical sections minimal** — do I/O and computation OUTSIDE the lock

---

## Python Concurrency Reality: GIL, Threads, Async, Processes

> **A Google or Uber interviewer WILL ask:** *"Does threading actually help in Python?"* Be ready.

### The GIL (Global Interpreter Lock)

CPython has a **Global Interpreter Lock** — only one thread executes Python bytecode at a time, even on multi-core machines.

**Implications:**

| Workload | Threads help? | Why |
|----------|---------------|-----|
| **CPU-bound** (math, parsing, compression) | ❌ No | GIL serializes execution |
| **I/O-bound** (network, disk, DB) | ✅ Yes | GIL released during I/O syscalls |
| **C-extension heavy** (NumPy, ML) | ✅ Yes | NumPy releases the GIL |

### Pick the Right Tool

```
Workload type        | Tool                            | Why
---------------------|---------------------------------|---------------------------
CPU-bound            | multiprocessing / ProcessPool   | Bypass GIL via separate processes
I/O-bound, < 100s    | threading / ThreadPoolExecutor  | Simple, GIL released on I/O
I/O-bound, 1000s+    | asyncio                         | Single thread, no GIL contention
Mixed                | asyncio + run_in_executor       | Offload blocking to thread pool
```

### What to Say in Interview

> "In CPython the GIL means threads don't speed up CPU-bound work — for that I'd use `multiprocessing`. But threads still work for I/O-bound code because the GIL is released during system calls. For high-concurrency I/O like a web server with thousands of connections, `asyncio` is more memory-efficient than threads. Python 3.13 has experimental free-threaded mode (PEP 703) that removes the GIL."

### Threads vs Asyncio Quick Comparison

```python
# Threads — preemptive, OS-scheduled, ~8MB stack each
with ThreadPoolExecutor(max_workers=10) as pool:
    pool.map(fetch, urls)

# Asyncio — cooperative, single-threaded, ~KB per coroutine
async def main():
    await asyncio.gather(*[fetch(u) for u in urls])
```

**Rule of thumb:** threads for ≤ hundreds of concurrent operations, asyncio for thousands.

---

## Folder Structure

In a machine coding round, organize your solution like a mini-project. Even if you write it in one file during the interview, **explain** this structure verbally.

```
concurrency/
├── primitives/
│   ├── blocking_queue.py          # Problem 3
│   ├── read_write_lock.py         # Problem 7
│   └── thread_pool.py             # Problem 5
├── rate_limiter/
│   ├── rate_limiter.py            # ABC (interface)
│   ├── token_bucket.py            # Problem 4
│   └── sliding_window.py          # Problem 10
├── cache/
│   └── lru_cache.py               # Problem 8
├── patterns/
│   ├── bounded_buffer.py          # Problem 2
│   ├── dining_philosophers.py     # Problem 9
│   ├── print_in_order.py          # Problem 11
│   ├── foobar.py                  # Problem 12
│   └── scheduled_executor.py      # Problem 13
└── tests/
    └── test_all.py                # Test harness (Barrier-based stress tests)
```

**What to say:** "I'd organize this into primitives, domain logic, and tests. The rate limiter has an ABC so we can swap Token Bucket and Sliding Window interchangeably."

---

## 1. Lock + Race Condition

**Asked at:** Every company. This is the foundation.

**What they test:** Can you identify a race condition? Can you fix it? Can you explain WHY it happens?

### The Bug

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        counter += 1  # NOT thread-safe

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start(); t2.start()
t1.join(); t2.join()

print(f"Expected: 2,000,000 | Got: {counter}")  # Got: ~1,500,000
```

### Why It Breaks

`counter += 1` is THREE steps, not one:

```
Thread A: READ counter  → 42
Thread B: READ counter  → 42       ← same old value!
Thread A: WRITE 43
Thread B: WRITE 43                 ← overwrites A's work!

Lost update: expected 44, got 43.
```

This is a **read-modify-write** race condition.

### The Fix

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(1_000_000):
        with lock:
            counter += 1

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start(); t2.start()
t1.join(); t2.join()

print(f"Counter: {counter}")  # Always 2,000,000
```

### What to Say in Interview

> "`counter += 1` is a read-modify-write — it reads the current value, adds 1, and writes back. Two threads can read the same old value and both write the same new value, losing one update. Wrapping it in a lock ensures only one thread does the read-modify-write at a time."

### Other Race Condition Types

| Type | Example | Fix |
|------|---------|-----|
| Read-modify-write | `counter += 1` | Lock |
| Check-then-act | `if key not in dict: dict[key] = v` | Lock the entire check+act |
| Compound action | `a -= x; b += x` (transfer) | Lock both together |

---

## 2. Producer-Consumer / Bounded Buffer

**Asked at:** Uber, Amazon, Google, Goldman Sachs

**The #1 most asked concurrency problem.** If you learn one thing, learn this.

### Problem

- Multiple **producers** add items to a buffer
- Multiple **consumers** remove items
- Buffer has a **max capacity**
- Producers **block** when full
- Consumers **block** when empty

### Key Insight

You need **two conditions** on the **same lock**:
- `not_full` — producers wait on this, consumers notify it
- `not_empty` — consumers wait on this, producers notify it

> **Why share the same lock?** Both conditions guard the same shared state (`self._buffer`). Sharing the lock ensures `notify()` is always called while holding the lock that the waiter will re-acquire — required for correctness.

### Solution

```python
import threading
import time
import random
from collections import deque
from typing import Any

class BoundedBuffer:
    """Thread-safe bounded buffer for producer-consumer pattern.

    - produce() blocks when buffer is full.
    - consume() blocks when buffer is empty.
    """

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        # deque gives O(1) popleft; list.pop(0) is O(n) — interviewer will catch
        self._buffer: deque[Any] = deque()
        self._lock = threading.Lock()
        self._not_full = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)

    @property
    def capacity(self) -> int:
        return self._capacity

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0

    def is_full(self) -> bool:
        with self._lock:
            return len(self._buffer) >= self._capacity

    def produce(self, item: Any) -> None:
        with self._not_full:                              # acquires self._lock
            while len(self._buffer) >= self._capacity:    # WHILE not IF
                self._not_full.wait()                     # release lock + sleep

            self._buffer.append(item)
            self._not_empty.notify()                      # wake ONE consumer

    def consume(self) -> Any:
        with self._not_empty:                             # acquires self._lock
            while len(self._buffer) == 0:                 # WHILE not IF
                self._not_empty.wait()                    # release lock + sleep

            item = self._buffer.popleft()                 # O(1)
            self._not_full.notify()                       # wake ONE producer
            return item
```

### Test It

```python
def producer(buf: BoundedBuffer, pid: int, count: int) -> None:
    for i in range(count):
        item = f"P{pid}-{i}"
        buf.produce(item)
        print(f"  Produced: {item} | size={buf.size}")
        time.sleep(random.uniform(0.05, 0.15))

def consumer(buf: BoundedBuffer, cid: int, count: int) -> None:
    for _ in range(count):
        item = buf.consume()
        print(f"  Consumed: {item} | size={buf.size}")
        time.sleep(random.uniform(0.1, 0.3))

buf = BoundedBuffer(capacity=3)

threads: list[threading.Thread] = []
for i in range(2):
    threads.append(threading.Thread(target=producer, args=(buf, i, 5)))
    threads.append(threading.Thread(target=consumer, args=(buf, i, 5)))

for t in threads: t.start()
for t in threads: t.join()
```

### How condition.wait() Works (Explain This!)

```
condition.wait() does 3 things atomically:
  1. RELEASE the lock        ← so other threads can acquire it
  2. SLEEP the thread        ← no CPU wasted (unlike busy-wait)
  3. When notified:
     - WAKE UP
     - RE-ACQUIRE the lock   ← back in critical section
     - Continue after wait()
```

### Why while, not if?

**Spurious wakeups:** A thread can wake up even without `notify()`. The `while` loop re-checks the condition and goes back to sleep if it's still not met. Interviewers specifically look for this.

```python
# ❌ BAD
if len(self.buffer) == 0:
    self.not_empty.wait()     # What if woken spuriously? Processes empty buffer!

# ✅ GOOD
while len(self.buffer) == 0:
    self.not_empty.wait()     # Re-checks, goes back to sleep if still empty
```

---

## 3. Blocking Queue (from Scratch)

**Asked at:** Amazon, Google, Uber, Goldman Sachs

**Same pattern as Producer-Consumer** but packaged as a reusable data structure with shutdown support.

### Problem

Implement a queue where:
- `put(item)` blocks if full
- `get(timeout)` blocks if empty, supports timeout
- `shutdown()` gracefully stops all waiting threads

### Solution

```python
import threading
import time
from collections import deque
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class BlockingQueue(Generic[T]):
    """Thread-safe blocking queue with bounded capacity.

    - put() blocks when full.
    - get() blocks when empty, supports timeout.
    - shutdown() gracefully wakes all blocked threads.
    """

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._queue: deque[T] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._shutdown = False

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def is_shutdown(self) -> bool:
        with self._lock:
            return self._shutdown

    def put(self, item: T) -> None:
        """Add item to queue. Blocks if queue is at capacity."""
        with self._not_full:
            while len(self._queue) >= self._capacity:
                if self._shutdown:
                    raise RuntimeError("Queue is shut down")
                self._not_full.wait()

            self._queue.append(item)
            self._not_empty.notify()

    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """Remove and return item. Blocks if empty. Returns None on shutdown.

        Correctly handles spurious wakeups + total deadline so timeout
        does NOT reset on each loop iteration.
        """
        deadline = (time.monotonic() + timeout) if timeout is not None else None

        with self._not_empty:
            while len(self._queue) == 0:
                if self._shutdown:
                    return None

                if deadline is None:
                    self._not_empty.wait()
                else:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("Timed out waiting for item")
                    # wait() may return early (spurious); the while-loop re-checks
                    self._not_empty.wait(timeout=remaining)

            item = self._queue.popleft()
            self._not_full.notify()
            return item

    def shutdown(self) -> None:
        """Signal shutdown — wake all blocked threads so they can exit."""
        with self._lock:
            self._shutdown = True
            self._not_empty.notify_all()
            self._not_full.notify_all()
```

### What Makes This Different from Problem 2?

| Feature | Bounded Buffer | Blocking Queue |
|---------|---------------|----------------|
| Timeout support | No | Yes (`wait(timeout)`) |
| Shutdown | No | Yes (graceful stop) |
| Return value on shutdown | N/A | `None` (not exception) |
| Reusable API | Demo code | Production-style class |

### Common Bug: Resetting Timeout in Loop

```python
# ❌ WRONG — total wait can be N × timeout if there are spurious wakeups / contention
while len(self._queue) == 0:
    self._not_empty.wait(timeout=timeout)   # restarts every loop!

# ✅ CORRECT — track absolute deadline, pass remaining each iteration
deadline = time.monotonic() + timeout
while len(self._queue) == 0:
    remaining = deadline - time.monotonic()
    if remaining <= 0: raise TimeoutError(...)
    self._not_empty.wait(timeout=remaining)
```

### What to Say in Interview

> "This is the same two-condition pattern as producer-consumer. The additions are: timeout support tracked as an absolute deadline so spurious wakeups don't extend the total wait, and a shutdown flag that wakes all blocked threads with `notify_all()` so they can exit cleanly."

---

## 4. Rate Limiter — Token Bucket

**Asked at:** Uber, Google, Stripe, Amazon

**Uber's favorite.** They use token buckets for API rate limiting, surge pricing, and driver dispatch throttling.

### Problem

Allow at most N requests per second. Excess requests are rejected immediately.

### How Token Bucket Works

```
Bucket holds up to `capacity` tokens (e.g., 5).
Each request costs 1 token.
Tokens refill at `rate` tokens/second.
Empty bucket → request REJECTED.

Timeline (rate=2/sec, capacity=3):
  t=0.0  tokens=3  [request → ALLOW, tokens=2]
  t=0.1  tokens=2.2 [request → ALLOW, tokens=1.2]
  t=0.2  tokens=1.4 [request → ALLOW, tokens=0.4]
  t=0.3  tokens=0.6 [request → REJECT, tokens<1]
  t=1.0  tokens=2.0 [refilled over time]
```

### Solution

```python
import threading
import time
from abc import ABC, abstractmethod

# --- Interface (ABC) ---

class RateLimiter(ABC):
    """Abstract base for all rate limiter implementations.
    Swap TokenBucket / SlidingWindow without changing callers."""

    @abstractmethod
    def allow(self) -> bool:
        """Returns True if request is allowed, False if rate-limited."""
        ...


# --- Token Bucket Implementation ---

class TokenBucketRateLimiter(RateLimiter):
    """Rate limiter using the Token Bucket algorithm.

    - Tokens refill at a steady rate.
    - Each request consumes one token.
    - Allows bursts up to `capacity`.
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """
        Args:
            rate: Tokens added per second.
            capacity: Max tokens in bucket (burst size).
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)      # Start full
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Lazily add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def allow(self) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False
```

### Test It

```python
limiter: RateLimiter = TokenBucketRateLimiter(rate=5, capacity=5)

def make_requests(client_id: int) -> None:
    for i in range(10):
        status = "ALLOWED" if limiter.allow() else "REJECTED"
        print(f"Client-{client_id} Request-{i}: {status}")
        time.sleep(0.05)

threads = [threading.Thread(target=make_requests, args=(i,)) for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
```

### Why This Design?

| Design Choice | Why |
|---------------|-----|
| Lazy refill (no background thread) | Simpler, no extra thread. Refill on each `allow()` call |
| `time.monotonic()` not `time.time()` | Monotonic clock can't go backwards (system time can) |
| `min(capacity, tokens + new)` | Cap at capacity — don't accumulate infinite tokens |
| Single lock | Simple and correct. For high throughput, shard by user ID |

### Follow-up: Per-User Rate Limiter (with Eviction)

> **Trap:** A naive per-user map grows unboundedly — every unique user creates a permanent limiter. Uber/Stripe interviewers always probe this.

```python
import time

class PerUserRateLimiter:
    """Per-user token bucket with idle eviction (TTL).

    - Outer lock protects the user→(limiter, last_seen) map.
    - Each inner limiter has its own lock for allow().
    - Idle entries are evicted after `idle_ttl` seconds.
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        idle_ttl: float = 600.0,
        max_users: int = 100_000,
    ) -> None:
        self._rate = rate
        self._capacity = capacity
        self._idle_ttl = idle_ttl
        self._max_users = max_users
        self._user_limiters: dict[str, tuple[TokenBucketRateLimiter, float]] = {}
        self._lock = threading.Lock()

    def allow(self, user_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            entry = self._user_limiters.get(user_id)
            if entry is None:
                if len(self._user_limiters) >= self._max_users:
                    self._evict_idle(now)
                limiter = TokenBucketRateLimiter(self._rate, self._capacity)
            else:
                limiter, _ = entry
            self._user_limiters[user_id] = (limiter, now)

        # Call allow() OUTSIDE the outer lock — each limiter has its own lock
        return limiter.allow()

    def _evict_idle(self, now: float) -> None:
        """Caller must hold self._lock."""
        cutoff = now - self._idle_ttl
        stale = [uid for uid, (_, ts) in self._user_limiters.items() if ts < cutoff]
        for uid in stale:
            del self._user_limiters[uid]
```

> **What to say:** "Without eviction this map grows unboundedly — every unique user permanently consumes memory. I track last-seen timestamps and evict idle entries when we hit a soft cap. In production I'd back this with Redis + TTL."

---

## 5. Thread Pool from Scratch

**Asked at:** Uber, Google, Amazon

**Tests deep understanding:** worker threads, task queues, futures, and coordinated shutdown.

### Problem

Implement a pool of N reusable worker threads that:
- Accept tasks via `submit()` and **return a `Future`** for the result
- Execute them on the next available worker
- Support graceful `shutdown()` (finish pending tasks, then stop)

### Mental Model

```
submit(task) → returns Future → [Task Queue] → Worker picks up → executes
                                                              → future.set_result(...)
                                                              OR future.set_exception(...)

shutdown():
  1. Set flag
  2. notify_all workers (wake them from wait)
  3. Workers drain remaining tasks, then exit
  4. Main thread joins all workers
```

### Solution

```python
import threading
import logging
from collections import deque
from typing import Any, Callable, Generic, TypeVar, Optional

logger = logging.getLogger(__name__)

R = TypeVar('R')

class Future(Generic[R]):
    """Minimal Future for getting a task's result or exception.

    Real concurrent.futures.Future has more (cancel, callbacks, etc.) —
    mention this and only build what's needed for the interview.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._result: Optional[R] = None
        self._exception: Optional[BaseException] = None

    def set_result(self, result: R) -> None:
        with self._lock:
            self._result = result
        self._done.set()

    def set_exception(self, exc: BaseException) -> None:
        with self._lock:
            self._exception = exc
        self._done.set()

    def result(self, timeout: Optional[float] = None) -> R:
        if not self._done.wait(timeout=timeout):
            raise TimeoutError("Future not ready")
        if self._exception is not None:
            raise self._exception
        return self._result  # type: ignore[return-value]

    def done(self) -> bool:
        return self._done.is_set()


class ThreadPool:
    """Fixed-size thread pool that accepts and executes tasks concurrently.

    - submit() enqueues a task, returns a Future for its result.
    - shutdown() gracefully stops all workers after pending tasks complete.
    """

    def __init__(self, num_workers: int) -> None:
        self._tasks: deque[tuple[Callable, tuple, dict, Future]] = deque()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._shutdown_flag = False
        self._workers: list[threading.Thread] = []

        for i in range(num_workers):
            t = threading.Thread(
                target=self._worker, name=f"Worker-{i}", daemon=True
            )
            t.start()
            self._workers.append(t)

    def _worker(self) -> None:
        """Worker loop: wait for task → execute → set future → repeat."""
        while True:
            with self._condition:
                while len(self._tasks) == 0 and not self._shutdown_flag:
                    self._condition.wait()

                if self._shutdown_flag and len(self._tasks) == 0:
                    return  # Exit thread

                task, args, kwargs, future = self._tasks.popleft()

            # Execute OUTSIDE the lock — critical for concurrency!
            try:
                result = task(*args, **kwargs)
                future.set_result(result)
            except BaseException as e:
                # Propagate via Future, also log so failures aren't silent
                logger.exception(
                    "%s: task raised", threading.current_thread().name
                )
                future.set_exception(e)

    def submit(self, task: Callable[..., R], *args: Any, **kwargs: Any) -> Future[R]:
        """Enqueue a task. Returns a Future for the result. Wakes one idle worker."""
        future: Future[R] = Future()
        with self._condition:
            if self._shutdown_flag:
                raise RuntimeError("Pool is shut down")
            self._tasks.append((task, args, kwargs, future))
            self._condition.notify()    # Wake ONE worker
        return future

    def shutdown(self, wait: bool = True) -> None:
        """Signal all workers to finish pending tasks and stop."""
        with self._condition:
            self._shutdown_flag = True
            self._condition.notify_all()  # Wake ALL workers

        if wait:
            for t in self._workers:
                t.join()

    @property
    def pending_tasks(self) -> int:
        with self._lock:
            return len(self._tasks)
```

### Test It

```python
import time

def process(task_id: int) -> int:
    print(f"{threading.current_thread().name}: Start task {task_id}")
    time.sleep(0.5)
    return task_id * 10

pool = ThreadPool(num_workers=3)
futures = [pool.submit(process, i) for i in range(10)]

for f in futures:
    print("result:", f.result())

pool.shutdown(wait=True)
print("All done!")
```

### Key Points to Mention

1. **Execute outside the lock** — If you hold the lock while executing tasks, only one task runs at a time. Defeats the purpose.
2. **Return a Future** — Real-world pools (`concurrent.futures.ThreadPoolExecutor`) return futures so callers get results AND exceptions. A raw `submit()` that swallows exceptions in `print()` is a red flag for senior interviewers.
3. **`notify()` vs `notify_all()`** — `submit` uses `notify()` (wake one worker). `shutdown` uses `notify_all()` (wake all workers so they can exit).
4. **Graceful shutdown** — Workers finish their current task and drain the queue before exiting.
5. **Daemon threads** — Workers won't keep the program alive if you forget to call `shutdown()`.
6. **Catch `BaseException`, not `Exception`** — so `KeyboardInterrupt` / `SystemExit` raised in the task surface to the caller via `future.result()`.

---

## 6. Deadlock — 4 Conditions + Fixes

**Asked at:** Every company (theory + code)

### The Classic Deadlock

```python
import threading
import time

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:                # Holds A
        time.sleep(0.1)
        with lock_b:            # Waits for B... forever
            print("Thread 1")

def thread_2():
    with lock_b:                # Holds B
        time.sleep(0.1)
        with lock_a:            # Waits for A... forever
            print("Thread 2")

t1 = threading.Thread(target=thread_1)
t2 = threading.Thread(target=thread_2)
t1.start(); t2.start()
# HANGS FOREVER
```

### 4 Conditions (ALL Must Be True)

| # | Condition | Meaning | Break It By |
|---|-----------|---------|-------------|
| 1 | **Mutual Exclusion** | Only one thread holds the lock | Use lock-free structures |
| 2 | **Hold and Wait** | Hold one lock, wait for another | Acquire all locks at once |
| 3 | **No Preemption** | Can't force-take a lock | Use timeouts |
| 4 | **Circular Wait** | A→B, B→A | **Always lock in same order** |

### Fix 1: Consistent Lock Ordering (Best Fix)

```python
class BankAccount:
    """Thread-safe bank account with deadlock-free transfers."""

    _next_id = 0
    _id_lock = threading.Lock()

    def __init__(self, owner: str, balance: float = 0) -> None:
        with BankAccount._id_lock:           # protect ID generation too!
            self._id = BankAccount._next_id
            BankAccount._next_id += 1
        self._owner = owner
        self._balance = balance
        self._lock = threading.Lock()

    @property
    def id(self) -> int:
        return self._id

    @property
    def balance(self) -> float:
        with self._lock:
            return self._balance

    def deposit(self, amount: float) -> None:
        with self._lock:
            self._balance += amount

    def withdraw(self, amount: float) -> bool:
        with self._lock:
            if self._balance >= amount:
                self._balance -= amount
                return True
            return False

    @staticmethod
    def transfer(source: 'BankAccount', target: 'BankAccount', amount: float) -> bool:
        """Deadlock-free transfer — always lock the lower ID first."""
        first, second = sorted([source, target], key=lambda a: a._id)

        with first._lock:
            with second._lock:
                if source._balance >= amount:
                    source._balance -= amount
                    target._balance += amount
                    return True
                return False

    def __repr__(self) -> str:
        return f"BankAccount(id={self._id}, owner='{self._owner}', balance={self.balance})"
```

**Why this works:** Breaks circular wait. If everyone locks in the same order (lower ID first), no cycle can form.

**Test It:**

```python
alice = BankAccount("Alice", 1000)
bob = BankAccount("Bob", 1000)

def transfer_loop(src: BankAccount, dst: BankAccount) -> None:
    for _ in range(100):
        BankAccount.transfer(src, dst, 10)

t1 = threading.Thread(target=transfer_loop, args=(alice, bob))
t2 = threading.Thread(target=transfer_loop, args=(bob, alice))
t1.start(); t2.start()
t1.join(); t2.join()

print(f"{alice}")    # balance varies
print(f"{bob}")      # balance varies
print(f"Total: {alice.balance + bob.balance}")  # Always 2000
```

### Fix 2: Timeout

```python
def safe_work():
    if lock_a.acquire(timeout=1):
        try:
            if lock_b.acquire(timeout=1):
                try:
                    do_work()
                finally:
                    lock_b.release()
            else:
                print("Couldn't get lock_b — retry later")
        finally:
            lock_a.release()
    else:
        print("Couldn't get lock_a — retry later")
```

### Livelock (Follow-up Question)

Threads are running but making no progress — they keep releasing and retrying in lockstep.

```python
# ❌ Livelock — both threads keep "being polite"
def polite(my_lock, other_lock):
    while True:
        my_lock.acquire()
        if not other_lock.acquire(blocking=False):
            my_lock.release()       # "After you!"
            continue                # Other thread does the same thing!
        break
```

**Fix:** Add **random backoff** to break symmetry.

```python
import random

def fixed(my_lock, other_lock):
    while True:
        my_lock.acquire()
        if not other_lock.acquire(blocking=False):
            my_lock.release()
            time.sleep(random.uniform(0.001, 0.01))  # Random!
            continue
        break
```

### What to Say in Interview

> "Deadlock needs all four conditions: mutual exclusion, hold-and-wait, no preemption, and circular wait. The easiest to break is circular wait — I always acquire locks in a consistent global order, like sorting by object ID."

---

## 7. Reader-Writer Lock

**Asked at:** Google, Microsoft, Uber

### Problem

- Multiple **readers** can read simultaneously
- A **writer** needs exclusive access (no readers, no other writers)
- Prevent **writer starvation** (readers shouldn't keep starving writers)

### Mental Model

```
State 1: Multiple readers active       → new readers OK, writers WAIT
State 2: One writer active             → everyone else WAITS
State 3: Writer waiting                → new readers also WAIT (prevents starvation)
```

### Solution

```python
import threading
from contextlib import contextmanager
from typing import Iterator

class ReadWriteLock:
    """Writer-preferring read-write lock.

    - Multiple readers can hold the lock concurrently.
    - A writer gets exclusive access (no readers, no other writers).
    - Waiting writers block new readers to prevent writer starvation.

    Supports context manager usage:
        with rw_lock.read():
            ...
        with rw_lock.write():
            ...
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._can_read = threading.Condition(self._lock)
        self._can_write = threading.Condition(self._lock)
        self._readers = 0
        self._writing = False
        self._waiting_writers = 0

    def acquire_read(self) -> None:
        with self._lock:
            while self._writing or self._waiting_writers > 0:
                self._can_read.wait()
            self._readers += 1

    def release_read(self) -> None:
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._can_write.notify()

    def acquire_write(self) -> None:
        with self._lock:
            self._waiting_writers += 1
            try:
                while self._writing or self._readers > 0:
                    self._can_write.wait()
                self._writing = True
            finally:
                # decrement on success AND on exception (e.g., interrupted wait)
                self._waiting_writers -= 1

    def release_write(self) -> None:
        with self._lock:
            self._writing = False
            self._can_read.notify_all()     # Wake ALL waiting readers
            self._can_write.notify()        # Wake ONE waiting writer

    @contextmanager
    def read(self) -> Iterator[None]:
        """Context manager for read access: `with rw_lock.read():`"""
        self.acquire_read()
        try:
            yield
        finally:
            self.release_read()

    @contextmanager
    def write(self) -> Iterator[None]:
        """Context manager for write access: `with rw_lock.write():`"""
        self.acquire_write()
        try:
            yield
        finally:
            self.release_write()
```

### Test It

```python
import time

rw_lock = ReadWriteLock()
shared_data: dict[str, int] = {"value": 0}

def reader(rid: int) -> None:
    for _ in range(3):
        with rw_lock.read():                            # Context manager!
            print(f"Reader-{rid} reads: {shared_data['value']}")
            time.sleep(0.1)

def writer(wid: int) -> None:
    for i in range(3):
        with rw_lock.write():                           # Context manager!
            shared_data["value"] += 1
            print(f"Writer-{wid} wrote: {shared_data['value']}")
            time.sleep(0.2)

threads = (
    [threading.Thread(target=reader, args=(i,)) for i in range(3)] +
    [threading.Thread(target=writer, args=(i,)) for i in range(2)]
)
for t in threads: t.start()
for t in threads: t.join()
```

### Key Design Decision: Writer-Preferring

This implementation **blocks new readers** if a writer is waiting (`_waiting_writers > 0`). This prevents writer starvation.

| Policy | Behavior | Risk |
|--------|----------|------|
| Reader-preferring | New readers always allowed | Writers starve |
| **Writer-preferring** ✓ | New readers blocked if writer waiting | Readers may wait longer |
| Fair | FIFO ordering | More complex to implement |

---

## 8. Thread-Safe LRU Cache

**Asked at:** Uber, Amazon, Meta, Google

### Problem

Implement an LRU cache with `get(key)` and `put(key, value)` that's safe for concurrent access.

### Solution

```python
import threading
from collections import OrderedDict
from typing import TypeVar, Generic, Optional, Hashable

K = TypeVar('K', bound=Hashable)
V = TypeVar('V')

class ThreadSafeLRUCache(Generic[K, V]):
    """Thread-safe Least Recently Used cache with O(1) get/put.

    - get() returns None on miss (not -1).
    - put() evicts the least recently used entry when full.
    - All operations are atomic under a single lock.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._capacity = capacity
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    @property
    def capacity(self) -> int:
        return self._capacity

    def get(self, key: K) -> Optional[V]:
        """Get value by key. Returns None on miss. Marks as recently used."""
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: K, value: V) -> None:
        """Insert or update entry. Evicts LRU if at capacity."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                if len(self._cache) >= self._capacity:
                    self._cache.popitem(last=False)     # Evict LRU (front)
                self._cache[key] = value

    def contains(self, key: K) -> bool:
        with self._lock:
            return key in self._cache

    def remove(self, key: K) -> Optional[V]:
        """Remove and return value for key. Returns None if not found."""
        with self._lock:
            return self._cache.pop(key, None)
```

### Test It

```python
import time

cache: ThreadSafeLRUCache[str, str] = ThreadSafeLRUCache(capacity=3)

def writer(tid: int) -> None:
    for i in range(5):
        key, val = f"k{tid}-{i}", f"v{tid}-{i}"
        cache.put(key, val)
        print(f"Thread-{tid} put {key}={val} | size={cache.size}")
        time.sleep(0.05)

def reader(tid: int) -> None:
    for i in range(5):
        val = cache.get(f"k0-{i}")
        print(f"Thread-{tid} get k0-{i} = {val}")
        time.sleep(0.05)

threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
threads += [threading.Thread(target=reader, args=(i,)) for i in range(2)]
for t in threads: t.start()
for t in threads: t.join()
```

### Follow-up: Striped Locking (Higher Throughput, Approximate LRU)

If the interviewer asks "How would you scale this?":

```python
class StripedLRUCache(Generic[K, V]):
    """Sharded LRU cache for higher concurrent throughput.

    Splits into N shards by key hash. Each shard has its own lock and
    its own LRU order. Keys in different shards are accessed concurrently.

    TRADEOFF: This is approximate LRU, NOT global LRU. Eviction happens
    per-shard, so a hot shard can evict items more recently used (globally)
    than items kept in a cold shard. This is the same tradeoff Guava /
    Caffeine make. Call it out before the interviewer does.
    """

    def __init__(self, capacity: int, num_stripes: int = 16) -> None:
        self._num_stripes = num_stripes
        shard_cap = max(1, capacity // num_stripes)
        self._shards: list[ThreadSafeLRUCache[K, V]] = [
            ThreadSafeLRUCache(shard_cap) for _ in range(num_stripes)
        ]

    def _get_shard(self, key: K) -> ThreadSafeLRUCache[K, V]:
        return self._shards[hash(key) % self._num_stripes]

    def get(self, key: K) -> Optional[V]:
        return self._get_shard(key).get(key)

    def put(self, key: K, value: V) -> None:
        self._get_shard(key).put(key, value)

    def contains(self, key: K) -> bool:
        return self._get_shard(key).contains(key)
```

> "Instead of one global lock, I split the cache into 16 shards by hashing the key. Each shard has its own lock — different shards run in parallel, reducing contention by ~16x. The tradeoff is that LRU eviction is now per-shard, not global, so it's an *approximation* of LRU. Guava and Caffeine make the same tradeoff in production."

---

## 9. Dining Philosophers

**Asked at:** LeetCode 1226, Google, Microsoft

### Problem

5 philosophers at a round table. Each needs 2 adjacent forks to eat. Prevent deadlock.

### Solution: Lock Ordering

```python
import threading
import time
import random

class DiningPhilosophers:
    """Deadlock-free dining philosophers using consistent lock ordering.

    Each philosopher always picks up the lower-numbered fork first,
    breaking the circular wait condition.
    """

    def __init__(self, num_philosophers: int = 5) -> None:
        self._n = num_philosophers
        self._forks: list[threading.Lock] = [
            threading.Lock() for _ in range(num_philosophers)
        ]

    def philosopher(self, pid: int, num_meals: int = 3) -> None:
        left = pid
        right = (pid + 1) % self._n

        # KEY: always pick the lower-numbered fork first
        first = min(left, right)
        second = max(left, right)

        for meal in range(num_meals):
            # Think
            time.sleep(random.uniform(0.1, 0.3))

            # Pick up forks (consistent order — no deadlock!)
            self._forks[first].acquire()
            self._forks[second].acquire()

            # Eat
            print(f"Philosopher {pid}: Eating meal {meal + 1}")
            time.sleep(random.uniform(0.1, 0.2))

            # Put down forks (reverse order)
            self._forks[second].release()
            self._forks[first].release()

        print(f"Philosopher {pid}: Done!")


dp = DiningPhilosophers(num_philosophers=5)
threads = [threading.Thread(target=dp.philosopher, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()
```

### Why Lock Ordering Works

Without ordering: P0 grabs fork-0, P1 grabs fork-1, P2 grabs fork-2... → circular wait → deadlock.

With ordering (`min` first): P4 tries to grab fork-0 before fork-4 (since `min(4,0)=0`). So P4 and P0 compete for fork-0 first — no cycle possible.

### Alternative: Semaphore (Limit Diners)

```python
class DiningPhilosophersV2:
    """Deadlock-free dining via semaphore: at most N-1 can sit at once."""

    def __init__(self, num_philosophers: int = 5) -> None:
        self._n = num_philosophers
        self._forks: list[threading.Lock] = [
            threading.Lock() for _ in range(num_philosophers)
        ]
        self._seats = threading.Semaphore(num_philosophers - 1)

    def philosopher(self, pid: int, num_meals: int = 3) -> None:
        left = pid
        right = (pid + 1) % self._n

        for meal in range(num_meals):
            self._seats.acquire()         # Limit concurrent diners
            self._forks[left].acquire()
            self._forks[right].acquire()

            print(f"Philosopher {pid}: Eating meal {meal + 1}")
            time.sleep(0.1)

            self._forks[right].release()
            self._forks[left].release()
            self._seats.release()
```

> "If at most N-1 philosophers can sit at the table, at least one will always have both forks available. This breaks the circular wait condition."

---

## 10. Rate Limiter — Sliding Window

**Asked at:** Uber, Google, Meta

### How Sliding Window Differs from Token Bucket

| | Token Bucket | Sliding Window (log) | Sliding Window (counter) |
|---|---|---|---|
| Tracks | Token count | Timestamp of each request | Count per sub-window |
| Allows bursts? | Yes (up to capacity) | No (strict count per window) | No (slightly approximate) |
| Memory | O(1) | O(N), N = max_requests | O(1) |
| Use case | API throttling with burst | Strict, exact rate enforcement | Strict at scale |

### Solution: Exact Sliding Window (Log)

```python
import threading
import time
from collections import deque

class SlidingWindowRateLimiter(RateLimiter):
    """Rate limiter using exact sliding window over request timestamps.

    - Tracks the timestamp of each request in a deque.
    - Rejects if count within the window exceeds max_requests.
    - No bursts allowed (unlike Token Bucket).
    - Memory: O(max_requests).

    CAVEAT: under sustained burst, the deque can hold up to max_requests
    entries per limiter — fine for small limits (e.g., 100/sec) but
    expensive for very high limits. For high-throughput, prefer the
    counter-based approximation below.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            now = time.monotonic()

            # Remove expired timestamps
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()

            if len(self._timestamps) < self._max_requests:
                self._timestamps.append(now)
                return True
            return False
```

### Solution: Counter-Based Sliding Window (O(1) memory, approximate)

```python
class SlidingWindowCounterRateLimiter(RateLimiter):
    """Approximate sliding window using current + previous bucket counts.

    Memory is O(1) per limiter regardless of throughput. Used by Cloudflare,
    Stripe, and many edge rate limiters where memory matters more than
    perfect precision.

    Estimated count = previous_count * (1 - elapsed_in_current/window)
                    + current_count
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._curr_start = time.monotonic()
        self._curr_count = 0
        self._prev_count = 0
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._curr_start

            if elapsed >= 2 * self._window:
                # Both windows are stale
                self._prev_count = 0
                self._curr_count = 0
                self._curr_start = now
                elapsed = 0
            elif elapsed >= self._window:
                # Roll forward one window
                self._prev_count = self._curr_count
                self._curr_count = 0
                self._curr_start += self._window
                elapsed -= self._window

            weight = 1 - (elapsed / self._window)
            estimated = self._prev_count * weight + self._curr_count

            if estimated < self._max_requests:
                self._curr_count += 1
                return True
            return False
```

**Note:** Both implement the same `RateLimiter` ABC defined in Problem 4. You can swap them anywhere:

```python
limiter: RateLimiter = TokenBucketRateLimiter(rate=10, capacity=10)               # bursts
limiter: RateLimiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1) # strict, exact
limiter: RateLimiter = SlidingWindowCounterRateLimiter(10, 1)                      # strict, O(1) mem
```

---

## 11. Print In Order

**Asked at:** LeetCode 1114, Amazon, Google

### Problem

Three threads call `first()`, `second()`, `third()` in any order. Output must always be "first second third".

### Solution

```python
import threading

class PrintInOrder:
    """Ensures three functions execute in order regardless of thread start order.

    Uses Events for pure signaling — no shared data to protect.
    """

    def __init__(self) -> None:
        self._first_done = threading.Event()
        self._second_done = threading.Event()

    def first(self) -> None:
        print("first", end=" ")
        self._first_done.set()

    def second(self) -> None:
        self._first_done.wait()       # Block until first() completes
        print("second", end=" ")
        self._second_done.set()

    def third(self) -> None:
        self._second_done.wait()      # Block until second() completes
        print("third")


# Test: threads start in reverse order, output is always "first second third"
order = PrintInOrder()
threads = [
    threading.Thread(target=order.third),
    threading.Thread(target=order.first),
    threading.Thread(target=order.second),
]
for t in threads: t.start()
for t in threads: t.join()
# Output: first second third
```

**Why Events:** No shared data to protect — we just need signaling. Events are simpler than Conditions for pure signaling.

---

## 12. Print FooBar Alternately

**Asked at:** LeetCode 1115, Google, Meta

### Problem

Two threads print "foobar" N times, strictly alternating. Output: `foobarfoobarfoobar...`

### Solution

```python
import threading

class FooBar:
    """Two threads alternate printing 'foo' and 'bar' N times.

    Pattern: Two events ping-ponging.
    Thread A waits on its event, prints, clears its own, then sets B's.
    """

    def __init__(self, n: int) -> None:
        self._n = n
        self._foo_event = threading.Event()
        self._bar_event = threading.Event()
        self._foo_event.set()    # foo goes first

    def foo(self) -> None:
        for _ in range(self._n):
            self._foo_event.wait()
            print("foo", end="", flush=True)
            self._foo_event.clear()
            self._bar_event.set()

    def bar(self) -> None:
        for _ in range(self._n):
            self._bar_event.wait()
            print("bar", end="", flush=True)
            self._bar_event.clear()
            self._foo_event.set()


# Test
fb = FooBar(n=3)
t1 = threading.Thread(target=fb.foo)
t2 = threading.Thread(target=fb.bar)
t1.start(); t2.start()
t1.join(); t2.join()
print()
# Output: foobarfoobarfoobar
```

**Pattern:** Two events ping-ponging. Thread A waits on its event, prints, clears its own, then sets B's. Thread B does the reverse.

---

## 13. Scheduled Task Executor

**Asked at:** Uber, Google, Amazon

### Problem

Run tasks at a future time, or repeatedly at fixed intervals. Think: retry failed payments, send ride reminders.

### Key Insight

Use a **min-heap** ordered by execution time. Workers sleep until the next task is due using `condition.wait(timeout)`.

> **Why a `task_id` tiebreaker?** `heapq` will compare the next field if `run_at` ties. `Callable` objects aren't comparable (`<` is not defined), so without an integer tiebreaker, `heappush` raises `TypeError` on tie. The monotonically-increasing `task_id` makes ties deterministic AND avoids comparing callables.

### Solution

```python
import threading
import time
import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

@dataclass(order=True)
class ScheduledTask:
    """A task scheduled for future execution. Ordered by (run_at, task_id)
    for the min-heap. task_id breaks ties so we never compare Callables."""
    run_at: float
    task_id: int
    func: Callable = field(compare=False)
    args: tuple = field(default=(), compare=False)
    period: float = field(default=0, compare=False)   # 0 = one-shot


class ScheduledExecutor:
    """Runs tasks at a future time, or repeatedly at fixed intervals.

    Uses a min-heap ordered by execution time. Workers sleep until
    the next task is due via condition.wait(timeout) — no busy polling.

    Periodic tasks use 'fixed-rate' semantics: the next run_at is computed
    from the *previous scheduled* run_at, not from completion time.
    This prevents drift if a task takes a long time.

    Use cases: retry failed payments, send ride reminders, heartbeats.
    """

    def __init__(self, num_workers: int = 2) -> None:
        self._task_queue: list[ScheduledTask] = []   # Min-heap
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._task_counter = 0
        self._shutdown_flag = False
        self._workers: list[threading.Thread] = []

        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)

    def schedule(self, func: Callable, delay_seconds: float, *args: Any) -> None:
        """Run func once after delay_seconds."""
        run_at = time.monotonic() + delay_seconds
        with self._condition:
            self._task_counter += 1
            heapq.heappush(
                self._task_queue,
                ScheduledTask(run_at, self._task_counter, func, args)
            )
            self._condition.notify()

    def schedule_at_fixed_rate(
        self, func: Callable, initial_delay: float, period: float, *args: Any
    ) -> None:
        """Run func every `period` seconds, starting after initial_delay.
        Fixed-rate: next = scheduled + period (no drift from execution time)."""
        if period <= 0:
            raise ValueError("period must be positive")
        run_at = time.monotonic() + initial_delay
        with self._condition:
            self._task_counter += 1
            heapq.heappush(
                self._task_queue,
                ScheduledTask(run_at, self._task_counter, func, args, period)
            )
            self._condition.notify()

    def _worker(self) -> None:
        while True:
            task: Optional[ScheduledTask] = None

            with self._condition:
                while True:
                    if self._shutdown_flag:
                        return

                    if not self._task_queue:
                        self._condition.wait()
                        continue

                    next_run = self._task_queue[0].run_at
                    now = time.monotonic()

                    if now >= next_run:
                        task = heapq.heappop(self._task_queue)
                        break
                    else:
                        # Sleep until next task is due (or new task arrives)
                        self._condition.wait(timeout=next_run - now)

            # Execute OUTSIDE the lock
            try:
                task.func(*task.args)
            except Exception as e:
                print(f"Task error: {e}")

            # Reschedule if periodic — FIXED RATE (no drift)
            if task.period > 0:
                with self._condition:
                    self._task_counter += 1
                    next_run_at = task.run_at + task.period
                    # If we fell badly behind, skip missed runs to catch up
                    now = time.monotonic()
                    if next_run_at < now:
                        # snap forward to the next aligned slot
                        missed = int((now - next_run_at) // task.period) + 1
                        next_run_at += missed * task.period
                    heapq.heappush(
                        self._task_queue,
                        ScheduledTask(
                            next_run_at,
                            self._task_counter,
                            task.func,
                            task.args,
                            task.period,
                        )
                    )
                    self._condition.notify()

    def shutdown(self) -> None:
        """Stop all workers after current tasks complete."""
        with self._condition:
            self._shutdown_flag = True
            self._condition.notify_all()
        for t in self._workers:
            t.join()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._task_queue)
```

### Test It

```python
scheduler = ScheduledExecutor(num_workers=2)

scheduler.schedule(
    lambda: print(f"[{time.strftime('%H:%M:%S')}] One-time task!"), 2
)
scheduler.schedule_at_fixed_rate(
    lambda: print(f"[{time.strftime('%H:%M:%S')}] Heartbeat"), 0, 1
)
scheduler.schedule(
    lambda: print(f"[{time.strftime('%H:%M:%S')}] Delayed task!"), 5
)

time.sleep(6)
scheduler.shutdown()
print("Scheduler stopped.")
```

### Fixed-Rate vs Fixed-Delay (Common Follow-up)

| Mode | Next run = | Use case |
|------|------------|----------|
| **Fixed-rate** (this code) | `previous_scheduled + period` | Heartbeats, metrics — must run at consistent times |
| Fixed-delay | `completion_time + period` | Retry-with-cooldown — gap between runs matters |

> "The bug to avoid is `next = time.monotonic() + period` after execution — that's neither fixed-rate nor fixed-delay, it drifts by however long the task took. Java's `ScheduledExecutorService` exposes both `scheduleAtFixedRate` and `scheduleWithFixedDelay` for this reason."

### Why Heap + Condition.wait(timeout)?

- **Heap** gives O(log n) insert and O(1) peek at the earliest task
- **`wait(timeout)`** sleeps the worker exactly until the next task is due — no busy polling
- If a **new earlier task** is submitted, `notify()` wakes the worker to recalculate the wait time

---

## Testing Concurrent Code

> Interviewers often ask: *"How would you test this is actually thread-safe?"* A great answer separates senior candidates.

### Pattern 1: `threading.Barrier` for Maximum Contention

A `Barrier` makes all threads start at exactly the same moment, maximizing the chance of races.

```python
import threading

def test_counter_no_races():
    counter = ThreadSafeCounter()
    n_threads, n_iters = 16, 10_000
    barrier = threading.Barrier(n_threads)

    def worker():
        barrier.wait()                   # all threads start together
        for _ in range(n_iters):
            counter.increment()

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert counter.value == n_threads * n_iters, \
        f"Race! expected {n_threads*n_iters}, got {counter.value}"
```

### Pattern 2: Invariant Checks Under Load

For BankAccount transfer (Problem 6): total balance must always equal initial total.

```python
def test_transfer_preserves_total():
    accts = [BankAccount(f"A{i}", 1000) for i in range(10)]
    initial_total = sum(a.balance for a in accts)
    barrier = threading.Barrier(20)

    def chaos():
        barrier.wait()
        import random
        for _ in range(1000):
            src, dst = random.sample(accts, 2)
            BankAccount.transfer(src, dst, random.randint(1, 50))

    threads = [threading.Thread(target=chaos) for _ in range(20)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert sum(a.balance for a in accts) == initial_total
```

### Pattern 3: Deadlock Detection via Timeout

```python
def test_no_deadlock():
    t = threading.Thread(target=run_dining_philosophers)
    t.start()
    t.join(timeout=10)
    assert not t.is_alive(), "Deadlock detected — thread still running after 10s"
```

### What to Mention

- **Race conditions are non-deterministic** — a test passing once doesn't prove correctness. Run with `pytest-repeat` or in a loop.
- **Tools:** `ThreadSanitizer` (C/C++/Rust), Java's `jcstress`, Python's `faulthandler` for deadlock dumps.
- **GIL caveat:** the GIL hides some races in CPython that would manifest in Jython / PyPy / free-threaded builds. Stress tests with `n_threads >> n_cores` and small critical sections still expose them.

---

## Interview Delivery Tips

### Before Coding (2 min)

1. **Clarify:** "How many producers/consumers? Is there a max capacity? Do we need graceful shutdown?"
2. **Identify shared state:** List every variable that multiple threads touch
3. **Pick primitives:** "I'll use a Condition variable because threads need to wait for a state change"

### While Coding (15-20 min)

4. **Name things clearly:** `not_full`, `not_empty`, `shutdown_flag` — not `cv1`, `cv2`, `flag`
5. **Always `while` with `wait()`** — say "for spurious wakeups" out loud
6. **Execute outside the lock** — show you know about lock granularity
7. **Use `with` for all locks** — never forget to release
8. **Use `deque`, not `list`** for queues — `list.pop(0)` is O(n)

### After Coding (3-5 min)

9. **Walk through with 2 threads:** "Thread A calls produce(), buffer is full, so it waits. Thread B calls consume(), removes an item, notifies not_full. Thread A wakes up, re-checks the while, buffer has space, adds the item."
10. **State complexity:** "put() and get() are both O(1). Space is O(capacity)."
11. **Mention edge cases:** shutdown, timeout, empty/full boundaries
12. **Propose a test plan:** Barrier-based stress test + invariant check (see Testing section)

### Common Follow-ups to Prepare

| Question | Your Answer |
|----------|-------------|
| "Does threading help in Python?" | GIL serializes Python bytecode → great for I/O, useless for CPU-bound (use `multiprocessing`) |
| "Threads or asyncio?" | Threads for ≤ hundreds of ops; asyncio for thousands of I/O-bound (lower memory) |
| "How would you scale this?" | Shard by key/user, each shard has its own lock |
| "Can you make it lock-free?" | Use CAS / compare-and-swap (mention, don't implement unless asked) |
| "What about fairness?" | Use a FIFO queue for lock acquisition, or `queue.Queue` which is inherently FIFO |
| "What happens on shutdown?" | Set flag, `notify_all()`, workers drain queue, then exit |
| "Why not use `queue.Queue`?" | "I would in production, but you asked me to build it from scratch" |
| "How do you test it?" | `threading.Barrier` to maximize contention + invariant checks + run in a loop |
| "Fixed-rate vs fixed-delay scheduling?" | Fixed-rate = `prev_scheduled + period` (heartbeats); Fixed-delay = `completion + period` (retries) |
| "What about exceptions in workers?" | Propagate via `Future.set_exception`, also log — never swallow silently |