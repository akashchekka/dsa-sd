---
description: Interview preparation guide for Python multithreading, synchronization, debugging, and concurrent system design
---

# Multithreading & Concurrency in Python — FAANG Interview Guide

> **Goal:** Understand concurrency from scratch, then solve machine coding / LLD rounds at Uber, Google, Meta, Amazon, etc. All examples in Python.

---

## Table of Contents

- [Multithreading \& Concurrency in Python — FAANG Interview Guide](#multithreading--concurrency-in-python--faang-interview-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Why Concurrency?](#1-why-concurrency)
  - [Concurrency vs Parallelism](#concurrency-vs-parallelism)
    - [Key Terms (Just 4 to Start)](#key-terms-just-4-to-start)
  - [2. Threads, Processes \& the GIL](#2-threads-processes--the-gil)
    - [Thread vs Process](#thread-vs-process)
    - [Shared and Private Thread State](#what-threads-share-and-keep-private)
    - [Thread Lifecycle and Switch Costs](#thread-lifecycle-and-context-switching)
    - [Runtime and OS Thread Models](#user-threads-vs-kernel-threads)
    - [Scheduling and Workload Selection](#scheduling-and-workload-type)
    - [Python's GIL (Global Interpreter Lock)](#pythons-gil-global-interpreter-lock)
  - [3. Creating Threads](#3-creating-threads)
    - [Basic Thread Creation](#basic-thread-creation)
    - [Daemon Threads](#daemon-threads)
    - [Key Methods](#key-methods)
  - [4. Race Conditions — The Core Problem](#4-race-conditions--the-core-problem)
    - [The Classic Bug](#the-classic-bug)
    - [Why Does This Happen?](#why-does-this-happen)
    - [Types of Race Conditions](#types-of-race-conditions)
    - [Fix: Use a Lock](#fix-use-a-lock)
    - [Data Race vs Race Condition](#data-race-vs-race-condition)
    - [Atomicity, Visibility, and Ordering](#atomicity-visibility-and-ordering)
    - [Happens-Before](#happens-before)
    - [Python Interview Rules for Shared State](#python-interview-rules-for-shared-state)
  - [5. Locks (Mutex)](#5-locks-mutex)
    - [Basic Usage](#basic-usage)
    - [Ownership and Lock Granularity](#lock-ownership-and-granularity)
    - [Bank Account Example](#bank-account-example)
    - [Rules for Using Locks](#rules-for-using-locks)
  - [6. RLock (Reentrant Lock)](#6-rlock-reentrant-lock)
    - [When Do You Need RLock?](#when-do-you-need-rlock)
  - [7. Condition Variables](#7-condition-variables)
    - [The Problem Without Conditions](#the-problem-without-conditions)
    - [The Solution: Condition Variables](#the-solution-condition-variables)
    - [How `condition.wait()` Works (3 Steps, Atomic)](#how-conditionwait-works-3-steps-atomic)
    - [Key Methods](#key-methods-1)
    - [Why `while` Not `if`?](#why-while-not-if)
  - [8. Semaphores](#8-semaphores)
    - [BoundedSemaphore — Safer Version](#boundedsemaphore--safer-version)
    - [Semaphore vs Lock](#semaphore-vs-lock)
  - [9. Events](#9-events)
    - [Event Methods](#event-methods)
    - [Event vs Condition](#event-vs-condition)
  - [10. Barriers](#10-barriers)
  - [11. Thread-Safe Data Structures](#11-thread-safe-data-structures)
    - [queue.Queue — Thread-Safe Queue](#queuequeue--thread-safe-queue)
    - [Queue Variants](#queue-variants)
    - [collections.deque vs queue.Queue](#collectionsdeque-vs-queuequeue)
  - [12. Deadlock, Livelock \& Starvation](#12-deadlock-livelock--starvation)
    - [Deadlock](#deadlock)
    - [4 Conditions for Deadlock (ALL must be true)](#4-conditions-for-deadlock-all-must-be-true)
    - [Fix: Consistent Lock Ordering](#fix-consistent-lock-ordering)
    - [Fix: Timeout](#fix-timeout)
    - [Livelock](#livelock)
    - [Starvation](#starvation)
    - [Priority Inversion](#priority-inversion)
    - [Deadlock Prevention Checklist](#deadlock-prevention-checklist)
    - [Summary](#summary)
  - [13. Thread Pool (concurrent.futures)](#13-thread-pool-concurrentfutures)
    - [map() — Simpler API](#map--simpler-api)
    - [ProcessPoolExecutor — For CPU-Bound Work](#processpoolexecutor--for-cpu-bound-work)
    - [When to Use What](#when-to-use-what)
    - [Sizing a Thread Pool](#sizing-a-thread-pool)
    - [Backpressure and Queue Capacity](#backpressure-and-queue-capacity)
    - [Thread Pool Failure Modes](#thread-pool-failure-modes)
    - [Shutdown and Exception Handling](#shutdown-and-exception-handling)
  - [14. async/await (asyncio)](#14-asyncawait-asyncio)
    - [async vs threading — When to Use](#async-vs-threading--when-to-use)
    - [asyncio Synchronization (same concepts!)](#asyncio-synchronization-same-concepts)
  - [Production Concurrency Debugging](#concurrency-debugging)
    - [Diagnostic Symptom Map](#symptom-to-cause-map)
    - [Nine-Step Debugging Workflow](#systematic-debugging-workflow)
    - [Deadlock Wait-For Graphs](#wait-for-graphs)
    - [Python Thread Stack Capture](#capturing-python-thread-stacks)
    - [Deterministic Timing Reproduction](#making-timing-bugs-reproducible)
    - [Concurrent Correctness Tests](#testing-concurrent-code)
  - [Senior-Level Concurrency Topics](#advanced-concurrency-topics)
    - [CAS and Lock-Free Algorithms](#compare-and-swap-and-lock-free-algorithms)
    - [ABA Hazard](#the-aba-problem)
    - [Spinlock Trade-Offs](#spinlocks)
    - [Memory Ordering and Fences](#memory-ordering-and-fences)
    - [False Sharing](#false-sharing)
    - [Lock Striping and Sharding](#lock-striping-and-sharding)
    - [Work-Stealing Schedulers](#work-stealing)
  - [15. Common Patterns Cheat Sheet](#15-common-patterns-cheat-sheet)
  - [16. Machine Coding Problems](#16-machine-coding-problems)
    - [16.1 Producer-Consumer (Bounded Buffer)](#161-producer-consumer-bounded-buffer)
    - [16.2 Reader-Writer Lock](#162-reader-writer-lock)
    - [16.3 Thread-Safe LRU Cache](#163-thread-safe-lru-cache)
    - [16.4 Rate Limiter (Token Bucket)](#164-rate-limiter-token-bucket)
    - [16.5 Rate Limiter (Sliding Window)](#165-rate-limiter-sliding-window)
    - [16.6 Print In Order / Sequence Controller](#166-print-in-order--sequence-controller)
    - [16.7 Print FooBar Alternately](#167-print-foobar-alternately)
    - [16.8 Dining Philosophers](#168-dining-philosophers)
    - [16.9 Blocking Queue](#169-blocking-queue)
    - [16.10 Thread Pool from Scratch](#1610-thread-pool-from-scratch)
    - [16.11 Scheduled Task Executor (Uber)](#1611-scheduled-task-executor-uber)
    - [16.12 Ride Matching System (Uber)](#1612-ride-matching-system-uber)
    - [16.13 Concurrent Web Crawler](#1613-concurrent-web-crawler)
    - [16.14 Traffic Signal Controller](#1614-traffic-signal-controller)
    - [16.15 Async Job Scheduler](#1615-async-job-scheduler)
  - [17. Interview Quick Reference](#17-interview-quick-reference)
    - [Python Concurrency Primitives](#python-concurrency-primitives)
    - [Decision Flowchart](#decision-flowchart)
    - [Common Interview Q\&A](#common-interview-qa)
    - [Machine Coding Round Tips](#machine-coding-round-tips)

---

## 1. Why Concurrency?

## Concurrency vs Parallelism

**Concurrency** = Your program is structured to handle multiple tasks. They may not run at the exact same time — they take turns.

**Parallelism** = Multiple tasks actually execute at the same instant on different CPU cores.

```
Concurrency (1 core, interleaving):
  Task A: ████░░░░████░░░░
  Task B: ░░░░████░░░░████
  → Only one runs at any instant, but both make progress

Parallelism (2 cores, simultaneous):
  Core 1: ████████████████  Task A
  Core 2: ████████████████  Task B
  → Both run at the same instant
```

**Key point:** Concurrency is about **structure** (dealing with many things). Parallelism is about **execution** (doing many things at once).

You can have:
- **Concurrency without parallelism** — `async`/`await` on a single core. Tasks take turns at `await` points, but only one runs at a time.
- **Parallelism without concurrency** — A single loop split across 4 cores using `multiprocessing`. One task, multiple cores.
- **Both** — A web server using a thread pool on a multi-core machine. Multiple requests handled by multiple threads running on separate cores.

In Python specifically:
* **Threads** provide concurrency. Traditional CPython usually does not run pure Python bytecode in parallel, but I/O and native code that releases the GIL can overlap, and free-threaded builds change this constraint
* **Processes** (`multiprocessing`) can provide CPU parallelism because each process has an independent interpreter
* **asyncio** normally provides cooperative concurrency on one event-loop thread; CPU work must be offloaded to execute in parallel

### Key Terms (Just 4 to Start)

| Term | One-Line Definition |
|------|---------------------|
| **Thread** | A lightweight worker inside your program |
| **Lock** | Only one thread can enter the protected section at a time |
| **Race condition** | Bug caused by two threads touching the same data at the same time |
| **Deadlock** | Two threads waiting for each other forever — both stuck |

---

## 2. Threads, Processes & the GIL

### Thread vs Process

**Process** = Independent program with its own memory. Isolated but expensive to create.

**Thread** = Lightweight worker inside a process. Shares memory with other threads — fast but needs synchronization.

| | Process | Thread |
|---|---|---|
| **Memory** | Separate (isolated) | Shared (same memory) |
| **Cost** | Heavy (~MB of memory) | Light (~KB of memory) |
| **Communication** | Hard (pipes, queues) | Easy (shared variables) |
| **Failure isolation** | Stronger; another process can survive | Weaker; shared state can be corrupted, and native faults can terminate the process |

An uncaught Python exception normally terminates only the affected thread and is reported through `threading.excepthook`. The process can continue in a partially completed state, which is why thread-task failures still need explicit reporting and recovery.

### What Threads Share and Keep Private

Threads in one process execute in the same address space. That makes communication cheap, but it also creates shared-state hazards.

| Shared by Threads | Private to Each Thread |
|-------------------|------------------------|
| Heap objects | Call stack and local stack frames |
| Module globals and class variables | CPU registers and program counter |
| Open files and sockets | Thread-local storage |
| Process code and loaded libraries | Scheduling state and thread ID |

A local variable is private only while the object remains confined to that thread. If a local variable points to a shared mutable object, the object is still shared.

```python
shared = []

def worker():
    local_alias = shared  # The reference is local; the list is shared.
    local_alias.append("item")
```

**Interview test:** Identify the shared mutable state first. Then define the invariant that synchronization must preserve.

### Thread Lifecycle and Context Switching

A simplified thread lifecycle is:

```text
NEW -> READY -> RUNNING -> BLOCKED/WAITING -> READY -> TERMINATED
```

* A ready thread can run but is waiting for CPU time
* A running thread currently has a CPU
* A blocked thread waits for I/O, a lock, a condition, or another resource
* A terminated thread has completed and cannot be restarted

A **context switch** saves one thread's execution state and restores another's. It enables concurrency, but it costs CPU time and can disrupt caches and branch predictors. Too many runnable threads can reduce throughput because the system spends more time scheduling and moving state than doing useful work.

Thread creation and destruction also have costs: stack allocation, runtime bookkeeping, and operating-system scheduling. This is why services generally reuse workers through pools instead of creating one thread per small task.

### User Threads vs Kernel Threads

* Kernel threads are known and scheduled by the operating system
* User-level threads are scheduled by a runtime in user space
* Many runtimes map user tasks onto a smaller or equal number of kernel threads

Python `threading.Thread` uses native operating-system threads in standard CPython. An `asyncio` task is different: it is a user-space coroutine scheduled cooperatively by an event loop, usually on one kernel thread.

The interview distinction is who controls scheduling. Kernel threads can be preempted by the OS. Coroutines normally yield at explicit suspension points such as `await`.

### Scheduling and Workload Type

Modern operating systems normally use **preemptive scheduling**. A running thread can lose the CPU when its time slice expires, a higher-priority thread becomes runnable, or the thread blocks.

Important terms:

* Time slice or quantum: approximate interval before the scheduler may preempt a thread
* Oversubscription: more runnable threads than available CPU cores
* Fairness: whether runnable threads receive a reasonable opportunity to execute
* Affinity: restricting a thread to particular CPU cores
* Starvation: a runnable thread repeatedly fails to obtain CPU or a resource

Workload type influences design:

| Workload | Behavior | Typical Python Choice |
|----------|----------|-----------------------|
| CPU-bound | Spends most time computing | Processes, native code, or free-threaded execution when supported |
| I/O-bound | Frequently waits on network, disk, or database I/O | Threads or `asyncio` |
| Mixed | Alternates computation and blocking | Measure, isolate CPU work, and bound both queues and concurrency |

Thread count is not a correctness property. It is a performance and capacity decision that should be validated with measurements.

### Python's GIL (Global Interpreter Lock)

Traditional CPython builds use a **GIL** (Global Interpreter Lock). It normally permits only one thread at a time to execute Python bytecode in a process, even on a multi-core machine.

```
Without GIL (Java, C++):
  Core 1: Thread A ████████████
  Core 2: Thread B ████████████   ← True parallel

With GIL (Python):
  Core 1: Thread A ████░░░░████░░░░████
  Core 1: Thread B ░░░░████░░░░████░░░░  ← Interleaved, not parallel
```

**Does this mean threads are useless in Python?** No.

* **I/O-bound work** (network calls, file reads, database queries): Threads remain useful because blocking I/O generally releases the GIL
* **CPU-bound Python work** (math, transformations): Processes are a common choice because each process has an independent interpreter
* **Native extensions**: Some libraries release the GIL while running native code and can execute work in parallel
* **Free-threaded CPython builds**: Newer CPython versions can be built without the GIL, but extension compatibility, overhead, and deployment support must be considered

**For interviews:** Never use the GIL as a substitute for synchronization. Code must protect multi-step invariants with locks or higher-level thread-safe abstractions. A correct explanation is that the GIL often limits CPU-bound bytecode parallelism on traditional CPython, while threads remain useful for I/O and operations that release the GIL.

```python
# I/O-bound → use threads (GIL is released during I/O)
import threading

def download(url):
    response = requests.get(url)  # GIL released here!
    return response.text

# CPU-bound → use processes (each has own GIL)
from multiprocessing import Process

def compute(data):
    return sum(x * x for x in data)  # CPU-heavy
```

---

## 3. Creating Threads

### Basic Thread Creation

```python
import threading
import time

def worker(name, seconds):
    print(f"{name}: Starting")
    time.sleep(seconds)  # Simulates work
    print(f"{name}: Done")

# Create threads
t1 = threading.Thread(target=worker, args=("Thread-1", 2))
t2 = threading.Thread(target=worker, args=("Thread-2", 1))

# Start them (they run concurrently)
t1.start()
t2.start()

# Wait for both to finish
t1.join()
t2.join()

print("All done!")
```

Output:
```
Thread-1: Starting
Thread-2: Starting
Thread-2: Done      ← finishes first (only 1 second)
Thread-1: Done
All done!
```

### Daemon Threads

A daemon thread dies automatically when the main program exits.

```python
# Daemon thread — won't keep the program alive
t = threading.Thread(target=worker, args=("Background", 10), daemon=True)
t.start()
# Program exits immediately — daemon thread is killed
```

### Key Methods

| Method | What It Does |
|--------|--------------|
| `t.start()` | Begin executing the thread |
| `t.join()` | Wait for the thread to finish |
| `t.join(timeout=5)` | Wait at most 5 seconds |
| `t.is_alive()` | Check if thread is still running |
| `t.daemon = True` | Thread dies when main thread exits |
| `threading.current_thread()` | Get the current thread object |

---

## 4. Race Conditions — The Core Problem

A **race condition** happens when two threads read/write the same variable and the result depends on timing.

### The Classic Bug

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        counter += 1  # NOT thread-safe!

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)

t1.start()
t2.start()
t1.join()
t2.join()

print(counter)  # Required logical result: 2,000,000, but no lock protects it.
```

Some CPython versions and schedules may happen to print the expected value. That does not make the operation a documented synchronization mechanism. Use a controlled interleaving, shown later in the debugging section, when demonstrating the lost update deterministically.

### Why Does This Happen?

`counter += 1` looks like one operation, but it's actually THREE:

```
1. Read counter value     (e.g., 42)
2. Add 1                  (43)
3. Write back             (counter = 43)
```

Two threads can interleave these steps:

```
Thread A: Read counter (42)
Thread B: Read counter (42)     ← Reads SAME old value!
Thread A: Write 43
Thread B: Write 43              ← Overwrites A's work!

Expected: 44, Got: 43 — one update LOST
```

### Types of Race Conditions

| Type | Example | Fix |
|------|---------|-----|
| **Read-modify-write** | `counter += 1` | Use a Lock |
| **Check-then-act** | `if key not in dict: dict[key] = val` | Atomic operation or Lock |
| **Compound action** | Transfer: `a -= x; b += x` | Lock both |

### Fix: Use a Lock

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(1_000_000):
        with lock:          # Only one thread enters at a time
            counter += 1

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start()
t2.start()
t1.join()
t2.join()

print(counter)  # Always 2,000,000 ✓
```

### Data Race vs Race Condition

The terms overlap but are not identical:

* A **data race** occurs when threads access the same memory concurrently, at least one access is a write, and no required synchronization orders those accesses
* A **race condition** is any correctness bug whose outcome depends on timing or event order

A check-then-act race can occur even when each individual operation is thread-safe:

```python
if key not in cache:       # Atomicity of this lookup is not enough.
    cache[key] = compute() # Another thread may insert between the steps.
```

Protect the complete invariant, not individual lines. The critical operation is "insert exactly once if absent," so the check and update must be coordinated as one logical action.

### Atomicity, Visibility, and Ordering

Correct concurrent code must reason about three separate properties:

| Property | Question |
|----------|----------|
| Atomicity | Can another thread observe or interfere with a partially completed operation? |
| Visibility | When one thread writes data, what ensures another thread sees it? |
| Ordering | What prevents reads and writes from being observed in an unsafe order? |

One source line does not imply one atomic operation. Atomic operations also do not automatically make a multi-step business invariant atomic.

```python
# The invariant is balance_a + balance_b == constant.
balance_a -= amount
balance_b += amount
```

Even if each assignment were atomic, another thread could observe the state between them. A lock around the entire transfer protects the invariant.

### Happens-Before

**Happens-before** is a reasoning relationship. If action A happens-before action B, B must observe the effects that the memory model guarantees from A. It is about guaranteed ordering, not wall-clock timestamps.

Common synchronization edges include:

* Actions before releasing a lock are ordered before actions after another thread acquires the same lock
* Writes performed before `Event.set()` are intended to be observed by a thread after `Event.wait()` succeeds
* A thread's actions occur before another thread successfully returns from `join()` on it
* Enqueuing and dequeuing through a thread-safe queue coordinate publication of the item

```python
payload = None
ready = threading.Event()

def producer():
    global payload
    payload = build_payload()
    ready.set()               # Publish readiness after initialization.

def consumer():
    ready.wait()
    use(payload)              # Reads only after the synchronization point.
```

Without a synchronization edge, reasoning that "the writer probably ran first" is insufficient.

### Python Interview Rules for Shared State

* Do not depend on accidental atomicity of a CPython implementation detail
* Do not treat the GIL as a memory-visibility or invariant-protection mechanism
* Use `Lock` for shared invariants and `Queue` for ownership transfer
* Publish initialized data through a lock, event, condition, queue, future, or thread lifecycle operation
* Keep the synchronization policy inside the class that owns the mutable state
* Document whether methods are thread-safe and whether callbacks execute under a lock

The safest interview statement is: "I will make synchronization explicit so the design remains correct across interpreter versions and implementations."

---

## 5. Locks (Mutex)

A Lock (Mutex = **Mut**ual **Ex**clusion) ensures only one thread can execute a section of code at a time. Other threads wait until the lock is released.

### Basic Usage

```python
import threading

lock = threading.Lock()

# Method 1: with statement (preferred — auto-releases)
with lock:
    # critical section — only one thread here at a time
    shared_data.append(item)

# Method 2: manual acquire/release
lock.acquire()
try:
    shared_data.append(item)
finally:
    lock.release()  # ALWAYS release in finally!

# Method 3: non-blocking try
if lock.acquire(blocking=False):
    try:
        do_work()
    finally:
        lock.release()
else:
    # couldn't get the lock — do something else
    pass

# Method 4: timeout
if lock.acquire(timeout=5.0):
    try:
        do_work()
    finally:
        lock.release()
else:
    print("Timed out waiting for lock")
```

### Lock Ownership and Granularity

Many languages distinguish an owner-tracking mutex from a semaphore. In Python, `threading.Lock` does not track ownership: any thread may release a locked lock, although releasing an unlocked lock raises `RuntimeError`. `threading.RLock` does track ownership and must be released by the thread that acquired it.

Even when the runtime permits cross-thread release, prefer structured ownership through `with`. It makes control flow reviewable and prevents accidental over-release.

Lock granularity is a throughput-versus-complexity trade-off:

| Strategy | Advantages | Costs |
|----------|------------|-------|
| Coarse-grained lock | Simple invariants, easier correctness proof | More contention, unrelated work blocks |
| Fine-grained locks | More independent operations can proceed | More lock bookkeeping and deadlock risk |
| Lock striping | Bounded number of locks with parallel key access | Hash collisions and complex multi-key operations |

Start with one coarse lock for correctness. Split it only after measurement identifies contention, and define a total acquisition order before introducing multiple locks.

### Bank Account Example

```python
import threading

class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance
        self._lock = threading.Lock()

    def deposit(self, amount):
        with self._lock:
            self.balance += amount

    def withdraw(self, amount):
        with self._lock:
            if self.balance >= amount:
                self.balance -= amount
                return True
            return False

    def transfer(self, other, amount):
        # Need to lock BOTH accounts — but be careful of deadlock!
        # Solution: always lock in a consistent order (by id)
        first, second = sorted([self, other], key=id)
        with first._lock:
            with second._lock:
                if self.balance >= amount:
                    self.balance -= amount
                    other.balance += amount
                    return True
                return False
```

### Rules for Using Locks

1. **Keep critical sections SHORT** — hold the lock for as little time as possible
2. **Always release** — use `with` statement or `try/finally`
3. **Don't do I/O while holding a lock** — other threads will be blocked for a long time
4. **Lock on private objects** — don't expose your lock to external code
5. **Consistent ordering** — if you need multiple locks, always acquire in the same order

---

## 6. RLock (Reentrant Lock)

A regular `Lock` will deadlock if the same thread tries to acquire it twice. An `RLock` (Reentrant Lock) allows the **same thread** to acquire it multiple times.

```python
import threading

lock = threading.Lock()
rlock = threading.RLock()

# ❌ DEADLOCK with regular Lock
def bad():
    with lock:
        with lock:  # Same thread tries again — DEADLOCK!
            print("Never reaches here")

# ✅ Works with RLock
def good():
    with rlock:
        with rlock:  # Same thread — allowed! (count goes to 2)
            print("This works!")
        # count drops to 1
    # count drops to 0 — lock released
```

### When Do You Need RLock?

When a method that holds a lock calls another method that also needs the same lock:

```python
class SafeList:
    def __init__(self):
        self._items = []
        self._lock = threading.RLock()  # RLock because methods call each other

    def append(self, item):
        with self._lock:
            self._items.append(item)

    def extend(self, items):
        with self._lock:
            for item in items:
                self.append(item)  # Calls append() which also acquires _lock
                                   # With Lock → deadlock. With RLock → works!

    def size(self):
        with self._lock:
            return len(self._items)
```

| | `Lock` | `RLock` |
|---|---|---|
| Same thread re-acquire | ❌ Deadlock | ✅ Allowed |
| Performance | Slightly faster | Slightly slower (tracks owner) |
| When to use | Simple cases | When methods call each other |

---

## 7. Condition Variables

A `Condition` variable lets threads **wait** for something to become true, and lets other threads **notify** them when it does.

### The Problem Without Conditions

```python
# ❌ Busy waiting — wastes CPU spinning endlessly
while not data_ready:
    pass  # Checking over and over — terrible!
process(data)
```

### The Solution: Condition Variables

```python
import threading
import time

condition = threading.Condition()
data = None
data_ready = False

def producer():
    global data, data_ready
    time.sleep(2)  # Simulate slow work

    with condition:
        data = "Hello from producer!"
        data_ready = True
        condition.notify()  # Wake up ONE waiting thread

def consumer():
    global data, data_ready

    with condition:
        while not data_ready:       # ALWAYS use while, not if
            condition.wait()        # Release lock + sleep (atomic)
                                    # Re-acquires lock when woken up
        print(f"Got: {data}")

t1 = threading.Thread(target=consumer)
t2 = threading.Thread(target=producer)
t1.start()
t2.start()
t1.join()
t2.join()
```

### How `condition.wait()` Works (3 Steps, Atomic)

```
1. Release the lock          ← so other threads can acquire it
2. Sleep the thread          ← no CPU wasted
3. When notified:
   - Wake up
   - Re-acquire the lock     ← back in critical section
   - Continue after wait()
```

### Key Methods

| Method | What It Does |
|--------|--------------|
| `condition.wait()` | Release lock + sleep until notified |
| `condition.wait(timeout=5)` | Wait at most 5 seconds |
| `condition.notify()` | Wake ONE waiting thread |
| `condition.notify_all()` | Wake ALL waiting threads |

### Why `while` Not `if`?

```python
# ❌ BAD — spurious wakeup can cause bugs
with condition:
    if not data_ready:       # If woken up spuriously, skips wait
        condition.wait()     # and processes invalid data!
    process(data)

# ✅ GOOD — re-checks after every wakeup
with condition:
    while not data_ready:    # If woken up spuriously, checks again
        condition.wait()     # and goes back to sleep
    process(data)
```

**Interview Tip:** Interviewers specifically check if you use `while` with `wait()`. Always explain: "I use `while` instead of `if` because of spurious wakeups."

---

## 8. Semaphores

A Semaphore allows up to **N threads** to enter a section simultaneously.

- `Lock` = Semaphore with N=1
- `Semaphore(5)` = allows 5 threads at once

```python
import threading
import time

# Allow at most 3 concurrent database connections
db_semaphore = threading.Semaphore(3)

def query_database(query_id):
    print(f"Query {query_id}: Waiting for connection...")
    with db_semaphore:                  # Decrements count (blocks if 0)
        print(f"Query {query_id}: Connected! (executing)")
        time.sleep(2)                   # Simulate query
        print(f"Query {query_id}: Done")
    # Auto-releases — increments count

# Launch 10 queries — only 3 run at a time
threads = [threading.Thread(target=query_database, args=(i,)) for i in range(10)]
for t in threads: t.start()
for t in threads: t.join()
```

### BoundedSemaphore — Safer Version

`BoundedSemaphore` raises an error if you release more times than you acquire. Use it to catch bugs.

```python
sem = threading.BoundedSemaphore(3)

sem.release()  # ValueError: Semaphore released too many times
# Regular Semaphore would silently allow it — dangerous!
```

### Semaphore vs Lock

| | Lock | Semaphore |
|---|---|---|
| Max threads inside | 1 | N |
| Use case | Mutual exclusion | Connection pools, rate limiting |
| Who can release in Python? | Any thread, although structured same-thread release is preferred | Any thread |

---

## 9. Events

An `Event` is the simplest signaling mechanism — a boolean flag that threads can wait on.

```python
import threading
import time

start_event = threading.Event()

def worker(name):
    print(f"{name}: Waiting for signal...")
    start_event.wait()       # Block until event is set
    print(f"{name}: GO!")

# Create workers that all wait for the starting gun
threads = [threading.Thread(target=worker, args=(f"Runner-{i}",)) for i in range(5)]
for t in threads: t.start()

time.sleep(2)
print("Ready... Set...")
start_event.set()   # All 5 threads wake up simultaneously

for t in threads: t.join()
```

### Event Methods

| Method | What It Does |
|--------|--------------|
| `event.set()` | Set the flag — all waiters wake up |
| `event.clear()` | Reset the flag — future waiters will block |
| `event.wait()` | Block until flag is set |
| `event.wait(timeout=5)` | Wait at most 5 seconds, returns `True` if set |
| `event.is_set()` | Check if flag is set (non-blocking) |

### Event vs Condition

| | Event | Condition |
|---|---|---|
| Has a lock? | No | Yes (built-in) |
| Can protect data? | No | Yes |
| Complexity | Simple | More powerful |
| Use when | Just signaling | Signaling + data protection |

---

## 10. Barriers

A `Barrier` makes N threads all wait for each other at a checkpoint before proceeding.

```python
import threading

barrier = threading.Barrier(3)  # Wait for 3 threads

def phase_worker(name):
    # Phase 1
    print(f"{name}: Phase 1 done")
    barrier.wait()      # All 3 must reach here before any continues

    # Phase 2
    print(f"{name}: Phase 2 done")
    barrier.wait()      # Barrier is reusable!

    # Phase 3
    print(f"{name}: Phase 3 done")

threads = [threading.Thread(target=phase_worker, args=(f"Worker-{i}",)) for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
```

Output (phases never overlap):
```
Worker-0: Phase 1 done
Worker-2: Phase 1 done
Worker-1: Phase 1 done
← all 3 reached barrier, now proceed →
Worker-1: Phase 2 done
Worker-0: Phase 2 done
Worker-2: Phase 2 done
...
```

---

## 11. Thread-Safe Data Structures

Python provides one built-in thread-safe data structure — `queue.Queue`. For everything else, you protect with locks.

### queue.Queue — Thread-Safe Queue

```python
import queue
import threading

q = queue.Queue(maxsize=10)  # Bounded queue (0 = unlimited)

def producer():
    for i in range(20):
        q.put(i)            # Blocks if full
        print(f"Produced: {i}")

def consumer():
    while True:
        item = q.get()      # Blocks if empty
        print(f"Consumed: {item}")
        q.task_done()       # Signal that item is processed

t1 = threading.Thread(target=producer)
t2 = threading.Thread(target=consumer, daemon=True)
t1.start()
t2.start()
t1.join()
q.join()  # Wait until all items are processed (all task_done() called)
```

### Queue Variants

| Queue | Order | Use Case |
|-------|-------|----------|
| `queue.Queue` | FIFO | Standard producer-consumer |
| `queue.LifoQueue` | LIFO (stack) | DFS-like processing |
| `queue.PriorityQueue` | Lowest first | Task scheduling by priority |

```python
# Priority Queue — lowest value comes out first
pq = queue.PriorityQueue()
pq.put((3, "low priority"))
pq.put((1, "high priority"))
pq.put((2, "medium priority"))

print(pq.get())  # (1, 'high priority')
print(pq.get())  # (2, 'medium priority')
```

### collections.deque vs queue.Queue

| | `collections.deque` | `queue.Queue` |
|---|---|---|
| **Thread-safe?** | Individual ops atomic, no blocking | Yes — has internal Lock, blocks |
| **Blocking?** | No — raises `IndexError` if empty | Yes — `get()` waits for items |
| **Use case** | DSA / single-threaded code | Multi-threaded producer-consumer |
| **Performance** | Faster (no locking overhead) | Slower (locking cost) |

**Rule:** Use `collections.deque` for algorithms. Use `queue.Queue` for threads.

---

## 12. Deadlock, Livelock & Starvation

### Deadlock

Two threads each hold a lock the other needs. Neither can proceed. **Program hangs forever.**

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

# DEADLOCK — both threads wait forever
```

### 4 Conditions for Deadlock (ALL must be true)

| Condition | Meaning | How to Break It |
|-----------|---------|-----------------|
| **Mutual exclusion** | Only one thread can hold the lock | Use lock-free structures |
| **Hold and wait** | Thread holds one lock, waits for another | Acquire all locks at once |
| **No preemption** | Can't force-take a lock | Use timeouts |
| **Circular wait** | A waits for B, B waits for A | Always lock in same order |

### Fix: Consistent Lock Ordering

```python
def transfer(account_a, account_b, amount):
    # Always lock the account with the smaller id first
    first, second = sorted([account_a, account_b], key=lambda a: a.id)

    with first.lock:
        with second.lock:
            if account_a.balance >= amount:
                account_a.balance -= amount
                account_b.balance += amount
```

### Fix: Timeout

```python
def safe_transfer():
    if lock_a.acquire(timeout=1):
        try:
            if lock_b.acquire(timeout=1):
                try:
                    do_transfer()
                finally:
                    lock_b.release()
            else:
                print("Could not get lock_b — retry later")
        finally:
            lock_a.release()
    else:
        print("Could not get lock_a — retry later")
```

### Livelock

Threads are running but making no progress — they keep reacting to each other in a loop and never move forward.

```python
# ❌ Livelock — both threads keep "being polite"
def polite_thread(my_lock, other_lock, name):
    while True:
        my_lock.acquire()
        if not other_lock.acquire(blocking=False):
            my_lock.release()       # "After you!"
            time.sleep(0.001)       # Try again — but so does the other thread!
            continue
        # ... never reaches here
```

**Fix:** Add random backoff to break symmetry.

```python
import random

def fixed_thread(my_lock, other_lock, name):
    while True:
        my_lock.acquire()
        if not other_lock.acquire(blocking=False):
            my_lock.release()
            time.sleep(random.uniform(0.001, 0.01))  # Random backoff!
            continue
        break  # Got both locks!
```

### Starvation

One thread never gets the lock because other threads keep grabbing it first.

Mitigations include reducing lock hold time, partitioning shared state, limiting aggressive retries, or using a primitive with an explicit fairness guarantee. Python's basic locks do not promise strict FIFO acquisition, and `queue.Queue` should not be described as a general fair-lock replacement.

### Priority Inversion

Priority inversion occurs when a high-priority thread needs a lock held by a low-priority thread, while medium-priority work keeps preempting the low-priority owner.

```text
Low priority:    owns Lock A, needs CPU to release it
High priority:   waits for Lock A
Medium priority: keeps running and delays the low-priority owner
```

The effective result is inverted: medium-priority work delays high-priority work. Operating systems can mitigate this through **priority inheritance**, temporarily raising the lock owner's priority. Application-level mitigations include short critical sections, avoiding blocking I/O while holding a lock, and reducing priority-sensitive lock sharing.

### Deadlock Prevention Checklist

* Define a total lock order and acquire nested locks only in that order
* Keep critical sections small and never call slow external systems while holding a lock
* Avoid invoking unknown callbacks while holding a lock because they may re-enter the component
* Avoid nested locks when state can be partitioned or ownership can be transferred through a queue
* Use timeouts for recovery and diagnostics, not as proof that the algorithm is deadlock-free
* Release partially acquired resources before retrying, preferably with bounded randomized backoff
* Include shutdown paths in lock-order analysis

### Summary

| Problem | Threads Running? | Progress? | Typical Mitigation |
|---------|------------------|-----------|--------------------|
| **Deadlock** | No, affected threads are blocked | None | Lock ordering, fewer nested locks |
| **Livelock** | Yes | None | Randomized or bounded backoff |
| **Starvation** | Some are | Some threads make no progress | Fairness policy, partitioning, bounded retries |
| **Priority inversion** | Some are | High-priority work is delayed | Priority inheritance, short critical sections |

---

## 13. Thread Pool (concurrent.futures)

Creating threads is expensive. A thread pool keeps a fixed set of threads and reuses them.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def fetch_url(url):
    time.sleep(1)  # Simulate network request
    return f"Data from {url}"

urls = [f"https://api.example.com/{i}" for i in range(10)]

# Thread pool with 4 workers — processes 10 URLs using only 4 threads
with ThreadPoolExecutor(max_workers=4) as executor:
    # Submit all tasks
    future_to_url = {executor.submit(fetch_url, url): url for url in urls}

    # Process results as they complete (not in submission order)
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result = future.result()
            print(f"{url}: {result}")
        except Exception as e:
            print(f"{url}: Error — {e}")
```

### map() — Simpler API

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    # Results come back in input order (unlike as_completed)
    results = executor.map(fetch_url, urls)
    for result in results:
        print(result)
```

### ProcessPoolExecutor — For CPU-Bound Work

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(n):
    return sum(i * i for i in range(n))

# Uses separate processes — bypasses GIL
with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(cpu_heavy, [10**6, 10**6, 10**6, 10**6])
    for r in results:
        print(r)
```

### When to Use What

| Work Type | Use | Why |
|-----------|-----|-----|
| I/O-bound (network, disk) | `ThreadPoolExecutor` | GIL released during I/O |
| CPU-bound (computation) | `ProcessPoolExecutor` | Separate GIL per process |
| High-concurrency I/O | `asyncio` | Even lighter than threads |

### Sizing a Thread Pool

There is no universal worker-count formula.

* CPU-bound work usually starts near the number of available cores to avoid oversubscription
* I/O-bound work may benefit from more workers because many workers are blocked at any moment
* Downstream limits such as database connections, API quotas, memory, and file descriptors often matter more than CPU count

A useful starting estimate for a stable I/O-heavy workload is:

$$
N_{threads} \approx N_{cores}\left(1 + \frac{W}{S}\right)
$$

Here, $W$ is average wait time and $S$ is average service or compute time. Treat this as a hypothesis. Measure throughput, queue delay, tail latency, memory, context switches, and downstream saturation before selecting a production value.

### Backpressure and Queue Capacity

A fixed number of workers does not protect a system if producers can create tasks faster than workers complete them. An unbounded task queue converts overload into growing latency and memory usage.

Common overload policies are:

* Block the producer until capacity is available
* Reject immediately or after a timeout
* Drop work that is stale or low priority
* Run the task in the caller to slow the producer
* Shed load before an already saturated dependency

Python's `ThreadPoolExecutor` does not expose a simple bounded submission queue. For strict backpressure, place a bounded `queue.Queue` in front of workers, guard submissions with a semaphore, or build a small executor with an explicit capacity policy.

### Thread Pool Failure Modes

| Failure Mode | Typical Cause | Prevention |
|--------------|---------------|------------|
| Pool exhaustion | Every worker blocks indefinitely | Timeouts, cancellation, isolate blocking dependencies |
| Nested-submit deadlock | A worker submits to the same pool and waits while all workers do the same | Avoid synchronous child waits or use separate execution resources |
| Queue growth | Arrival rate exceeds service rate | Bounded queue and explicit rejection policy |
| Starvation | Long tasks occupy workers needed by short or high-priority tasks | Separate pools or priority-aware scheduling |
| Retry storm | Failures trigger immediate synchronized retries | Exponential backoff, jitter, retry budget |
| Hidden task failure | Caller never inspects a failed `Future` | Consume results and report exceptions |

Classic one-worker deadlock:

```python
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor(max_workers=1)

def outer():
    inner_future = pool.submit(lambda: 42)
    return inner_future.result()  # The only worker waits for queued inner work.

pool.submit(outer).result()
```

### Shutdown and Exception Handling

Decide these lifecycle semantics during design:

* Whether shutdown drains queued tasks or cancels tasks that have not started
* Whether submissions after shutdown fail immediately
* How running tasks receive cooperative cancellation
* Whether shutdown has a timeout and what happens when workers do not stop
* Where task exceptions are stored, logged, retried, or returned

`Future.result()` re-raises the task exception in the caller. If results are ignored, failures can remain unnoticed. A worker should catch task failures at its execution boundary so one bad task does not silently terminate custom worker logic.

---

## 14. async/await (asyncio)

`asyncio` is Python's way to handle thousands of concurrent I/O operations with a **single thread**. It's NOT multithreading — it's cooperative multitasking.

`async`/`await` uses a single thread with an **event loop**. When a task hits `await`, it pauses and lets other tasks run. When the awaited result is ready, the task resumes. No threads are created.

```python
import asyncio

async def fetch_data(name, seconds):
    print(f"{name}: Starting request")
    await asyncio.sleep(seconds)    # "I'm waiting — others can run"
    print(f"{name}: Got response")
    return f"Data from {name}"

async def main():
    # Launch 3 "requests" concurrently — single thread!
    results = await asyncio.gather(
        fetch_data("API-1", 2),
        fetch_data("API-2", 1),
        fetch_data("API-3", 3),
    )
    print(results)

asyncio.run(main())
```

Output:
```
API-1: Starting request
API-2: Starting request
API-3: Starting request
API-2: Got response      ← 1 second
API-1: Got response      ← 2 seconds
API-3: Got response      ← 3 seconds (total time: ~3s, not 6s)
```

### async vs threading — When to Use

| | `threading` | `asyncio` |
|---|---|---|
| Parallelism model | OS-level threads | Single-thread event loop |
| Overhead per task | ~KB (thread stack) | ~bytes (coroutine) |
| Max concurrent tasks | ~1000s | ~100,000s |
| Blocking calls OK? | Yes | NO — blocks the event loop |
| Best for | Mixed I/O + CPU, legacy code | High-concurrency I/O |

### asyncio Synchronization (same concepts!)

```python
# asyncio has its own Lock, Semaphore, Event, Condition — same API
lock = asyncio.Lock()
semaphore = asyncio.Semaphore(5)
event = asyncio.Event()

async def safe_write():
    async with lock:
        # critical section
        pass

async def limited_access():
    async with semaphore:
        # at most 5 concurrent
        pass
```

**Interview Tip:** If asked about async, explain the event loop: "One thread processes tasks cooperatively. When a task hits `await` (I/O wait), it yields control so other tasks can run. No locking needed for the same coroutine."

---

## Concurrency Debugging

Concurrency bugs are often intermittent because logging, breakpoints, CPU load, and thread count change the schedule. Debug the wait relationships and state invariants rather than adding arbitrary sleeps.

### Symptom-to-Cause Map

| Symptom | Likely Causes | First Evidence to Collect |
|---------|---------------|---------------------------|
| Application hangs, CPU low | Deadlock, missed signal, blocking I/O | Thread stacks, lock waits, dependency latency |
| CPU near 100%, little progress | Busy wait, livelock, retry loop | CPU profile, repeated stacks, retry metrics |
| Tail latency rises under load | Lock contention, queueing, downstream saturation | Queue depth, lock wait time, p95/p99 latency |
| Thread count keeps growing | Thread leak, unbounded thread-per-request design | Thread count by name and creation stacks |
| Queue grows continuously | Producers outpace consumers | Arrival rate, service rate, oldest-task age |
| Workers idle but tasks stall | Lost notification, dependency cycle, scheduling bug | Queue state, conditions, task dependency graph |
| Occasional wrong result | Race condition, unsafe publication | Failed invariant, operation history, shared writes |
| Throughput falls as threads increase | Contention, context switching, false sharing | Context switches, CPU profile, lock contention |
| Memory grows with load | Unbounded queue, retained futures, task leak | Heap profile, queue size, pending task count |

### Systematic Debugging Workflow

1. Establish whether the failure is incorrect state, no progress, or poor performance.
2. Record CPU, memory, thread count, queue depth, throughput, error rate, and latency percentiles.
3. Capture multiple thread dumps several seconds apart. Repeated identical blocked stacks are more useful than one snapshot.
4. Identify each thread's state: running, waiting for a lock or condition, blocked on I/O, or idle on a work queue.
5. Map resource ownership and waiting relationships. Search for cycles and resources with many waiters.
6. Find the code path that acquired the resource and verify every release path, including exceptions and shutdown.
7. Reproduce with controlled synchronization, not long sleeps.
8. Fix the invariant or coordination protocol. Adding more locks without a policy often creates another failure.
9. Verify with stress, timeout, cancellation, failure-injection, and shutdown tests.

For contention, distinguish **lock hold time** from **lock wait time**. A tiny critical section can still become a bottleneck if every operation requires the same lock.

### Wait-For Graphs

A wait-for graph turns a hang into a cycle-detection problem.

```text
Thread T1 -> waits for Lock B -> owned by Thread T2
Thread T2 -> waits for Lock A -> owned by Thread T1

T1 -> T2 -> T1  means deadlock
```

Construct it from thread stacks, lock instrumentation, and runtime diagnostics:

1. For each blocked thread, record the resource it waits for.
2. For each resource, record its current owner.
3. Replace `thread -> resource -> owner` with `thread -> owner`.
4. Find directed cycles.

No cycle does not mean the system is healthy. A thread may be blocked forever on I/O, a notification that was lost, or a resource whose owner has failed.

### Capturing Python Thread Stacks

Python can dump all current thread stacks with `faulthandler`:

```python
import faulthandler
import sys

faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
```

For a process that occasionally hangs, enable periodic dumps during diagnosis:

```python
import faulthandler

faulthandler.dump_traceback_later(30, repeat=True)
```

Cancel periodic dumping after the diagnostic window with `faulthandler.cancel_dump_traceback_later()`. Stack dumps show where threads are executing or waiting, but basic Python locks do not always expose ownership. Add thread names, queue metrics, task IDs, and narrowly scoped lock-wait instrumentation when ownership is unclear.

External profilers and operating-system debuggers can help when threads are blocked inside native extensions or system calls. Prefer sampling tools for a live incident because attaching a debugger can alter timing.

### Making Timing Bugs Reproducible

Use `Barrier`, `Event`, or test hooks to force the dangerous interleaving:

```python
import threading

both_read = threading.Barrier(2)
counter = 0

def unsafe_increment():
    global counter
    observed = counter
    both_read.wait()  # Both threads capture the same old value.
    counter = observed + 1
```

This test deterministically demonstrates a lost update. Arbitrary `sleep()` calls only increase probability and can produce slow, flaky tests.

Other useful techniques include:

* Run the test many times with recorded random seeds
* Vary worker counts, queue capacities, and task durations
* Inject exceptions, timeouts, cancellations, and partial shutdowns
* Pause execution at lock boundaries through explicit test hooks
* Log monotonic timestamps, thread names, operation IDs, and state transitions

### Testing Concurrent Code

Test properties, not one expected schedule:

* Safety: forbidden states never occur
* Liveness: submitted work eventually completes or fails within a defined timeout
* Conservation: produced items equal consumed plus intentionally rejected items
* At-most-once or exactly-once semantics: match the stated contract
* Capacity: queue size and active-resource count never exceed limits
* Shutdown: blocked producers and consumers wake and terminate predictably

Always use time-bounded joins in tests so a deadlock becomes a failure instead of hanging the test suite:

```python
thread.join(timeout=2)
assert not thread.is_alive(), "worker failed to terminate"
```

Linearizability is a strong correctness model for concurrent objects: each completed operation should appear to take effect at one instant between its invocation and response. In interviews, identify the **linearization point**, such as the append performed while holding the queue lock.

---

## Advanced Concurrency Topics

These topics are most useful for senior interviews and deep follow-ups. Explain the trade-off before proposing a low-level mechanism.

### Compare-And-Swap and Lock-Free Algorithms

**Compare-and-swap (CAS)** atomically performs this operation:

```text
if memory == expected:
    memory = desired
    return success
return failure
```

An optimistic update loop reads a value, computes a replacement, and retries if another thread changed the value first. CAS is the foundation of many atomic counters, lock-free stacks, and concurrent queues.

Terms interviewers may ask about:

* Lock-free: system-wide progress is guaranteed, although one thread may starve
* Wait-free: every operation completes in a bounded number of its own steps
* Obstruction-free: a thread completes if it eventually runs alone

Lock-free does not mean race-free or automatically faster. Algorithms still need correct memory ordering, safe memory reclamation, retry control, and protection from ABA. Under contention, repeated CAS failures can waste CPU.

Python's standard `threading` API does not provide a general CAS primitive for arbitrary Python objects. Use locks and thread-safe queues in normal Python code unless a specialized library or native extension provides well-defined atomics.

### The ABA Problem

CAS may see the expected value and assume nothing changed, even though the value changed from A to B and back to A.

```text
Thread 1 reads head = A
Thread 2 changes A -> B -> A
Thread 1 CAS(A, C) succeeds, but the structure changed in between
```

Common defenses pair the value with a version counter, use tagged pointers, or use a safe memory-reclamation scheme such as hazard pointers or epochs. The interview insight is that equality of the current value does not prove absence of intervening changes.

### Spinlocks

A spinlock repeatedly checks for availability instead of sleeping:

```text
while not try_acquire(lock):
    continue
```

Spinning can be useful only when the expected hold time is extremely short, a CPU core is available, and blocking plus waking would cost more. It performs badly under contention, on a single core, when the owner is descheduled, or when the critical section blocks.

Do not implement spinlocks in ordinary Python interview code. The interpreter, GIL on traditional builds, and scheduler make a blocking `Lock` or higher-level primitive a better default.

### Memory Ordering and Fences

Compilers and CPUs may reorder independent operations for performance, and cores may observe writes at different times. Memory-ordering modes describe which reorderings an atomic operation permits:

* Relaxed: atomicity without cross-variable ordering
* Acquire: later operations do not move before the acquire
* Release: earlier operations do not move after the release
* Sequentially consistent: operations behave as if participating in one global order

A memory fence restricts reordering and visibility. In high-level Python, use synchronization primitives instead of hand-written fences. At senior level, explain that mutual exclusion and visibility are separate concerns, while a correctly implemented lock provides both the exclusion and ordering required around its critical section.

### False Sharing

False sharing occurs when threads update different variables that occupy the same CPU cache line. The variables are logically independent, but cache-coherence traffic repeatedly moves or invalidates the shared line.

```text
Cache line: [counter_for_thread_1 | counter_for_thread_2]
Core 1 writes left field <-> Core 2 writes right field
```

Symptoms include reduced throughput as threads increase, despite little logical lock contention. Mitigations include padding or aligning hot per-thread fields, batching updates, and using local counters followed by aggregation. It is most visible in native code, shared-memory arrays, or free-threaded parallel execution rather than ordinary GIL-bound Python bytecode.

### Lock Striping and Sharding

Lock striping maps different keys to different locks:

```python
stripe = hash(key) % len(locks)
with locks[stripe]:
    update(key)
```

It improves throughput when accesses are spread across stripes. Trade-offs include more complex multi-key operations, possible hot stripes, approximate rather than global LRU semantics, and deadlock risk when an operation needs several stripes. Acquire multiple stripes in a globally consistent index order.

### Work Stealing

In a work-stealing scheduler, each worker owns a local deque. A worker normally consumes its own tasks; an idle worker steals tasks from another worker's deque.

Benefits include reduced contention on one global queue, improved cache locality, and dynamic load balancing for irregular task trees. Costs include more complex termination detection, synchronization among deques, and less predictable execution order.

Work stealing is especially useful for recursive fork-join workloads. A simple service handling independent requests often benefits more from a bounded central queue and clear backpressure.

---

## 15. Common Patterns Cheat Sheet

```
Pattern                 | Python Tool                    | Use When
------------------------|--------------------------------|----------------------------------
Mutual exclusion        | threading.Lock()               | Protect shared data
Reentrant locking       | threading.RLock()              | Methods calling each other
Wait for condition      | threading.Condition()          | Producer-consumer
Limit concurrency       | threading.Semaphore(N)         | Connection pools, rate limiting
Signal all threads      | threading.Event()              | Start gate, shutdown signal
Sync at checkpoints     | threading.Barrier(N)           | Phased execution
Thread-safe queue       | queue.Queue()                  | Producer-consumer pipeline
Thread pool             | concurrent.futures.Executor    | Reuse threads for many tasks
Async I/O               | asyncio                        | High-concurrency network I/O
Timer / periodic task   | threading.Timer()              | Delayed execution
```

---

## 16. Machine Coding Problems

These are the actual problems asked in FAANG LLD/machine coding rounds. Each one teaches a concurrency pattern.

---

### 16.1 Producer-Consumer (Bounded Buffer)

**Asked at:** Uber, Amazon, Google, Goldman Sachs

**Problem:** Multiple producers add items to a buffer. Multiple consumers remove items. Buffer has a max capacity. Producers block when full. Consumers block when empty.

**Concepts:** Condition variables, mutual exclusion, blocking

```python
import threading
import time
import random

class BoundedBuffer:
    def __init__(self, capacity):
        self.buffer = []
        self.capacity = capacity
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)

    def produce(self, item):
        with self.not_full:
            while len(self.buffer) >= self.capacity:
                self.not_full.wait()    # Wait until space available

            self.buffer.append(item)
            print(f"  Produced: {item} | Buffer size: {len(self.buffer)}")
            self.not_empty.notify()     # Wake a consumer

    def consume(self):
        with self.not_empty:
            while len(self.buffer) == 0:
                self.not_empty.wait()   # Wait until item available

            item = self.buffer.pop(0)
            print(f"  Consumed: {item} | Buffer size: {len(self.buffer)}")
            self.not_full.notify()      # Wake a producer
            return item


def producer(buffer, producer_id, count):
    for i in range(count):
        item = f"P{producer_id}-{i}"
        buffer.produce(item)
        time.sleep(random.uniform(0.1, 0.3))

def consumer(buffer, consumer_id, count):
    for _ in range(count):
        buffer.consume()
        time.sleep(random.uniform(0.2, 0.5))


# Test
buffer = BoundedBuffer(capacity=3)

producers = [threading.Thread(target=producer, args=(buffer, i, 5)) for i in range(2)]
consumers = [threading.Thread(target=consumer, args=(buffer, i, 5)) for i in range(2)]

for t in producers + consumers: t.start()
for t in producers + consumers: t.join()
```

**Key Points to Mention in Interview:**
- Two condition variables: `not_full` (producers wait on) and `not_empty` (consumers wait on)
- `while` loop for wait — handles spurious wakeups
- `notify()` wakes one waiter; use `notify_all()` if multiple waiters might need to wake

---

### 16.2 Reader-Writer Lock

**Asked at:** Google, Microsoft, Uber

**Problem:** Multiple readers can read simultaneously, but a writer needs exclusive access.

**Concepts:** Shared vs exclusive locking, starvation prevention

```python
import threading
import time

class ReadWriteLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._readers_ok = threading.Condition(self._lock)
        self._writers_ok = threading.Condition(self._lock)
        self._readers = 0
        self._writing = False
        self._waiting_writers = 0

    def acquire_read(self):
        with self._lock:
            # Wait if someone is writing OR writers are waiting (prevent writer starvation)
            while self._writing or self._waiting_writers > 0:
                self._readers_ok.wait()
            self._readers += 1

    def release_read(self):
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._writers_ok.notify()   # Wake a waiting writer

    def acquire_write(self):
        with self._lock:
            self._waiting_writers += 1
            while self._writing or self._readers > 0:
                self._writers_ok.wait()
            self._waiting_writers -= 1
            self._writing = True

    def release_write(self):
        with self._lock:
            self._writing = False
            self._readers_ok.notify_all()  # Wake all waiting readers
            self._writers_ok.notify()       # Wake one waiting writer


# Usage
rw_lock = ReadWriteLock()
shared_data = {"value": 0}

def reader(reader_id):
    for _ in range(3):
        rw_lock.acquire_read()
        try:
            print(f"Reader-{reader_id} reads: {shared_data['value']}")
            time.sleep(0.1)
        finally:
            rw_lock.release_read()

def writer(writer_id):
    for i in range(3):
        rw_lock.acquire_write()
        try:
            shared_data["value"] += 1
            print(f"Writer-{writer_id} wrote: {shared_data['value']}")
            time.sleep(0.2)
        finally:
            rw_lock.release_write()

threads = (
    [threading.Thread(target=reader, args=(i,)) for i in range(3)] +
    [threading.Thread(target=writer, args=(i,)) for i in range(2)]
)
for t in threads: t.start()
for t in threads: t.join()
```

**Key Design Decision:** This implementation is **writer-preferring** — if a writer is waiting, new readers also wait. This prevents writer starvation.

---

### 16.3 Thread-Safe LRU Cache

**Asked at:** Uber, Amazon, Meta, Google

**Problem:** Implement an LRU cache that supports concurrent `get` and `put` operations.

**Concepts:** Lock granularity, OrderedDict

```python
import threading
from collections import OrderedDict

class ThreadSafeLRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return -1
            self.cache.move_to_end(key)  # Mark as recently used
            return self.cache[key]

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = value
            else:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)  # Remove LRU (front)
                self.cache[key] = value
```

**Follow-up: Striped Locking for Higher Throughput**

```python
class StripedLRUCache:
    """
    Splits into N shards, each with its own lock.
    Different keys accessed concurrently if they hash to different shards.
    """
    def __init__(self, capacity: int, num_stripes: int = 16):
        self.num_stripes = num_stripes
        shard_cap = max(1, capacity // num_stripes)
        self.shards = [OrderedDict() for _ in range(num_stripes)]
        self.locks = [threading.Lock() for _ in range(num_stripes)]
        self.shard_capacity = shard_cap

    def _shard(self, key):
        return hash(key) % self.num_stripes

    def get(self, key):
        idx = self._shard(key)
        with self.locks[idx]:
            if key not in self.shards[idx]:
                return -1
            self.shards[idx].move_to_end(key)
            return self.shards[idx][key]

    def put(self, key, value):
        idx = self._shard(key)
        with self.locks[idx]:
            if key in self.shards[idx]:
                self.shards[idx].move_to_end(key)
                self.shards[idx][key] = value
            else:
                if len(self.shards[idx]) >= self.shard_capacity:
                    self.shards[idx].popitem(last=False)
                self.shards[idx][key] = value
```

---

### 16.4 Rate Limiter (Token Bucket)

**Asked at:** Uber, Google, Stripe, Amazon

**Problem:** Allow at most N requests per time window. Excess requests are rejected.

**Concepts:** Token refill, thread-safe state

**Token Bucket:** A bucket holds up to N tokens. Each request costs a token. Tokens refill at a fixed rate. Empty bucket = rejected.

```python
import threading
import time

class TokenBucketRateLimiter:
    def __init__(self, rate: float, capacity: int):
        """
        rate: tokens added per second
        capacity: max tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity  # Start full
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def allow(self) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


# Test: 5 requests/sec, burst capacity of 5
limiter = TokenBucketRateLimiter(rate=5, capacity=5)

def make_requests(client_id):
    for i in range(10):
        allowed = "ALLOWED" if limiter.allow() else "REJECTED"
        print(f"Client-{client_id} Request-{i}: {allowed}")
        time.sleep(0.05)

threads = [threading.Thread(target=make_requests, args=(i,)) for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
```

---

### 16.5 Rate Limiter (Sliding Window)

**Asked at:** Uber, Google, Meta

**Concepts:** Deque as timestamp window, cleanup of expired entries

```python
import threading
import time
from collections import deque

class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self.timestamps = deque()
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.monotonic()

            # Remove expired timestamps
            while self.timestamps and now - self.timestamps[0] >= self.window:
                self.timestamps.popleft()

            if len(self.timestamps) < self.max_requests:
                self.timestamps.append(now)
                return True
            return False


# Per-user rate limiter
class PerUserRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self.user_limiters = {}
        self.lock = threading.Lock()

    def allow(self, user_id: str) -> bool:
        with self.lock:
            if user_id not in self.user_limiters:
                self.user_limiters[user_id] = SlidingWindowRateLimiter(
                    self.max_requests, self.window
                )
        return self.user_limiters[user_id].allow()
```

---

### 16.6 Print In Order / Sequence Controller

**Asked at:** LeetCode 1114, Amazon, Google

**Problem:** Three threads call `first()`, `second()`, `third()`. Ensure they always execute in order.

**Concepts:** Event-based signaling

```python
import threading

class PrintInOrder:
    def __init__(self):
        self.first_done = threading.Event()
        self.second_done = threading.Event()

    def first(self):
        print("first", end=" ")
        self.first_done.set()

    def second(self):
        self.first_done.wait()      # Wait until first() is done
        print("second", end=" ")
        self.second_done.set()

    def third(self):
        self.second_done.wait()     # Wait until second() is done
        print("third")


# Threads start in random order, output is always "first second third"
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

---

### 16.7 Print FooBar Alternately

**Asked at:** LeetCode 1115, Google, Meta

**Problem:** Two threads must print "foobar" N times, alternating.

**Concepts:** Mutual signaling between threads

```python
import threading

class FooBar:
    def __init__(self, n):
        self.n = n
        self.foo_event = threading.Event()
        self.bar_event = threading.Event()
        self.foo_event.set()    # foo goes first

    def foo(self):
        for _ in range(self.n):
            self.foo_event.wait()
            print("foo", end="")
            self.foo_event.clear()
            self.bar_event.set()

    def bar(self):
        for _ in range(self.n):
            self.bar_event.wait()
            print("bar", end=" ")
            self.bar_event.clear()
            self.foo_event.set()


fb = FooBar(3)
t1 = threading.Thread(target=fb.foo)
t2 = threading.Thread(target=fb.bar)
t1.start(); t2.start()
t1.join(); t2.join()
# Output: foobar foobar foobar
```

---

### 16.8 Dining Philosophers

**Asked at:** LeetCode 1226, Google, Microsoft

**Problem:** 5 philosophers at a round table. Each needs 2 forks to eat. Adjacent philosophers share a fork. Prevent deadlock.

**Concepts:** Deadlock avoidance via lock ordering

```python
import threading
import time
import random

class DiningPhilosophers:
    def __init__(self, n=5):
        self.n = n
        self.forks = [threading.Lock() for _ in range(n)]

    def philosopher(self, phil_id):
        left = phil_id
        right = (phil_id + 1) % self.n

        # Deadlock fix: always pick the lower-numbered fork first
        first = min(left, right)
        second = max(left, right)

        for meal in range(3):
            # Think
            print(f"Philosopher {phil_id}: Thinking...")
            time.sleep(random.uniform(0.1, 0.3))

            # Pick up forks (in consistent order — no deadlock!)
            self.forks[first].acquire()
            self.forks[second].acquire()

            # Eat
            print(f"Philosopher {phil_id}: Eating meal {meal + 1}")
            time.sleep(random.uniform(0.1, 0.2))

            # Put down forks
            self.forks[second].release()
            self.forks[first].release()

        print(f"Philosopher {phil_id}: Done!")


dp = DiningPhilosophers(5)
threads = [threading.Thread(target=dp.philosopher, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()
```

**Alternative: Limit Diners with Semaphore**

```python
class DiningPhilosophersV2:
    def __init__(self, n=5):
        self.n = n
        self.forks = [threading.Lock() for _ in range(n)]
        self.seats = threading.Semaphore(n - 1)  # Only N-1 can try at once

    def philosopher(self, phil_id):
        left = phil_id
        right = (phil_id + 1) % self.n

        for meal in range(3):
            self.seats.acquire()    # Limit concurrent diners → no deadlock
            self.forks[left].acquire()
            self.forks[right].acquire()

            print(f"Philosopher {phil_id}: Eating meal {meal + 1}")
            time.sleep(0.1)

            self.forks[right].release()
            self.forks[left].release()
            self.seats.release()
```

---

### 16.9 Blocking Queue

**Asked at:** Amazon, Google, Uber, Goldman Sachs

**Problem:** Implement a queue from scratch where `put()` blocks if full and `get()` blocks if empty.

**Concepts:** Condition variables, graceful shutdown

```python
import threading
from collections import deque

class BlockingQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.queue = deque()
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)
        self._shutdown = False

    def put(self, item):
        with self.not_full:
            while len(self.queue) >= self.capacity:
                if self._shutdown:
                    raise RuntimeError("Queue is shut down")
                self.not_full.wait()
            self.queue.append(item)
            self.not_empty.notify()

    def get(self, timeout=None):
        with self.not_empty:
            while len(self.queue) == 0:
                if self._shutdown:
                    return None
                if not self.not_empty.wait(timeout=timeout):
                    raise TimeoutError("Timed out waiting for item")
            item = self.queue.popleft()
            self.not_full.notify()
            return item

    def size(self):
        with self.lock:
            return len(self.queue)

    def shutdown(self):
        with self.lock:
            self._shutdown = True
            self.not_empty.notify_all()
            self.not_full.notify_all()
```

---

### 16.10 Thread Pool from Scratch

**Asked at:** Uber, Google, Amazon

**Problem:** Implement a thread pool that accepts tasks, runs them on worker threads, and supports graceful shutdown.

**Concepts:** Worker threads, task queue, shutdown coordination

```python
import threading
from collections import deque

class ThreadPool:
    def __init__(self, num_workers: int):
        self.tasks = deque()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.shutdown_flag = False
        self.workers = []

        for i in range(num_workers):
            t = threading.Thread(target=self._worker, name=f"Worker-{i}", daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while True:
            with self.condition:
                while len(self.tasks) == 0 and not self.shutdown_flag:
                    self.condition.wait()

                if self.shutdown_flag and len(self.tasks) == 0:
                    return  # Exit thread

                task, args, kwargs = self.tasks.popleft()

            # Execute OUTSIDE the lock — so other workers can pick up tasks
            try:
                task(*args, **kwargs)
            except Exception as e:
                print(f"{threading.current_thread().name}: Error — {e}")

    def submit(self, task, *args, **kwargs):
        with self.condition:
            if self.shutdown_flag:
                raise RuntimeError("Pool is shut down")
            self.tasks.append((task, args, kwargs))
            self.condition.notify()  # Wake one worker

    def shutdown(self, wait=True):
        with self.condition:
            self.shutdown_flag = True
            self.condition.notify_all()  # Wake all workers so they can exit

        if wait:
            for t in self.workers:
                t.join()


# Usage
import time

def process(task_id):
    print(f"{threading.current_thread().name}: Processing task {task_id}")
    time.sleep(0.5)
    print(f"{threading.current_thread().name}: Done task {task_id}")

pool = ThreadPool(num_workers=3)

for i in range(10):
    pool.submit(process, i)

time.sleep(4)
pool.shutdown(wait=True)
print("All done!")
```

---

### 16.11 Scheduled Task Executor (Uber)

**Asked at:** Uber, Google, Amazon

**Problem:** Implement a scheduler that can run tasks at a future time, or repeatedly at fixed intervals. Think: retry failed payments, send ride reminders, clean up expired surge pricing.

**Concepts:** Min-heap for scheduling, condition variable with timeout

```python
import threading
import time
import heapq

class ScheduledExecutor:
    def __init__(self, num_workers=2):
        self.task_queue = []        # Min-heap of (run_time, task_id, func, args, interval)
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.task_counter = 0
        self.shutdown_flag = False
        self.workers = []

        for i in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def schedule(self, func, delay_seconds, *args):
        """Run func once after delay_seconds."""
        run_at = time.monotonic() + delay_seconds
        with self.condition:
            self.task_counter += 1
            heapq.heappush(self.task_queue, (run_at, self.task_counter, func, args, 0))
            self.condition.notify()

    def schedule_at_fixed_rate(self, func, initial_delay, period, *args):
        """Run func repeatedly every `period` seconds."""
        run_at = time.monotonic() + initial_delay
        with self.condition:
            self.task_counter += 1
            heapq.heappush(self.task_queue, (run_at, self.task_counter, func, args, period))
            self.condition.notify()

    def _worker(self):
        while True:
            with self.condition:
                while True:
                    if self.shutdown_flag:
                        return

                    if not self.task_queue:
                        self.condition.wait()
                        continue

                    next_run_time = self.task_queue[0][0]
                    now = time.monotonic()

                    if now >= next_run_time:
                        # Time to run!
                        run_at, task_id, func, args, period = heapq.heappop(self.task_queue)
                        break
                    else:
                        # Wait until next task is due (or new task arrives)
                        self.condition.wait(timeout=next_run_time - now)

            # Execute OUTSIDE the lock
            try:
                func(*args)
            except Exception as e:
                print(f"Task error: {e}")

            # Reschedule if periodic
            if period > 0:
                with self.condition:
                    self.task_counter += 1
                    next_run = time.monotonic() + period
                    heapq.heappush(self.task_queue,
                                   (next_run, self.task_counter, func, args, period))
                    self.condition.notify()

    def shutdown(self):
        with self.condition:
            self.shutdown_flag = True
            self.condition.notify_all()
        for t in self.workers:
            t.join()


# Usage
scheduler = ScheduledExecutor(num_workers=2)

scheduler.schedule(lambda: print(f"[{time.strftime('%H:%M:%S')}] One-time task!"), 2)
scheduler.schedule_at_fixed_rate(
    lambda: print(f"[{time.strftime('%H:%M:%S')}] Heartbeat"), 0, 1
)
scheduler.schedule(lambda: print(f"[{time.strftime('%H:%M:%S')}] Delayed task!"), 5)

time.sleep(6)
scheduler.shutdown()
```

---

### 16.12 Ride Matching System (Uber)

**Asked at:** Uber machine coding rounds

**Problem:** Build a concurrent ride matching system. Riders request rides, drivers go online/offline, and a matcher pairs them. Multiple matchers and requests happen concurrently.

**Concepts:** Multiple condition variables, background worker thread, nearest-match algorithm

```python
import threading
import time
import random
from collections import deque
from dataclasses import dataclass
from enum import Enum

class RideStatus(Enum):
    REQUESTED = "REQUESTED"
    MATCHED = "MATCHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

@dataclass
class Location:
    lat: float
    lng: float

    def distance_to(self, other):
        return ((self.lat - other.lat)**2 + (self.lng - other.lng)**2) ** 0.5

@dataclass
class Driver:
    id: str
    name: str
    location: Location
    available: bool = True

@dataclass
class RideRequest:
    id: str
    rider_name: str
    pickup: Location
    dropoff: Location
    status: RideStatus = RideStatus.REQUESTED
    driver: Driver = None


class RideMatchingSystem:
    def __init__(self):
        self.available_drivers = []
        self.pending_requests = deque()
        self.active_rides = {}              # ride_id → RideRequest
        self.lock = threading.Lock()
        self.new_request = threading.Condition(self.lock)
        self.driver_available = threading.Condition(self.lock)
        self.shutdown_flag = False

        # Background matcher thread
        self.matcher = threading.Thread(target=self._match_loop, daemon=True)
        self.matcher.start()

    def add_driver(self, driver: Driver):
        with self.driver_available:
            self.available_drivers.append(driver)
            print(f"[SYSTEM] Driver {driver.name} is now online")
            self.driver_available.notify_all()

    def remove_driver(self, driver_id: str):
        with self.lock:
            self.available_drivers = [d for d in self.available_drivers if d.id != driver_id]

    def request_ride(self, request: RideRequest):
        with self.new_request:
            self.pending_requests.append(request)
            print(f"[RIDER]  {request.rider_name} requested ride {request.id}")
            self.new_request.notify()

    def complete_ride(self, ride_id: str):
        with self.driver_available:
            if ride_id in self.active_rides:
                ride = self.active_rides.pop(ride_id)
                ride.status = RideStatus.COMPLETED
                ride.driver.available = True
                self.available_drivers.append(ride.driver)
                print(f"[DONE]   Ride {ride_id} completed. {ride.driver.name} is free")
                self.driver_available.notify_all()

    def _find_nearest_driver(self, pickup: Location):
        if not self.available_drivers:
            return None
        return min(self.available_drivers, key=lambda d: d.location.distance_to(pickup))

    def _match_loop(self):
        while True:
            with self.new_request:
                while len(self.pending_requests) == 0 and not self.shutdown_flag:
                    self.new_request.wait()
                if self.shutdown_flag:
                    return
                request = self.pending_requests[0]

            with self.driver_available:
                while not self.available_drivers and not self.shutdown_flag:
                    self.driver_available.wait(timeout=5)
                if self.shutdown_flag:
                    return

                driver = self._find_nearest_driver(request.pickup)
                if driver is None:
                    continue
                self.available_drivers.remove(driver)
                driver.available = False

            with self.lock:
                if self.pending_requests and self.pending_requests[0] is request:
                    self.pending_requests.popleft()
                    request.driver = driver
                    request.status = RideStatus.MATCHED
                    self.active_rides[request.id] = request
                    dist = driver.location.distance_to(request.pickup)
                    print(f"[MATCH]  Ride {request.id} → Driver {driver.name} "
                          f"(distance: {dist:.2f})")

    def shutdown(self):
        with self.new_request:
            self.shutdown_flag = True
            self.new_request.notify_all()
        with self.driver_available:
            self.driver_available.notify_all()


# --- Simulation ---
system = RideMatchingSystem()

drivers = [
    Driver("D1", "Alice", Location(40.7, -74.0)),
    Driver("D2", "Bob",   Location(40.8, -73.9)),
    Driver("D3", "Carol", Location(40.6, -74.1)),
]
for d in drivers:
    system.add_driver(d)

time.sleep(0.1)

# Riders request rides concurrently
def rider_thread(rider_id):
    req = RideRequest(
        id=f"R{rider_id}",
        rider_name=f"Rider-{rider_id}",
        pickup=Location(40.7 + random.uniform(-0.1, 0.1),
                        -74.0 + random.uniform(-0.1, 0.1)),
        dropoff=Location(40.8, -73.9),
    )
    system.request_ride(req)

riders = [threading.Thread(target=rider_thread, args=(i,)) for i in range(5)]
for r in riders: r.start()
for r in riders: r.join()

time.sleep(2)

# Complete some rides → drivers free → pending rides get matched
system.complete_ride("R0")
system.complete_ride("R1")

time.sleep(2)
system.shutdown()
```

---

### 16.13 Concurrent Web Crawler

**Asked at:** Google, Meta, Amazon, LeetCode 1242

**Problem:** Crawl pages starting from a URL. Multiple threads fetch pages concurrently. Don't visit the same URL twice.

**Concepts:** Thread coordination, visited set, termination detection

```python
import threading
import time
import random
from collections import deque

class ConcurrentCrawler:
    def __init__(self, num_workers=4):
        self.visited = set()
        self.visited_lock = threading.Lock()
        self.queue = deque()
        self.queue_lock = threading.Lock()
        self.condition = threading.Condition(self.queue_lock)
        self.active_workers = 0
        self.results = []
        self.results_lock = threading.Lock()
        self.num_workers = num_workers

    def crawl(self, start_url, get_links_func):
        with self.visited_lock:
            self.visited.add(start_url)
        with self.condition:
            self.queue.append(start_url)
            self.condition.notify()

        workers = []
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker, args=(get_links_func,))
            t.start()
            workers.append(t)

        for t in workers:
            t.join()
        return self.results

    def _worker(self, get_links_func):
        while True:
            with self.condition:
                while len(self.queue) == 0:
                    if self.active_workers == 0:
                        self.condition.notify_all()
                        return  # No work and no one working → done
                    self.condition.wait(timeout=1)
                    if len(self.queue) == 0 and self.active_workers == 0:
                        self.condition.notify_all()
                        return

                url = self.queue.popleft()
                self.active_workers += 1

            # Fetch page (outside lock)
            try:
                links = get_links_func(url)
                with self.results_lock:
                    self.results.append(url)

                with self.visited_lock:
                    new_urls = [u for u in links if u not in self.visited]
                    self.visited.update(new_urls)

                with self.condition:
                    for u in new_urls:
                        self.queue.append(u)
                    self.condition.notify_all()
            finally:
                with self.condition:
                    self.active_workers -= 1
                    if self.active_workers == 0 and len(self.queue) == 0:
                        self.condition.notify_all()


# Mock web graph
web_graph = {
    "example.com":   ["example.com/a", "example.com/b"],
    "example.com/a": ["example.com/c", "example.com/d"],
    "example.com/b": ["example.com/d", "example.com/e"],
    "example.com/c": [],
    "example.com/d": ["example.com/e"],
    "example.com/e": [],
}

def mock_fetch(url):
    time.sleep(random.uniform(0.1, 0.3))
    return web_graph.get(url, [])

crawler = ConcurrentCrawler(num_workers=3)
results = crawler.crawl("example.com", mock_fetch)
print(f"\nCrawled {len(results)} pages: {results}")
```

---

### 16.14 Traffic Signal Controller

**Asked at:** Uber, Goldman Sachs

**Problem:** A 4-way intersection with traffic lights. Cars arrive on different roads. Only one direction can have green. Cars wait until their direction is green.

**Concepts:** Condition variables, background cycling thread

```python
import threading
import time
import random
from enum import Enum

class Direction(Enum):
    NORTH_SOUTH = "NORTH_SOUTH"
    EAST_WEST = "EAST_WEST"

class TrafficSignal:
    def __init__(self, green_duration=3):
        self.current_green = Direction.NORTH_SOUTH
        self.lock = threading.Lock()
        self.ns_green = threading.Condition(self.lock)
        self.ew_green = threading.Condition(self.lock)
        self.green_duration = green_duration
        self.running = True

        self.signal_thread = threading.Thread(target=self._cycle, daemon=True)
        self.signal_thread.start()

    def _cycle(self):
        while self.running:
            time.sleep(self.green_duration)
            with self.lock:
                if self.current_green == Direction.NORTH_SOUTH:
                    self.current_green = Direction.EAST_WEST
                    print(f"\n--- GREEN: EAST-WEST | RED: NORTH-SOUTH ---")
                    self.ew_green.notify_all()
                else:
                    self.current_green = Direction.NORTH_SOUTH
                    print(f"\n--- GREEN: NORTH-SOUTH | RED: EAST-WEST ---")
                    self.ns_green.notify_all()

    def cross(self, car_id: str, direction: Direction):
        with self.lock:
            while self.current_green != direction:
                if direction == Direction.NORTH_SOUTH:
                    self.ns_green.wait()
                else:
                    self.ew_green.wait()
            print(f"  Car {car_id} crossing ({direction.value})")

    def stop(self):
        self.running = False


signal = TrafficSignal(green_duration=2)

def car(car_id, direction):
    time.sleep(random.uniform(0, 3))
    print(f"Car {car_id} arrives ({direction.value})")
    signal.cross(car_id, direction)

threads = []
for i in range(10):
    d = random.choice([Direction.NORTH_SOUTH, Direction.EAST_WEST])
    threads.append(threading.Thread(target=car, args=(f"C{i}", d)))

for t in threads: t.start()
for t in threads: t.join()
signal.stop()
```

---

### 16.15 Async Job Scheduler

**Asked at:** Uber, Meta, Google

**Problem:** A job scheduler that accepts jobs with dependencies (DAG). A job runs only after all its dependencies complete. Independent jobs run concurrently.

**Concepts:** Topological ordering, dynamic readiness tracking, thread pool

```python
import threading
import time
from collections import defaultdict, deque

class Job:
    def __init__(self, job_id: str, func, dependencies=None):
        self.id = job_id
        self.func = func
        self.dependencies = dependencies or []

class JobScheduler:
    def __init__(self, num_workers=4):
        self.num_workers = num_workers

    def execute(self, jobs: list):
        # Build graph
        graph = {}
        in_degree = defaultdict(int)
        dependents = defaultdict(list)

        for job in jobs:
            graph[job.id] = job
            in_degree[job.id] = len(job.dependencies)
            for dep in job.dependencies:
                dependents[dep].append(job.id)

        lock = threading.Lock()
        condition = threading.Condition(lock)
        ready_queue = deque()
        completed = set()
        total = len(jobs)

        # Seed: jobs with no dependencies
        for job in jobs:
            if in_degree[job.id] == 0:
                ready_queue.append(job.id)

        def worker():
            while True:
                with condition:
                    while len(ready_queue) == 0:
                        if len(completed) == total:
                            return
                        condition.wait()
                    if len(completed) == total:
                        return
                    job_id = ready_queue.popleft()

                # Execute outside lock
                job = graph[job_id]
                print(f"[{threading.current_thread().name}] Running: {job_id}")
                try:
                    job.func()
                except Exception as e:
                    print(f"Job {job_id} failed: {e}")

                # Unblock dependents
                with condition:
                    completed.add(job_id)
                    for dep_id in dependents[job_id]:
                        in_degree[dep_id] -= 1
                        if in_degree[dep_id] == 0:
                            ready_queue.append(dep_id)
                    condition.notify_all()

        workers = [threading.Thread(target=worker, name=f"W-{i}")
                   for i in range(self.num_workers)]
        for w in workers: w.start()
        for w in workers: w.join()
        print("All jobs completed!")


# Diamond dependency: A,B → C → D. E is independent.
def make_task(name, duration=0.5):
    def task():
        time.sleep(duration)
        print(f"  >> {name} done")
    return task

jobs = [
    Job("A", make_task("A")),
    Job("B", make_task("B")),
    Job("C", make_task("C"), dependencies=["A", "B"]),
    Job("D", make_task("D"), dependencies=["C"]),
    Job("E", make_task("E")),  # Independent — runs in parallel with A,B
]

scheduler = JobScheduler(num_workers=3)
scheduler.execute(jobs)
```

---

## 17. Interview Quick Reference

### Python Concurrency Primitives

```
Primitive              | Import                    | What It Does
-----------------------|---------------------------|-------------------------------------
Lock                   | threading.Lock()          | Mutual exclusion (1 thread at a time)
RLock                  | threading.RLock()         | Same thread can acquire multiple times
Condition              | threading.Condition()     | wait/notify for coordination
Semaphore              | threading.Semaphore(N)    | Allow N concurrent threads
BoundedSemaphore       | threading.BoundedSemaphore(N) | Errors on over-release
Event                  | threading.Event()         | Simple boolean flag for signaling
Barrier                | threading.Barrier(N)      | Wait for N threads at checkpoint
Queue                  | queue.Queue(maxsize)      | Thread-safe FIFO (blocks full/empty)
Timer                  | threading.Timer(secs, fn) | Run function after delay
ThreadPoolExecutor     | concurrent.futures        | Reusable thread pool
asyncio.Lock           | asyncio                   | Async-compatible lock
```

### Decision Flowchart

```
What kind of work?
  │
  ├── I/O-bound (network, disk, DB)
  │     ├── Few concurrent ops       → threading.Thread
  │     ├── Many concurrent ops      → ThreadPoolExecutor
  │     └── Very many (10K+)         → asyncio
  │
  └── CPU-bound (math, processing)
        ├── Can parallelize           → ProcessPoolExecutor
        └── Can't parallelize         → optimize algorithm
```

### Common Interview Q&A

| Question | Answer |
|----------|--------|
| What is the GIL? | Traditional CPython mechanism that normally permits one thread at a time to execute Python bytecode |
| Threads useful despite GIL? | Yes; blocking I/O and many native operations release it, and free-threaded builds are also available |
| Lock vs RLock? | RLock lets same thread acquire multiple times; Lock deadlocks |
| Why `while` not `if` with `wait()`? | Spurious wakeups — thread can wake without notify |
| `notify()` vs `notify_all()`? | `notify()` wakes one, `notify_all()` wakes all |
| How to prevent deadlock? | Consistent lock ordering, timeouts, or acquire all atomically |
| Semaphore vs Lock? | Lock = 1 thread max. Semaphore = N threads max |
| Event vs Condition? | Event = simple flag. Condition = flag + built-in lock |
| `queue.Queue` vs `deque`? | Queue = thread-safe blocking. deque = fast, single-thread/DSA |
| Thread vs Process? | Thread shares memory (fast, risky). Process isolated (slow, safe) |
| When to use asyncio? | High-concurrency I/O (thousands of connections, one thread) |
| What is happens-before? | A synchronization-backed guarantee that one action's effects are ordered before another action |
| Atomic operation vs thread-safe operation? | Atomicity covers one indivisible step; thread safety preserves the complete shared-state contract |
| CPU low but requests stuck? | Inspect repeated thread stacks for deadlock, missed signaling, pool exhaustion, or blocked I/O |
| Why can a thread pool deadlock? | Workers can synchronously wait for tasks queued behind them in the same exhausted pool |
| What is priority inversion? | High-priority work waits for a resource held by low-priority work that is delayed by medium-priority work |
| What is the ABA problem? | CAS sees A again and misses that the value changed from A to B and back to A |

### Machine Coding Round Tips

1. **Clarify first:** Ask about scale, thread count, fairness, and shutdown behavior
2. **Draw the model:** Which threads exist? What do they share? Where are the critical sections?
3. **Identify shared state:** Every shared mutable variable needs a lock
4. **Pick the right primitive:** Don't use Condition when Event suffices
5. **Always use `with` for locks:** Prevents forgetting to release
6. **Always use `while` with `wait()`:** Handles spurious wakeups
7. **Keep critical sections minimal:** Do I/O and computation outside locks
8. **Walk through with 2-3 threads:** Show the interviewer there's no race condition
9. **Handle shutdown:** Show you can gracefully stop worker threads
10. **State complexity:** Time and space for each operation
