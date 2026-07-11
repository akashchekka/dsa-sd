# Multithreading & Concurrency in C# — FAANG Interview Guide

> **Goal:** Understand concurrency from scratch, then solve machine coding / LLD rounds at Uber, Google, Meta, Amazon, etc. All examples in C#.

---

## Table of Contents

- [Multithreading \& Concurrency in C# — FAANG Interview Guide](#multithreading--concurrency-in-c--faang-interview-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Why Concurrency?](#1-why-concurrency)
  - [Concurrency vs Parallelism](#concurrency-vs-parallelism)
    - [Key Terms (Just 4 to Start)](#key-terms-just-4-to-start)
  - [2. Threads, Processes \& the CLR](#2-threads-processes--the-clr)
    - [Thread vs Process](#thread-vs-process)
    - [C# vs Python: No GIL](#c-vs-python-no-gil)
  - [3. Creating Threads](#3-creating-threads)
    - [Basic Thread Creation](#basic-thread-creation)
    - [Background Threads](#background-threads)
    - [Key Properties \& Methods](#key-properties--methods)
  - [4. Race Conditions — The Core Problem](#4-race-conditions--the-core-problem)
    - [The Classic Bug](#the-classic-bug)
    - [Why Does This Happen?](#why-does-this-happen)
    - [Types of Race Conditions](#types-of-race-conditions)
    - [Fix: Use a Lock](#fix-use-a-lock)
  - [5. lock \& Monitor (Mutex)](#5-lock--monitor-mutex)
    - [Basic Usage](#basic-usage)
    - [Bank Account Example](#bank-account-example)
    - [Mutex — Cross-Process Locking](#mutex--cross-process-locking)
    - [Rules for Using Locks](#rules-for-using-locks)
  - [6. Reentrant Locking (Monitor is Reentrant)](#6-reentrant-locking-monitor-is-reentrant)
  - [7. Monitor.Wait / Pulse (Condition Variables)](#7-monitorwait--pulse-condition-variables)
    - [The Problem Without Conditions](#the-problem-without-conditions)
    - [The Solution: Monitor.Wait / Pulse](#the-solution-monitorwait--pulse)
    - [How Monitor.Wait() Works (3 Steps, Atomic)](#how-monitorwait-works-3-steps-atomic)
    - [Key Methods](#key-methods)
    - [Why while Not if?](#why-while-not-if)
  - [8. Semaphores](#8-semaphores)
    - [SemaphoreSlim — Lightweight Version](#semaphoreslim--lightweight-version)
    - [Semaphore vs Lock](#semaphore-vs-lock)
  - [9. Events (ManualResetEvent \& AutoResetEvent)](#9-events-manualresetevent--autoresetevent)
    - [ManualResetEventSlim — Lightweight Version](#manualreseteventslim--lightweight-version)
    - [AutoResetEvent vs ManualResetEvent](#autoresetevent-vs-manualresetevent)
  - [10. Barriers](#10-barriers)
  - [11. Interlocked \& Volatile](#11-interlocked--volatile)
    - [Interlocked — Lock-Free Atomic Operations](#interlocked--lock-free-atomic-operations)
    - [volatile — Memory Visibility](#volatile--memory-visibility)
  - [12. Thread-Safe Data Structures](#12-thread-safe-data-structures)
    - [BlockingCollection — Thread-Safe Producer-Consumer](#blockingcollection--thread-safe-producer-consumer)
    - [Concurrent Collections](#concurrent-collections)
    - [Channel — Modern Async Producer-Consumer](#channel--modern-async-producer-consumer)
  - [13. Deadlock, Livelock \& Starvation](#13-deadlock-livelock--starvation)
    - [Deadlock](#deadlock)
    - [4 Conditions for Deadlock (ALL must be true)](#4-conditions-for-deadlock-all-must-be-true)
    - [Fix: Consistent Lock Ordering](#fix-consistent-lock-ordering)
    - [Fix: Timeout](#fix-timeout)
    - [Livelock](#livelock)
    - [Starvation](#starvation)
    - [Summary](#summary)
  - [14. Thread Pool \& Task Parallel Library (TPL)](#14-thread-pool--task-parallel-library-tpl)
    - [Task — The Modern Way](#task--the-modern-way)
    - [Parallel.For / Parallel.ForEach](#parallelfor--parallelforeach)
    - [PLINQ — Parallel LINQ](#plinq--parallel-linq)
    - [When to Use What](#when-to-use-what)
  - [15. async/await](#15-asyncawait)
    - [Task vs ValueTask](#task-vs-valuetask)
    - [ConfigureAwait](#configureawait)
    - [CancellationToken — Cooperative Cancellation](#cancellationtoken--cooperative-cancellation)
    - [async Synchronization Primitives](#async-synchronization-primitives)
    - [async vs Threading — When to Use](#async-vs-threading--when-to-use)
  - [16. Common Patterns Cheat Sheet](#16-common-patterns-cheat-sheet)
  - [17. Machine Coding Problems](#17-machine-coding-problems)
    - [17.1 Producer-Consumer (Bounded Buffer)](#171-producer-consumer-bounded-buffer)
    - [17.2 Reader-Writer Lock](#172-reader-writer-lock)
    - [17.3 Thread-Safe LRU Cache](#173-thread-safe-lru-cache)
    - [17.4 Rate Limiter (Token Bucket)](#174-rate-limiter-token-bucket)
    - [17.5 Rate Limiter (Sliding Window)](#175-rate-limiter-sliding-window)
    - [17.6 Print In Order / Sequence Controller](#176-print-in-order--sequence-controller)
    - [17.7 Print FooBar Alternately](#177-print-foobar-alternately)
    - [17.8 Dining Philosophers](#178-dining-philosophers)
    - [17.9 Blocking Queue](#179-blocking-queue)
    - [17.10 Thread Pool from Scratch](#1710-thread-pool-from-scratch)
    - [17.11 Scheduled Task Executor (Uber)](#1711-scheduled-task-executor-uber)
    - [17.12 Ride Matching System (Uber)](#1712-ride-matching-system-uber)
    - [17.13 Concurrent Web Crawler](#1713-concurrent-web-crawler)
    - [17.14 Traffic Signal Controller](#1714-traffic-signal-controller)
    - [17.15 Async Job Scheduler (DAG)](#1715-async-job-scheduler-dag)
  - [18. Interview Quick Reference](#18-interview-quick-reference)
    - [C# Concurrency Primitives](#c-concurrency-primitives)
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

In C# specifically:
- **Threads** give you both concurrency AND parallelism (no GIL like Python — threads truly run in parallel on multi-core machines).
- **Task Parallel Library (TPL)** abstracts thread management — lets the runtime decide how many threads to use.
- **async/await** gives you concurrency (potentially parallelism depending on `SynchronizationContext`).
- **Parallel.For / PLINQ** give data parallelism for CPU-bound work.

### Key Terms (Just 4 to Start)

| Term | One-Line Definition |
|------|---------------------|
| **Thread** | A lightweight worker inside your program |
| **Lock** | Only one thread can enter the protected section at a time |
| **Race condition** | Bug caused by two threads touching the same data at the same time |
| **Deadlock** | Two threads waiting for each other forever — both stuck |

---

## 2. Threads, Processes & the CLR

### Thread vs Process

**Process** = Independent program with its own memory. Isolated but expensive to create.

**Thread** = Lightweight worker inside a process. Shares memory with other threads — fast but needs synchronization.

| | Process | Thread |
|---|---|---|
| **Memory** | Separate (isolated) | Shared (same heap) |
| **Cost** | Heavy (~MB of memory) | Light (~1MB stack default) |
| **Communication** | Hard (pipes, named pipes, IPC) | Easy (shared variables) |
| **Crash impact** | Only that process dies | Whole program can crash |

### C# vs Python: No GIL

Unlike Python, C# has **no Global Interpreter Lock**. The CLR allows true parallel execution of threads on multiple cores.

```
Python with GIL:
  Core 1: Thread A ████░░░░████░░░░████
  Core 1: Thread B ░░░░████░░░░████░░░░  ← Interleaved, not parallel

C# (no GIL):
  Core 1: Thread A ████████████████
  Core 2: Thread B ████████████████  ← True parallel execution!
```

This means:
- **CPU-bound work benefits from threads** in C# (unlike Python where you need `multiprocessing`).
- **Race conditions are more dangerous** — they occur more frequently because threads truly run simultaneously.
- **All synchronization concepts are critical** — you can't rely on the GIL accidentally serializing operations.

**For interviews:** C# concurrency questions expect you to handle true parallelism. Every shared mutable variable needs explicit synchronization.

---

## 3. Creating Threads

### Basic Thread Creation

```csharp
using System;
using System.Threading;

class Program
{
    static void Worker(string name, int milliseconds)
    {
        Console.WriteLine($"{name}: Starting");
        Thread.Sleep(milliseconds);  // Simulates work
        Console.WriteLine($"{name}: Done");
    }

    static void Main()
    {
        // Create threads
        var t1 = new Thread(() => Worker("Thread-1", 2000));
        var t2 = new Thread(() => Worker("Thread-2", 1000));

        // Start them (they run concurrently)
        t1.Start();
        t2.Start();

        // Wait for both to finish
        t1.Join();
        t2.Join();

        Console.WriteLine("All done!");
    }
}
```

Output:
```
Thread-1: Starting
Thread-2: Starting
Thread-2: Done      ← finishes first (only 1 second)
Thread-1: Done
All done!
```

### Background Threads

A background thread dies automatically when the main program exits (like Python daemon threads).

```csharp
// Background thread — won't keep the program alive
var t = new Thread(() => Worker("Background", 10000));
t.IsBackground = true;
t.Start();
// Program can exit immediately — background thread is killed
```

### Key Properties & Methods

| Member | What It Does |
|--------|--------------|
| `t.Start()` | Begin executing the thread |
| `t.Join()` | Wait for the thread to finish |
| `t.Join(5000)` | Wait at most 5 seconds (returns `bool`) |
| `t.IsAlive` | Check if thread is still running |
| `t.IsBackground = true` | Thread dies when main thread exits |
| `t.Priority` | Set thread priority (`Lowest` to `Highest`) |
| `Thread.CurrentThread` | Get the current thread object |
| `Thread.Sleep(ms)` | Pause the current thread |

---

## 4. Race Conditions — The Core Problem

A **race condition** happens when two threads read/write the same variable and the result depends on timing.

### The Classic Bug

```csharp
using System;
using System.Threading;

class Program
{
    static int counter = 0;

    static void Increment()
    {
        for (int i = 0; i < 1_000_000; i++)
        {
            counter++;  // NOT thread-safe!
        }
    }

    static void Main()
    {
        var t1 = new Thread(Increment);
        var t2 = new Thread(Increment);

        t1.Start();
        t2.Start();
        t1.Join();
        t2.Join();

        Console.WriteLine(counter);  // Expected: 2,000,000. Actual: ~1,500,000 (random!)
    }
}
```

### Why Does This Happen?

`counter++` looks like one operation, but it's actually THREE:

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

In C# this is **worse than Python** because threads truly run in parallel — the race happens more frequently.

### Types of Race Conditions

| Type | Example | Fix |
|------|---------|-----|
| **Read-modify-write** | `counter++` | `Interlocked.Increment` or `lock` |
| **Check-then-act** | `if (!dict.ContainsKey(k)) dict[k] = v` | `ConcurrentDictionary.GetOrAdd` or `lock` |
| **Compound action** | Transfer: `a -= x; b += x` | Lock both |

### Fix: Use a Lock

```csharp
using System;
using System.Threading;

class Program
{
    static int counter = 0;
    static readonly object lockObj = new object();

    static void Increment()
    {
        for (int i = 0; i < 1_000_000; i++)
        {
            lock (lockObj)          // Only one thread enters at a time
            {
                counter++;
            }
        }
    }

    static void Main()
    {
        var t1 = new Thread(Increment);
        var t2 = new Thread(Increment);

        t1.Start();
        t2.Start();
        t1.Join();
        t2.Join();

        Console.WriteLine(counter);  // Always 2,000,000 ✓
    }
}
```

Or better — use `Interlocked` for simple atomic operations:

```csharp
static void Increment()
{
    for (int i = 0; i < 1_000_000; i++)
    {
        Interlocked.Increment(ref counter);  // Atomic, no lock needed!
    }
}
```

---

## 5. lock & Monitor (Mutex)

The `lock` keyword is syntactic sugar for `Monitor.Enter` / `Monitor.Exit`. It ensures only one thread can execute a section of code at a time.

### Basic Usage

```csharp
private readonly object _lock = new object();

// Method 1: lock statement (preferred — auto-releases)
lock (_lock)
{
    // critical section — only one thread here at a time
    sharedList.Add(item);
}

// Method 2: Manual Monitor (what lock compiles to)
bool lockTaken = false;
try
{
    Monitor.Enter(_lock, ref lockTaken);
    sharedList.Add(item);
}
finally
{
    if (lockTaken) Monitor.Exit(_lock);  // ALWAYS release in finally!
}

// Method 3: TryEnter with timeout
if (Monitor.TryEnter(_lock, TimeSpan.FromSeconds(5)))
{
    try
    {
        DoWork();
    }
    finally
    {
        Monitor.Exit(_lock);
    }
}
else
{
    Console.WriteLine("Timed out waiting for lock");
}
```

### Bank Account Example

```csharp
public class BankAccount
{
    private decimal _balance;
    private readonly object _lock = new object();

    public BankAccount(decimal balance) => _balance = balance;

    public decimal Balance
    {
        get { lock (_lock) { return _balance; } }
    }

    public void Deposit(decimal amount)
    {
        lock (_lock)
        {
            _balance += amount;
        }
    }

    public bool Withdraw(decimal amount)
    {
        lock (_lock)
        {
            if (_balance >= amount)
            {
                _balance -= amount;
                return true;
            }
            return false;
        }
    }

    public bool Transfer(BankAccount other, decimal amount)
    {
        // Need to lock BOTH accounts — but be careful of deadlock!
        // Solution: always lock in a consistent order (by hashcode / id)
        object first, second;
        if (GetHashCode() < other.GetHashCode())
        {
            first = _lock;
            second = other._lock;
        }
        else
        {
            first = other._lock;
            second = _lock;
        }

        lock (first)
        {
            lock (second)
            {
                if (_balance >= amount)
                {
                    _balance -= amount;
                    other._balance += amount;
                    return true;
                }
                return false;
            }
        }
    }
}
```

### Mutex — Cross-Process Locking

`Mutex` is a heavier lock that works across processes (e.g., ensuring only one instance of an app runs).

```csharp
// Named mutex — works across processes
using var mutex = new Mutex(false, "Global\\MyAppMutex");

if (mutex.WaitOne(TimeSpan.FromSeconds(5)))
{
    try
    {
        // Only one process can be here at a time
        Console.WriteLine("Got the mutex — running!");
    }
    finally
    {
        mutex.ReleaseMutex();
    }
}
else
{
    Console.WriteLine("Another instance is already running");
}
```

| | `lock` / `Monitor` | `Mutex` |
|---|---|---|
| Scope | Single process | Cross-process |
| Performance | Fast (user-mode) | Slow (kernel object) |
| Use case | Protecting shared data | Single-instance app, cross-process sync |

### Rules for Using Locks

1. **Keep critical sections SHORT** — hold the lock for as little time as possible
2. **Always release** — use `lock` statement (auto-releases) or `try/finally`
3. **Don't do I/O while holding a lock** — other threads will be blocked for a long time
4. **Lock on private objects** — NEVER lock on `this`, `typeof(T)`, or string literals
5. **Consistent ordering** — if you need multiple locks, always acquire in the same order
6. **Never lock on value types** — they get boxed to different objects each time

```csharp
// ❌ BAD — don't lock on these!
lock (this)              // External code could lock on same object
lock (typeof(MyClass))   // Shared across entire AppDomain
lock ("myLock")          // Interned strings are shared

// ✅ GOOD — lock on a private dedicated object
private readonly object _lock = new object();
lock (_lock)
```

---

## 6. Reentrant Locking (Monitor is Reentrant)

Unlike Python's `Lock` (which deadlocks on re-entry), C#'s `lock` / `Monitor` is already reentrant. The same thread can acquire the same lock multiple times without deadlocking.

```csharp
private readonly object _lock = new object();

// ✅ Works fine — Monitor is reentrant
void Outer()
{
    lock (_lock)
    {
        Inner();  // Same thread acquires _lock again — no deadlock!
    }
}

void Inner()
{
    lock (_lock)  // Re-entrant — increments count internally
    {
        Console.WriteLine("This works!");
    }
    // count decremented
}
// count drops to 0 — lock released
```

This means methods that hold a lock can freely call other methods that also need the same lock:

```csharp
public class SafeList<T>
{
    private readonly List<T> _items = new();
    private readonly object _lock = new object();

    public void Add(T item)
    {
        lock (_lock)
        {
            _items.Add(item);
        }
    }

    public void AddRange(IEnumerable<T> items)
    {
        lock (_lock)
        {
            foreach (var item in items)
            {
                Add(item);  // Calls Add() which also acquires _lock
                             // Works because Monitor is reentrant!
            }
        }
    }

    public int Count
    {
        get { lock (_lock) { return _items.Count; } }
    }
}
```

| | Python `Lock` | Python `RLock` | C# `lock` / `Monitor` |
|---|---|---|---|
| Same thread re-acquire | ❌ Deadlock | ✅ Allowed | ✅ Allowed (built-in) |
| Need separate type? | Yes (use `RLock`) | — | No (always reentrant) |

---

## 7. Monitor.Wait / Pulse (Condition Variables)

`Monitor.Wait` and `Monitor.Pulse` are C#'s equivalent of condition variables. They let threads **wait** for something to become true, and let other threads **notify** them when it does.

### The Problem Without Conditions

```csharp
// ❌ Busy waiting — wastes CPU spinning endlessly
while (!dataReady)
{
    // Checking over and over — terrible!
}
Process(data);
```

### The Solution: Monitor.Wait / Pulse

```csharp
using System;
using System.Threading;

class Program
{
    static readonly object _lock = new object();
    static string? data = null;
    static bool dataReady = false;

    static void Producer()
    {
        Thread.Sleep(2000);  // Simulate slow work

        lock (_lock)
        {
            data = "Hello from producer!";
            dataReady = true;
            Monitor.Pulse(_lock);  // Wake up ONE waiting thread
        }
    }

    static void Consumer()
    {
        lock (_lock)
        {
            while (!dataReady)              // ALWAYS use while, not if
            {
                Monitor.Wait(_lock);        // Release lock + sleep (atomic)
                                            // Re-acquires lock when woken up
            }
            Console.WriteLine($"Got: {data}");
        }
    }

    static void Main()
    {
        var t1 = new Thread(Consumer);
        var t2 = new Thread(Producer);
        t1.Start();
        t2.Start();
        t1.Join();
        t2.Join();
    }
}
```

### How Monitor.Wait() Works (3 Steps, Atomic)

```
1. Release the lock          ← so other threads can acquire it
2. Sleep the thread          ← no CPU wasted
3. When pulsed:
   - Wake up
   - Re-acquire the lock     ← back in critical section
   - Continue after Wait()
```

### Key Methods

| Method | What It Does |
|--------|--------------|
| `Monitor.Wait(obj)` | Release lock + sleep until pulsed |
| `Monitor.Wait(obj, timeout)` | Wait at most N milliseconds |
| `Monitor.Pulse(obj)` | Wake ONE waiting thread |
| `Monitor.PulseAll(obj)` | Wake ALL waiting threads |

**Important:** You must hold the lock (`Monitor.Enter` / inside `lock`) before calling `Wait`, `Pulse`, or `PulseAll`.

### Why while Not if?

```csharp
// ❌ BAD — spurious wakeup can cause bugs
lock (_lock)
{
    if (!dataReady)            // If woken up spuriously, skips wait
        Monitor.Wait(_lock);   // and processes invalid data!
    Process(data);
}

// ✅ GOOD — re-checks after every wakeup
lock (_lock)
{
    while (!dataReady)         // If woken up spuriously, checks again
        Monitor.Wait(_lock);   // and goes back to sleep
    Process(data);
}
```

**Interview Tip:** Interviewers specifically check if you use `while` with `Wait()`. Always explain: "I use `while` instead of `if` because of spurious wakeups."

---

## 8. Semaphores

A `Semaphore` allows up to **N threads** to enter a section simultaneously.

- `lock` = Semaphore with N=1
- `Semaphore(0, 5)` = allows 5 threads at once

```csharp
using System;
using System.Threading;

class Program
{
    // Allow at most 3 concurrent database connections
    static readonly SemaphoreSlim dbSemaphore = new SemaphoreSlim(3, 3);

    static void QueryDatabase(int queryId)
    {
        Console.WriteLine($"Query {queryId}: Waiting for connection...");
        dbSemaphore.Wait();    // Decrements count (blocks if 0)
        try
        {
            Console.WriteLine($"Query {queryId}: Connected! (executing)");
            Thread.Sleep(2000);  // Simulate query
            Console.WriteLine($"Query {queryId}: Done");
        }
        finally
        {
            dbSemaphore.Release();  // Increments count
        }
    }

    static void Main()
    {
        // Launch 10 queries — only 3 run at a time
        var threads = Enumerable.Range(0, 10)
            .Select(i => new Thread(() => QueryDatabase(i)))
            .ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
    }
}
```

### SemaphoreSlim — Lightweight Version

| | `Semaphore` | `SemaphoreSlim` |
|---|---|---|
| Scope | Cross-process (named) | Single process |
| Performance | Slower (kernel object) | Faster (user-mode) |
| Async support | No | Yes (`WaitAsync()`) |
| Use case | Cross-process limiting | In-process concurrency control |

```csharp
// SemaphoreSlim supports async!
var sem = new SemaphoreSlim(3);

async Task QueryAsync(int id)
{
    await sem.WaitAsync();  // Async-friendly — doesn't block thread
    try
    {
        await httpClient.GetAsync($"https://api.example.com/{id}");
    }
    finally
    {
        sem.Release();
    }
}
```

### Semaphore vs Lock

| | `lock` | `Semaphore` |
|---|---|---|
| Max threads inside | 1 | N |
| Use case | Mutual exclusion | Connection pools, rate limiting |
| Who can release? | Only the holder | Any thread |
| Reentrant? | Yes (Monitor) | No |

---

## 9. Events (ManualResetEvent & AutoResetEvent)

An `Event` is a signaling mechanism — a boolean flag that threads can wait on.

```csharp
using System;
using System.Threading;

class Program
{
    static readonly ManualResetEventSlim startEvent = new ManualResetEventSlim(false);

    static void Worker(string name)
    {
        Console.WriteLine($"{name}: Waiting for signal...");
        startEvent.Wait();       // Block until event is set
        Console.WriteLine($"{name}: GO!");
    }

    static void Main()
    {
        // Create workers that all wait for the starting gun
        var threads = Enumerable.Range(0, 5)
            .Select(i => new Thread(() => Worker($"Runner-{i}")))
            .ToList();
        threads.ForEach(t => t.Start());

        Thread.Sleep(2000);
        Console.WriteLine("Ready... Set...");
        startEvent.Set();   // All 5 threads wake up simultaneously

        threads.ForEach(t => t.Join());
    }
}
```

### ManualResetEventSlim — Lightweight Version

| Method | What It Does |
|--------|--------------|
| `event.Set()` | Set the flag — all waiters wake up |
| `event.Reset()` | Reset the flag — future waiters will block |
| `event.Wait()` | Block until flag is set |
| `event.Wait(timeout)` | Wait at most N ms, returns `bool` |
| `event.IsSet` | Check if flag is set (non-blocking) |

### AutoResetEvent vs ManualResetEvent

| | `ManualResetEvent` | `AutoResetEvent` |
|---|---|---|
| After `Set()` | Stays signaled (all waiters pass) | Automatically resets (only ONE waiter passes) |
| Like a... | Gate (stays open) | Turnstile (lets one through, then closes) |
| Use when | Broadcast to all waiters | Wake one waiting thread at a time |

```csharp
// AutoResetEvent — like a turnstile
var autoEvent = new AutoResetEvent(false);

void Waiter(int id)
{
    autoEvent.WaitOne();  // Only ONE thread passes per Set()
    Console.WriteLine($"Thread {id} passed through!");
}

// Start 3 waiters
for (int i = 0; i < 3; i++)
{
    int id = i;
    new Thread(() => Waiter(id)).Start();
}

autoEvent.Set();  // Releases exactly 1 thread
Thread.Sleep(100);
autoEvent.Set();  // Releases exactly 1 more
Thread.Sleep(100);
autoEvent.Set();  // Releases the last one
```

---

## 10. Barriers

A `Barrier` makes N threads all wait for each other at a checkpoint before proceeding.

```csharp
using System;
using System.Threading;

class Program
{
    static readonly Barrier barrier = new Barrier(3, b =>
    {
        // This callback runs once per phase (after all participants arrive)
        Console.WriteLine($"--- Phase {b.CurrentPhaseNumber} complete ---");
    });

    static void PhaseWorker(string name)
    {
        // Phase 1
        Console.WriteLine($"{name}: Phase 1 done");
        barrier.SignalAndWait();  // All 3 must reach here before any continues

        // Phase 2
        Console.WriteLine($"{name}: Phase 2 done");
        barrier.SignalAndWait();  // Barrier is reusable!

        // Phase 3
        Console.WriteLine($"{name}: Phase 3 done");
    }

    static void Main()
    {
        var threads = Enumerable.Range(0, 3)
            .Select(i => new Thread(() => PhaseWorker($"Worker-{i}")))
            .ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
    }
}
```

Output (phases never overlap):
```
Worker-0: Phase 1 done
Worker-2: Phase 1 done
Worker-1: Phase 1 done
--- Phase 0 complete ---
Worker-1: Phase 2 done
Worker-0: Phase 2 done
Worker-2: Phase 2 done
--- Phase 1 complete ---
...
```

---

## 11. Interlocked & Volatile

### Interlocked — Lock-Free Atomic Operations

`Interlocked` provides atomic operations without needing a lock. Much faster for simple operations.

```csharp
using System.Threading;

static int counter = 0;

// Atomic increment/decrement
Interlocked.Increment(ref counter);       // counter++ (atomic)
Interlocked.Decrement(ref counter);       // counter-- (atomic)

// Atomic add
Interlocked.Add(ref counter, 5);          // counter += 5 (atomic)

// Atomic exchange (set and return old value)
int old = Interlocked.Exchange(ref counter, 100);   // counter = 100, returns old

// Atomic compare-and-swap (CAS) — the building block of lock-free code
// "If counter == expected, set it to newValue. Return old value."
int expected = 42;
int newValue = 43;
int original = Interlocked.CompareExchange(ref counter, newValue, expected);
if (original == expected)
{
    // Swap succeeded — counter is now 43
}
else
{
    // Someone else changed it — retry
}
```

**CAS Pattern (Lock-Free Update):**

```csharp
// Lock-free increment pattern using CAS
static void SafeIncrement()
{
    int original, newValue;
    do
    {
        original = counter;
        newValue = original + 1;
    }
    while (Interlocked.CompareExchange(ref counter, newValue, original) != original);
}
```

### volatile — Memory Visibility

`volatile` ensures a field is always read from main memory (not CPU cache). It prevents the compiler/CPU from reordering reads/writes.

```csharp
class Worker
{
    private volatile bool _running = true;  // volatile ensures visibility

    public void DoWork()
    {
        while (_running)  // Without volatile, compiler might cache this
        {
            // ... do work ...
        }
    }

    public void Stop()
    {
        _running = false;  // Other thread sees this immediately
    }
}
```

| | `volatile` | `Interlocked` | `lock` |
|---|---|---|---|
| Use for | Visibility of a single field | Atomic read-modify-write | Compound operations |
| Performance | Fastest | Fast | Slowest |
| Example | Boolean flags | Counters | Transfer between accounts |

**Rule:** Use `volatile` for simple flags. Use `Interlocked` for counters. Use `lock` for compound operations.

---

## 12. Thread-Safe Data Structures

### BlockingCollection<T> — Thread-Safe Producer-Consumer

```csharp
using System.Collections.Concurrent;
using System.Threading;

var queue = new BlockingCollection<int>(boundedCapacity: 10);  // Bounded

void Producer()
{
    for (int i = 0; i < 20; i++)
    {
        queue.Add(i);             // Blocks if full
        Console.WriteLine($"Produced: {i}");
    }
    queue.CompleteAdding();        // Signal no more items
}

void Consumer()
{
    foreach (var item in queue.GetConsumingEnumerable())  // Blocks if empty, exits on complete
    {
        Console.WriteLine($"Consumed: {item}");
    }
}

var t1 = new Thread(Producer);
var t2 = new Thread(Consumer);
t1.Start();
t2.Start();
t1.Join();
t2.Join();
```

### Concurrent Collections

| Collection | Thread-Safe Equivalent Of | Use Case |
|------------|--------------------------|----------|
| `ConcurrentDictionary<K,V>` | `Dictionary<K,V>` | Shared lookup table |
| `ConcurrentQueue<T>` | `Queue<T>` | FIFO producer-consumer |
| `ConcurrentStack<T>` | `Stack<T>` | LIFO processing |
| `ConcurrentBag<T>` | `List<T>` (unordered) | Thread-local + shared pool |
| `BlockingCollection<T>` | Bounded queue | Blocking producer-consumer |

```csharp
// ConcurrentDictionary — atomic operations
var dict = new ConcurrentDictionary<string, int>();

dict.TryAdd("key", 1);                          // Atomic add
dict.AddOrUpdate("key", 1, (k, old) => old + 1); // Atomic upsert
int val = dict.GetOrAdd("key", 42);              // Atomic get-or-create

// ConcurrentQueue — lock-free FIFO
var cq = new ConcurrentQueue<string>();
cq.Enqueue("item");
if (cq.TryDequeue(out string? result))
{
    Console.WriteLine(result);
}
```

### Channel<T> — Modern Async Producer-Consumer

`Channel<T>` (from `System.Threading.Channels`) is the modern, async-friendly alternative to `BlockingCollection`.

```csharp
using System.Threading.Channels;

var channel = Channel.CreateBounded<int>(new BoundedChannelOptions(10)
{
    FullMode = BoundedChannelFullMode.Wait  // Block when full
});

async Task ProducerAsync()
{
    for (int i = 0; i < 20; i++)
    {
        await channel.Writer.WriteAsync(i);   // Async — doesn't block thread
        Console.WriteLine($"Produced: {i}");
    }
    channel.Writer.Complete();
}

async Task ConsumerAsync()
{
    await foreach (var item in channel.Reader.ReadAllAsync())  // Async enumeration
    {
        Console.WriteLine($"Consumed: {item}");
    }
}

await Task.WhenAll(ProducerAsync(), ConsumerAsync());
```

| | `BlockingCollection<T>` | `Channel<T>` |
|---|---|---|
| Blocking model | Synchronous (blocks thread) | Async (`await`) |
| Thread usage | Ties up threads | Frees threads while waiting |
| Use case | Thread-based code | async/await code |
| Performance | Good | Better (less allocation) |

---

## 13. Deadlock, Livelock & Starvation

### Deadlock

Two threads each hold a lock the other needs. Neither can proceed. **Program hangs forever.**

```csharp
static readonly object lockA = new object();
static readonly object lockB = new object();

void Thread1()
{
    lock (lockA)                // Holds A
    {
        Thread.Sleep(100);
        lock (lockB)            // Waits for B... forever
        {
            Console.WriteLine("Thread 1");
        }
    }
}

void Thread2()
{
    lock (lockB)                // Holds B
    {
        Thread.Sleep(100);
        lock (lockA)            // Waits for A... forever
        {
            Console.WriteLine("Thread 2");
        }
    }
}

// DEADLOCK — both threads wait forever
```

### 4 Conditions for Deadlock (ALL must be true)

| Condition | Meaning | How to Break It |
|-----------|---------|-----------------|
| **Mutual exclusion** | Only one thread can hold the lock | Use lock-free structures (`Interlocked`, `Concurrent*`) |
| **Hold and wait** | Thread holds one lock, waits for another | Acquire all locks at once |
| **No preemption** | Can't force-take a lock | Use `Monitor.TryEnter` with timeouts |
| **Circular wait** | A waits for B, B waits for A | Always lock in same order |

### Fix: Consistent Lock Ordering

```csharp
public bool Transfer(BankAccount other, decimal amount)
{
    // Always lock the account with the smaller hash first
    object first = GetHashCode() < other.GetHashCode() ? _lock : other._lock;
    object second = first == _lock ? other._lock : _lock;

    lock (first)
    {
        lock (second)
        {
            if (_balance >= amount)
            {
                _balance -= amount;
                other._balance += amount;
                return true;
            }
            return false;
        }
    }
}
```

### Fix: Timeout

```csharp
void SafeTransfer()
{
    bool gotA = false, gotB = false;
    try
    {
        gotA = Monitor.TryEnter(lockA, TimeSpan.FromSeconds(1));
        if (gotA)
        {
            gotB = Monitor.TryEnter(lockB, TimeSpan.FromSeconds(1));
            if (gotB)
            {
                DoTransfer();
            }
            else
            {
                Console.WriteLine("Could not get lockB — retry later");
            }
        }
        else
        {
            Console.WriteLine("Could not get lockA — retry later");
        }
    }
    finally
    {
        if (gotB) Monitor.Exit(lockB);
        if (gotA) Monitor.Exit(lockA);
    }
}
```

### Livelock

Threads are running but making no progress — they keep reacting to each other and never advance.

```csharp
// ❌ Livelock — both threads keep "being polite"
void PoliteThread(object myLock, object otherLock)
{
    while (true)
    {
        lock (myLock)
        {
            if (!Monitor.TryEnter(otherLock))
            {
                // "After you!" — release and retry, but so does the other thread!
                Thread.Sleep(1);
                continue;
            }
            try { DoWork(); }
            finally { Monitor.Exit(otherLock); }
            break;
        }
    }
}
```

**Fix:** Add random backoff to break symmetry.

```csharp
var rng = new Random();

void FixedThread(object myLock, object otherLock)
{
    while (true)
    {
        lock (myLock)
        {
            if (!Monitor.TryEnter(otherLock))
            {
                Thread.Sleep(rng.Next(1, 10));  // Random backoff!
                continue;
            }
            try { DoWork(); }
            finally { Monitor.Exit(otherLock); }
            break;
        }
    }
}
```

### Starvation

One thread never gets the lock because other threads keep grabbing it first.

**Fix:** Use fair structures (`SemaphoreSlim`, `BlockingCollection` which are FIFO) or priority scheduling.

### Summary

| Problem | Threads Running? | Progress? | Fix |
|---------|-----------------|-----------|-----|
| **Deadlock** | No (blocked) | None | Lock ordering, timeout |
| **Livelock** | Yes (spinning) | None | Random backoff |
| **Starvation** | Some are | Some, not all | Fair scheduling, queues |

---

## 14. Thread Pool & Task Parallel Library (TPL)

Creating threads is expensive (~1MB stack per thread). The `ThreadPool` keeps a set of threads and reuses them. `Task` is the modern abstraction over the thread pool.

### Task — The Modern Way

```csharp
using System;
using System.Threading.Tasks;

string FetchUrl(string url)
{
    Thread.Sleep(1000);  // Simulate network request
    return $"Data from {url}";
}

var urls = Enumerable.Range(0, 10).Select(i => $"https://api.example.com/{i}").ToArray();

// Submit tasks — they run on the ThreadPool
var tasks = urls.Select(url => Task.Run(() => FetchUrl(url))).ToArray();

// Process results as they complete (not in submission order)
while (tasks.Length > 0)
{
    int completedIndex = Task.WaitAny(tasks);
    Console.WriteLine(tasks[completedIndex].Result);
    tasks = tasks.Where((_, i) => i != completedIndex).ToArray();
}

// Or wait for all
var allTasks = urls.Select(url => Task.Run(() => FetchUrl(url))).ToArray();
Task.WaitAll(allTasks);
foreach (var t in allTasks)
{
    Console.WriteLine(t.Result);
}
```

**Continuations:**

```csharp
Task.Run(() => FetchUrl("https://api.example.com/1"))
    .ContinueWith(t =>
    {
        if (t.IsCompletedSuccessfully)
            Console.WriteLine($"Got: {t.Result}");
        else
            Console.WriteLine($"Error: {t.Exception?.Message}");
    });
```

### Parallel.For / Parallel.ForEach

For CPU-bound data parallelism — automatically partitions work across cores.

```csharp
using System.Threading.Tasks;

// Parallel.For — split a loop across cores
Parallel.For(0, 1000, i =>
{
    // Each iteration may run on a different thread
    ComputeHeavy(i);
});

// Parallel.ForEach — parallel iteration over a collection
var items = Enumerable.Range(0, 1000).ToList();
Parallel.ForEach(items, new ParallelOptions { MaxDegreeOfParallelism = 4 }, item =>
{
    ProcessItem(item);
});
```

### PLINQ — Parallel LINQ

```csharp
// Sequential LINQ
var results = data.Where(x => x > 0).Select(x => Compute(x)).ToList();

// Parallel LINQ — same query, parallel execution
var parallelResults = data.AsParallel()
    .WithDegreeOfParallelism(4)
    .Where(x => x > 0)
    .Select(x => Compute(x))
    .ToList();
```

### When to Use What

| Work Type | Use | Why |
|-----------|-----|-----|
| I/O-bound (network, disk) | `async/await` with `Task` | Doesn't block threads |
| CPU-bound (computation) | `Parallel.For` / `Task.Run` | True parallelism on all cores |
| Data parallelism | `PLINQ` | Declarative parallel queries |
| Background work | `Task.Run` | Offload to thread pool |
| Fire-and-forget | `Task.Run` (but handle exceptions!) | Quick background tasks |

---

## 15. async/await

`async`/`await` is C#'s way to handle I/O-bound work efficiently. Unlike Python's `asyncio`, C#'s async model is **deeply integrated** into the language and runtime — it's the primary way to write concurrent code.

```csharp
using System;
using System.Net.Http;
using System.Threading.Tasks;

async Task<string> FetchDataAsync(string name, int delayMs)
{
    Console.WriteLine($"{name}: Starting request");
    await Task.Delay(delayMs);    // "I'm waiting — thread is freed for other work"
    Console.WriteLine($"{name}: Got response");
    return $"Data from {name}";
}

async Task Main()
{
    // Launch 3 requests concurrently
    var results = await Task.WhenAll(
        FetchDataAsync("API-1", 2000),
        FetchDataAsync("API-2", 1000),
        FetchDataAsync("API-3", 3000)
    );

    foreach (var r in results)
        Console.WriteLine(r);
}
// Total time: ~3 seconds (not 6)
```

### Task vs ValueTask

| | `Task<T>` | `ValueTask<T>` |
|---|---|---|
| Allocation | Heap allocation every time | Stack-allocated when result is synchronous |
| Use when | Default choice | Hot paths with frequent sync completion |
| Can await multiple times? | Yes | NO — await only once |

```csharp
// ValueTask — avoids allocation when cache hits
public ValueTask<int> GetValueAsync(string key)
{
    if (_cache.TryGetValue(key, out int cached))
        return new ValueTask<int>(cached);   // No heap allocation!

    return new ValueTask<int>(LoadFromDbAsync(key));  // Falls back to Task
}
```

### ConfigureAwait

```csharp
// In library code — don't capture SynchronizationContext
var data = await httpClient.GetStringAsync(url).ConfigureAwait(false);

// In UI code (WPF, WinForms) — DO capture context to update UI
var data = await httpClient.GetStringAsync(url);  // Default: captures context
label.Text = data;  // Runs on UI thread
```

| | `ConfigureAwait(true)` (default) | `ConfigureAwait(false)` |
|---|---|---|
| Resumes on | Original context (UI thread) | Any thread pool thread |
| Use in | UI code, ASP.NET (pre-Core) | Library code, ASP.NET Core |
| Performance | Slower (context switch) | Faster |

### CancellationToken — Cooperative Cancellation

```csharp
using System.Threading;

async Task LongOperationAsync(CancellationToken ct)
{
    for (int i = 0; i < 100; i++)
    {
        ct.ThrowIfCancellationRequested();  // Check for cancellation
        await Task.Delay(100, ct);          // Pass token to async methods
        Console.WriteLine($"Step {i}");
    }
}

// Usage
var cts = new CancellationTokenSource();

// Cancel after 2 seconds
cts.CancelAfter(TimeSpan.FromSeconds(2));

try
{
    await LongOperationAsync(cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Operation was cancelled!");
}
finally
{
    cts.Dispose();
}
```

### async Synchronization Primitives

```csharp
// SemaphoreSlim supports async
var semaphore = new SemaphoreSlim(5);

async Task LimitedAsync()
{
    await semaphore.WaitAsync();    // Async-friendly
    try { await DoWorkAsync(); }
    finally { semaphore.Release(); }
}

// No async lock in BCL — use SemaphoreSlim(1, 1) as async mutex
var asyncLock = new SemaphoreSlim(1, 1);

async Task SafeWriteAsync()
{
    await asyncLock.WaitAsync();
    try
    {
        // critical section (async-safe)
        await File.WriteAllTextAsync("file.txt", "data");
    }
    finally
    {
        asyncLock.Release();
    }
}
```

**Warning: Never use `lock` with `await`!**

```csharp
// ❌ COMPILE ERROR — can't await inside lock
lock (_lock)
{
    await DoSomethingAsync();  // CS1996: Cannot await in the body of a lock statement
}

// ✅ Use SemaphoreSlim(1, 1) instead
await _asyncLock.WaitAsync();
try
{
    await DoSomethingAsync();
}
finally
{
    _asyncLock.Release();
}
```

### async vs Threading — When to Use

| | `Thread` / `Task.Run` | `async/await` |
|---|---|---|
| Model | OS threads on thread pool | Continuation-based, frees threads |
| Overhead | ~1MB stack per thread | ~bytes per state machine |
| Blocking calls | OK | NO — blocks the thread pool |
| Best for | CPU-bound, legacy sync code | I/O-bound, scalable servers |
| Max concurrency | ~1000s of threads | ~100,000s of tasks |

---

## 16. Common Patterns Cheat Sheet

```
Pattern                 | C# Tool                            | Use When
------------------------|------------------------------------|----------------------------------
Mutual exclusion        | lock / Monitor                     | Protect shared data
Atomic operations       | Interlocked                        | Simple counters, flags
Wait for condition      | Monitor.Wait / Pulse               | Producer-consumer (sync)
Limit concurrency       | SemaphoreSlim(N)                   | Connection pools, rate limiting
Signal all threads      | ManualResetEventSlim               | Start gate, shutdown signal
Signal one thread       | AutoResetEvent                     | Wake one waiter at a time
Sync at checkpoints     | Barrier                            | Phased execution
Thread-safe queue       | BlockingCollection<T>              | Sync producer-consumer
Async queue             | Channel<T>                         | Async producer-consumer
Thread-safe dictionary  | ConcurrentDictionary<K,V>          | Shared lookup table
Thread pool             | Task.Run / ThreadPool              | Reuse threads for many tasks
Async I/O               | async/await                        | Network, disk, database
CPU parallelism         | Parallel.For / PLINQ               | Data-parallel computation
Cancellation            | CancellationToken                  | Cooperative cancellation
Async mutex             | SemaphoreSlim(1, 1)                | Async-safe critical section
Timer / periodic task   | System.Threading.Timer             | Delayed / repeated execution
Cross-process lock      | Mutex (named)                      | Single-instance app
```

---

## 17. Machine Coding Problems

These are the actual problems asked in FAANG LLD/machine coding rounds. Each one teaches a concurrency pattern.

---

### 17.1 Producer-Consumer (Bounded Buffer)

**Asked at:** Uber, Amazon, Google, Goldman Sachs

**Problem:** Multiple producers add items to a buffer. Multiple consumers remove items. Buffer has a max capacity. Producers block when full. Consumers block when empty.

**Concepts:** Monitor.Wait/Pulse, mutual exclusion, blocking

```csharp
using System;
using System.Collections.Generic;
using System.Threading;

public class BoundedBuffer<T>
{
    private readonly Queue<T> _buffer = new();
    private readonly int _capacity;
    private readonly object _lock = new object();

    public BoundedBuffer(int capacity) => _capacity = capacity;

    public void Produce(T item)
    {
        lock (_lock)
        {
            while (_buffer.Count >= _capacity)
                Monitor.Wait(_lock);    // Wait until space available

            _buffer.Enqueue(item);
            Console.WriteLine($"  Produced: {item} | Buffer size: {_buffer.Count}");
            Monitor.PulseAll(_lock);    // Wake consumers (and other producers)
        }
    }

    public T Consume()
    {
        lock (_lock)
        {
            while (_buffer.Count == 0)
                Monitor.Wait(_lock);    // Wait until item available

            T item = _buffer.Dequeue();
            Console.WriteLine($"  Consumed: {item} | Buffer size: {_buffer.Count}");
            Monitor.PulseAll(_lock);    // Wake producers (and other consumers)
            return item;
        }
    }
}

// Test
class Program
{
    static void Main()
    {
        var buffer = new BoundedBuffer<string>(3);

        void Producer(int id)
        {
            for (int i = 0; i < 5; i++)
            {
                buffer.Produce($"P{id}-{i}");
                Thread.Sleep(Random.Shared.Next(100, 300));
            }
        }

        void Consumer(int id)
        {
            for (int i = 0; i < 5; i++)
            {
                buffer.Consume();
                Thread.Sleep(Random.Shared.Next(200, 500));
            }
        }

        var threads = new List<Thread>();
        for (int i = 0; i < 2; i++)
        {
            int id = i;
            threads.Add(new Thread(() => Producer(id)));
            threads.Add(new Thread(() => Consumer(id)));
        }
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
    }
}
```

**Key Points to Mention in Interview:**
- `Monitor.Wait` / `Monitor.PulseAll` on the same lock object
- `while` loop for wait — handles spurious wakeups
- `PulseAll` wakes all waiters since we share one condition (producers + consumers wait on same lock)
- Alternatively, use `BlockingCollection<T>` for production code

---

### 17.2 Reader-Writer Lock

**Asked at:** Google, Microsoft, Uber

**Problem:** Multiple readers can read simultaneously, but a writer needs exclusive access.

**Concepts:** Shared vs exclusive locking, starvation prevention

**Using ReaderWriterLockSlim (Built-in):**

```csharp
using System;
using System.Threading;

public class ThreadSafeData
{
    private readonly ReaderWriterLockSlim _rwLock = new();
    private Dictionary<string, int> _data = new();

    public int Read(string key)
    {
        _rwLock.EnterReadLock();        // Multiple readers allowed
        try
        {
            return _data.GetValueOrDefault(key, -1);
        }
        finally
        {
            _rwLock.ExitReadLock();
        }
    }

    public void Write(string key, int value)
    {
        _rwLock.EnterWriteLock();       // Exclusive access
        try
        {
            _data[key] = value;
        }
        finally
        {
            _rwLock.ExitWriteLock();
        }
    }
}
```

**From Scratch (Interview Version):**

```csharp
using System;
using System.Threading;

public class ReadWriteLock
{
    private readonly object _lock = new object();
    private int _readers = 0;
    private bool _writing = false;
    private int _waitingWriters = 0;

    public void AcquireRead()
    {
        lock (_lock)
        {
            // Wait if someone is writing OR writers are waiting (prevent writer starvation)
            while (_writing || _waitingWriters > 0)
                Monitor.Wait(_lock);
            _readers++;
        }
    }

    public void ReleaseRead()
    {
        lock (_lock)
        {
            _readers--;
            if (_readers == 0)
                Monitor.PulseAll(_lock);    // Wake waiting writers
        }
    }

    public void AcquireWrite()
    {
        lock (_lock)
        {
            _waitingWriters++;
            while (_writing || _readers > 0)
                Monitor.Wait(_lock);
            _waitingWriters--;
            _writing = true;
        }
    }

    public void ReleaseWrite()
    {
        lock (_lock)
        {
            _writing = false;
            Monitor.PulseAll(_lock);        // Wake all waiting readers + writers
        }
    }
}

// Usage
var rwLock = new ReadWriteLock();
var sharedData = new Dictionary<string, int> { { "value", 0 } };

void Reader(int id)
{
    for (int i = 0; i < 3; i++)
    {
        rwLock.AcquireRead();
        try
        {
            Console.WriteLine($"Reader-{id} reads: {sharedData["value"]}");
            Thread.Sleep(100);
        }
        finally
        {
            rwLock.ReleaseRead();
        }
    }
}

void Writer(int id)
{
    for (int i = 0; i < 3; i++)
    {
        rwLock.AcquireWrite();
        try
        {
            sharedData["value"]++;
            Console.WriteLine($"Writer-{id} wrote: {sharedData["value"]}");
            Thread.Sleep(200);
        }
        finally
        {
            rwLock.ReleaseWrite();
        }
    }
}
```

**Key Design Decision:** This implementation is **writer-preferring** — if a writer is waiting, new readers also wait. This prevents writer starvation.

---

### 17.3 Thread-Safe LRU Cache

**Asked at:** Uber, Amazon, Meta, Google

**Problem:** Implement an LRU cache that supports concurrent `Get` and `Put` operations.

**Concepts:** Lock granularity, linked list + dictionary

```csharp
using System;
using System.Collections.Generic;
using System.Threading;

public class ThreadSafeLRUCache<TKey, TValue> where TKey : notnull
{
    private readonly int _capacity;
    private readonly Dictionary<TKey, LinkedListNode<(TKey Key, TValue Value)>> _map;
    private readonly LinkedList<(TKey Key, TValue Value)> _list;
    private readonly object _lock = new object();

    public ThreadSafeLRUCache(int capacity)
    {
        _capacity = capacity;
        _map = new(capacity);
        _list = new();
    }

    public TValue? Get(TKey key)
    {
        lock (_lock)
        {
            if (!_map.TryGetValue(key, out var node))
                return default;

            _list.Remove(node);
            _list.AddLast(node);        // Mark as recently used
            return node.Value.Value;
        }
    }

    public void Put(TKey key, TValue value)
    {
        lock (_lock)
        {
            if (_map.TryGetValue(key, out var existing))
            {
                _list.Remove(existing);
                existing.Value = (key, value);
                _list.AddLast(existing);
            }
            else
            {
                if (_map.Count >= _capacity)
                {
                    // Evict LRU (front)
                    var lru = _list.First!;
                    _map.Remove(lru.Value.Key);
                    _list.RemoveFirst();
                }

                var node = new LinkedListNode<(TKey, TValue)>((key, value));
                _list.AddLast(node);
                _map[key] = node;
            }
        }
    }
}
```

**Follow-up: Striped Locking for Higher Throughput**

```csharp
public class StripedLRUCache<TValue>
{
    private readonly int _numStripes;
    private readonly ThreadSafeLRUCache<string, TValue>[] _shards;

    public StripedLRUCache(int capacity, int numStripes = 16)
    {
        _numStripes = numStripes;
        int shardCap = Math.Max(1, capacity / numStripes);
        _shards = new ThreadSafeLRUCache<string, TValue>[numStripes];
        for (int i = 0; i < numStripes; i++)
            _shards[i] = new ThreadSafeLRUCache<string, TValue>(shardCap);
    }

    private int GetShard(string key) => Math.Abs(key.GetHashCode()) % _numStripes;

    public TValue? Get(string key) => _shards[GetShard(key)].Get(key);
    public void Put(string key, TValue value) => _shards[GetShard(key)].Put(key, value);
}
```

---

### 17.4 Rate Limiter (Token Bucket)

**Asked at:** Uber, Google, Stripe, Amazon

**Problem:** Allow at most N requests per time window. Excess requests are rejected.

**Concepts:** Token refill, thread-safe state

```csharp
using System;
using System.Diagnostics;
using System.Threading;

public class TokenBucketRateLimiter
{
    private readonly double _rate;         // tokens per second
    private readonly int _capacity;
    private double _tokens;
    private long _lastRefillTicks;
    private readonly object _lock = new object();

    public TokenBucketRateLimiter(double rate, int capacity)
    {
        _rate = rate;
        _capacity = capacity;
        _tokens = capacity;               // Start full
        _lastRefillTicks = Stopwatch.GetTimestamp();
    }

    private void Refill()
    {
        long now = Stopwatch.GetTimestamp();
        double elapsed = (double)(now - _lastRefillTicks) / Stopwatch.Frequency;
        double newTokens = elapsed * _rate;
        _tokens = Math.Min(_capacity, _tokens + newTokens);
        _lastRefillTicks = now;
    }

    public bool Allow()
    {
        lock (_lock)
        {
            Refill();
            if (_tokens >= 1)
            {
                _tokens -= 1;
                return true;
            }
            return false;
        }
    }
}

// Test: 5 requests/sec, burst capacity of 5
var limiter = new TokenBucketRateLimiter(rate: 5, capacity: 5);

void MakeRequests(int clientId)
{
    for (int i = 0; i < 10; i++)
    {
        string status = limiter.Allow() ? "ALLOWED" : "REJECTED";
        Console.WriteLine($"Client-{clientId} Request-{i}: {status}");
        Thread.Sleep(50);
    }
}

var threads = Enumerable.Range(0, 3)
    .Select(i => new Thread(() => MakeRequests(i)))
    .ToList();
threads.ForEach(t => t.Start());
threads.ForEach(t => t.Join());
```

---

### 17.5 Rate Limiter (Sliding Window)

**Asked at:** Uber, Google, Meta

**Concepts:** Queue as timestamp window, cleanup of expired entries

```csharp
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

public class SlidingWindowRateLimiter
{
    private readonly int _maxRequests;
    private readonly double _windowSeconds;
    private readonly Queue<long> _timestamps = new();
    private readonly object _lock = new object();

    public SlidingWindowRateLimiter(int maxRequests, double windowSeconds)
    {
        _maxRequests = maxRequests;
        _windowSeconds = windowSeconds;
    }

    public bool Allow()
    {
        lock (_lock)
        {
            long now = Stopwatch.GetTimestamp();
            long windowTicks = (long)(_windowSeconds * Stopwatch.Frequency);

            // Remove expired timestamps
            while (_timestamps.Count > 0 && now - _timestamps.Peek() >= windowTicks)
                _timestamps.Dequeue();

            if (_timestamps.Count < _maxRequests)
            {
                _timestamps.Enqueue(now);
                return true;
            }
            return false;
        }
    }
}

// Per-user rate limiter
public class PerUserRateLimiter
{
    private readonly int _maxRequests;
    private readonly double _windowSeconds;
    private readonly ConcurrentDictionary<string, SlidingWindowRateLimiter> _userLimiters = new();

    public PerUserRateLimiter(int maxRequests, double windowSeconds)
    {
        _maxRequests = maxRequests;
        _windowSeconds = windowSeconds;
    }

    public bool Allow(string userId)
    {
        var limiter = _userLimiters.GetOrAdd(userId,
            _ => new SlidingWindowRateLimiter(_maxRequests, _windowSeconds));
        return limiter.Allow();
    }
}
```

---

### 17.6 Print In Order / Sequence Controller

**Asked at:** LeetCode 1114, Amazon, Google

**Problem:** Three threads call `First()`, `Second()`, `Third()`. Ensure they always execute in order.

**Concepts:** Event-based signaling

```csharp
using System;
using System.Threading;

public class PrintInOrder
{
    private readonly ManualResetEventSlim _firstDone = new(false);
    private readonly ManualResetEventSlim _secondDone = new(false);

    public void First()
    {
        Console.Write("first ");
        _firstDone.Set();
    }

    public void Second()
    {
        _firstDone.Wait();         // Wait until First() is done
        Console.Write("second ");
        _secondDone.Set();
    }

    public void Third()
    {
        _secondDone.Wait();        // Wait until Second() is done
        Console.Write("third");
    }
}

// Threads start in random order, output is always "first second third"
var order = new PrintInOrder();
var threads = new[]
{
    new Thread(order.Third),
    new Thread(order.First),
    new Thread(order.Second),
};
foreach (var t in threads) t.Start();
foreach (var t in threads) t.Join();
// Output: first second third
```

---

### 17.7 Print FooBar Alternately

**Asked at:** LeetCode 1115, Google, Meta

**Problem:** Two threads must print "foobar" N times, alternating.

**Concepts:** Mutual signaling between threads

```csharp
using System;
using System.Threading;

public class FooBar
{
    private readonly int _n;
    private readonly AutoResetEvent _fooEvent = new(true);   // foo goes first
    private readonly AutoResetEvent _barEvent = new(false);

    public FooBar(int n) => _n = n;

    public void Foo()
    {
        for (int i = 0; i < _n; i++)
        {
            _fooEvent.WaitOne();
            Console.Write("foo");
            _barEvent.Set();
        }
    }

    public void Bar()
    {
        for (int i = 0; i < _n; i++)
        {
            _barEvent.WaitOne();
            Console.Write("bar ");
            _fooEvent.Set();
        }
    }
}

var fb = new FooBar(3);
var t1 = new Thread(fb.Foo);
var t2 = new Thread(fb.Bar);
t1.Start(); t2.Start();
t1.Join(); t2.Join();
// Output: foobar foobar foobar
```

---

### 17.8 Dining Philosophers

**Asked at:** LeetCode 1226, Google, Microsoft

**Problem:** 5 philosophers at a round table. Each needs 2 forks to eat. Adjacent philosophers share a fork. Prevent deadlock.

**Concepts:** Deadlock avoidance via lock ordering

```csharp
using System;
using System.Threading;

public class DiningPhilosophers
{
    private readonly int _n;
    private readonly object[] _forks;

    public DiningPhilosophers(int n = 5)
    {
        _n = n;
        _forks = new object[n];
        for (int i = 0; i < n; i++)
            _forks[i] = new object();
    }

    public void Philosopher(int id)
    {
        int left = id;
        int right = (id + 1) % _n;

        // Deadlock fix: always pick the lower-numbered fork first
        int first = Math.Min(left, right);
        int second = Math.Max(left, right);

        for (int meal = 0; meal < 3; meal++)
        {
            // Think
            Console.WriteLine($"Philosopher {id}: Thinking...");
            Thread.Sleep(Random.Shared.Next(100, 300));

            // Pick up forks (in consistent order — no deadlock!)
            lock (_forks[first])
            {
                lock (_forks[second])
                {
                    // Eat
                    Console.WriteLine($"Philosopher {id}: Eating meal {meal + 1}");
                    Thread.Sleep(Random.Shared.Next(100, 200));
                }
            }
        }

        Console.WriteLine($"Philosopher {id}: Done!");
    }
}

var dp = new DiningPhilosophers(5);
var threads = Enumerable.Range(0, 5)
    .Select(i => new Thread(() => dp.Philosopher(i)))
    .ToList();
threads.ForEach(t => t.Start());
threads.ForEach(t => t.Join());
```

**Alternative: Limit Diners with Semaphore**

```csharp
public class DiningPhilosophersV2
{
    private readonly int _n;
    private readonly object[] _forks;
    private readonly SemaphoreSlim _seats;

    public DiningPhilosophersV2(int n = 5)
    {
        _n = n;
        _forks = new object[n];
        for (int i = 0; i < n; i++) _forks[i] = new object();
        _seats = new SemaphoreSlim(n - 1);  // Only N-1 can try at once
    }

    public void Philosopher(int id)
    {
        int left = id;
        int right = (id + 1) % _n;

        for (int meal = 0; meal < 3; meal++)
        {
            _seats.Wait();          // Limit concurrent diners → no deadlock
            lock (_forks[left])
            {
                lock (_forks[right])
                {
                    Console.WriteLine($"Philosopher {id}: Eating meal {meal + 1}");
                    Thread.Sleep(100);
                }
            }
            _seats.Release();
        }
    }
}
```

---

### 17.9 Blocking Queue

**Asked at:** Amazon, Google, Uber, Goldman Sachs

**Problem:** Implement a queue from scratch where `Put()` blocks if full and `Get()` blocks if empty.

**Concepts:** Monitor.Wait/Pulse, graceful shutdown

```csharp
using System;
using System.Collections.Generic;
using System.Threading;

public class BlockingQueue<T>
{
    private readonly int _capacity;
    private readonly Queue<T> _queue = new();
    private readonly object _lock = new object();
    private bool _shutdown = false;

    public BlockingQueue(int capacity) => _capacity = capacity;

    public void Put(T item)
    {
        lock (_lock)
        {
            while (_queue.Count >= _capacity)
            {
                if (_shutdown) throw new InvalidOperationException("Queue is shut down");
                Monitor.Wait(_lock);
            }
            _queue.Enqueue(item);
            Monitor.PulseAll(_lock);
        }
    }

    public T Get(int timeoutMs = -1)
    {
        lock (_lock)
        {
            while (_queue.Count == 0)
            {
                if (_shutdown) throw new InvalidOperationException("Queue is shut down");
                if (!Monitor.Wait(_lock, timeoutMs == -1 ? Timeout.Infinite : timeoutMs))
                    throw new TimeoutException("Timed out waiting for item");
            }
            T item = _queue.Dequeue();
            Monitor.PulseAll(_lock);
            return item;
        }
    }

    public bool TryGet(out T? item, int timeoutMs = 0)
    {
        lock (_lock)
        {
            if (_queue.Count == 0)
            {
                if (timeoutMs <= 0 || !Monitor.Wait(_lock, timeoutMs))
                {
                    item = default;
                    return false;
                }
            }
            if (_queue.Count > 0)
            {
                item = _queue.Dequeue();
                Monitor.PulseAll(_lock);
                return true;
            }
            item = default;
            return false;
        }
    }

    public int Count
    {
        get { lock (_lock) { return _queue.Count; } }
    }

    public void Shutdown()
    {
        lock (_lock)
        {
            _shutdown = true;
            Monitor.PulseAll(_lock);
        }
    }
}
```

---

### 17.10 Thread Pool from Scratch

**Asked at:** Uber, Google, Amazon

**Problem:** Implement a thread pool that accepts tasks, runs them on worker threads, and supports graceful shutdown.

**Concepts:** Worker threads, task queue, shutdown coordination

```csharp
using System;
using System.Collections.Generic;
using System.Threading;

public class CustomThreadPool : IDisposable
{
    private readonly Queue<Action> _tasks = new();
    private readonly object _lock = new object();
    private readonly List<Thread> _workers = new();
    private bool _shutdown = false;

    public CustomThreadPool(int numWorkers)
    {
        for (int i = 0; i < numWorkers; i++)
        {
            var t = new Thread(WorkerLoop)
            {
                Name = $"Worker-{i}",
                IsBackground = true
            };
            t.Start();
            _workers.Add(t);
        }
    }

    private void WorkerLoop()
    {
        while (true)
        {
            Action? task;
            lock (_lock)
            {
                while (_tasks.Count == 0 && !_shutdown)
                    Monitor.Wait(_lock);

                if (_shutdown && _tasks.Count == 0)
                    return;  // Exit thread

                task = _tasks.Dequeue();
            }

            // Execute OUTSIDE the lock — so other workers can pick up tasks
            try
            {
                task();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"{Thread.CurrentThread.Name}: Error — {ex.Message}");
            }
        }
    }

    public void Submit(Action task)
    {
        lock (_lock)
        {
            if (_shutdown) throw new InvalidOperationException("Pool is shut down");
            _tasks.Enqueue(task);
            Monitor.Pulse(_lock);  // Wake one worker
        }
    }

    public void Shutdown(bool waitForCompletion = true)
    {
        lock (_lock)
        {
            _shutdown = true;
            Monitor.PulseAll(_lock);  // Wake all workers so they can exit
        }

        if (waitForCompletion)
        {
            foreach (var t in _workers)
                t.Join();
        }
    }

    public void Dispose() => Shutdown();
}

// Usage
using var pool = new CustomThreadPool(numWorkers: 3);

for (int i = 0; i < 10; i++)
{
    int taskId = i;
    pool.Submit(() =>
    {
        Console.WriteLine($"{Thread.CurrentThread.Name}: Processing task {taskId}");
        Thread.Sleep(500);
        Console.WriteLine($"{Thread.CurrentThread.Name}: Done task {taskId}");
    });
}

Thread.Sleep(4000);
pool.Shutdown(waitForCompletion: true);
Console.WriteLine("All done!");
```

---

### 17.11 Scheduled Task Executor (Uber)

**Asked at:** Uber, Google, Amazon

**Problem:** Implement a scheduler that can run tasks at a future time, or repeatedly at fixed intervals.

**Concepts:** Min-heap (PriorityQueue) for scheduling, Monitor.Wait with timeout

```csharp
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

public class ScheduledExecutor : IDisposable
{
    private record ScheduledTask(
        long RunAtTicks,
        int Id,
        Action Func,
        double PeriodSeconds
    ) : IComparable<ScheduledTask>
    {
        public int CompareTo(ScheduledTask? other)
            => RunAtTicks.CompareTo(other?.RunAtTicks ?? 0);
    }

    private readonly PriorityQueue<ScheduledTask, long> _queue = new();
    private readonly object _lock = new object();
    private int _taskCounter = 0;
    private bool _shutdown = false;
    private readonly List<Thread> _workers = new();

    public ScheduledExecutor(int numWorkers = 2)
    {
        for (int i = 0; i < numWorkers; i++)
        {
            var t = new Thread(WorkerLoop) { IsBackground = true };
            t.Start();
            _workers.Add(t);
        }
    }

    public void Schedule(Action func, double delaySeconds)
    {
        long runAt = Stopwatch.GetTimestamp()
            + (long)(delaySeconds * Stopwatch.Frequency);
        lock (_lock)
        {
            var task = new ScheduledTask(runAt, ++_taskCounter, func, 0);
            _queue.Enqueue(task, task.RunAtTicks);
            Monitor.PulseAll(_lock);
        }
    }

    public void ScheduleAtFixedRate(Action func, double initialDelay, double period)
    {
        long runAt = Stopwatch.GetTimestamp()
            + (long)(initialDelay * Stopwatch.Frequency);
        lock (_lock)
        {
            var task = new ScheduledTask(runAt, ++_taskCounter, func, period);
            _queue.Enqueue(task, task.RunAtTicks);
            Monitor.PulseAll(_lock);
        }
    }

    private void WorkerLoop()
    {
        while (true)
        {
            ScheduledTask? task = null;

            lock (_lock)
            {
                while (true)
                {
                    if (_shutdown) return;

                    if (_queue.Count == 0)
                    {
                        Monitor.Wait(_lock);
                        continue;
                    }

                    _queue.TryPeek(out var next, out _);
                    long now = Stopwatch.GetTimestamp();

                    if (now >= next!.RunAtTicks)
                    {
                        _queue.Dequeue();
                        task = next;
                        break;
                    }
                    else
                    {
                        double waitMs = (double)(next.RunAtTicks - now)
                            / Stopwatch.Frequency * 1000;
                        Monitor.Wait(_lock, Math.Max(1, (int)waitMs));
                    }
                }
            }

            // Execute outside lock
            try
            {
                task!.Func();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Task error: {ex.Message}");
            }

            // Reschedule if periodic
            if (task.PeriodSeconds > 0)
            {
                long nextRun = Stopwatch.GetTimestamp()
                    + (long)(task.PeriodSeconds * Stopwatch.Frequency);
                lock (_lock)
                {
                    var next = task with
                    {
                        RunAtTicks = nextRun,
                        Id = ++_taskCounter
                    };
                    _queue.Enqueue(next, next.RunAtTicks);
                    Monitor.PulseAll(_lock);
                }
            }
        }
    }

    public void Shutdown()
    {
        lock (_lock)
        {
            _shutdown = true;
            Monitor.PulseAll(_lock);
        }
        foreach (var t in _workers) t.Join();
    }

    public void Dispose() => Shutdown();
}

// Usage
using var scheduler = new ScheduledExecutor(numWorkers: 2);

scheduler.Schedule(() =>
    Console.WriteLine($"[{DateTime.Now:HH:mm:ss}] One-time task!"), 2);

scheduler.ScheduleAtFixedRate(() =>
    Console.WriteLine($"[{DateTime.Now:HH:mm:ss}] Heartbeat"), 0, 1);

scheduler.Schedule(() =>
    Console.WriteLine($"[{DateTime.Now:HH:mm:ss}] Delayed task!"), 5);

Thread.Sleep(6000);
scheduler.Shutdown();
```

---

### 17.12 Ride Matching System (Uber)

**Asked at:** Uber machine coding rounds

**Problem:** Build a concurrent ride matching system. Riders request rides, drivers go online/offline, and a matcher pairs them.

**Concepts:** Multiple wait conditions, background worker thread, nearest-match algorithm

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

public record Location(double Lat, double Lng)
{
    public double DistanceTo(Location other)
        => Math.Sqrt(Math.Pow(Lat - other.Lat, 2) + Math.Pow(Lng - other.Lng, 2));
}

public enum RideStatus { Requested, Matched, Completed, Cancelled }

public class Driver
{
    public string Id { get; init; } = "";
    public string Name { get; init; } = "";
    public Location Location { get; set; } = new(0, 0);
    public bool Available { get; set; } = true;
}

public class RideRequest
{
    public string Id { get; init; } = "";
    public string RiderName { get; init; } = "";
    public Location Pickup { get; init; } = new(0, 0);
    public Location Dropoff { get; init; } = new(0, 0);
    public RideStatus Status { get; set; } = RideStatus.Requested;
    public Driver? AssignedDriver { get; set; }
}

public class RideMatchingSystem : IDisposable
{
    private readonly List<Driver> _availableDrivers = new();
    private readonly Queue<RideRequest> _pendingRequests = new();
    private readonly Dictionary<string, RideRequest> _activeRides = new();
    private readonly object _lock = new object();
    private bool _shutdown = false;
    private readonly Thread _matcher;

    public RideMatchingSystem()
    {
        _matcher = new Thread(MatchLoop) { IsBackground = true };
        _matcher.Start();
    }

    public void AddDriver(Driver driver)
    {
        lock (_lock)
        {
            _availableDrivers.Add(driver);
            Console.WriteLine($"[SYSTEM] Driver {driver.Name} is now online");
            Monitor.PulseAll(_lock);
        }
    }

    public void RequestRide(RideRequest request)
    {
        lock (_lock)
        {
            _pendingRequests.Enqueue(request);
            Console.WriteLine($"[RIDER]  {request.RiderName} requested ride {request.Id}");
            Monitor.PulseAll(_lock);
        }
    }

    public void CompleteRide(string rideId)
    {
        lock (_lock)
        {
            if (_activeRides.Remove(rideId, out var ride))
            {
                ride.Status = RideStatus.Completed;
                ride.AssignedDriver!.Available = true;
                _availableDrivers.Add(ride.AssignedDriver);
                Console.WriteLine($"[DONE]   Ride {rideId} completed. {ride.AssignedDriver.Name} is free");
                Monitor.PulseAll(_lock);
            }
        }
    }

    private void MatchLoop()
    {
        while (true)
        {
            lock (_lock)
            {
                while ((_pendingRequests.Count == 0 || _availableDrivers.Count == 0)
                       && !_shutdown)
                {
                    Monitor.Wait(_lock);
                }

                if (_shutdown) return;

                var request = _pendingRequests.Dequeue();
                var driver = _availableDrivers
                    .OrderBy(d => d.Location.DistanceTo(request.Pickup))
                    .First();

                _availableDrivers.Remove(driver);
                driver.Available = false;
                request.AssignedDriver = driver;
                request.Status = RideStatus.Matched;
                _activeRides[request.Id] = request;

                double dist = driver.Location.DistanceTo(request.Pickup);
                Console.WriteLine($"[MATCH]  Ride {request.Id} → Driver {driver.Name} "
                    + $"(distance: {dist:F2})");
            }
        }
    }

    public void Shutdown()
    {
        lock (_lock)
        {
            _shutdown = true;
            Monitor.PulseAll(_lock);
        }
        _matcher.Join();
    }

    public void Dispose() => Shutdown();
}

// --- Simulation ---
using var system = new RideMatchingSystem();

var drivers = new[]
{
    new Driver { Id = "D1", Name = "Alice", Location = new(40.7, -74.0) },
    new Driver { Id = "D2", Name = "Bob",   Location = new(40.8, -73.9) },
    new Driver { Id = "D3", Name = "Carol", Location = new(40.6, -74.1) },
};
foreach (var d in drivers) system.AddDriver(d);

Thread.Sleep(100);

var riderThreads = Enumerable.Range(0, 5).Select(i =>
{
    return new Thread(() =>
    {
        system.RequestRide(new RideRequest
        {
            Id = $"R{i}",
            RiderName = $"Rider-{i}",
            Pickup = new(40.7 + Random.Shared.NextDouble() * 0.2 - 0.1,
                         -74.0 + Random.Shared.NextDouble() * 0.2 - 0.1),
            Dropoff = new(40.8, -73.9)
        });
    });
}).ToList();

riderThreads.ForEach(t => t.Start());
riderThreads.ForEach(t => t.Join());

Thread.Sleep(2000);
system.CompleteRide("R0");
system.CompleteRide("R1");
Thread.Sleep(2000);
system.Shutdown();
```

---

### 17.13 Concurrent Web Crawler

**Asked at:** Google, Meta, Amazon, LeetCode 1242

**Problem:** Crawl pages starting from a URL. Multiple threads fetch pages concurrently. Don't visit the same URL twice.

**Concepts:** Thread coordination, visited set, termination detection

```csharp
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

public class ConcurrentCrawler
{
    private readonly ConcurrentDictionary<string, bool> _visited = new();
    private readonly Queue<string> _queue = new();
    private readonly object _lock = new object();
    private int _activeWorkers = 0;
    private readonly ConcurrentBag<string> _results = new();
    private readonly int _numWorkers;

    public ConcurrentCrawler(int numWorkers = 4) => _numWorkers = numWorkers;

    public List<string> Crawl(string startUrl, Func<string, List<string>> getLinks)
    {
        _visited[startUrl] = true;
        lock (_lock)
        {
            _queue.Enqueue(startUrl);
            Monitor.PulseAll(_lock);
        }

        var workers = Enumerable.Range(0, _numWorkers)
            .Select(_ => new Thread(() => Worker(getLinks)))
            .ToList();
        workers.ForEach(t => t.Start());
        workers.ForEach(t => t.Join());

        return _results.ToList();
    }

    private void Worker(Func<string, List<string>> getLinks)
    {
        while (true)
        {
            string? url;
            lock (_lock)
            {
                while (_queue.Count == 0)
                {
                    if (_activeWorkers == 0)
                    {
                        Monitor.PulseAll(_lock);
                        return;  // No work and no one working → done
                    }
                    Monitor.Wait(_lock, 1000);
                    if (_queue.Count == 0 && _activeWorkers == 0)
                    {
                        Monitor.PulseAll(_lock);
                        return;
                    }
                }
                url = _queue.Dequeue();
                _activeWorkers++;
            }

            // Fetch page (outside lock)
            try
            {
                var links = getLinks(url);
                _results.Add(url);

                var newUrls = links.Where(u => _visited.TryAdd(u, true)).ToList();

                lock (_lock)
                {
                    foreach (var u in newUrls)
                        _queue.Enqueue(u);
                    Monitor.PulseAll(_lock);
                }
            }
            finally
            {
                lock (_lock)
                {
                    _activeWorkers--;
                    if (_activeWorkers == 0 && _queue.Count == 0)
                        Monitor.PulseAll(_lock);
                }
            }
        }
    }
}

// Mock web graph
var webGraph = new Dictionary<string, List<string>>
{
    ["example.com"]   = new() { "example.com/a", "example.com/b" },
    ["example.com/a"] = new() { "example.com/c", "example.com/d" },
    ["example.com/b"] = new() { "example.com/d", "example.com/e" },
    ["example.com/c"] = new(),
    ["example.com/d"] = new() { "example.com/e" },
    ["example.com/e"] = new(),
};

List<string> MockFetch(string url)
{
    Thread.Sleep(Random.Shared.Next(100, 300));
    return webGraph.GetValueOrDefault(url, new List<string>());
}

var crawler = new ConcurrentCrawler(numWorkers: 3);
var results = crawler.Crawl("example.com", MockFetch);
Console.WriteLine($"\nCrawled {results.Count} pages: {string.Join(", ", results)}");
```

---

### 17.14 Traffic Signal Controller

**Asked at:** Uber, Goldman Sachs

**Problem:** A 4-way intersection with traffic lights. Cars wait until their direction is green.

**Concepts:** Monitor.Wait/Pulse, background cycling thread

```csharp
using System;
using System.Threading;

public enum Direction { NorthSouth, EastWest }

public class TrafficSignal : IDisposable
{
    private Direction _currentGreen = Direction.NorthSouth;
    private readonly object _lock = new object();
    private readonly int _greenDurationMs;
    private bool _running = true;
    private readonly Thread _cycleThread;

    public TrafficSignal(int greenDurationMs = 3000)
    {
        _greenDurationMs = greenDurationMs;
        _cycleThread = new Thread(Cycle) { IsBackground = true };
        _cycleThread.Start();
    }

    private void Cycle()
    {
        while (_running)
        {
            Thread.Sleep(_greenDurationMs);
            lock (_lock)
            {
                _currentGreen = _currentGreen == Direction.NorthSouth
                    ? Direction.EastWest
                    : Direction.NorthSouth;
                Console.WriteLine($"\n--- GREEN: {_currentGreen} ---");
                Monitor.PulseAll(_lock);
            }
        }
    }

    public void Cross(string carId, Direction direction)
    {
        lock (_lock)
        {
            while (_currentGreen != direction)
                Monitor.Wait(_lock);
            Console.WriteLine($"  Car {carId} crossing ({direction})");
        }
    }

    public void Dispose()
    {
        _running = false;
        _cycleThread.Join(5000);
    }
}

using var signal = new TrafficSignal(greenDurationMs: 2000);

var threads = Enumerable.Range(0, 10).Select(i =>
{
    var dir = Random.Shared.Next(2) == 0 ? Direction.NorthSouth : Direction.EastWest;
    return new Thread(() =>
    {
        Thread.Sleep(Random.Shared.Next(0, 3000));
        Console.WriteLine($"Car C{i} arrives ({dir})");
        signal.Cross($"C{i}", dir);
    });
}).ToList();

threads.ForEach(t => t.Start());
threads.ForEach(t => t.Join());
```

---

### 17.15 Async Job Scheduler (DAG)

**Asked at:** Uber, Meta, Google

**Problem:** A job scheduler that accepts jobs with dependencies (DAG). A job runs only after all its dependencies complete. Independent jobs run concurrently.

**Concepts:** Topological ordering, dynamic readiness tracking, thread pool

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

public class Job
{
    public string Id { get; init; } = "";
    public Action Work { get; init; } = () => { };
    public List<string> Dependencies { get; init; } = new();
}

public class JobScheduler
{
    private readonly int _numWorkers;

    public JobScheduler(int numWorkers = 4) => _numWorkers = numWorkers;

    public void Execute(List<Job> jobs)
    {
        // Build graph
        var graph = jobs.ToDictionary(j => j.Id);
        var inDegree = jobs.ToDictionary(j => j.Id, j => j.Dependencies.Count);
        var dependents = new Dictionary<string, List<string>>();
        foreach (var job in jobs)
        {
            foreach (var dep in job.Dependencies)
            {
                if (!dependents.ContainsKey(dep))
                    dependents[dep] = new();
                dependents[dep].Add(job.Id);
            }
        }

        var readyQueue = new Queue<string>();
        var completed = new HashSet<string>();
        var total = jobs.Count;
        var lockObj = new object();

        // Seed: jobs with no dependencies
        foreach (var job in jobs)
        {
            if (inDegree[job.Id] == 0)
                readyQueue.Enqueue(job.Id);
        }

        void Worker()
        {
            while (true)
            {
                string? jobId;
                lock (lockObj)
                {
                    while (readyQueue.Count == 0)
                    {
                        if (completed.Count == total)
                        {
                            Monitor.PulseAll(lockObj);
                            return;
                        }
                        Monitor.Wait(lockObj);
                    }
                    if (completed.Count == total) return;
                    jobId = readyQueue.Dequeue();
                }

                // Execute outside lock
                var job = graph[jobId];
                Console.WriteLine($"[{Thread.CurrentThread.Name}] Running: {jobId}");
                try
                {
                    job.Work();
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Job {jobId} failed: {ex.Message}");
                }

                // Unblock dependents
                lock (lockObj)
                {
                    completed.Add(jobId);
                    if (dependents.TryGetValue(jobId, out var deps))
                    {
                        foreach (var depId in deps)
                        {
                            inDegree[depId]--;
                            if (inDegree[depId] == 0)
                                readyQueue.Enqueue(depId);
                        }
                    }
                    Monitor.PulseAll(lockObj);
                }
            }
        }

        var workers = Enumerable.Range(0, _numWorkers)
            .Select(i =>
            {
                var t = new Thread(Worker) { Name = $"W-{i}" };
                return t;
            }).ToList();
        workers.ForEach(w => w.Start());
        workers.ForEach(w => w.Join());
        Console.WriteLine("All jobs completed!");
    }
}

// Diamond dependency: A,B → C → D. E is independent.
Action MakeTask(string name, int durationMs = 500)
{
    return () =>
    {
        Thread.Sleep(durationMs);
        Console.WriteLine($"  >> {name} done");
    };
}

var jobs = new List<Job>
{
    new() { Id = "A", Work = MakeTask("A") },
    new() { Id = "B", Work = MakeTask("B") },
    new() { Id = "C", Work = MakeTask("C"), Dependencies = { "A", "B" } },
    new() { Id = "D", Work = MakeTask("D"), Dependencies = { "C" } },
    new() { Id = "E", Work = MakeTask("E") },  // Independent — runs in parallel with A,B
};

var scheduler = new JobScheduler(numWorkers: 3);
scheduler.Execute(jobs);
```

---

## 18. Interview Quick Reference

### C# Concurrency Primitives

```
Primitive                  | Namespace / Type              | What It Does
---------------------------|-------------------------------|-------------------------------------------
lock / Monitor             | System.Threading              | Mutual exclusion (reentrant)
Mutex                      | System.Threading              | Cross-process mutual exclusion
Monitor.Wait/Pulse         | System.Threading              | Condition variable (wait/notify)
SemaphoreSlim              | System.Threading              | Allow N concurrent threads (async-ready)
Semaphore                  | System.Threading              | Cross-process semaphore
ManualResetEventSlim       | System.Threading              | Boolean flag — stays set (broadcast)
AutoResetEvent             | System.Threading              | Auto-resets — wakes one waiter per Set
Barrier                    | System.Threading              | Wait for N threads at checkpoint
Interlocked                | System.Threading              | Atomic inc/dec/CAS — no lock needed
volatile                   | (keyword)                     | Memory visibility for single fields
ReaderWriterLockSlim       | System.Threading              | Multiple readers OR one writer
SpinLock                   | System.Threading              | Very short critical sections (no alloc)
CountdownEvent             | System.Threading              | Wait until N signals received
BlockingCollection<T>      | System.Collections.Concurrent | Thread-safe blocking queue
ConcurrentDictionary<K,V>  | System.Collections.Concurrent | Thread-safe dictionary
ConcurrentQueue<T>         | System.Collections.Concurrent | Lock-free FIFO queue
Channel<T>                 | System.Threading.Channels     | Async producer-consumer
Task / Task<T>             | System.Threading.Tasks        | Async operations on thread pool
Parallel.For/ForEach       | System.Threading.Tasks        | Data-parallel loops
CancellationToken          | System.Threading              | Cooperative cancellation
TaskCompletionSource<T>    | System.Threading.Tasks        | Manual control over Task completion
```

### Decision Flowchart

```
What kind of work?
  │
  ├── I/O-bound (network, disk, DB)
  │     ├── Few concurrent ops       → async/await with Task
  │     ├── Many concurrent ops      → async/await + SemaphoreSlim to throttle
  │     └── Very many (10K+)         → async/await + Channel<T>
  │
  └── CPU-bound (math, processing)
        ├── Data-parallel            → Parallel.For / PLINQ
        ├── Task-parallel            → Task.Run + Task.WhenAll
        └── Fine-grained control     → Thread + lock
```

### Common Interview Q&A

| Question | Answer |
|----------|--------|
| Does C# have a GIL? | No — true parallel execution on multiple cores |
| `lock` vs `Mutex`? | `lock` = in-process, fast. `Mutex` = cross-process, slow |
| Is `lock` reentrant? | Yes — same thread can acquire multiple times (unlike Python's `Lock`) |
| Why `while` not `if` with `Wait()`? | Spurious wakeups — thread can wake without Pulse |
| `Pulse()` vs `PulseAll()`? | `Pulse` wakes one, `PulseAll` wakes all |
| How to prevent deadlock? | Consistent lock ordering, `Monitor.TryEnter` with timeout |
| `SemaphoreSlim` vs `Semaphore`? | Slim = in-process, async-ready. Full = cross-process |
| `lock` with `await`? | ❌ Compile error — use `SemaphoreSlim(1,1)` as async mutex |
| `Task.Run` vs `new Thread`? | `Task.Run` uses thread pool (reuse). `new Thread` creates fresh |
| `ConcurrentDictionary` vs `Dictionary + lock`? | `ConcurrentDictionary` for simple ops. Lock for compound ops |
| `volatile` vs `Interlocked`? | `volatile` = visibility only. `Interlocked` = atomic read-modify-write |
| `BlockingCollection` vs `Channel`? | `BlockingCollection` = sync (blocks thread). `Channel` = async |
| `Task` vs `ValueTask`? | `Task` always allocates. `ValueTask` avoids alloc when sync |
| `ConfigureAwait(false)`? | Don't capture sync context — use in library code |
| `Thread` vs `Task`? | Thread = OS thread, heavy. Task = work item on pool, lightweight |

### Machine Coding Round Tips

1. **Clarify first:** Ask about scale, thread count, fairness, cancellation, and shutdown behavior
2. **Draw the model:** Which threads exist? What do they share? Where are the critical sections?
3. **Identify shared state:** Every shared mutable variable needs synchronization
4. **Pick the right primitive:** Don't use `Monitor.Wait/Pulse` when `ManualResetEventSlim` suffices
5. **Always use `lock` (not manual Monitor):** Prevents forgetting to release
6. **Always use `while` with `Monitor.Wait()`:** Handles spurious wakeups
7. **Keep critical sections minimal:** Do I/O and computation outside locks
8. **Implement `IDisposable`:** Show you can clean up threads and resources
9. **Handle shutdown:** Show graceful stop with `Monitor.PulseAll` to unblock all waiters
10. **Consider `CancellationToken`:** Show cooperative cancellation for long operations
11. **Never lock on `this` or `typeof`:** Always use a private `object` field
12. **State complexity:** Time and space for each operation
