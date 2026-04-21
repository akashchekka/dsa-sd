# Multithreading & Concurrency – Interview Guide

## Table of Contents

1. [Concurrency Overview](#1-concurrency-overview)
2. [Concurrency vs Parallelism](#2-concurrency-vs-parallelism)
3. [Processes vs Threads](#3-processes-vs-threads)
4. [Thread Lifecycle](#4-thread-lifecycle)
5. [Race Conditions](#5-race-conditions)
6. [Mutex](#6-mutex)
7. [Semaphores](#7-semaphores)
8. [Condition Variables](#8-condition-variables)
9. [Coarse-Grained vs Fine-Grained Locking](#9-coarse-grained-vs-fine-grained-locking)
10. [Reentrant Locks](#10-reentrant-locks)
11. [Try-Lock](#11-try-lock)
12. [Compare-and-Swap (CAS)](#12-compare-and-swap-cas)
13. [Deadlock](#13-deadlock)
14. [Livelock](#14-livelock)
15. [Signaling Pattern](#15-signaling-pattern)
16. [Thread Pool Pattern](#16-thread-pool-pattern)
17. [Producer-Consumer Pattern](#17-producer-consumer-pattern)
18. [Reader-Writer Pattern](#18-reader-writer-pattern)
19. [Thread-Safe Cache](#19-thread-safe-cache)
20. [Thread-Safe Blocking Queue](#20-thread-safe-blocking-queue)
21. [Async/Await and Task-Based Asynchronous Pattern](#21-asyncawait-and-task-based-asynchronous-pattern)
22. [Volatile and Memory Barriers](#22-volatile-and-memory-barriers)
23. [Concurrent Collections](#23-concurrent-collections)
24. [Cancellation Tokens](#24-cancellation-tokens)
25. [Thread-Local Storage](#25-thread-local-storage)
26. [Immutability and Thread Safety](#26-immutability-and-thread-safety)
27. [Parallel Programming (PLINQ & Parallel Class)](#27-parallel-programming-plinq--parallel-class)
28. [Async Streams (IAsyncEnumerable)](#28-async-streams-iasyncenumerable)
29. [Thread Starvation and ThreadPool Tuning](#29-thread-starvation-and-threadpool-tuning)
30. [Context Switching and False Sharing](#30-context-switching-and-false-sharing)
31. [Lock-Free and Wait-Free Algorithms](#31-lock-free-and-wait-free-algorithms)
32. [Priority Inversion](#32-priority-inversion)
33. [Fork-Join Pattern](#33-fork-join-pattern)
34. [Timers in .NET](#34-timers-in-net)
35. [Interview Questions](#35-interview-questions)

---

## 1. Concurrency Overview

**Concurrency** is the ability of a system to handle multiple tasks that are in progress at the same time. The tasks may not be executing simultaneously — they can be interleaved on a single core.

Think of a single-core CPU running a web server. It can't physically execute two requests at the same instant, but it can rapidly switch between them — serving a bit of Request A, then a bit of Request B, then back to A. From the outside, both requests appear to be handled "at the same time." That's concurrency.

Concurrency is fundamentally about **managing complexity**. Modern software must deal with network calls, disk I/O, user input, timers, and background tasks all happening together. Without concurrency, a program would freeze entirely while waiting for a database query to return.

### Why Concurrency Matters

| Benefit | Example |
|---|---|
| **Responsiveness** | UI stays interactive while loading data |
| **Throughput** | Web server handles thousands of requests |
| **Resource utilization** | CPU does work while waiting for I/O |
| **Scalability** | Distribute work across cores/machines |

### Concurrency Models

There are several ways to structure concurrent programs. Each model offers a different tradeoff between performance, safety, and complexity. In **shared memory**, threads read and write the same data — this is fast but requires careful synchronization. In **message passing**, threads or processes communicate by sending messages instead of sharing state directly, which eliminates many synchronization bugs at the cost of some overhead.

| Model | Description | C# Support |
|---|---|---|
| **Shared Memory** | Threads share the same address space | Default model |
| **Message Passing** | Processes communicate via messages | `Channel<T>`, `System.Threading.Channels` |
| **Actor Model** | Isolated actors with message queues | Akka.NET, Orleans |
| **CSP (Communicating Sequential Processes)** | Processes synchronize via channels | `Channel<T>` |

```csharp
// Shared memory — threads share a variable
int counter = 0;
var threads = Enumerable.Range(0, 10).Select(_ => new Thread(() =>
{
    for (int i = 0; i < 1000; i++)
        Interlocked.Increment(ref counter);
})).ToList();

threads.ForEach(t => t.Start());
threads.ForEach(t => t.Join());
Console.WriteLine(counter); // 10000 — correct with Interlocked
```

---

## 2. Concurrency vs Parallelism

This is one of the most frequently confused pairs of terms in interviews. **Concurrency** is about the structure of your program — it's about *dealing* with multiple things at once. **Parallelism** is about execution — it's about *doing* multiple things at once.

A single-core machine can be concurrent (switching between tasks) but never truly parallel. A multi-core machine can be both. You need concurrency to take advantage of parallelism, but concurrency is valuable even without it — for example, a GUI app uses concurrency on a single thread to stay responsive while fetching data.

Rob Pike (Go language creator) put it best: *"Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once."*

| | Concurrency | Parallelism |
|---|---|---|
| **Definition** | Managing multiple tasks at once | Executing multiple tasks at the same instant |
| **Cores needed** | 1+ (interleaving) | 2+ (true simultaneous) |
| **Goal** | Structure / responsiveness | Speed / throughput |
| **Analogy** | One cook juggling multiple dishes | Multiple cooks each cooking a dish |
| **Example** | async/await on a single thread | `Parallel.ForEach` across cores |

```
Concurrency (1 core):
  Task A: ████░░░░████░░░░████
  Task B: ░░░░████░░░░████░░░░

Parallelism (2 cores):
  Core 1: ████████████████████  Task A
  Core 2: ████████████████████  Task B
```

```csharp
// Concurrency — async I/O, single thread can handle both
async Task ConcurrentExample()
{
    Task<string> download1 = HttpClient.GetStringAsync("https://api1.example.com");
    Task<string> download2 = HttpClient.GetStringAsync("https://api2.example.com");
    string[] results = await Task.WhenAll(download1, download2);
}

// Parallelism — CPU-bound work across multiple cores
void ParallelExample()
{
    var numbers = Enumerable.Range(1, 1_000_000).ToList();
    Parallel.ForEach(numbers, n =>
    {
        // Each iteration can run on a different core
        double result = Math.Sqrt(n) * Math.Log(n);
    });
}
```

**Interview Tip:** Concurrency is about **structure** (dealing with many things). Parallelism is about **execution** (doing many things). You can have concurrency without parallelism (async on single core) and parallelism without concurrency (SIMD instructions).

---

## 3. Processes vs Threads

A **process** is an independent program in execution. It has its own memory space (code, data, heap, stack), file handles, and security context. The operating system isolates processes from each other — one process crashing won't bring down another. However, this isolation comes at a cost: creating a process is expensive, and communicating between processes requires explicit IPC (Inter-Process Communication) mechanisms like pipes, sockets, or shared memory.

A **thread** is the smallest unit of execution within a process. Multiple threads in the same process share the same memory space — they can read and write the same variables directly. This makes communication between threads trivially fast (just read a shared variable), but it also makes it dangerous: without proper synchronization, threads can corrupt shared data. Creating threads is much cheaper than creating processes because there's no need to duplicate the entire address space.

In practice, most concurrent programs in C# use threads (or Tasks, which run on threads) because the shared-memory model is efficient. Processes are used when you need isolation — for example, running untrusted code in a sandbox, or using multiple CPU cores in languages that have a GIL (Global Interpreter Lock) like Python.

| Feature | Process | Thread |
|---|---|---|
| **Memory** | Own address space | Shares process memory |
| **Creation cost** | Heavy (new address space, OS resources) | Lightweight (shared resources) |
| **Communication** | IPC (pipes, sockets, shared memory) | Direct memory access |
| **Isolation** | Complete — crash doesn't affect others | None — crash can kill process |
| **Context switch** | Expensive (TLB flush, page tables) | Cheaper (same address space) |
| **OS entity** | Yes | Yes (kernel threads) |

```csharp
// Creating a process
using var process = new Process
{
    StartInfo = new ProcessStartInfo
    {
        FileName = "dotnet",
        Arguments = "--version",
        RedirectStandardOutput = true,
        UseShellExecute = false
    }
};
process.Start();
string output = process.StandardOutput.ReadToEnd();
process.WaitForExit();

// Creating a thread
var thread = new Thread(() =>
{
    Console.WriteLine($"Thread {Thread.CurrentThread.ManagedThreadId} running");
});
thread.IsBackground = true;  // won't keep app alive
thread.Start();
thread.Join();                // wait for completion
```

### User-Space Threads (Fibers/Green Threads)

Not all threads are equal. **Kernel threads** are managed by the operating system — the OS scheduler decides when each thread runs. **User-space threads** (also called green threads or fibers) are managed by the application runtime, which can switch between them much more cheaply because no kernel involvement is needed. Go's goroutines are a famous example: you can spin up millions of goroutines because each costs only ~2KB of stack space, compared to ~1MB for an OS thread.

In .NET, `Task` and `async/await` give you something similar — you can have millions of Tasks in flight, but they're multiplexed onto a small pool of OS threads by the ThreadPool scheduler.

| Type | Scheduled by | Context switch | Examples |
|---|---|---|---|
| Kernel thread | OS kernel | Expensive | `Thread`, pthreads |
| User thread / Fiber | Runtime | Very cheap | Go goroutines, Erlang processes |
| .NET Tasks | ThreadPool + scheduler | Cooperative | `Task`, `async/await` |

---

## 4. Thread Lifecycle

Every thread goes through a series of states from birth to death. Understanding this lifecycle is essential for debugging multithreaded programs — when you take a thread dump and see a thread in `WaitSleepJoin` state, you know it's blocked on something (a `lock`, a `Thread.Sleep`, or a `Thread.Join` call).

A thread starts in the **Unstarted** state when you create it with `new Thread(...)`. It moves to **Runnable** when you call `Start()`. The OS scheduler then picks it up and puts it in the **Running** state. If the thread calls `Sleep()`, `Wait()`, or `Join()`, it moves to **Waiting/Blocked** — it won't consume CPU time until the blocking condition is resolved. When the thread's method returns, it enters the **Terminated** state and cannot be restarted.

```
          Start()
  New ──────────► Runnable ◄──────────┐
                    │                  │
                    │ CPU scheduled    │ Sleep/Wait
                    ▼                  │ completed
                 Running ─────────► Waiting/Blocked
                    │                  │
                    │ Work done        │ Interrupt/
                    ▼                  │ Abort
                Terminated            │
                    ▲                  │
                    └──────────────────┘
```

### Thread States in C#

| State | `ThreadState` Value | Description |
|---|---|---|
| Unstarted | `Unstarted` | Created but `Start()` not called |
| Running | `Running` | Executing on CPU |
| WaitSleepJoin | `WaitSleepJoin` | Blocked on `Sleep`, `Wait`, `Join` |
| Stopped | `Stopped` | Execution completed |
| Suspended | `Suspended` | Deprecated — do not use |
| Background | `Background` | Won't prevent app exit |

```csharp
var thread = new Thread(() =>
{
    Console.WriteLine("Working...");
    Thread.Sleep(1000);
    Console.WriteLine("Done");
});

Console.WriteLine(thread.ThreadState); // Unstarted
thread.Start();
Console.WriteLine(thread.ThreadState); // Running (or WaitSleepJoin)
thread.Join();
Console.WriteLine(thread.ThreadState); // Stopped
```

### Foreground vs Background Threads

This distinction is critical to understand: a .NET application stays alive as long as at least one **foreground thread** is running. When all foreground threads finish, the CLR shuts down the process — any running **background threads** are abruptly killed without getting a chance to clean up. By default, threads created with `new Thread()` are foreground threads. All ThreadPool threads (and therefore all `Task.Run` tasks) are background threads.

This means if you start a background thread to save data to disk and your `Main` method exits, that background thread will be killed mid-write. Always `Join()` or `await` important work before exiting.

```csharp
// Foreground — app waits for it to finish
var fg = new Thread(() => Thread.Sleep(5000));
fg.IsBackground = false; // default
fg.Start();

// Background — killed when all foreground threads exit
var bg = new Thread(() => Thread.Sleep(5000));
bg.IsBackground = true;
bg.Start();

// Task threads are background by default
```

---

## 5. Race Conditions

A **race condition** occurs when the outcome of a program depends on the relative timing or ordering of thread execution — something the programmer has no control over. Race conditions are among the most insidious bugs in software because they're non-deterministic: the code might work correctly 99.9% of the time and fail only under specific timing conditions, making them extremely hard to reproduce and debug.

The root cause is almost always **unprotected access to shared mutable state**. When two threads read and write the same variable without synchronization, the final result depends on which thread "wins the race" to read or write first. The terrifying part is that `counter++` looks like a single operation in C#, but it's actually three operations at the CPU level: read the value, increment it, write it back. Another thread can sneak in between any of these steps.

```csharp
// ❌ Race condition — increment is NOT atomic
// Read-Modify-Write: 3 separate operations
int counter = 0;

var tasks = Enumerable.Range(0, 100).Select(_ => Task.Run(() =>
{
    for (int i = 0; i < 10_000; i++)
        counter++; // NOT thread-safe
})).ToArray();

Task.WaitAll(tasks);
Console.WriteLine(counter); // < 1,000,000 — lost updates!
```

### Why It Happens — Non-Atomic Read-Modify-Write

```
Thread A:  Read counter (0) → Increment (1) → Write (1)
Thread B:     Read counter (0) → Increment (1) → Write (1)  ← LOST UPDATE
Expected: 2, Got: 1
```

### Fixes

```csharp
// Fix 1: Interlocked (lock-free atomic operation)
Interlocked.Increment(ref counter);

// Fix 2: lock (mutual exclusion)
lock (_lockObj)
{
    counter++;
}

// Fix 3: Use thread-safe type
ConcurrentDictionary<string, int> safeDict = new();
safeDict.AddOrUpdate("key", 1, (k, v) => v + 1);
```

### Types of Race Conditions

| Type | Description |
|---|---|
| **Check-then-act** | `if (dict.ContainsKey(k)) dict[k]++` — gap between check and act |
| **Read-modify-write** | `counter++` — not atomic |
| **Compound action** | Multiple operations that should be atomic but aren't |

```csharp
// ❌ Check-then-act race
if (!dict.ContainsKey("key"))
    dict["key"] = ComputeExpensiveValue(); // another thread may add between check and set

// ✅ Fix with ConcurrentDictionary
dict.GetOrAdd("key", _ => ComputeExpensiveValue());
```

---

## 6. Mutex

A **Mutex** (mutual exclusion) is the most fundamental synchronization primitive. It ensures that only one thread can enter a **critical section** (a block of code that accesses shared resources) at a time. Think of it as a bathroom lock — when one person locks the door, everyone else must wait outside until they're done.

In C#, the most common way to achieve mutual exclusion is the `lock` statement, which is syntactic sugar for `Monitor.Enter` and `Monitor.Exit`. Under the hood, `lock` uses a hybrid approach: it first tries a lightweight spin in user mode (for very short waits), and if the lock is still held, it falls back to a kernel-mode wait that puts the thread to sleep. This means short critical sections are very cheap, while long-held locks properly yield the CPU.

The `Mutex` class (capital M) is heavier — it's a kernel object that works across processes. You'd use it when you need to coordinate between separate applications (e.g., ensuring only one instance of your app runs at a time).

### `lock` Statement (Monitor Under the Hood)

```csharp
public class ThreadSafeCounter
{
    private int _count;
    private readonly object _lock = new();

    public void Increment()
    {
        lock (_lock)  // Acquires Monitor; releases on exit
        {
            _count++;
        }
    }

    public int GetCount()
    {
        lock (_lock)
        {
            return _count;
        }
    }
}
```

### `Monitor` — Explicit Control

```csharp
bool lockTaken = false;
try
{
    Monitor.TryEnter(_lock, TimeSpan.FromSeconds(5), ref lockTaken);
    if (lockTaken)
    {
        // Critical section
    }
    else
    {
        // Timeout — handle gracefully
    }
}
finally
{
    if (lockTaken) Monitor.Exit(_lock);
}
```

### `Mutex` Class — Cross-Process Synchronization

```csharp
// Named mutex — ensures single instance of application
using var mutex = new Mutex(initiallyOwned: false, name: "Global\\MyAppMutex");

if (!mutex.WaitOne(TimeSpan.FromSeconds(3)))
{
    Console.WriteLine("Another instance is running!");
    return;
}

try
{
    Console.WriteLine("Running exclusively...");
    // Application logic
}
finally
{
    mutex.ReleaseMutex();
}
```

| Feature | `lock` / `Monitor` | `Mutex` |
|---|---|---|
| Scope | Within process | Cross-process |
| Performance | Fast (user-mode spin) | Slow (kernel object) |
| Reentrant | Yes | Yes |
| Timeout | `Monitor.TryEnter` | `WaitOne(timeout)` |
| Use case | Protecting shared data | Single app instance, file access |

---

## 7. Semaphores

A **Semaphore** is a generalization of a mutex. While a mutex says "only one thread at a time," a semaphore says "up to N threads at a time." It works by maintaining an internal counter. When a thread calls `Wait()`, the counter decrements. If the counter is already 0, the thread blocks until another thread calls `Release()`, which increments the counter.

The classic real-world analogy is a parking lot: if a lot has 50 spaces, 50 cars can enter. The 51st car must wait at the entrance until someone leaves. The semaphore doesn't care *which* car is in *which* space — it only tracks how many spaces are occupied.

A key difference from mutexes: semaphores have **no ownership**. Any thread can release a semaphore, not just the one that acquired it. This makes them flexible but also means you can accidentally release more times than you acquired, leading to subtle bugs.

- **Binary Semaphore** (count=1): Acts like a mutex but without ownership tracking
- **Counting Semaphore** (count=N): Allows N concurrent accessors

```csharp
// Limit to 3 concurrent connections
var semaphore = new SemaphoreSlim(initialCount: 3, maxCount: 3);

async Task AccessDatabaseAsync(int id)
{
    Console.WriteLine($"Task {id}: Waiting for permit...");
    await semaphore.WaitAsync();  // decrement count (blocks if 0)
    try
    {
        Console.WriteLine($"Task {id}: Connected ({semaphore.CurrentCount} slots left)");
        await Task.Delay(2000);   // simulate DB work
    }
    finally
    {
        semaphore.Release();      // increment count
        Console.WriteLine($"Task {id}: Released");
    }
}

// Launch 10 tasks — only 3 run concurrently
var tasks = Enumerable.Range(1, 10)
    .Select(i => AccessDatabaseAsync(i));
await Task.WhenAll(tasks);
```

### Rate Limiting with Semaphore

```csharp
public class RateLimiter
{
    private readonly SemaphoreSlim _semaphore;
    private readonly int _maxRequests;
    private readonly TimeSpan _window;

    public RateLimiter(int maxRequests, TimeSpan window)
    {
        _maxRequests = maxRequests;
        _window = window;
        _semaphore = new SemaphoreSlim(maxRequests, maxRequests);
    }

    public async Task<T> ExecuteAsync<T>(Func<Task<T>> action)
    {
        await _semaphore.WaitAsync();
        try
        {
            return await action();
        }
        finally
        {
            // Release after window expires to enforce rate
            _ = Task.Delay(_window).ContinueWith(_ => _semaphore.Release());
        }
    }
}
```

| Feature | `Mutex` | `Semaphore` |
|---|---|---|
| Max concurrent | 1 | N |
| Ownership | Thread that locked must unlock | Any thread can release |
| Reentrant | Yes | No (each Wait decrements) |
| Use case | Exclusive access | Connection pools, rate limiting |

---

## 8. Condition Variables

A **condition variable** solves a very specific problem: *"I'm holding a lock, but I can't proceed until some condition is true. I need to release the lock, sleep, and wake up when the condition might have changed — all without missing a signal."*

Without condition variables, you'd have to do **busy waiting** (spinning in a loop checking the condition), which wastes CPU. Condition variables let a thread efficiently sleep and get woken up only when another thread signals that the condition may have changed.

The key operation is `Monitor.Wait(_lock)` which does three things **atomically**: (1) releases the lock, (2) puts the thread to sleep, (3) re-acquires the lock when woken up. This atomicity is crucial — if releasing the lock and sleeping were separate steps, another thread could change the condition and signal *between* those steps, causing the signal to be lost forever.

In C#, `Monitor.Wait` / `Monitor.Pulse` / `Monitor.PulseAll` serve this purpose. `Pulse` wakes one waiting thread; `PulseAll` wakes all of them (each must still re-acquire the lock before proceeding).

```csharp
public class BoundedBuffer<T>
{
    private readonly Queue<T> _queue = new();
    private readonly int _capacity;
    private readonly object _lock = new();

    public BoundedBuffer(int capacity) { _capacity = capacity; }

    public void Enqueue(T item)
    {
        lock (_lock)
        {
            // Wait while buffer is full
            while (_queue.Count >= _capacity)
                Monitor.Wait(_lock);  // release lock + sleep atomically

            _queue.Enqueue(item);
            Monitor.PulseAll(_lock);  // wake all waiters
        }
    }

    public T Dequeue()
    {
        lock (_lock)
        {
            // Wait while buffer is empty
            while (_queue.Count == 0)
                Monitor.Wait(_lock);

            T item = _queue.Dequeue();
            Monitor.PulseAll(_lock);  // wake producers waiting on full
            return item;
        }
    }
}
```

### `ManualResetEventSlim` / `AutoResetEvent` — Event-Based Signaling

```csharp
// ManualResetEventSlim — stays signaled until manually reset
var gate = new ManualResetEventSlim(initialState: false);

// Worker thread
Task.Run(() =>
{
    Console.WriteLine("Worker: Waiting for signal...");
    gate.Wait();                // blocks until Set()
    Console.WriteLine("Worker: Proceeding!");
});

Thread.Sleep(2000);
gate.Set();   // signal ALL waiters — gate stays open
// gate.Reset(); // must manually close

// AutoResetEvent — auto-resets after releasing ONE waiter
var turnstile = new AutoResetEvent(initialState: false);
turnstile.Set();      // releases exactly one waiting thread, then resets
```

| Mechanism | Releases | Auto-Reset | Use Case |
|---|---|---|---|
| `Monitor.Pulse` | One waiter | N/A | Condition variables |
| `Monitor.PulseAll` | All waiters | N/A | Broadcast notification |
| `AutoResetEvent` | One waiter | Yes | Turnstile / handoff |
| `ManualResetEventSlim` | All waiters | No | Gate / barrier |

**Interview Tip:** Always use `while` (not `if`) when checking conditions after `Wait` — **spurious wakeups** can occur.

---

## 9. Coarse-Grained vs Fine-Grained Locking

When you have shared data that needs protection, you face a fundamental design decision: **how many locks should you use?**

**Coarse-grained locking** uses a single lock to protect everything. It's simple and hard to get wrong, but it creates a bottleneck — every thread must wait for the same lock, even if they're accessing completely unrelated data. Imagine a library with one door: only one person can enter or leave at a time, even though there are thousands of books on different floors.

**Fine-grained locking** uses multiple locks, each protecting a subset of the data. This allows threads working on different subsets to proceed in parallel. The library now has one door per floor — people on different floors don't block each other. However, this introduces complexity: you must be careful about lock ordering (to avoid deadlocks) and ensuring that operations spanning multiple locks are handled correctly.

The technique of splitting one lock into multiple locks based on data partitioning is called **lock striping**. `ConcurrentDictionary` in .NET uses this internally — it maintains an array of locks, and each key maps to a specific lock based on its hash code.

### Coarse-Grained — One Lock for Everything

```csharp
// ❌ Coarse-grained — single lock bottleneck
public class CoarseGrainedCache
{
    private readonly Dictionary<string, object> _cache = new();
    private readonly object _lock = new();

    public object Get(string key)
    {
        lock (_lock) { return _cache.GetValueOrDefault(key); }
    }

    public void Set(string key, object value)
    {
        lock (_lock) { _cache[key] = value; }
    }

    public void Delete(string key)
    {
        lock (_lock) { _cache.Remove(key); }
    }
}
```

### Fine-Grained — Lock Striping

```csharp
// ✅ Fine-grained — lock striping for higher throughput
public class StripedCache<TKey, TValue>
{
    private readonly int _stripeCount;
    private readonly Dictionary<TKey, TValue>[] _buckets;
    private readonly object[] _locks;

    public StripedCache(int stripeCount = 16)
    {
        _stripeCount = stripeCount;
        _buckets = new Dictionary<TKey, TValue>[stripeCount];
        _locks = new object[stripeCount];

        for (int i = 0; i < stripeCount; i++)
        {
            _buckets[i] = new Dictionary<TKey, TValue>();
            _locks[i] = new object();
        }
    }

    private int GetStripe(TKey key) =>
        (key.GetHashCode() & 0x7FFFFFFF) % _stripeCount;

    public TValue Get(TKey key)
    {
        int stripe = GetStripe(key);
        lock (_locks[stripe])
        {
            return _buckets[stripe].GetValueOrDefault(key);
        }
    }

    public void Set(TKey key, TValue value)
    {
        int stripe = GetStripe(key);
        lock (_locks[stripe])
        {
            _buckets[stripe][key] = value;
        }
    }
}
```

| Aspect | Coarse-Grained | Fine-Grained |
|---|---|---|
| **Complexity** | Simple | Complex |
| **Contention** | High (all threads compete for one lock) | Low (threads hit different stripes) |
| **Deadlock risk** | Low | Higher (multiple locks) |
| **Throughput** | Low under load | High under load |
| **When to use** | Low contention, simple data | High contention, partitionable data |

**Interview Tip:** `ConcurrentDictionary` in .NET uses lock striping internally. Default stripe count = `Environment.ProcessorCount * 4`.

---

## 10. Reentrant Locks

A **reentrant lock** allows the same thread to acquire the lock multiple times without deadlocking itself. It maintains a count and releases only when the count drops to zero.

```csharp
// C# lock / Monitor is reentrant by default
public class ReentrantExample
{
    private readonly object _lock = new();
    private int _value;

    public void MethodA()
    {
        lock (_lock)         // acquire (count=1)
        {
            _value++;
            MethodB();       // same thread re-enters (count=2)
        }                    // release (count=1, then 0)
    }

    public void MethodB()
    {
        lock (_lock)         // same thread — doesn't deadlock!
        {
            _value *= 2;
        }
    }
}
```

### Custom Reentrant Lock with Timeout

```csharp
public class ReentrantLockWithTimeout
{
    private readonly object _lock = new();
    private int _ownerThreadId = -1;
    private int _recursionCount;

    public bool TryAcquire(TimeSpan timeout)
    {
        int currentId = Environment.CurrentManagedThreadId;

        lock (_lock)
        {
            if (_ownerThreadId == currentId)
            {
                _recursionCount++;
                return true;
            }

            DateTime deadline = DateTime.UtcNow + timeout;
            while (_ownerThreadId != -1)
            {
                var remaining = deadline - DateTime.UtcNow;
                if (remaining <= TimeSpan.Zero) return false;
                Monitor.Wait(_lock, remaining);
            }

            _ownerThreadId = currentId;
            _recursionCount = 1;
            return true;
        }
    }

    public void Release()
    {
        lock (_lock)
        {
            if (_ownerThreadId != Environment.CurrentManagedThreadId)
                throw new InvalidOperationException("Current thread does not own the lock");

            if (--_recursionCount == 0)
            {
                _ownerThreadId = -1;
                Monitor.Pulse(_lock);
            }
        }
    }
}
```

| Lock Type | Reentrant? | Notes |
|---|---|---|
| `lock` / `Monitor` | ✅ Yes | Default in C# |
| `Mutex` | ✅ Yes | Cross-process, slower |
| `SemaphoreSlim` | ❌ No | Count-based, no ownership |
| `SpinLock` | ❌ No | Lightweight, short critical sections |
| `ReaderWriterLockSlim` | ✅ Configurable | `LockRecursionPolicy.SupportsRecursion` |

---

## 11. Try-Lock

**Try-Lock** is a non-blocking attempt to acquire a lock. Instead of waiting forever (which risks deadlock), you say "try to get this lock within 100ms — if you can't, give up and I'll handle it differently." This gives you an escape hatch from situations where blocking would be dangerous.

Try-lock is particularly useful for **deadlock avoidance**. Consider the classic problem of transferring money between two accounts: you need to lock both accounts, but two concurrent transfers (A→B and B→A) can deadlock. With try-lock, if you can't get the second lock, you release the first and retry — no deadlock possible.

In C#, `Monitor.TryEnter` provides try-lock semantics. You can specify a timeout — if the lock isn't available within that time, it returns `false` instead of blocking forever.

```csharp
// Monitor.TryEnter — try-lock in C#
public class TryLockExample
{
    private readonly object _lock = new();
    private int _resource;

    public bool TryUpdate(int value, TimeSpan timeout)
    {
        bool lockTaken = false;
        try
        {
            Monitor.TryEnter(_lock, timeout, ref lockTaken);
            if (lockTaken)
            {
                _resource = value;
                return true;
            }
            else
            {
                Console.WriteLine("Could not acquire lock — skipping");
                return false;
            }
        }
        finally
        {
            if (lockTaken) Monitor.Exit(_lock);
        }
    }
}
```

### Deadlock Avoidance with Try-Lock

```csharp
// Acquire two locks without deadlocking
public bool TransferMoney(Account from, Account to, decimal amount)
{
    bool lock1 = false, lock2 = false;
    try
    {
        lock1 = Monitor.TryEnter(from.Lock, TimeSpan.FromSeconds(1));
        lock2 = Monitor.TryEnter(to.Lock, TimeSpan.FromSeconds(1));

        if (lock1 && lock2)
        {
            if (from.Balance >= amount)
            {
                from.Balance -= amount;
                to.Balance += amount;
                return true;
            }
        }
        return false;  // retry later
    }
    finally
    {
        if (lock2) Monitor.Exit(to.Lock);
        if (lock1) Monitor.Exit(from.Lock);
    }
}
```

### SpinLock — Try-Lock for Very Short Critical Sections

```csharp
private SpinLock _spinLock = new();

public void CriticalSection()
{
    bool lockTaken = false;
    try
    {
        _spinLock.Enter(ref lockTaken);  // spins in user-mode (no context switch)
        // Very short critical section only!
    }
    finally
    {
        if (lockTaken) _spinLock.Exit();
    }
}
```

**Interview Tip:** Use try-lock to avoid deadlocks in lock-ordering problems. If you can't get all needed locks, release everything and retry with backoff.

---

## 12. Compare-and-Swap (CAS)

**Compare-and-Swap (CAS)** is the fundamental building block of all lock-free programming. It's a CPU instruction (not a software construct) that performs three things atomically: read a memory location, compare it to an expected value, and if they match, write a new value. If they don't match, it means another thread modified the value between your read and your write — so you read again and retry.

Why is CAS so important? Locks are "pessimistic" — they assume contention will happen and prevent it upfront. CAS is "optimistic" — it assumes contention is rare and just retries when it does happen. Under low contention, CAS avoids the overhead of acquiring/releasing locks entirely. Under high contention, the retry loop can spin, so CAS works best when critical sections are very short.

In C#, `Interlocked.CompareExchange` provides CAS. All `Interlocked` methods (`Increment`, `Add`, `Exchange`) are built on CAS internally. Every `ConcurrentDictionary`, `ConcurrentQueue`, and other lock-free data structure uses CAS at its core.

```
CAS(location, expected, newValue):
    atomically {
        if (*location == expected) {
            *location = newValue;
            return true;   // success
        }
        return false;      // someone else changed it — retry
    }
```

### C# — `Interlocked.CompareExchange`

```csharp
// Lock-free counter using CAS
public class LockFreeCounter
{
    private int _count;

    public void Increment()
    {
        int original, updated;
        do
        {
            original = _count;                    // read current
            updated = original + 1;               // compute new value
        } while (Interlocked.CompareExchange(ref _count, updated, original) != original);
        // If _count changed between read and CAS → retry
    }

    public int Value => Volatile.Read(ref _count);
}
```

### Lock-Free Stack (Treiber Stack)

```csharp
public class LockFreeStack<T>
{
    private class Node
    {
        public T Value;
        public Node Next;
        public Node(T value) { Value = value; }
    }

    private Node _head;

    public void Push(T value)
    {
        var node = new Node(value);
        Node original;
        do
        {
            original = _head;
            node.Next = original;
        } while (Interlocked.CompareExchange(ref _head, node, original) != original);
    }

    public bool TryPop(out T value)
    {
        Node original;
        do
        {
            original = _head;
            if (original == null) { value = default; return false; }
        } while (Interlocked.CompareExchange(ref _head, original.Next, original) != original);

        value = original.Value;
        return true;
    }
}
```

### ABA Problem

The ABA problem is a subtle pitfall of CAS. Suppose Thread 1 reads a value `A`, gets preempted, and Thread 2 changes the value to `B`, then back to `A`. When Thread 1 resumes, its CAS succeeds because the value is still `A` — but the *meaning* of that `A` may have changed. For example, in a lock-free linked list, a node might have been removed and a completely different node allocated at the same memory address.

In managed languages like C#, the ABA problem is largely mitigated by garbage collection — objects aren't reused at the same memory address while any reference exists. But in unmanaged code (C/C++), it's a real danger that requires tagged pointers or hazard pointers to solve.

```
Thread 1: Reads A
Thread 2: Changes A → B → A
Thread 1: CAS succeeds (sees A) — but the state is different!
```

**Fix:** Use a version counter alongside the value, or use immutable nodes (as in managed languages like C# where GC prevents reuse).

### Interlocked Operations in C#

| Method | Description |
|---|---|
| `Interlocked.Increment(ref x)` | Atomic `x++` |
| `Interlocked.Decrement(ref x)` | Atomic `x--` |
| `Interlocked.Add(ref x, value)` | Atomic `x += value` |
| `Interlocked.Exchange(ref x, newVal)` | Atomic swap, returns old |
| `Interlocked.CompareExchange(ref x, newVal, expected)` | CAS, returns old |
| `Interlocked.Read(ref long x)` | Atomic 64-bit read on 32-bit |

---

## 13. Deadlock

A **deadlock** is the worst-case failure mode in concurrent programming: two or more threads are permanently frozen, each waiting for a resource that the other holds. No thread can make progress, and unlike a crash, the program doesn't terminate — it just hangs silently. In production, deadlocks can be incredibly hard to diagnose because the system appears to be running (CPU may be low, no errors in logs) but stops processing requests.

The classic example is two bank accounts: Thread 1 locks Account A and tries to lock Account B, while Thread 2 locks Account B and tries to lock Account A. Neither can proceed, and neither will ever release its lock.

Deadlock was formally studied by Edward Coffman Jr. in 1971, who identified four conditions that must ALL hold simultaneously for a deadlock to occur. Breaking any single condition prevents deadlock entirely.

### Four Necessary Conditions (Coffman Conditions)

| Condition | Description |
|---|---|
| **Mutual Exclusion** | Resource can't be shared |
| **Hold and Wait** | Thread holds one lock and waits for another |
| **No Preemption** | Locks can't be forcibly taken |
| **Circular Wait** | A → B → C → A cycle |

**Break ANY one condition to prevent deadlock.**

```csharp
// ❌ Classic deadlock
var lockA = new object();
var lockB = new object();

// Thread 1: locks A then B
Task.Run(() => { lock (lockA) { Thread.Sleep(100); lock (lockB) { } } });

// Thread 2: locks B then A
Task.Run(() => { lock (lockB) { Thread.Sleep(100); lock (lockA) { } } });
// DEADLOCK — both threads wait forever
```

### Prevention Strategies

```csharp
// Strategy 1: Lock ordering — always acquire in consistent order
public void Transfer(Account from, Account to, decimal amount)
{
    // Order by ID to prevent circular wait
    var first  = from.Id < to.Id ? from : to;
    var second = from.Id < to.Id ? to : from;

    lock (first.Lock)
    {
        lock (second.Lock)
        {
            from.Balance -= amount;
            to.Balance += amount;
        }
    }
}

// Strategy 2: Timeout (break "no preemption")
bool lockTaken = false;
Monitor.TryEnter(lockA, TimeSpan.FromSeconds(1), ref lockTaken);
if (!lockTaken) { /* release all locks, retry */ }

// Strategy 3: Single lock (break "hold and wait")
lock (_globalLock)
{
    // Access all resources under one lock
}
```

### Deadlock Detection in .NET

```csharp
// Using WaitHandle.WaitAll with timeout
bool acquired = WaitHandle.WaitAll(
    new WaitHandle[] { mutex1, mutex2 },
    timeout: TimeSpan.FromSeconds(10));

if (!acquired)
    Console.WriteLine("Potential deadlock detected!");
```

---

## 14. Livelock

A **livelock** is deadlock's evil twin. In a deadlock, threads are stuck doing nothing. In a livelock, threads are *actively running* but making no progress — they keep reacting to each other in a loop, like two people in a hallway who keep stepping aside to let the other pass, but always step the same way.

Livelocks often arise from well-intentioned deadlock avoidance: if two threads detect potential deadlock and "politely" release their resources and retry, they might release and retry in perfect synchronization forever. The fix is to introduce **randomness** (random backoff) to break the symmetry.

Livelocks are harder to detect than deadlocks because threads are running and consuming CPU. You'll see high CPU usage but no actual work being done. In monitoring, it looks like the system is busy but throughput is zero.

```
Analogy: Two people in a hallway keep stepping aside for each other
         — both move but neither passes.
```

```csharp
// ❌ Livelock — both threads keep yielding to each other
public class LivelockExample
{
    private bool _resourceAAvailable = true;
    private bool _resourceBAvailable = true;

    public void Thread1Work()
    {
        while (true)
        {
            lock (this)
            {
                if (_resourceAAvailable)
                {
                    _resourceAAvailable = false;

                    if (!_resourceBAvailable)
                    {
                        // "Politely" release A and retry
                        _resourceAAvailable = true;
                        continue; // LIVELOCK — keeps releasing
                    }
                    _resourceBAvailable = false;
                    break;
                }
            }
        }
    }
}
```

### Fix — Random Backoff

```csharp
// ✅ Add random jitter to break symmetry
public async Task<bool> TryAcquireBothAsync()
{
    var rng = new Random();
    for (int attempt = 0; attempt < 10; attempt++)
    {
        bool gotA = Monitor.TryEnter(_lockA, TimeSpan.FromMilliseconds(50));
        if (gotA)
        {
            bool gotB = Monitor.TryEnter(_lockB, TimeSpan.FromMilliseconds(50));
            if (gotB) return true;

            Monitor.Exit(_lockA); // release and retry
        }

        // Random backoff to break symmetry
        await Task.Delay(rng.Next(10, 100));
    }
    return false;
}
```

| | Deadlock | Livelock | Starvation |
|---|---|---|---|
| **Threads running?** | No (blocked) | Yes (spinning) | Some are |
| **Progress?** | None | None | Some threads, not others |
| **Detection** | Thread dumps | CPU at 100% | Monitoring wait times |
| **Fix** | Lock ordering, timeout | Random backoff | Fair locks, priority |

---

## 15. Signaling Pattern

The **signaling pattern** is how threads communicate "I'm done" or "you can proceed now" to other threads. Instead of threads constantly polling a variable to check if something happened (which wastes CPU), signaling lets a thread sleep efficiently and be woken up only when the event it's waiting for actually occurs.

.NET provides several signaling primitives, each designed for a specific coordination scenario:
- **ManualResetEventSlim**: A gate that opens and stays open. All waiting threads pass through. You must manually close it.
- **AutoResetEvent**: A turnstile that lets exactly one thread through per signal, then automatically closes.
- **CountdownEvent**: Waits for N signals before proceeding — perfect for "wait for all workers to finish."
- **Barrier**: Synchronizes threads at checkpoints — all threads must reach the barrier before any can proceed to the next phase.

These are more specialized than `Monitor.Wait/Pulse` and convey clearer intent in code.

Threads coordinate by **signaling** — one thread notifies another that a condition is met.

### ManualResetEvent — Gate Pattern

```csharp
// Gate: block multiple threads until initialization is complete
public class ServiceInitializer
{
    private static readonly ManualResetEventSlim _ready = new(false);

    public static void Initialize()
    {
        Task.Run(() =>
        {
            Console.WriteLine("Loading config...");
            Thread.Sleep(3000);
            Console.WriteLine("Ready!");
            _ready.Set();  // open the gate — all waiters proceed
        });
    }

    public static void WaitForReady()
    {
        _ready.Wait();  // blocks until Set() is called
    }
}
```

### CountdownEvent — Fan-Out/Fan-In

```csharp
// Wait for N tasks to complete before proceeding
var countdown = new CountdownEvent(5);

for (int i = 0; i < 5; i++)
{
    int taskId = i;
    Task.Run(() =>
    {
        Console.WriteLine($"Task {taskId} working...");
        Thread.Sleep(new Random().Next(500, 2000));
        Console.WriteLine($"Task {taskId} done");
        countdown.Signal();   // decrement count
    });
}

countdown.Wait();  // blocks until count reaches 0
Console.WriteLine("All tasks completed!");
```

### Barrier — Phased Execution

```csharp
// All threads must reach the barrier before any can proceed to next phase
var barrier = new Barrier(participantCount: 3, (b) =>
{
    Console.WriteLine($"--- Phase {b.CurrentPhaseNumber} complete ---");
});

for (int i = 0; i < 3; i++)
{
    int threadId = i;
    Task.Run(() =>
    {
        for (int phase = 0; phase < 3; phase++)
        {
            Console.WriteLine($"Thread {threadId}: Phase {phase} work");
            Thread.Sleep(new Random().Next(100, 500));
            barrier.SignalAndWait();  // wait for all participants
        }
    });
}
```

---

## 16. Thread Pool Pattern

Creating a new OS thread is expensive: it costs about 1MB of stack memory, requires kernel-mode transitions, and takes hundreds of microseconds. If your web server creates a new thread for every incoming request and handles 10,000 requests per second, that's 10,000 threads — 10GB of stack memory alone, plus catastrophic context-switching overhead.

The **thread pool pattern** solves this by maintaining a fixed set of pre-created worker threads. Work items are submitted to a queue, and idle threads pick up the next item. When a thread finishes a task, it goes back to the pool instead of being destroyed. This amortizes the thread creation cost across many tasks and keeps the thread count bounded.

In .NET, the `ThreadPool` class provides a built-in, well-tuned thread pool. You almost never need to create threads directly — `Task.Run` queues work to the ThreadPool automatically. The pool dynamically adjusts its size using a **hill-climbing algorithm**: it adds threads slowly when the queue builds up and retires them when they're idle.

A **thread pool** maintains a pool of pre-created threads that pick up work from a queue, avoiding the overhead of creating/destroying threads.

```
                    ┌──────────────────────────┐
   Task Queue       │   Thread Pool             │
  ┌─────────┐      │  ┌────┐ ┌────┐ ┌────┐    │
  │ Task 1  │──────│─►│ T1 │ │ T2 │ │ T3 │    │
  │ Task 2  │      │  └────┘ └────┘ └────┘    │
  │ Task 3  │      │  ┌────┐ ┌────┐            │
  │  ...    │      │  │ T4 │ │ T5 │            │
  └─────────┘      │  └────┘ └────┘            │
                    └──────────────────────────┘
```

### .NET ThreadPool

```csharp
// Queue work to the thread pool
ThreadPool.QueueUserWorkItem(_ =>
{
    Console.WriteLine($"Running on thread {Thread.CurrentThread.ManagedThreadId}");
});

// Configure pool size
ThreadPool.SetMinThreads(workerThreads: 4, completionPortThreads: 4);
ThreadPool.SetMaxThreads(workerThreads: 100, completionPortThreads: 100);

// Get pool info
ThreadPool.GetAvailableThreads(out int workers, out int io);
Console.WriteLine($"Available: {workers} worker, {io} I/O");
```

### Task.Run — Preferred Way

```csharp
// Task.Run queues work to ThreadPool and returns a Task
var task = Task.Run(() =>
{
    return ExpensiveComputation();
});
int result = await task;
```

### Custom Thread Pool

```csharp
public class SimpleThreadPool : IDisposable
{
    private readonly BlockingCollection<Action> _workQueue = new();
    private readonly Thread[] _threads;

    public SimpleThreadPool(int threadCount)
    {
        _threads = new Thread[threadCount];
        for (int i = 0; i < threadCount; i++)
        {
            _threads[i] = new Thread(WorkerLoop) { IsBackground = true };
            _threads[i].Start();
        }
    }

    private void WorkerLoop()
    {
        foreach (var work in _workQueue.GetConsumingEnumerable())
        {
            try { work(); }
            catch (Exception ex) { Console.WriteLine($"Error: {ex.Message}"); }
        }
    }

    public void Submit(Action work) => _workQueue.Add(work);

    public void Dispose()
    {
        _workQueue.CompleteAdding();
        foreach (var t in _threads) t.Join();
        _workQueue.Dispose();
    }
}
```

**Interview Tip:** Never create threads manually for short-lived work. Use `Task.Run` or `ThreadPool.QueueUserWorkItem`. Thread creation costs ~1MB stack + OS overhead.

---

## 17. Producer-Consumer Pattern

The **producer-consumer pattern** is one of the most widely used concurrency patterns in real-world systems. Producers generate work items (messages, tasks, data) and place them into a shared buffer. Consumers take items from the buffer and process them. The buffer acts as a **decoupling layer** — producers and consumers don't need to know about each other, and they can run at different speeds.

This pattern is everywhere: message queues (RabbitMQ, Kafka), logging systems (log events are produced by application code and consumed by a writer), web servers (requests are produced by the network layer and consumed by request handlers), and data processing pipelines.

The buffer is usually **bounded** (has a maximum capacity). When the buffer is full, producers block until consumers make room. When the buffer is empty, consumers block until producers add items. This **backpressure** mechanism prevents fast producers from overwhelming slow consumers and running the system out of memory.

Producers add items to a shared buffer. Consumers remove items. The buffer decouples them.

```
Producer 1 ──►  ┌─────────────────┐  ──► Consumer 1
Producer 2 ──►  │  Bounded Buffer  │  ──► Consumer 2
Producer 3 ──►  └─────────────────┘  ──► Consumer 3
```

### Using `BlockingCollection<T>`

```csharp
public class ProducerConsumer
{
    private readonly BlockingCollection<int> _buffer = new(boundedCapacity: 10);

    public async Task RunAsync()
    {
        // Start producers and consumers
        var producers = Enumerable.Range(1, 3).Select(id => Task.Run(() => Produce(id)));
        var consumers = Enumerable.Range(1, 2).Select(id => Task.Run(() => Consume(id)));

        await Task.WhenAll(producers);
        _buffer.CompleteAdding();   // signal no more items
        await Task.WhenAll(consumers);
    }

    private void Produce(int producerId)
    {
        for (int i = 0; i < 20; i++)
        {
            _buffer.Add(i);  // blocks if buffer is full
            Console.WriteLine($"Producer {producerId}: Added {i}");
        }
    }

    private void Consume(int consumerId)
    {
        foreach (var item in _buffer.GetConsumingEnumerable())
        {
            Console.WriteLine($"Consumer {consumerId}: Processing {item}");
            Thread.Sleep(100); // simulate work
        }
    }
}
```

### Using `Channel<T>` (Modern, High-Performance)

```csharp
public class ChannelProducerConsumer
{
    public async Task RunAsync()
    {
        var channel = Channel.CreateBounded<string>(new BoundedChannelOptions(100)
        {
            FullMode = BoundedChannelFullMode.Wait,
            SingleReader = false,
            SingleWriter = false
        });

        // Producer
        var producer = Task.Run(async () =>
        {
            for (int i = 0; i < 50; i++)
            {
                await channel.Writer.WriteAsync($"Message {i}");
            }
            channel.Writer.Complete();
        });

        // Multiple consumers
        var consumers = Enumerable.Range(1, 3).Select(id => Task.Run(async () =>
        {
            await foreach (var item in channel.Reader.ReadAllAsync())
            {
                Console.WriteLine($"Consumer {id}: {item}");
                await Task.Delay(50);
            }
        }));

        await Task.WhenAll(consumers.Append(producer));
    }
}
```

### Pipeline Pattern (Multi-Stage Producer-Consumer)

```csharp
// Stage 1: Read → Stage 2: Transform → Stage 3: Write
public async Task PipelineAsync()
{
    var stage1to2 = Channel.CreateBounded<string>(100);
    var stage2to3 = Channel.CreateBounded<string>(100);

    var reader = Task.Run(async () =>
    {
        foreach (var line in File.ReadLines("input.txt"))
            await stage1to2.Writer.WriteAsync(line);
        stage1to2.Writer.Complete();
    });

    var transformer = Task.Run(async () =>
    {
        await foreach (var line in stage1to2.Reader.ReadAllAsync())
            await stage2to3.Writer.WriteAsync(line.ToUpper());
        stage2to3.Writer.Complete();
    });

    var writer = Task.Run(async () =>
    {
        await using var sw = new StreamWriter("output.txt");
        await foreach (var line in stage2to3.Reader.ReadAllAsync())
            await sw.WriteLineAsync(line);
    });

    await Task.WhenAll(reader, transformer, writer);
}
```

---

## 18. Reader-Writer Pattern

Many data structures are read far more often than they are written. A configuration store might be read 10,000 times per second but updated once per minute. Using a regular `lock` would serialize all those reads unnecessarily — there's no reason two threads can't read the same config simultaneously.

The **reader-writer pattern** exploits this asymmetry. It allows **unlimited concurrent readers** but requires **exclusive access for writers**. When a writer wants to modify the data, it waits until all current readers finish, then blocks new readers until it's done. This gives much better throughput than a regular lock in read-heavy workloads.

.NET provides `ReaderWriterLockSlim` for this pattern. It supports three modes:
- **Read lock**: Multiple threads can hold read locks simultaneously. No writers allowed.
- **Write lock**: Only one thread can hold a write lock. No readers or other writers allowed.
- **Upgradeable read lock**: A read lock that can be upgraded to a write lock. Only one upgradeable lock at a time (to prevent deadlock during upgrade).

Multiple readers can access concurrently, but writers need exclusive access.

```
Readers:  R1 ████  R2 ████  R3 ████     (concurrent — OK)
Writer:   ░░░░░░░░░░░░░░░░░░ W1 ████    (exclusive — blocks all)
```

### `ReaderWriterLockSlim`

```csharp
public class ThreadSafeList<T>
{
    private readonly List<T> _list = new();
    private readonly ReaderWriterLockSlim _rwLock = new();

    public T Get(int index)
    {
        _rwLock.EnterReadLock();       // multiple readers allowed
        try
        {
            return _list[index];
        }
        finally
        {
            _rwLock.ExitReadLock();
        }
    }

    public IReadOnlyList<T> GetAll()
    {
        _rwLock.EnterReadLock();
        try
        {
            return _list.ToList();     // snapshot
        }
        finally
        {
            _rwLock.ExitReadLock();
        }
    }

    public void Add(T item)
    {
        _rwLock.EnterWriteLock();      // exclusive access
        try
        {
            _list.Add(item);
        }
        finally
        {
            _rwLock.ExitWriteLock();
        }
    }

    public bool Remove(T item)
    {
        _rwLock.EnterWriteLock();
        try
        {
            return _list.Remove(item);
        }
        finally
        {
            _rwLock.ExitWriteLock();
        }
    }

    // Upgradeable read — start as reader, upgrade to writer if needed
    public void AddIfNotExists(T item)
    {
        _rwLock.EnterUpgradeableReadLock();
        try
        {
            if (!_list.Contains(item))
            {
                _rwLock.EnterWriteLock();
                try
                {
                    _list.Add(item);
                }
                finally
                {
                    _rwLock.ExitWriteLock();
                }
            }
        }
        finally
        {
            _rwLock.ExitUpgradeableReadLock();
        }
    }
}
```

| Lock Mode | Concurrent Readers | Concurrent Writers | Use When |
|---|---|---|---|
| Read | ✅ Many | ❌ None | Reading shared data |
| Write | ❌ None | ❌ One only | Modifying shared data |
| Upgradeable Read | ✅ Many readers | ❌ One upgradeable | Read then maybe write |

**Interview Tip:** `ReaderWriterLockSlim` is preferred over `ReaderWriterLock` (old, slower). Use it when reads vastly outnumber writes (e.g., cache, config). If reads ≈ writes, a simple `lock` may be faster.

---

## 19. Thread-Safe Cache

A **cache** stores the results of expensive operations (database queries, API calls, computations) so they can be reused without repeating the work. In a multi-threaded application, the cache is shared across threads, which introduces two challenges:

1. **Concurrent reads and writes**: Multiple threads may try to read and update the cache simultaneously. A regular `Dictionary` is not thread-safe — concurrent modifications can corrupt its internal data structures.

2. **Thundering herd / cache stampede**: When a cache entry expires or is missing, dozens of threads might all see the miss simultaneously and all try to compute the same expensive value. You want exactly one thread to compute it while the others wait for the result.

The solution to both problems is using `ConcurrentDictionary` with `Lazy<T>`. `ConcurrentDictionary` handles safe concurrent access, and wrapping values in `Lazy<T>` ensures the factory function runs exactly once — even if 100 threads call `GetOrAdd` for the same key at the same instant.

```csharp
public class ThreadSafeCache<TKey, TValue>
{
    private readonly ConcurrentDictionary<TKey, Lazy<TValue>> _cache = new();

    // GetOrAdd with Lazy<T> ensures the factory runs EXACTLY ONCE
    // even if multiple threads call simultaneously for the same key
    public TValue GetOrAdd(TKey key, Func<TKey, TValue> factory)
    {
        var lazy = _cache.GetOrAdd(key,
            k => new Lazy<TValue>(() => factory(k), LazyThreadSafetyMode.ExecutionAndPublication));
        return lazy.Value;
    }

    public bool TryRemove(TKey key) => _cache.TryRemove(key, out _);

    public void Clear() => _cache.Clear();

    public int Count => _cache.Count;
}
```

### Cache with TTL (Time-To-Live)

```csharp
public class TtlCache<TKey, TValue>
{
    private readonly ConcurrentDictionary<TKey, CacheEntry> _cache = new();
    private readonly TimeSpan _ttl;
    private readonly Timer _cleanupTimer;

    private record CacheEntry(TValue Value, DateTime ExpiresAt);

    public TtlCache(TimeSpan ttl)
    {
        _ttl = ttl;
        _cleanupTimer = new Timer(_ => EvictExpired(), null, ttl, ttl);
    }

    public TValue GetOrAdd(TKey key, Func<TKey, TValue> factory)
    {
        if (_cache.TryGetValue(key, out var entry) && entry.ExpiresAt > DateTime.UtcNow)
            return entry.Value;

        var value = factory(key);
        _cache[key] = new CacheEntry(value, DateTime.UtcNow + _ttl);
        return value;
    }

    public bool TryGet(TKey key, out TValue value)
    {
        if (_cache.TryGetValue(key, out var entry) && entry.ExpiresAt > DateTime.UtcNow)
        {
            value = entry.Value;
            return true;
        }
        value = default;
        return false;
    }

    private void EvictExpired()
    {
        var now = DateTime.UtcNow;
        foreach (var kvp in _cache)
        {
            if (kvp.Value.ExpiresAt <= now)
                _cache.TryRemove(kvp.Key, out _);
        }
    }
}
```

### `MemoryCache` — Built-in .NET Cache

```csharp
using Microsoft.Extensions.Caching.Memory;

var cache = new MemoryCache(new MemoryCacheOptions
{
    SizeLimit = 1000
});

cache.Set("user:42", user, new MemoryCacheEntryOptions
{
    AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(30),
    SlidingExpiration = TimeSpan.FromMinutes(10),
    Size = 1,
    Priority = CacheItemPriority.Normal
});

if (cache.TryGetValue("user:42", out User cachedUser))
    Console.WriteLine(cachedUser.Name);
```

**Interview Tip:** `ConcurrentDictionary.GetOrAdd` factory can run multiple times for the same key under contention. Wrap in `Lazy<T>` to guarantee single execution.

---

## 20. Thread-Safe Blocking Queue

A **blocking queue** is the backbone of the producer-consumer pattern. Unlike a regular queue where `Dequeue` throws an exception when empty, a blocking queue makes the consumer **wait** until an item is available. Similarly, if the queue is bounded (has a maximum size), `Enqueue` makes the producer **wait** until there's room.

This is a classic interview question at companies like Google and Amazon. The implementation requires condition variables (`Monitor.Wait/PulseAll`) to efficiently coordinate between producers and consumers. The key design points are:
- Use `while` loops (not `if`) for condition checks — spurious wakeups can occur
- Use `PulseAll` instead of `Pulse` to avoid missed signals
- Provide a `CompleteAdding()` method for graceful shutdown — consumers need to know when no more items will ever arrive

In production C#, use `BlockingCollection<T>` or `Channel<T>` instead of rolling your own. But understanding the implementation is essential for interviews.

A blocking queue blocks `Dequeue` when empty and `Enqueue` when full.

### Implementation from Scratch

```csharp
public class BlockingQueue<T>
{
    private readonly Queue<T> _queue = new();
    private readonly int _capacity;
    private readonly object _lock = new();
    private bool _isCompleted;

    public BlockingQueue(int capacity) { _capacity = capacity; }

    public void Enqueue(T item)
    {
        lock (_lock)
        {
            while (_queue.Count >= _capacity)
            {
                if (_isCompleted) throw new InvalidOperationException("Queue is completed");
                Monitor.Wait(_lock);
            }

            _queue.Enqueue(item);
            Monitor.PulseAll(_lock);  // wake consumers
        }
    }

    public bool TryDequeue(out T item, TimeSpan timeout)
    {
        lock (_lock)
        {
            DateTime deadline = DateTime.UtcNow + timeout;

            while (_queue.Count == 0)
            {
                if (_isCompleted) { item = default; return false; }

                var remaining = deadline - DateTime.UtcNow;
                if (remaining <= TimeSpan.Zero) { item = default; return false; }

                Monitor.Wait(_lock, remaining);
            }

            item = _queue.Dequeue();
            Monitor.PulseAll(_lock);  // wake producers
            return true;
        }
    }

    public void CompleteAdding()
    {
        lock (_lock)
        {
            _isCompleted = true;
            Monitor.PulseAll(_lock);  // wake all waiters so they can exit
        }
    }

    public IEnumerable<T> GetConsumingEnumerable()
    {
        while (true)
        {
            if (!TryDequeue(out T item, Timeout.InfiniteTimeSpan))
                yield break;
            yield return item;
        }
    }
}
```

### Usage

```csharp
var queue = new BlockingQueue<string>(capacity: 5);

// Producer
var producer = Task.Run(() =>
{
    for (int i = 0; i < 20; i++)
    {
        queue.Enqueue($"Item {i}");
        Console.WriteLine($"Produced: Item {i}");
    }
    queue.CompleteAdding();
});

// Consumer
var consumer = Task.Run(() =>
{
    foreach (var item in queue.GetConsumingEnumerable())
    {
        Console.WriteLine($"Consumed: {item}");
        Thread.Sleep(200);
    }
});

await Task.WhenAll(producer, consumer);
```

**Interview Tip:** This is a classic interview question — "implement a thread-safe bounded queue." Key points: `while` loops for conditions (not `if`), `PulseAll` to avoid missed signals, proper `CompleteAdding` for graceful shutdown.

---

## 21. Async/Await and Task-Based Asynchronous Pattern

This is arguably the most misunderstood topic in .NET concurrency. **`async/await` is NOT multithreading.** It's a mechanism for writing non-blocking code that doesn't waste threads while waiting for I/O operations.

Here's the key insight: when you call `await httpClient.GetStringAsync(url)`, no thread is sitting around waiting for the response. The current thread is **released back to the ThreadPool** to handle other work. When the HTTP response arrives (signaled by the OS via an I/O completion port), a ThreadPool thread picks up the continuation (the code after `await`) and runs it. This is how a single web server with 12 threads can handle 10,000 concurrent HTTP requests — each request is only using a thread when it's actively computing, not while waiting for database or network responses.

`Task.Run` is different — it explicitly queues CPU-bound work to a ThreadPool thread. Use `async/await` for I/O-bound work (database, HTTP, file) and `Task.Run` for CPU-bound work (compression, encryption, computation).

### async/await Is NOT Multithreading

```csharp
// This does NOT create a new thread — it releases the current thread during I/O
public async Task<string> FetchDataAsync(string url)
{
    using var client = new HttpClient();
    string result = await client.GetStringAsync(url); // thread returned to pool during wait
    return result.ToUpper();                           // continuation runs on pool thread
}
```

### Task Combinators

```csharp
// WhenAll — wait for ALL tasks (parallel fan-out)
var results = await Task.WhenAll(
    FetchDataAsync("https://api1.example.com"),
    FetchDataAsync("https://api2.example.com"),
    FetchDataAsync("https://api3.example.com")
);

// WhenAny — wait for FIRST task (racing / timeout)
var completed = await Task.WhenAny(
    FetchDataAsync("https://api.example.com"),
    Task.Delay(TimeSpan.FromSeconds(5))
);
if (completed is Task<string> dataTask)
    Console.WriteLine(await dataTask);
else
    Console.WriteLine("Timeout!");
```

### ValueTask — Avoid Allocation When Result Is Often Cached

```csharp
public ValueTask<int> GetCachedValueAsync(string key)
{
    if (_cache.TryGetValue(key, out int cached))
        return new ValueTask<int>(cached);  // no Task allocation

    return new ValueTask<int>(LoadFromDbAsync(key));
}
```

### ConfigureAwait

```csharp
// In library code — don't capture synchronization context
var data = await httpClient.GetStringAsync(url).ConfigureAwait(false);

// In UI code (WPF/WinForms) — capture context to update UI
var data = await httpClient.GetStringAsync(url); // defaults to ConfigureAwait(true)
labelStatus.Text = data;
```

### Common Pitfalls

```csharp
// ❌ Sync-over-async — can deadlock in UI/ASP.NET
var result = GetDataAsync().Result;  // BLOCKS thread
var result = GetDataAsync().GetAwaiter().GetResult(); // also blocks

// ❌ Async void — fire-and-forget, exceptions crash the app
async void OnClick() { await DoStuff(); } // only OK for event handlers

// ✅ Always return Task/Task<T>
async Task OnClickAsync() { await DoStuff(); }
```

---

## 22. Volatile and Memory Barriers

Modern CPUs and compilers aggressively optimize code for performance. Two optimizations that matter for multithreading are:

1. **Caching**: A CPU core may read a variable once and keep using its cached copy, never seeing updates from another core.
2. **Reordering**: The compiler and CPU can reorder instructions for efficiency. `a = 1; b = 2;` might execute as `b = 2; a = 1;` if the CPU decides that's faster.

Both optimizations are invisible in single-threaded code (they preserve "as-if" semantics), but in multi-threaded code, they can cause threads to see stale or inconsistent data. A thread might loop forever checking `while (_running)` because the CPU caches `_running = true` in a register and never re-reads from memory, even though another thread set it to `false`.

**`volatile`** tells the compiler and CPU: "Don't cache this variable — always read from and write to main memory." It prevents read/write reordering across volatile accesses. However, volatile is NOT a substitute for locks — it only guarantees visibility of individual reads/writes, not atomicity of compound operations like `_counter++`.

**Memory barriers (fences)** are the low-level primitives that enforce ordering. A write-release barrier ensures all preceding writes are visible before the barrier. A read-acquire barrier ensures all subsequent reads see the latest values. `Interlocked` operations include implicit full barriers.

### The Problem — CPU Reordering and Caching

```csharp
// ❌ Without volatile, compiler/CPU may reorder or cache in register
private bool _running = true;

void WorkerThread()
{
    while (_running)  // May never see update from another thread!
    {
        DoWork();
    }
}

void StopWorker() => _running = false;
```

### `volatile` Keyword

```csharp
// ✅ volatile ensures reads/writes are not cached or reordered
private volatile bool _running = true;

void WorkerThread()
{
    while (_running)  // Always reads from memory
    {
        DoWork();
    }
}
```

### `Volatile.Read` / `Volatile.Write` — More Explicit

```csharp
private int _flag;
private int _data;

void Producer()
{
    _data = 42;                        // write data first
    Volatile.Write(ref _flag, 1);       // write-release barrier
}

void Consumer()
{
    if (Volatile.Read(ref _flag) == 1)  // read-acquire barrier
        Console.WriteLine(_data);       // guaranteed to see 42
}
```

### Memory Barrier

```csharp
// Full fence — prevents ALL reordering across this point
Thread.MemoryBarrier();

// Interlocked operations include implicit barriers
Interlocked.Increment(ref _counter); // acts as a full fence
```

| Mechanism | Prevents Reordering | Use Case |
|---|---|---|
| `volatile` | Reads not cached, writes visible | Simple flags |
| `Volatile.Read/Write` | Acquire/release semantics | Lock-free data structures |
| `Thread.MemoryBarrier()` | Full fence | Rarely needed directly |
| `Interlocked.*` | Full fence + atomicity | Counters, CAS |

---

## 23. Concurrent Collections

.NET provides a set of thread-safe collections in the `System.Collections.Concurrent` namespace. These are designed from the ground up for multi-threaded access — they use lock-free algorithms (CAS) or lock striping internally, rather than just wrapping a regular collection with a lock.

**Why not just use `lock` around a `Dictionary`?** You could, and for simple cases it works fine. But lock-based wrappers have two problems: (1) contention — every operation takes the same lock, serializing all access; (2) composition — operations like "add if not exists" require holding the lock across multiple method calls, which is error-prone.

Concurrent collections provide **atomic compound operations** like `GetOrAdd`, `AddOrUpdate`, and `TryRemove` that do the check-and-act in a single thread-safe step. This eliminates the most common source of race conditions.

| Collection | Thread-Safe Equivalent | Lock Strategy |
|---|---|---|
| `Dictionary<K,V>` | `ConcurrentDictionary<K,V>` | Lock striping |
| `Queue<T>` | `ConcurrentQueue<T>` | Lock-free (CAS) |
| `Stack<T>` | `ConcurrentStack<T>` | Lock-free (CAS) |
| `List<T>` | `ConcurrentBag<T>` | Thread-local + stealing |
| `Queue<T>` (blocking) | `BlockingCollection<T>` | Monitor-based |

```csharp
// ConcurrentDictionary — atomic compound operations
var scores = new ConcurrentDictionary<string, int>();

scores.TryAdd("Alice", 100);
scores.AddOrUpdate("Alice", 0, (key, old) => old + 10);  // atomic
int score = scores.GetOrAdd("Bob", _ => ComputeScore());  // factory may run more than once

// ConcurrentQueue — lock-free FIFO
var queue = new ConcurrentQueue<string>();
queue.Enqueue("task1");
if (queue.TryDequeue(out string item))
    Console.WriteLine(item);

// ConcurrentBag — optimized for same-thread produce/consume
var bag = new ConcurrentBag<int>();
Parallel.For(0, 100, i => bag.Add(i));
Console.WriteLine(bag.Count); // 100

// ImmutableCollections — no locks needed, structural sharing
var list = ImmutableList.Create(1, 2, 3);
var newList = list.Add(4);  // returns new list, original unchanged
```

---

## 24. Cancellation Tokens

Long-running operations need a way to be stopped gracefully. In .NET, **cancellation tokens** provide a cooperative cancellation model. "Cooperative" means the running code must voluntarily check whether cancellation has been requested and respond accordingly — nobody forcibly kills the operation from outside.

This is much safer than thread abortion (which was deprecated in .NET for good reason). Thread abortion can leave data structures in a corrupt state because the thread might be killed in the middle of a write. Cooperative cancellation lets the operation finish its current step cleanly, release resources, and exit gracefully.

The pattern involves three components:
- **`CancellationTokenSource`**: The controller that triggers cancellation (calls `Cancel()`)
- **`CancellationToken`**: A lightweight struct passed to the operation being cancelled. It checks for cancellation.
- **`OperationCanceledException`**: Thrown when cancellation is detected, signaling the caller that the operation was intentionally stopped (not an error).

```csharp
public async Task LongRunningOperationAsync(CancellationToken ct)
{
    for (int i = 0; i < 1000; i++)
    {
        ct.ThrowIfCancellationRequested();  // throws OperationCanceledException

        await Task.Delay(100, ct);           // pass token to async APIs
        Console.WriteLine($"Step {i}");
    }
}

// Usage
var cts = new CancellationTokenSource();
cts.CancelAfter(TimeSpan.FromSeconds(5));  // auto-cancel after 5s

try
{
    await LongRunningOperationAsync(cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Operation was cancelled");
}

// Linked tokens — cancel if ANY source cancels
var cts1 = new CancellationTokenSource();
var cts2 = new CancellationTokenSource();
var linked = CancellationTokenSource.CreateLinkedTokenSource(cts1.Token, cts2.Token);

// Register callback on cancellation
cts.Token.Register(() => Console.WriteLine("Cleanup on cancel"));
```

---

## 25. Thread-Local Storage

Sometimes the best way to handle shared state is to **not share it at all**. Thread-local storage gives each thread its own private copy of a variable. Since no two threads ever access the same copy, no synchronization is needed — zero locks, zero contention, zero overhead.

A common use case is `Random`: the `Random` class is not thread-safe, and wrapping it in a `lock` every time you need a random number creates a bottleneck. With `ThreadLocal<Random>`, each thread gets its own `Random` instance and can generate numbers without any coordination.

In .NET, there are three mechanisms for thread-local data, and choosing the right one depends on whether your code uses `async/await`:
- **`[ThreadStatic]`**: Simplest, but has a trap — the field initializer only runs for the first thread.
- **`ThreadLocal<T>`**: Provides a factory function that runs for each thread. Proper cleanup via `Dispose()`.
- **`AsyncLocal<T>`**: The only option that **flows across `await`**. When a continuation resumes on a different ThreadPool thread, `AsyncLocal` carries the value over. This is how `HttpContext.Current`, correlation IDs, and logging scopes work internally.

**Thread-local storage** gives each thread its own independent copy of a variable — no synchronization needed.

### `ThreadLocal<T>`

```csharp
// Each thread gets its own Random instance (Random is NOT thread-safe)
private static readonly ThreadLocal<Random> _rng = new(() =>
    new Random(Environment.CurrentManagedThreadId));

Parallel.For(0, 100, i =>
{
    int value = _rng.Value.Next(100);  // each thread uses its own Random
    Console.WriteLine($"Thread {Thread.CurrentThread.ManagedThreadId}: {value}");
});

// Dispose when done — important to avoid memory leaks
_rng.Dispose();
```

### `[ThreadStatic]` Attribute

```csharp
public class ThreadStaticExample
{
    [ThreadStatic]
    private static int _perThreadCounter;  // each thread has its own copy

    // ⚠️ WARNING: initializer runs ONLY for the first thread!
    [ThreadStatic]
    private static List<int> _perThreadList; // null for other threads!

    public static void Increment()
    {
        _perThreadList ??= new List<int>();  // must init per-thread
        _perThreadCounter++;
        _perThreadList.Add(_perThreadCounter);
    }
}
```

### `AsyncLocal<T>` — Flows Across Awaits

```csharp
// ThreadLocal does NOT flow across async/await — AsyncLocal does
private static readonly AsyncLocal<string> _correlationId = new();

public async Task HandleRequestAsync()
{
    _correlationId.Value = Guid.NewGuid().ToString();
    Console.WriteLine($"Start: {_correlationId.Value}");

    await SomeAsyncOperation();  // value flows across await

    Console.WriteLine($"End: {_correlationId.Value}");  // same value
}

// Used internally by: Activity, HttpContext.Current, logging scopes
```

| Mechanism | Flows across `await` | Initialization | Use case |
|---|---|---|---|
| `[ThreadStatic]` | ❌ | Only first thread | Simple per-thread state |
| `ThreadLocal<T>` | ❌ | Factory per thread ✅ | Per-thread expensive objects |
| `AsyncLocal<T>` | ✅ | Manual | Correlation IDs, logging context |

**Interview Tip:** `ThreadLocal<T>` doesn't flow across `await` because the continuation may run on a different thread. Use `AsyncLocal<T>` for anything that crosses async boundaries.

---

## 26. Immutability and Thread Safety

The simplest way to make something thread-safe is to make it **immutable** — if an object's state can never change after construction, any number of threads can read it concurrently without risk. There's nothing to synchronize because there are no writes.

This is a powerful insight: instead of carefully locking around mutable state, you can often redesign your data to be immutable and eliminate entire categories of concurrency bugs. The cost is that "modifying" an immutable object means creating a new one with the changed values, which can be expensive for large objects. However, immutable collections use **structural sharing** — when you add an element to an immutable list, the new list shares most of its internal nodes with the old one, so the copy is much cheaper than you'd expect.

.NET embraces immutability through several features:
- **`record` types** (C# 9+): Value equality and `with` expressions for non-destructive mutation
- **`System.Collections.Immutable`**: Immutable lists, dictionaries, sets with structural sharing
- **`System.Collections.Frozen`** (.NET 8+): Extremely fast read-optimized collections for data that never changes after creation
- **`readonly` structs and `init` properties**: Compile-time enforcement of immutability

Immutable objects are inherently thread-safe — no locks needed because state never changes.

### Immutable Class

```csharp
public class ImmutablePoint
{
    public int X { get; }
    public int Y { get; }

    public ImmutablePoint(int x, int y) { X = x; Y = y; }

    // "Mutation" returns a new object
    public ImmutablePoint WithX(int x) => new(x, Y);
    public ImmutablePoint WithY(int y) => new(X, y);
}

// Safe to share across threads without locks
var point = new ImmutablePoint(1, 2);
// Multiple threads can read point.X, point.Y concurrently
```

### Records — Built-in Immutability

```csharp
public record Config(string ConnectionString, int Timeout, bool EnableCache);

var config = new Config("Server=db", 30, true);
var updated = config with { Timeout = 60 };  // new object
// Original 'config' is unchanged — safe to read from any thread
```

### Immutable Collections

```csharp
using System.Collections.Immutable;

// Each operation returns a NEW collection
var list = ImmutableList.Create(1, 2, 3);
var newList = list.Add(4);         // list is unchanged
var dict = ImmutableDictionary<string, int>.Empty
    .Add("a", 1)
    .Add("b", 2);

// Builder pattern for batch modifications
var builder = ImmutableList.CreateBuilder<int>();
for (int i = 0; i < 1000; i++)
    builder.Add(i);
ImmutableList<int> result = builder.ToImmutable();
```

### Frozen Collections (.NET 8+) — Read-Optimized

```csharp
using System.Collections.Frozen;

// Create once, read many times — faster reads than Immutable*
var lookup = new Dictionary<string, int>
{
    ["alice"] = 1,
    ["bob"] = 2
}.ToFrozenDictionary();

int value = lookup["alice"];  // optimized for read-heavy, multi-threaded access
```

### Atomic Reference Swap with Immutable Objects

```csharp
// Lock-free updates using Interlocked + immutable objects
private ImmutableList<string> _items = ImmutableList<string>.Empty;

public void AddItem(string item)
{
    ImmutableList<string> original, updated;
    do
    {
        original = _items;
        updated = original.Add(item);
    } while (Interlocked.CompareExchange(ref _items, updated, original) != original);
}
```

| Approach | Thread-safe | Perf (reads) | Perf (writes) | Use case |
|---|---|---|---|---|
| `lock` + `List<T>` | ✅ | Blocked | Blocked | General purpose |
| `ConcurrentBag<T>` | ✅ | Good | Good | Frequent add/remove |
| `ImmutableList<T>` | ✅ | Good | Slower (copy) | Snapshot semantics |
| `FrozenDictionary` | ✅ | Fastest | ❌ (no mutation) | Static lookup tables |

---

## 27. Parallel Programming (PLINQ & Parallel Class)

When you have a CPU-bound operation that needs to process a large collection of data, you can split the work across multiple cores to get a near-linear speedup. .NET provides two high-level APIs for this: **PLINQ** and the **`Parallel` class**.

**PLINQ** (Parallel LINQ) lets you add `.AsParallel()` to any LINQ query and the runtime automatically partitions the data, processes chunks on different threads, and merges the results. It's the easiest way to parallelize data processing — often a one-line change. However, not all queries benefit: if the per-element work is trivial, the overhead of partitioning and merging can outweigh the parallelism benefit.

The **`Parallel` class** provides `Parallel.For`, `Parallel.ForEach`, and `Parallel.Invoke` for more explicit parallel loops. It gives you more control than PLINQ: you can set the degree of parallelism, use thread-local accumulators (to avoid contention on a shared result variable), and handle cancellation.

A critical rule: **never use `Parallel.ForEach` for I/O-bound work** (HTTP calls, database queries). It wastes ThreadPool threads by blocking them during I/O waits. Use `Parallel.ForEachAsync` (.NET 6+) or `Task.WhenAll` with `async/await` for I/O.

### PLINQ — Parallel LINQ

```csharp
var numbers = Enumerable.Range(1, 10_000_000);

// Parallel query — splits data across cores
var results = numbers
    .AsParallel()
    .WithDegreeOfParallelism(Environment.ProcessorCount)
    .Where(n => IsPrime(n))
    .OrderBy(n => n)  // ⚠️ ordering adds overhead
    .ToList();

// AsOrdered() preserves input order (slower)
var ordered = numbers.AsParallel().AsOrdered()
    .Select(n => n * 2)
    .ToList();

// ForAll — parallel side-effects (unordered)
numbers.AsParallel().Where(n => n % 2 == 0).ForAll(n =>
{
    ProcessItem(n);  // runs in parallel, no result collection
});

// Aggregate with thread-local accumulator
long sum = numbers.AsParallel().Aggregate(
    seed: 0L,                               // initial value per partition
    func: (subtotal, item) => subtotal + item, // partition accumulator
    resultSelector: total => total              // final selector
);
```

### `Parallel.ForEach` / `Parallel.For`

```csharp
var items = GetLargeDataSet();

// Basic parallel loop
Parallel.ForEach(items, item =>
{
    ProcessItem(item);  // CPU-bound work
});

// With options
Parallel.ForEach(items,
    new ParallelOptions
    {
        MaxDegreeOfParallelism = 4,
        CancellationToken = cts.Token
    },
    item => ProcessItem(item)
);

// With thread-local state (avoid contention)
long totalSize = 0;
Parallel.ForEach(files,
    localInit: () => 0L,                           // init per-thread accumulator
    body: (file, state, localSum) =>
    {
        long size = new FileInfo(file).Length;
        return localSum + size;                     // thread-local add
    },
    localFinally: localSum =>
    {
        Interlocked.Add(ref totalSize, localSum);   // merge at end
    }
);
```

### `Parallel.Invoke` — Fire Multiple Actions

```csharp
Parallel.Invoke(
    () => DownloadFile("file1.zip"),
    () => DownloadFile("file2.zip"),
    () => DownloadFile("file3.zip")
);
```

### `Parallel.ForEachAsync` (.NET 6+)

```csharp
// Async-friendly parallel loop
await Parallel.ForEachAsync(
    urls,
    new ParallelOptions { MaxDegreeOfParallelism = 10 },
    async (url, ct) =>
    {
        var content = await httpClient.GetStringAsync(url, ct);
        ProcessContent(content);
    }
);
```

**Interview Tip:** PLINQ and `Parallel.*` are for **CPU-bound** work. For **I/O-bound** work, use `Task.WhenAll` with `async/await`. Using `Parallel.ForEach` for I/O wastes ThreadPool threads.

---

## 28. Async Streams (IAsyncEnumerable)

`IAsyncEnumerable<T>` (introduced in C# 8) combines two concepts: **async/await** and **iterators** (`yield return`). It lets you produce and consume a sequence of items where each item may require an asynchronous operation to produce.

This is essential for streaming scenarios: reading rows from a database cursor, consuming messages from a message queue, tailing a log file, or receiving real-time data from an API. Without async streams, you'd either have to load everything into memory first (bad for large datasets) or write complex callback-based code.

With `await foreach`, the consumer naturally applies backpressure — the producer only generates the next item when the consumer is ready. This prevents unbounded buffering and memory exhaustion.

Process data as it arrives, asynchronously, without buffering everything in memory.

```csharp
// Producer — yields items asynchronously
public async IAsyncEnumerable<StockPrice> StreamPricesAsync(
    string symbol,
    [EnumeratorCancellation] CancellationToken ct = default)
{
    while (!ct.IsCancellationRequested)
    {
        var price = await FetchPriceAsync(symbol, ct);
        yield return price;
        await Task.Delay(1000, ct);  // poll every second
    }
}

// Consumer — processes items as they arrive
await foreach (var price in StreamPricesAsync("GOOG").WithCancellation(cts.Token))
{
    Console.WriteLine($"{price.Symbol}: ${price.Value}");
    if (price.Value > 200) break;  // can break early
}
```

### LINQ Over Async Streams (System.Linq.Async)

```csharp
// Requires NuGet: System.Linq.Async
var expensiveStocks = StreamPricesAsync("GOOG")
    .Where(p => p.Value > 150)
    .Take(10)
    .Select(p => $"{p.Symbol}: ${p.Value}");

await foreach (var s in expensiveStocks)
    Console.WriteLine(s);
```

### Channel-Backed Async Stream

```csharp
public ChannelReader<LogEntry> TailLogAsync(string path, CancellationToken ct)
{
    var channel = Channel.CreateUnbounded<LogEntry>();

    _ = Task.Run(async () =>
    {
        using var reader = new StreamReader(new FileStream(path, FileMode.Open,
            FileAccess.Read, FileShare.ReadWrite));
        reader.BaseStream.Seek(0, SeekOrigin.End);

        while (!ct.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(ct);
            if (line != null)
                await channel.Writer.WriteAsync(new LogEntry(line), ct);
            else
                await Task.Delay(100, ct);
        }
        channel.Writer.Complete();
    }, ct);

    return channel.Reader;
}

// Consume
await foreach (var entry in TailLogAsync("app.log", cts.Token).ReadAllAsync())
    Console.WriteLine(entry);
```

---

## 29. Thread Starvation and ThreadPool Tuning

**Thread starvation** is one of the most common production issues in .NET applications, and it's almost always caused by the same mistake: **synchronously blocking on async code** (calling `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()`).

Here's how it happens: the .NET ThreadPool has a limited number of threads (starts at `Environment.ProcessorCount`). When a thread calls `.Result` on an async method, it blocks — it can't do anything else until the result arrives. But the async method's continuation needs a ThreadPool thread to run. If all pool threads are blocked on `.Result`, there are no threads left to run continuations — and those continuations are what would unblock the waiting threads. **Complete deadlock.**

The ThreadPool's hill-climbing algorithm makes this worse: it detects high queue depth and slowly injects new threads (~1-2 per second), but if you're blocking hundreds of threads, it can take minutes to recover. Meanwhile, all requests time out.

The fix is simple in concept but often hard in practice: **go async all the way** — from the controller action down to the database call, every layer must use `await` instead of `.Result`. There should be no synchronous blocking anywhere in the request pipeline.

### What Is Thread Starvation?

The ThreadPool runs out of available threads because existing threads are **blocked** (not awaiting). New work items pile up in the queue.

```csharp
// ❌ Causes starvation — all pool threads blocked on .Result
var tasks = Enumerable.Range(0, 1000).Select(_ => Task.Run(() =>
{
    var result = SomeAsyncMethod().Result;  // BLOCKS a pool thread
}));
Task.WaitAll(tasks.ToArray());
// ThreadPool tries to inject new threads slowly (1-2/sec) — too slow

// ✅ Fix — async all the way
var tasks = Enumerable.Range(0, 1000).Select(_ => Task.Run(async () =>
{
    var result = await SomeAsyncMethod();  // releases thread during wait
}));
await Task.WhenAll(tasks);
```

### Symptoms

- Response times increase suddenly
- `ThreadPool.GetAvailableThreads` returns 0 workers
- Thread count climbs steadily (hill-climbing injects ~1-2/sec)
- CPU is low but app is unresponsive

### Diagnostics

```csharp
// Monitor thread pool health
ThreadPool.GetAvailableThreads(out int workers, out int io);
ThreadPool.GetMaxThreads(out int maxWorkers, out int maxIo);
ThreadPool.GetMinThreads(out int minWorkers, out int minIo);

Console.WriteLine($"Workers: {maxWorkers - workers}/{maxWorkers} in use");
Console.WriteLine($"IO: {maxIo - io}/{maxIo} in use");

// Quick fix (NOT a real solution — just buys time)
ThreadPool.SetMinThreads(200, 200);
```

### ThreadPool Hill-Climbing Algorithm

```
Min threads (default = core count)
    ↓
[Request burst] → queue builds up → inject 1 thread / 500ms
    ↓
Slowly ramps to handle load → stabilizes
    ↓
[Load drops] → threads idle → retire threads over time
```

**Interview Tip:** The #1 cause of thread starvation in .NET is **sync-over-async** (`.Result`, `.Wait()`, `.GetAwaiter().GetResult()` on hot paths). The fix is always: make the call chain fully async.

---

## 30. Context Switching and False Sharing

These are two performance-level concerns that you won't encounter in everyday coding but are critical for high-performance systems and commonly asked in senior-level interviews.

### Context Switching

**Context switching** is the cost of pausing one thread and resuming another. The OS must save all the state of the current thread (CPU registers, program counter, stack pointer) and load the saved state of the next thread. This takes 1-10 microseconds — insignificant for a single switch, but devastating at scale.

If you have 1,000 threads on a 4-core machine, the OS spends most of its time switching between threads rather than doing useful work. This is why the rule of thumb for CPU-bound work is to use only as many threads as there are cores. Context switching is also why `SpinLock` exists — for very short critical sections, spinning in user mode is cheaper than blocking (which would trigger two context switches: one to sleep and one to wake up).

When the OS switches the CPU from one thread to another:

1. Save current thread's registers, stack pointer, PC → thread control block
2. Load next thread's state
3. Flush CPU pipeline
4. (Cross-process) Flush TLB, switch page tables

| Type | Cost | Involves |
|---|---|---|
| Thread → Thread (same process) | ~1-10 µs | Register save/restore, scheduler |
| Process → Process | ~10-100 µs | + TLB flush, page table switch |
| User → Kernel mode | ~0.5-1 µs | Syscall/interrupt |

```csharp
// Too many threads = excessive context switching
// Rule of thumb: threads ≈ core count for CPU-bound work
var options = new ParallelOptions
{
    MaxDegreeOfParallelism = Environment.ProcessorCount
};
```

### False Sharing

**False sharing** is a subtle hardware-level performance killer. Modern CPUs don't read memory one byte at a time — they read entire **cache lines** (typically 64 bytes). When a CPU core writes to any byte in a cache line, it **invalidates** that cache line on all other cores, forcing them to re-fetch the entire line from main memory.

False sharing occurs when two threads modify **different variables** that happen to reside on the **same cache line**. Neither thread is actually sharing data with the other, but the CPU's cache coherence protocol treats them as if they are, causing the cache line to bounce between cores on every write. This can make parallel code 10-100x slower than expected.

The fix is **padding** — adding unused bytes between variables so they land on separate cache lines. In C#, you can use `StructLayout` with explicit field offsets to control memory layout.

When threads modify **different variables** that happen to be on the **same CPU cache line** (typically 64 bytes), the cache line bounces between cores — massive slowdown.

```csharp
// ❌ False sharing — counters are adjacent in memory (same cache line)
public class FalseSharingBad
{
    private int _counter1;  // same 64-byte cache line
    private int _counter2;  // as _counter1!

    public void IncrementCounter1() => Interlocked.Increment(ref _counter1);
    public void IncrementCounter2() => Interlocked.Increment(ref _counter2);
}

// ✅ Fix — pad to separate cache lines
[StructLayout(LayoutKind.Explicit, Size = 128)]
public struct PaddedCounter
{
    [FieldOffset(0)]  public int Value;
    // [FieldOffset(64)] would be next cache line
}

// Or use separate arrays with padding
public class FalseSharingFixed
{
    // Each counter on its own cache line
    [StructLayout(LayoutKind.Explicit, Size = 128)]
    private struct PaddedInt
    {
        [FieldOffset(0)] public int Value;
    }

    private PaddedInt _counter1;
    private PaddedInt _counter2;

    public void IncrementCounter1() => Interlocked.Increment(ref _counter1.Value);
    public void IncrementCounter2() => Interlocked.Increment(ref _counter2.Value);
}
```

### Performance Impact

```
False sharing:    Thread 1 writes _counter1
                  → Invalidates cache line on Core 2
                  → Core 2 must re-fetch from L3/main memory
                  → 10-100x slower than L1 cache hit

No false sharing: Each counter on its own cache line
                  → Each core works from its own L1 cache
                  → Full speed
```

**Interview Tip:** False sharing is a common cause of "my parallel code is slower than sequential." It's particularly insidious because the code looks correct — it's a hardware-level issue.

---

## 31. Lock-Free and Wait-Free Algorithms

Traditional lock-based concurrency has a fundamental problem: if a thread holding a lock gets preempted by the OS (context-switched out), **all other threads waiting for that lock are blocked**, even though they could theoretically make progress. Lock-free and wait-free algorithms eliminate this problem by using atomic operations (CAS) instead of locks.

Understanding the hierarchy of progress guarantees is important:
- **Blocking**: A thread can be blocked indefinitely (regular locks). If the lock holder crashes, everyone is stuck.
- **Lock-free**: At least one thread always makes progress, even if others are delayed. CAS-retry loops are lock-free — if your CAS fails, it means another thread succeeded.
- **Wait-free**: Every thread completes in a bounded number of steps, regardless of what other threads are doing. This is the strongest guarantee and hardest to achieve.

In practice, lock-free algorithms are sufficient for most high-performance needs. Wait-free algorithms are rare and complex — they're used in hard real-time systems where latency bounds are critical.

A word of caution: lock-free programming is notoriously difficult to get right. Even published academic papers have had bugs. In .NET, prefer the built-in concurrent collections (`ConcurrentQueue`, `ConcurrentStack`) which are already lock-free and battle-tested.

### Definitions

| Guarantee | Definition |
|---|---|
| **Blocking** | Threads can stall indefinitely (locks) |
| **Lock-free** | At least ONE thread makes progress in bounded steps |
| **Wait-free** | EVERY thread makes progress in bounded steps |
| **Obstruction-free** | A thread makes progress if run in isolation |

```
Wait-free ⊂ Lock-free ⊂ Obstruction-free ⊂ Non-blocking
```

### Lock-Free Counter (CAS Loop)

```csharp
public class LockFreeCounter
{
    private long _count;

    public void Increment()
    {
        long original, updated;
        do
        {
            original = Interlocked.Read(ref _count);
            updated = original + 1;
        } while (Interlocked.CompareExchange(ref _count, updated, original) != original);
        // Lock-free: if CAS fails, another thread succeeded → progress
    }

    public long Value => Interlocked.Read(ref _count);
}
```

### Wait-Free Read, Lock-Free Write

```csharp
// Copy-on-write: reads are wait-free, writes are lock-free
public class CopyOnWriteList<T>
{
    private volatile ImmutableList<T> _list = ImmutableList<T>.Empty;

    // Wait-free read — just returns the current reference
    public ImmutableList<T> Snapshot => _list;

    // Lock-free write — CAS loop
    public void Add(T item)
    {
        ImmutableList<T> original, updated;
        do
        {
            original = _list;
            updated = original.Add(item);
        } while (Interlocked.CompareExchange(ref _list, updated, original) != original);
    }
}
```

### When to Use Lock-Free vs Locks

| Criteria | Use Locks | Use Lock-Free |
|---|---|---|
| Complexity | Prefer (simpler) | When perf demands it |
| Critical section length | Long operations | Very short operations |
| Thread count | Low-moderate | Very high contention |
| Priority inversion | Possible | Avoided |
| Correctness | Easier to reason about | Very hard to get right |

**Interview Tip:** In practice, prefer `Interlocked.*` and `ConcurrentDictionary` over hand-rolled lock-free algorithms. Lock-free code is extremely hard to verify — even experts get it wrong.

---

## 32. Priority Inversion

**Priority inversion** occurs when a high-priority thread is blocked waiting for a lock held by a low-priority thread, while a medium-priority thread preempts the low-priority one.

```
Time →
High:   ████░░░░░░░░░░░░░████████   (blocked waiting for lock)
Medium: ░░░░████████████████░░░░░░░  (runs freely, preempts Low)
Low:    ████░░░░░░░░░░░░░░░░████░░   (holds lock, can't run because Medium preempts)

Result: High waits for Low, but Low can't run because Medium runs.
         High is effectively at Medium's mercy = PRIORITY INVERSION
```

### Real-World Example: Mars Pathfinder (1997)

The Mars Pathfinder rover experienced priority inversion causing system resets. A low-priority meteorological task held a shared mutex, blocking the high-priority bus task, while medium-priority tasks ran freely.

### Solutions

| Solution | How It Works |
|---|---|
| **Priority Inheritance** | Low-priority thread temporarily gets High's priority while holding the lock |
| **Priority Ceiling** | Lock has a ceiling priority — any thread holding it runs at that priority |
| **Lock-free algorithms** | No locks → no inversion |
| **Avoid shared resources** | Message passing, immutable data |

```csharp
// .NET doesn't have built-in priority inheritance, but you can avoid the issue:

// Strategy 1: Don't mix thread priorities (default for .NET)
// All ThreadPool threads run at Normal priority

// Strategy 2: Use lock-free operations
Interlocked.Increment(ref _counter);  // no lock to cause inversion

// Strategy 3: Keep critical sections extremely short
lock (_lock)
{
    _value = newValue;  // single assignment — held for nanoseconds
}

// Strategy 4: Use async instead of blocking
await semaphore.WaitAsync();  // doesn't block a thread
```

---

## 33. Fork-Join Pattern

The **fork-join pattern** is the parallel equivalent of divide-and-conquer. You split a big problem into smaller independent sub-problems (fork), solve each sub-problem in parallel, and combine their results (join). This is the most natural way to express parallelism for problems that can be decomposed.

In everyday .NET code, the most common form of fork-join is starting multiple async operations with `Task.WhenAll` — for example, loading a dashboard page by fetching user profile, recent orders, and notifications in parallel, then combining them into a single view model.

For CPU-bound work, recursive fork-join (like parallel merge sort) is powerful but requires care: you need a **depth limit** to stop forking below a certain problem size. Without it, you create thousands of tiny tasks whose scheduling overhead exceeds the actual computation.

Split (fork) work into subtasks, execute in parallel, then combine (join) results. This is the foundation of divide-and-conquer parallelism.

```
        ┌── Task A ──┐
Fork ───┤── Task B ──├─── Join → Result
        └── Task C ──┘
```

### Using `Task.WhenAll`

```csharp
public async Task<DashboardData> LoadDashboardAsync(int userId)
{
    // Fork — start all independent tasks
    var profileTask = GetProfileAsync(userId);
    var ordersTask = GetRecentOrdersAsync(userId);
    var statsTask = GetUserStatsAsync(userId);
    var notificationsTask = GetNotificationsAsync(userId);

    // Join — wait for all
    await Task.WhenAll(profileTask, ordersTask, statsTask, notificationsTask);

    // Combine
    return new DashboardData
    {
        Profile = profileTask.Result,
        Orders = ordersTask.Result,
        Stats = statsTask.Result,
        Notifications = notificationsTask.Result
    };
}
```

### Recursive Fork-Join (Parallel Merge Sort)

```csharp
public static int[] ParallelMergeSort(int[] arr, int depthLimit = 4)
{
    if (arr.Length <= 1) return arr;

    int mid = arr.Length / 2;
    var left = arr[..mid];
    var right = arr[mid..];

    if (depthLimit > 0)
    {
        // Fork
        var leftTask = Task.Run(() => ParallelMergeSort(left, depthLimit - 1));
        var rightTask = Task.Run(() => ParallelMergeSort(right, depthLimit - 1));

        // Join
        Task.WaitAll(leftTask, rightTask);
        return Merge(leftTask.Result, rightTask.Result);
    }
    else
    {
        // Below depth limit — run sequentially to avoid overhead
        return Merge(ParallelMergeSort(left, 0), ParallelMergeSort(right, 0));
    }
}

private static int[] Merge(int[] left, int[] right)
{
    var result = new int[left.Length + right.Length];
    int i = 0, j = 0, k = 0;

    while (i < left.Length && j < right.Length)
        result[k++] = left[i] <= right[j] ? left[i++] : right[j++];
    while (i < left.Length) result[k++] = left[i++];
    while (j < right.Length) result[k++] = right[j++];

    return result;
}
```

### Map-Reduce with PLINQ

```csharp
// Word count across files — map-reduce style
var wordCounts = Directory.GetFiles("docs", "*.txt")
    .AsParallel()
    .SelectMany(file => File.ReadAllText(file).Split(' '))  // MAP
    .GroupBy(word => word.ToLower())                         // SHUFFLE
    .ToDictionary(g => g.Key, g => g.Count());              // REDUCE
```

**Interview Tip:** Always set a depth limit for recursive fork-join. Without it, you create thousands of tasks for small subarrays — the task overhead dwarfs the computation.

---

## 34. Timers in .NET

.NET has five different timer classes, and choosing the wrong one is a common source of bugs. The most dangerous issue is **reentrancy**: with `System.Threading.Timer` and `System.Timers.Timer`, the callback fires on a ThreadPool thread. If the callback takes longer than the timer interval, the next tick fires while the previous one is still running, leading to overlapping executions and potential data corruption.

The modern solution is `PeriodicTimer` (.NET 6+), which is designed for async code and is inherently non-reentrant: the next tick only fires after you've processed the current one (because you `await` the next tick). For background services in ASP.NET Core, `PeriodicTimer` inside a `BackgroundService` is the recommended pattern.

For UI applications, always use the UI-thread timers (`System.Windows.Forms.Timer` or `DispatcherTimer`) because they fire on the UI thread, making it safe to update controls without `Invoke`/`Dispatcher.Invoke`.

| Timer | Thread | Reentrant | Async-Safe | Best For |
|---|---|---|---|---|
| `System.Threading.Timer` | ThreadPool | ⚠️ Yes | ❌ | Background services |
| `System.Timers.Timer` | ThreadPool | ⚠️ Yes | ❌ | Server-side periodic tasks |
| `PeriodicTimer` (.NET 6+) | Caller (async) | ❌ No | ✅ | Modern async loops |
| `System.Windows.Forms.Timer` | UI thread | ❌ No | ❌ | WinForms UI updates |
| `DispatcherTimer` | UI thread | ❌ No | ❌ | WPF UI updates |

### `PeriodicTimer` — Modern, Async-Safe (Preferred)

```csharp
public class HealthCheckService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(30));

        while (await timer.WaitForNextTickAsync(ct))
        {
            // Guaranteed non-reentrant — next tick waits for this to finish
            await CheckHealthAsync(ct);
        }
    }
}
```

### `System.Threading.Timer` — Reentrant Danger

```csharp
// ⚠️ Callback fires on ThreadPool — can overlap if slow!
var timer = new Timer(
    callback: _ => Console.WriteLine($"Tick at {DateTime.Now}"),
    state: null,
    dueTime: TimeSpan.Zero,           // start immediately
    period: TimeSpan.FromSeconds(1)   // repeat every 1s
);

// Prevent reentrancy manually
var reentrancyGuard = 0;
var safeTimer = new Timer(_ =>
{
    if (Interlocked.CompareExchange(ref reentrancyGuard, 1, 0) != 0)
        return;  // previous tick still running
    try
    {
        SlowWork();
    }
    finally
    {
        Interlocked.Exchange(ref reentrancyGuard, 0);
    }
}, null, TimeSpan.Zero, TimeSpan.FromSeconds(1));
```

**Interview Tip:** Classic mistake — `System.Threading.Timer` callbacks fire on ThreadPool threads and CAN overlap. Use `PeriodicTimer` in modern .NET to avoid reentrancy bugs.

---

## 35. Interview Questions

### Conceptual Questions

**Q1: What happens if you call `Task.Run` inside an ASP.NET request?**
> It queues work to the ThreadPool, consuming an extra thread. In ASP.NET, the request thread is already a pool thread, so you're burning two threads for one request. Only use `Task.Run` for CPU-bound work. For I/O, use `async/await` directly.

**Q2: What is thread starvation?**
> When the ThreadPool is exhausted — all threads are blocked (e.g., sync-over-async `.Result` calls), and new work items queue up indefinitely. Symptoms: increasing response times, timeouts. Fix: use async all the way down.

**Q3: Can you `lock` on a value type?**
> No. `lock` requires a reference type. `lock(42)` boxes the int, creating a new object each time — no mutual exclusion. Always lock on a dedicated `object` instance.

**Q4: Why is `lock(this)` bad?**
> External code can also lock on your instance: `lock(myObj)` — causing unexpected deadlocks. Always lock on a `private readonly object`.

```csharp
// ❌ Bad
public class BadLock
{
    public void DoWork() { lock (this) { } }
}

// ❌ Bad — string interning means different code may lock on same object
lock ("myLock") { }

// ❌ Bad — Type objects are shared
lock (typeof(MyClass)) { }

// ✅ Good
private readonly object _lock = new();
public void DoWork() { lock (_lock) { } }
```

**Q5: Difference between `Task.Run` and `Task.Factory.StartNew`?**
> `Task.Run` is a shorthand for `Task.Factory.StartNew` with safe defaults (`TaskScheduler.Default`, `DenyChildAttach`). `StartNew` has pitfalls: it doesn't unwrap `Task<Task>`, and uses the current scheduler by default (which may be a UI scheduler). **Always prefer `Task.Run`** unless you need `LongRunning`.

---

### Tricky Coding Questions

**Q6: What's wrong with this code?**

```csharp
// ❌ Bug — closures capture the variable, not the value
for (int i = 0; i < 10; i++)
{
    Task.Run(() => Console.WriteLine(i));
}
// Prints "10" ten times (or random values near 10)

// ✅ Fix — capture a local copy
for (int i = 0; i < 10; i++)
{
    int local = i;
    Task.Run(() => Console.WriteLine(local));
}
```

**Q7: Implement a thread-safe lazy initialization without `Lazy<T>`.**

```csharp
public class DoubleCheckedLocking<T> where T : class, new()
{
    private volatile T _instance;
    private readonly object _lock = new();

    public T Instance
    {
        get
        {
            if (_instance == null)          // first check (no lock)
            {
                lock (_lock)
                {
                    if (_instance == null)  // second check (with lock)
                        _instance = new T();
                }
            }
            return _instance;
        }
    }
}
```

**Q8: What's the output? Why?**

```csharp
async Task Main()
{
    Console.WriteLine("1");
    var task = DelayedPrint();
    Console.WriteLine("3");
    await task;
    Console.WriteLine("5");
}

async Task DelayedPrint()
{
    Console.WriteLine("2");
    await Task.Delay(100);
    Console.WriteLine("4");
}

// Output: 1, 2, 3, 4, 5
// "2" prints before "3" because async methods run synchronously until the first await
```

**Q9: Implement a read-write lock from scratch using Monitor.**

```csharp
public class ReadWriteLock
{
    private int _readers;
    private bool _writing;
    private readonly object _lock = new();

    public void EnterRead()
    {
        lock (_lock)
        {
            while (_writing)
                Monitor.Wait(_lock);
            _readers++;
        }
    }

    public void ExitRead()
    {
        lock (_lock)
        {
            _readers--;
            if (_readers == 0)
                Monitor.PulseAll(_lock);
        }
    }

    public void EnterWrite()
    {
        lock (_lock)
        {
            while (_writing || _readers > 0)
                Monitor.Wait(_lock);
            _writing = true;
        }
    }

    public void ExitWrite()
    {
        lock (_lock)
        {
            _writing = false;
            Monitor.PulseAll(_lock);
        }
    }
}
```

**Q10: Dining Philosophers — solve without deadlock.**

```csharp
public class DiningPhilosophers
{
    private readonly SemaphoreSlim[] _forks;
    private readonly int _count;

    public DiningPhilosophers(int count)
    {
        _count = count;
        _forks = Enumerable.Range(0, count)
            .Select(_ => new SemaphoreSlim(1, 1)).ToArray();
    }

    public async Task PhilosopherAsync(int id)
    {
        int left = id;
        int right = (id + 1) % _count;

        // Resource ordering — always pick lower-numbered fork first
        int first = Math.Min(left, right);
        int second = Math.Max(left, right);

        for (int meal = 0; meal < 3; meal++)
        {
            Console.WriteLine($"Philosopher {id}: Thinking...");
            await Task.Delay(new Random().Next(100, 500));

            await _forks[first].WaitAsync();
            await _forks[second].WaitAsync();

            Console.WriteLine($"Philosopher {id}: Eating (meal {meal + 1})");
            await Task.Delay(new Random().Next(100, 300));

            _forks[second].Release();
            _forks[first].Release();
        }
    }
}
```

**Q11: Implement `async/await`-based rate limiter.**

```csharp
public class AsyncRateLimiter
{
    private readonly SemaphoreSlim _semaphore;
    private readonly TimeSpan _interval;
    private readonly ConcurrentQueue<DateTime> _timestamps = new();

    public AsyncRateLimiter(int maxRequests, TimeSpan interval)
    {
        _semaphore = new SemaphoreSlim(maxRequests, maxRequests);
        _interval = interval;
    }

    public async Task<T> ThrottleAsync<T>(Func<Task<T>> action)
    {
        await _semaphore.WaitAsync();
        try
        {
            return await action();
        }
        finally
        {
            _ = ReleaseAfterDelay();
        }
    }

    private async Task ReleaseAfterDelay()
    {
        await Task.Delay(_interval);
        _semaphore.Release();
    }
}

// Usage: max 5 requests per second
var limiter = new AsyncRateLimiter(5, TimeSpan.FromSeconds(1));
var result = await limiter.ThrottleAsync(() => httpClient.GetStringAsync(url));
```

**Q12: What is the difference between `SemaphoreSlim` and `Semaphore`?**

| | `SemaphoreSlim` | `Semaphore` |
|---|---|---|
| Scope | In-process only | Cross-process (named) |
| Performance | Fast (user-mode) | Slow (kernel object) |
| Async support | ✅ `WaitAsync()` | ❌ |
| Use when | In-app throttling | Cross-process coordination |

**Q13: How does `CancellationToken` work internally?**
> `CancellationTokenSource` holds a flag. `CancellationToken` is a struct that reads from the same source. `Cancel()` sets the flag and invokes registered callbacks. `ThrowIfCancellationRequested()` checks the flag and throws `OperationCanceledException`. It's a cooperative model — code must check the token.

---

## Quick Reference Cheat Sheet

```
Synchronization Primitives:
  lock / Monitor            → In-process mutual exclusion (reentrant)
  Mutex                     → Cross-process mutual exclusion
  SemaphoreSlim             → Limit N concurrent accessors (in-process)
  ReaderWriterLockSlim      → Many readers OR one writer
  SpinLock                  → User-mode spin for very short critical sections

Signaling:
  ManualResetEventSlim      → Gate — open/close for all threads
  AutoResetEvent            → Turnstile — releases one thread per Set()
  CountdownEvent            → Wait for N signals
  Barrier                   → Sync threads at phase boundaries

Atomic / Lock-Free:
  Interlocked               → Lock-free atomic operations (CAS)
  volatile                  → Prevent caching/reordering of field
  Volatile.Read/Write       → Acquire/release memory barriers

Collections:
  ConcurrentDictionary      → Thread-safe dictionary (lock striping)
  ConcurrentQueue/Stack     → Lock-free FIFO/LIFO
  BlockingCollection        → Blocking producer-consumer wrapper
  Channel<T>                → High-perf async producer-consumer
  ImmutableList/Dict        → Copy-on-write, inherently thread-safe
  FrozenDictionary          → Read-optimized immutable (.NET 8+)

Async / Task:
  Task.Run                  → Queue CPU work to ThreadPool
  async/await               → Cooperative async I/O (not threading!)
  ValueTask<T>              → Avoid allocation for cached results
  IAsyncEnumerable<T>       → Async streaming / iteration
  CancellationToken         → Cooperative cancellation
  PeriodicTimer             → Non-reentrant async timer (.NET 6+)

Thread-Local:
  [ThreadStatic]            → Per-thread static field (no init propagation)
  ThreadLocal<T>            → Per-thread with factory (doesn't flow async)
  AsyncLocal<T>             → Flows across await (correlation IDs, context)

Parallelism:
  Parallel.ForEach          → Data parallelism across cores
  Parallel.ForEachAsync     → Async-friendly parallel loop (.NET 6+)
  PLINQ (.AsParallel())     → Parallel LINQ queries
  Task.WhenAll              → Fork-join for async tasks

Problems:
  Race condition            → Non-atomic read-modify-write
  Deadlock                  → Circular wait on locks
  Livelock                  → Threads run but make no progress
  Starvation                → Thread never gets CPU/lock
  Priority inversion        → High blocked by low via medium
  False sharing             → Cache line contention (hardware)
```
