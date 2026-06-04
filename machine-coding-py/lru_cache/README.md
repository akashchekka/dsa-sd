# LRU Cache

Classic O(1) Least-Recently-Used cache. The "interview chestnut" — get/put both in constant time, evict the stalest entry when full.

## Run

```pwsh
cd machine-coding-py
python -m lru_cache
```

## The subject

**Problem.** Memory is finite. You can keep only the most useful subset of recently used data in fast storage (RAM, CPU cache, browser cache, DNS cache). When the cache fills up, you must evict something — but *what*? LRU says: **evict whatever was used least recently**, on the bet that recently-used items are more likely to be needed again (temporal locality).

**Why it's *the* interview chestnut.** It looks like a data-structures puzzle but is really a composition problem:

- **Two requirements** that pull in opposite directions: O(1) key lookup (→ hash table) and O(1) ordering by recency (→ linked list). Neither structure alone solves both.
- **The trick** is recognizing you need *both* simultaneously, with the hash table's values being **pointers into** the linked list. Most candidates try to do it with one structure and end up O(n) somewhere.
- **Doubly-linked, not singly-linked** — because evicting a known node requires updating its predecessor, and walking to find the predecessor is O(n).
- **Sentinel nodes** — a dummy head and tail eliminate every `if node is None` edge case. Subtle but separates clean code from buggy code.
- **Generic + thread-safe** as natural follow-ups. The interview always escalates to "make it work for any key/value type" and "make it safe under concurrent access."

**Where LRU lives in the real world.** Redis `maxmemory-policy allkeys-lru`, browser HTTP cache, Linux page cache, CPU L1/L2/L3 caches, `functools.lru_cache` in Python, in-memory app caches (e.g., session stores).

**Core mental model.**
```
hash map → O(1) "is this key here? give me the node"
DLL      → O(1) "move this node to front" / "drop the tail"
together → O(1) get + O(1) put
```

**Core concepts exercised.** Composite data structures (hash + DLL), sentinel pattern, generics (`TypeVar`), interface segregation (`ICache`), decorator pattern (concurrent wrapper), capacity invariants, temporal locality.

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
