# Restaurant

A small **restaurant management system**. Tables place orders (each with one or more menu items); a fixed pool of cook threads cooks the highest-priority order first, then serves it and prints the bill. VIP orders always jump ahead of NORMAL ones.

## Run

```pwsh
cd machine-coding-py/restaurant
python __main__.py
```

## Problem

Orders arrive faster than the kitchen can cook them, and not every order is equal — a VIP or urgent order should be prepared before regular ones. A plain FIFO queue can't express that. We need a thread-safe queue that hands out the highest-priority order next and lets idle cooks wait without busy-spinning, all while tracking each order's lifecycle and bill.

## Design

```
place_order(table, [items], priority)
       |
       v
  [PriorityQueue]  --->  cook-1  }  each idle cook pulls the highest-priority
   (min-heap by         cook-2  }  order, cooks it (PLACED -> COOKING -> READY),
    priority)                       then serves it (-> SERVED) and bills the table
```

Components:

- `Menu` / `MenuItem` (`models/menu.py`) — the priced dishes the restaurant offers; `place_order` looks items up by name.
- `Order` / `Priority` / `OrderStatus` (`models/order.py`) — an order has an id, a table, a list of `MenuItem`s, a priority (`VIP = 0`, `NORMAL = 1`), and a status (`PLACED -> COOKING -> READY -> SERVED`). `total()` sums the bill.
- `CustomPriorityQueue` (`queues/priority_queue.py`) — a hand-rolled thread-safe blocking priority queue built on `heapq` and a `threading.Condition`. `get()` blocks while empty; `close()` wakes blocked cooks so they exit.
- `StdlibPriorityQueue` (`queues/stdlib_priority_queue.py`) — the same `put` / `get` / `close` interface backed by `queue.PriorityQueue`. Shows the batteries-included equivalent; `close()` uses a self-propagating sentinel for graceful shutdown.
- `Restaurant` (`services/restaurant.py`) — owns the menu, the queue, and N cook threads. Accepts either queue implementation via `order_queue=`. `place_order()` is the producer; each cook is a consumer that cooks, serves, and bills.

## Key decisions

- **`heapq` min-heap** — `get()` always returns the lowest priority value, so VIP orders are served before NORMAL ones.
- **`(priority, seq, item)` tuples** — a monotonic counter breaks ties so equal-priority orders keep FIFO order, and `Order` objects are never compared directly.
- **`threading.Condition`** — cooks `wait()` while the queue is empty (no busy-waiting) and are woken by `notify()` on each new order.
- **Unique order ids under a lock** — `place_order` hands out ids from a shared counter guarded by a lock, so concurrent callers never collide.
- **Graceful shutdown** — `close()` sets a flag and `notify_all()`s; blocked `get()` calls return `None`, which each cook treats as the signal to stop after the queue is drained.
