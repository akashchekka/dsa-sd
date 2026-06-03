# LRU Cache

Classic O(1) Least-Recently-Used cache. The "interview chestnut" — get/put both in constant time, evict the stalest entry when full.

## Run

```pwsh
cd machine-coding-py
python -m lru_cache
```

## What's implemented

```
dict[K, Node]          → O(1) key lookup
doubly linked list     → O(1) move-to-front + O(1) evict-tail
sentinel head & tail   → no null checks on edges
```

Two implementations:

- **`LruCache`** — single-threaded, the textbook version.
- **`ConcurrentLruCache`** — decorator wrapping `LruCache` with a lock for multi-threaded use.

## File layout

```
lru_cache/
├── __main__.py                       # demo: capacity 3, force one eviction
├── models/
│   └── lru_node.py                   # LruNode[K, V] — key, value, prev, next
├── interfaces/
│   └── cache.py                      # ICache[K, V] — get, put, remove, count
└── services/
    ├── lru_cache.py                  # LruCache — single-threaded reference impl
    └── concurrent_lru_cache.py       # ConcurrentLruCache — RLock wrapper
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Why doubly linked list?** | Removing arbitrary nodes in O(1) requires `prev` pointer | Singly linked = O(n) to find predecessor |
| **Sentinel head/tail** | Dummy nodes at both ends | Eliminates `if node is head/tail` checks everywhere |
| **Generic over K, V** | `TypeVar("K", bound=Hashable)`, `TypeVar("V")` | Same class works for `Cache[str, int]`, `Cache[UUID, bytes]`, etc. |
| **Interface separation** | `ICache` is the contract; two impls satisfy it | Caller depends on `ICache`, swap thread-safe variant in prod |
| **Capacity validation** | `capacity > 0` at construction | Fail-fast on misconfiguration |
| **Miss returns `None`** | `Optional[V]` | Pythonic; distinguishes "not present" from a stored `None`-ish value |

## How it works (put path)

```
put(key, value):
  if key in map:
    update node.value
    move node to head
  else:
    create node
    map[key] = node
    add to head
    if size > capacity:
      evict tail.prev
      del map[evicted.key]
```

All steps are O(1).

## Thread-safety

`LruCache` is **not** thread-safe. Concurrent `put` calls can corrupt the linked list. Wrap with `ConcurrentLruCache` for multi-threaded access. The wrapper uses a single `RLock` — fine for moderate contention; under heavy load, consider segmented/striped caching.

## How to extend

| Add… | Change |
|---|---|
| **TTL expiry** | Add `expires_at` to `LruNode`, check in `get` |
| **LFU (least-frequently-used)** | New `LfuCache(ICache)` with frequency buckets |
| **Write-through** | Decorator that calls a backing store before `put` returns |
| **Stats** | Counters around `get` (hit/miss) |
| **Bounded by memory not count** | Per-entry size hint + running total |

## Edge cases handled

- Update of existing key reuses the node (no allocation).
- Eviction at exactly capacity boundary.
- Remove of non-existent key returns `False`, no exception.

## Out of scope

- Persistence.
- Multi-process / distributed (would need Redis or similar).
- Async-friendly (`async def get`) — straightforward extension.
