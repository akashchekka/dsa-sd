# Python Queue

> A from-first-principles guide to the ideas behind threads, the GIL, condition
> variables, queues, backpressure, and event loops. Written to build intuition,
> not just list APIs. Every section ends with a one-line answer you can say in an
> interview.

---

## Table of Contents

1. [The GIL: "Python is single-threaded" — what that really means](#1-the-gil-python-is-single-threaded--what-that-really-means)
2. [Why you still need locks even with the GIL](#2-why-you-still-need-locks-even-with-the-gil)
3. [Threads sleep and wake: `wait()` and `notify()`](#3-threads-sleep-and-wake-wait-and-notify)
4. [Condition variables: a lock plus a waiting room](#4-condition-variables-a-lock-plus-a-waiting-room)
5. [Inside `queue.Queue`: one mutex, three waiting rooms](#5-inside-queuequeue-one-mutex-three-waiting-rooms)
6. [The producer/consumer handshake](#6-the-producerconsumer-handshake)
7. [Always re-check in a `while` loop](#7-always-re-check-in-a-while-loop)
8. [Backpressure: block vs. fail-fast](#8-backpressure-block-vs-fail-fast)
9. [Threads vs. asyncio: preemptive vs. cooperative](#9-threads-vs-asyncio-preemptive-vs-cooperative)
10. [`await` vs. `block=True`](#10-await-vs-blocktrue)
11. [Node.js event loop: same goal, different machinery](#11-nodejs-event-loop-same-goal-different-machinery)
12. [One-page summary](#12-one-page-summary)

---

## 1. The GIL: "Python is single-threaded" — what that really means

People say "Python is single-threaded." That is imprecise. The accurate version:

> CPython has **real OS threads**, but the **GIL** (Global Interpreter Lock)
> allows only **one thread to execute Python bytecode at a time.**

Two separate ideas that get conflated:

- **How many threads exist?** As many as you create. They are genuine OS threads scheduled by the operating system.
- **How many run Python code at once?** Exactly one. Threads take turns holding the GIL.

So "single-threaded" really means *"no two threads run Python bytecode truly in parallel"* — not *"there is only one thread."*

### Why threads still help: the GIL is released while waiting

This is the crucial part. The GIL is **not** held while a thread is blocked on I/O
or waiting. When a thread calls something that blocks — `queue.get()` on an empty
queue, `time.sleep()`, a socket read, `lock.acquire()`, `condition.wait()` —
CPython **releases the GIL** so another thread can run.

Trace a worker draining a queue:

1. Worker calls `inbox.get()` on an empty queue → blocks → **GIL released**, worker sleeps.
2. Another thread now holds the GIL, runs `publish(...)` → `put()` → `notify()`.
3. Worker wakes, reacquires the GIL when scheduled, processes the item.

Progress happens by **interleaving**, not by running at the same microsecond.

### Concurrency vs. parallelism

| | Runs Python in parallel? | Good for |
|---|---|---|
| **Concurrency** (threads + GIL) | No — interleaved | I/O-bound work (network, disk, queues) |
| **Parallelism** (multiprocessing / C ext) | Yes — multiple cores | CPU-bound work (number crunching) |

Threads shine for **I/O/wait-bound** work, where the thread mostly sleeps waiting.
For **CPU-bound** work the GIL serializes threads, so you reach for
`multiprocessing` or a native extension instead.

> **The 2026 footnote:** Python 3.13+ ships an experimental **free-threaded**
> build (PEP 703) that can run without the GIL — real bytecode parallelism. When
> the GIL is gone, your locks become load-bearing for real parallelism, not just
> for safe interleaving.

**One-liner:** *"CPython threads are real OS threads, but the GIL lets only one
run Python bytecode at a time. Blocking calls release the GIL, so a worker sleeps
while a publisher runs — that interleaving is enough for I/O-bound work."*

---

## 2. Why you still need locks even with the GIL

If only one thread runs Python at a time, why lock anything? Because the GIL
protects **one bytecode instruction**, not your **logical operation.**

A thread can be suspended *between* bytecodes. A single line of Python is often
several bytecodes, so a thread can be paused **mid-statement.** That breaks any
multi-step "check-then-act":

```python
topic = self._topics.get(name)   # bytecode(s) A
if topic is None:
    topic = Topic(name)          # <-- thread can be paused right here
    self._topics[name] = topic   # bytecode(s) B
```

Two threads can both run the check, both see `None`, and both create a topic — a
race, even under the GIL. That is why check-then-act must run under a lock:

```python
with self._lock:
    topic = self._topics.get(name)   # re-check under the lock
    if topic is None:
        topic = Topic(name)
        self._topics[name] = topic
```

> The GIL makes **individual bytecodes** atomic. It does **not** make your
> **critical sections** atomic. That is your job.

**One-liner:** *"The GIL only makes single bytecodes atomic, not my check-then-act
sections, because a thread can be preempted mid-statement — so I still need locks."*

---

## 3. Threads sleep and wake: `wait()` and `notify()`

`wait()` and `notify()` operate on **threads**:
`wait()` puts a thread to sleep; `notify()` wakes a sleeping thread. Three details
make it precise.

### `wait()` also releases the lock while sleeping

`wait()` does three things **atomically**:

```
1. release the lock          → so another thread can change the state
2. put this thread to sleep  → no CPU wasted (not a busy-loop)
3. on wakeup: re-acquire the lock before returning
```

Releasing the lock is essential — a sleeping thread that kept the lock would block
everyone from changing the very state it waits for. That is a deadlock.

### `notify()` makes a thread *runnable*, not *running*

`notify()` moves one waiting thread from "sleeping" to "ready." It cannot proceed
until it **re-acquires the lock**, which the notifier still holds:

```python
with self.not_empty:          # notifier holds the lock here
    self._put(item)
    self.not_empty.notify()   # marks a waiter runnable...
# lock released here → only NOW can the woken thread grab it and continue
```

The woken thread wakes up *inside* its own `wait()` call, reacquires the lock, and
then returns. It is a handoff, not an instant jump.

### You must hold the lock to call `wait()` or `notify()`

Both require the associated lock be held (hence they always run inside a
`with condition:` block). Calling them without the lock raises `RuntimeError`.

**One-liner:** *"`wait()` sleeps the calling thread and drops the lock; `notify()`
wakes one sleeping thread, which must reacquire the lock before continuing."*

---

## 4. Condition variables: a lock plus a waiting room

A **condition variable** = a lock + a "waiting room." It lets a thread sleep
efficiently until some state changes, instead of busy-looping and burning CPU.

```python
# ❌ Busy waiting — spins and wastes an entire core
while not ready:
    pass

# ✅ Condition variable — sleeps until signalled
with condition:
    while not ready:
        condition.wait()     # sleep, release lock; wake on notify()
    use(data)
```

| Method | What it does |
|---|---|
| `condition.wait()` | Release lock + sleep until notified (then reacquire lock) |
| `condition.wait(timeout)` | Same, but give up after `timeout` seconds |
| `condition.notify()` | Wake **one** waiting thread |
| `condition.notify_all()` | Wake **all** waiting threads (they race for the lock) |

**One-liner:** *"A condition variable is a lock with a waiting room — threads
`wait()` to sleep and others `notify()` to wake them, all without busy-looping."*

---

## 5. Inside `queue.Queue`: one mutex, three waiting rooms

`queue.Queue` is thread-safe because it is built on condition variables. It creates
**three** conditions that all share the **same** underlying mutex:

```python
self.mutex          = threading.Lock()
self.not_empty      = threading.Condition(self.mutex)  # consumers wait here
self.not_full       = threading.Condition(self.mutex)  # producers wait here
self.all_tasks_done = threading.Condition(self.mutex)  # join() waits here
```

- `not_empty` — a consumer waits here when the queue is **empty**.
- `not_full` — a producer waits here when a **bounded** queue is **full**.
- `all_tasks_done` — `join()` waits here until every item has been processed.

### Why share one mutex?

Because there is really only **one lock** protecting the queue's internal state,
with three separate waiting rooms on it. Holding *any* of the three conditions is
the same as holding the single mutex.

That is why `put()` can enter under `not_full` yet legally call
`not_empty.notify()` — the two conditions are backed by the **identical** lock
object. It looks like you are touching a "different" condition, but under the hood
it is the same lock.

**One-liner:** *"`queue.Queue` uses one mutex with three condition variables —
not-empty, not-full, and all-tasks-done — so producers, consumers, and `join()`
each have their own waiting room on the same lock."*

---

## 6. The producer/consumer handshake

Each side waits on its **own** condition and notifies the **other** side.

| Method | Enters under (may wait) | Notifies (wakes the other side) |
|---|---|---|
| `put` | `not_full` | `not_empty` |
| `get` | `not_empty` | `not_full` |

- **`put`** on a full bounded queue waits on `not_full` for a slot; after adding an
  item it calls `not_empty.notify()` to wake a waiting consumer.
- **`get`** on an empty queue waits on `not_empty` for an item; after removing one
  it calls `not_full.notify()` to wake a waiting producer.

```
put():  wait on not_full  ──►  add item  ──►  notify not_empty
get():  wait on not_empty ──►  take item ──►  notify not_full
```

The full cycle:

- `put` adds an item → notifies `not_empty` → a blocked `get` wakes.
- `get` removes an item → notifies `not_full` → a blocked `put` wakes.

This is the efficient blocking hand-off between producer and consumer — and you get
it without writing a single lock or sleep loop yourself.

**One-liner:** *"Producer waits on not-full and signals not-empty; consumer waits
on not-empty and signals not-full — one shared lock, two waiting rooms, each side
wakes the other."*

---

## 7. Always re-check in a `while` loop

Queue waits use `while`, never a plain `if`:

```python
while not self._qsize():
    self.not_empty.wait()
```

Returning from `wait()` only means the thread was **woken** — not that its
condition is now true. It must re-check because:

- **another consumer grabbed the item first** — woken, but too late,
- **`notify_all()`** woke several threads for a single item, or
- **spurious wakeup** — the OS/runtime can wake a thread with no `notify()` at all.

So the golden rule of condition variables is:

> **wake → reacquire the lock → re-check the condition → sleep again if still unsatisfied.**

Using `if` instead of `while` is a classic interview red flag — it processes state
that may no longer be valid.

**One-liner:** *"I loop on `while` around `wait()` because waking doesn't guarantee
the condition holds — spurious wakeups and lost races mean I must re-check."*

---

## 8. Backpressure: block vs. fail-fast

**Backpressure** is a slow consumer pushing back on a fast producer so the system
does not accumulate unbounded work.

- **Unbounded queue:** if publishers outpace the consumer, the queue grows forever
  until the process runs out of memory.
- **Bounded queue (`maxsize=N`):** caps how much can pile up and forces a decision
  when full.

Both behaviors map directly onto `queue.Queue`:

| Behavior | Call | When queue is full |
|---|---|---|
| **Block (backpressure)** | `put(item, block=True)` | Wait for a slot; producer is slowed to the consumer's rate |
| **Fail-fast** | `put(item, block=False)` | Raise `queue.Full` immediately; caller sheds load / retries / drops |

Other real-world policies (not built into `queue.Queue`, worth naming): drop-oldest,
drop-newest, or spill to disk.

Note: on an **unbounded** queue, `maxsize <= 0`, so `put` never blocks and never
raises `Full` — the "full" branch simply does not exist.

**One-liner:** *"Bounded queue plus `put(block=True)` gives backpressure — the
producer waits for space; `put(block=False)` fails fast with `queue.Full` so the
caller can shed load."*

---

## 9. Threads vs. asyncio: preemptive vs. cooperative

Both give you "one thing runs my code at a time," but the mechanism is opposite.

| | Threads + GIL | asyncio |
|---|---|---|
| How many OS threads | Many (one holds the GIL) | **One** |
| Runs your code one at a time? | Yes (GIL) | Yes (single thread) |
| When can it switch? | **Anytime** the runtime decides — **preemptive**, between bytecodes | **Only at `await`** — **cooperative** |
| Switch can land mid-statement? | **Yes** → need locks | **No** → check-then-act with no `await` is atomic |
| Who controls the switch | Interpreter / OS scheduler | Your `await` points |

- **Threads (preemptive):** many threads, one runs at a time, and it can be
  interrupted **anywhere** — even mid-statement — so you lock critical sections.
- **asyncio (cooperative):** one thread the entire time, interrupted **only where
  you write `await`** — so check-then-act with no `await` in the middle is atomic
  by construction, and needs no lock.

```python
# asyncio: no await in the middle → nothing else can interleave here
topic = topics.get(name)
if topic is None:
    topic = Topic(name)
    topics[name] = topic          # atomic by construction (no await)
```

The catch: in asyncio a **blocking** call (a slow synchronous DB call,
`time.sleep`, heavy CPU) freezes the **entire** loop — all coroutines stall,
because it is all one thread. In threads, one slow task only ties up its own
thread; the OS keeps the others moving.

**One-liner:** *"Threads are preemptive — the scheduler can interrupt anywhere, so
I need locks. asyncio is cooperative — it switches only at `await`, so no locks
between awaits, but a blocking call freezes everything."*

---

## 10. `await` vs. `block=True`

`asyncio.Queue` has **no `block` parameter.** The choice of *which call* you make
expresses the behavior:

| Behavior | `queue.Queue` (threads) | `asyncio.Queue` (event loop) |
|---|---|---|
| Wait until ready | `get(block=True)` | `await queue.get()` |
| Fail fast | `get(block=False)` → `queue.Empty` | `queue.get_nowait()` → `asyncio.QueueEmpty` |
| Wait for space | `put(block=True)` | `await queue.put(item)` |
| Fail fast on full | `put(block=False)` → `queue.Full` | `queue.put_nowait(item)` → `asyncio.QueueFull` |

`await queue.get()` gives you the **same waiting semantics** as `block=True`, but
the mechanism differs:

- **`block=True` (threads):** the OS thread **sleeps** (GIL released; another thread runs).
- **`await` (asyncio):** the coroutine **suspends**; **no thread blocks** — control
  returns to the event loop, which runs other coroutines on the same thread.

> `await queue.get()` = the "wait until ready" of `block=True`, achieved by
> yielding to the event loop instead of parking a thread.

**One-liner:** *"`asyncio.Queue` replaces `block=True` with `await queue.get()` and
`block=False` with `get_nowait()`. `await` waits the same way but suspends a
coroutine and yields to the loop instead of blocking a thread."*

---

## 11. Node.js event loop: same goal, different machinery

The **spirit** matches asyncio (don't block while waiting), but do not equate it
with Python threads.

### What's similar

Both serialize *your* code and get throughput by **not blocking on I/O**:

- **CPython:** many OS threads, GIL lets one run bytecode at a time.
- **Node.js:** one thread runs your JavaScript — the event loop — one callback at a time.

### The key difference

| | CPython threads | Node.js event loop |
|---|---|---|
| Model | **Preemptive** multithreading | **Cooperative** single thread |
| Who switches tasks | OS scheduler — anywhere | The loop — only at `await` / callback boundaries |
| How you wait | Thread **blocks** (GIL released) | You **don't block** — register a callback / `await`, return to the loop |
| Race conditions mid-task | **Yes** → need locks | **No** → a function runs to completion before other JS runs |

### Node is not single-threaded underneath

JS execution is single-threaded, but Node uses **libuv**, which has a background
**thread pool** (default 4) for work that cannot be async at the OS level — file
I/O, DNS, crypto, zlib. Your callbacks run on one thread; the blocking work is
offloaded to that pool and posted back as callbacks.

### The closest mapping

A message-bus worker loop and Node's loop rhyme:

```
worker loop:                 node loop:
while True:                  while (tasksPending):
    msg = inbox.get()   ≈        cb = readyQueue.dequeue()   # I/O completions, timers
    deliver(msg)                 cb()                         # run one callback to completion
```

Both are **a single consumer draining a queue of ready work, one item at a time.**
The difference is how an item becomes "ready": Node's OS/libuv pushes completed-I/O
callbacks; a bus's publishers push messages.

> Python's true analog to the Node model is **`asyncio`**, not `threading`.

**One-liner:** *"Node is a single-threaded cooperative event loop that switches
only at `await`, so no locks mid-task; my threaded bus is preemptive and needs
locks. Python's Node analog is `asyncio`, and Node still uses libuv's thread pool
for blocking I/O."*

---

## 12. One-page summary

| Concept | The crisp truth |
|---|---|
| "Python is single-threaded" | Many real OS threads; the GIL lets only one run bytecode at a time |
| GIL + I/O | Blocking calls release the GIL, so threads interleave and I/O-bound work speeds up |
| Why locks despite the GIL | The GIL makes single bytecodes atomic, not your check-then-act sections |
| `wait()` | Sleeps the calling thread and atomically releases the lock |
| `notify()` | Marks one sleeping thread runnable; it must reacquire the lock to proceed |
| Condition variable | A lock + a waiting room; sleep until signalled, no busy-loop |
| `queue.Queue` internals | One mutex, three conditions: not-empty, not-full, all-tasks-done |
| Producer/consumer | Wait on your own condition, notify the other side |
| `while` around `wait()` | Re-check after waking — spurious wakeups and lost races are real |
| Backpressure | Bounded queue + `block=True` (wait) or `block=False` (fail fast) |
| Threads vs asyncio | Preemptive (interrupt anywhere, need locks) vs cooperative (switch only at `await`) |
| `await` vs `block=True` | Same "wait until ready" semantics; suspends a coroutine vs parks a thread |
| Node.js | Cooperative single-thread loop (like asyncio); libuv thread pool does blocking I/O |
| CPU-bound work | Threads won't help under the GIL — use `multiprocessing` or native code |
