# Thread Pool

A fixed-size pool of worker threads that execute submitted tasks, returning a `Future` for each result. Interview-scoped (~45 min): the core mechanics without production overhead.

## Run

```pwsh
cd machine-coding-py/thread_pool
python __main__.py
```

## Problem

Creating a thread per task is expensive and unbounded — a burst of work spawns a thread per item, exhausting memory and thrashing the scheduler. A thread pool creates a fixed set of workers once and feeds them tasks through a shared queue. This caps concurrency and amortizes thread-creation cost.

## Design

```
submit(fn, *args) -> Future
       |
       v
  [task queue]  --->  worker-0  }
                      worker-1  }  each idle worker pulls a task,
                      worker-2  }  runs it, stores result on the Future
```

Components:

- `Future` (`models/future.py`) — a handle to a not-yet-computed result. `result()` blocks on a `threading.Event` until a worker calls `set_result` / `set_exception`. Exceptions raised by the task are re-raised to the caller.
- `ThreadPool` (`services/thread_pool.py`) — owns the task queue and N daemon worker threads. Each worker loops: pull `(future, fn, args, kwargs)`, run it, publish the outcome on the future. A failing task is captured on its future and never kills the worker.

## Key decisions

- **`queue.Queue`** for the task buffer — thread-safe and blocking, so workers wait for work without busy-spinning. `maxsize` gives optional backpressure.
- **Sentinel shutdown** — `shutdown()` enqueues one sentinel per worker. Because the queue is FIFO, all previously submitted tasks run before the sentinels are reached, giving a graceful drain. `wait=True` joins the workers.
- **Futures over callbacks** — the caller decides when to block (`result()`), and exceptions propagate naturally.
- **Daemon threads + context manager** — `with ThreadPool(...) as pool:` guarantees shutdown on exit.

## Deliberately out of scope

Kept out to fit the time box; each is a good follow-up discussion:

- Cancellation / timeouts per task, and `Future` states (pending/running/cancelled).
- Dynamic pool sizing, idle-worker reaping, work-stealing queues.
- `ProcessPoolExecutor`-style CPU parallelism (Python's GIL limits threads to I/O-bound speedups).
- Callbacks (`add_done_callback`) and `map` / `as_completed` helpers.
