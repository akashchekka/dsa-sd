# Rate Limiter

Four classic rate-limiting algorithms behind a common interface, keyed per-user (or per-API-key).

## Run

```pwsh
cd machine-coding-py/rate_limiter
python .\__main__.py
```

## The subject

**Problem.** Servers have finite capacity. A single misbehaving client (or attacker) can overwhelm a service with requests, denying service to everyone else. A **rate limiter** decides per request: *should we allow this, or reject it with HTTP 429?* — answering in microseconds, for millions of clients.

**Why it's a classic interview problem.** It seems mechanical but is actually a deep trade-off study:

- **No single "right" algorithm.** Token bucket, leaky bucket, fixed window, sliding window — each has different burst tolerance, memory cost, and accuracy at boundaries.
- **Boundary problem of fixed windows.** A "100 req/min" fixed-window limiter allows 200 requests in 2 seconds: 100 at the end of one minute, 100 at the start of the next. Sliding window fixes this — at the cost of memory.
- **Bursting vs. smoothing.** Token bucket allows controlled bursts (good for human users); leaky bucket smooths to a constant rate (good for downstream protection).
- **State per key.** Millions of users × per-user state = a memory and concurrency problem.
- **Distributed coordination** is the natural escalation: rate limits must hold across N servers.
- **Time is the central dependency.** Every algorithm computes "how much time has passed since X?"

**Core mental model.**
```
allow(key)? → look up per-key state → consult the clock → update state → decide
```

## What's implemented

| Algorithm | Shape | Burst behaviour | Memory | Accuracy at boundary |
|---|---|---|---|---|
| **Token Bucket** | Bucket fills at rate R, request takes 1 token | Allows bursts up to bucket capacity | O(1) per key | High |
| **Leaky Bucket** | Bucket drains at rate R, request adds 1 unit | No bursts above capacity; constant outflow | O(1) per key | High |
| **Fixed Window** | Counter resets every N seconds | Can allow ~2× limit at window boundary | O(1) per key | Coarse |
| **Sliding Window (Log)** | Deque of request timestamps in last N seconds | Exact rolling-window count | O(limit) per key | Most accurate |

All four implement the same `RateLimiter.allow_request(user_id) → bool` interface.

## Design patterns

| Pattern | Where | Why it works |
|---|---|---|
| **Strategy** | `RateLimiter` → Token / Leaky / Fixed / Sliding | All four algorithms share `allow_request()`, so the caller switches limiting policy without any code change — the interface hides very different internal state. |
| **Factory** | `RateLimiterFactory.create(type, ...)` | Centralizes selecting and wiring the right limiter from an enum, keeping the `if/else` on limiter type out of client code. |

---

## 1. Token Bucket

### Mental model
Imagine a **bucket that holds tokens**. The bucket refills at a constant rate (e.g., 2 tokens/sec) up to a maximum capacity. Each incoming request **consumes 1 token**. If the bucket has a token, the request is allowed; otherwise it's rejected.

```
        refill rate = 2 tokens/sec
              │
              ▼
       ┌────────────┐
       │ ●●●●●●     │  capacity = 10, current tokens = 6
       └─────┬──────┘
             │ request → consume 1 token → allowed
             ▼
```

### Behaviour
- **Allows bursts**: if the bucket is full, 10 requests can fire back-to-back instantly.
- **Long-term rate** converges to the refill rate.
- **Idle clients accumulate budget** (up to capacity).

### Example
`capacity=10, refill_rate=2/sec`. After 5 seconds of silence, the bucket is full (10 tokens).

| Time | Request | Tokens before | Tokens after | Verdict |
|---|---|---|---|---|
| t=0.0 | R1  | 10  | 9   | ALLOWED |
| t=0.0 | R2  | 9   | 8   | ALLOWED |
| ...  | ... | ... | ... | ... |
| t=0.0 | R10 | 1   | 0   | ALLOWED |
| t=0.0 | R11 | 0   | 0   | BLOCKED |
| t=0.5 | R12 | 1.0 | 0.0 | ALLOWED *(refilled 1 token in 0.5s)* |

### When to use
Public APIs where you want to **tolerate user bursts** (e.g., Stripe: "100 req/min, okay if 30 arrive at once").

---

## 2. Leaky Bucket

### Mental model
Imagine a **bucket with a hole at the bottom**. Water (requests) flows in from the top. Water leaks out at a constant rate. If the bucket overflows, the request is rejected.

```
       request ──► drip
                    │
              ┌─────▼──────┐
              │ ░░░░       │  capacity = 10, current water = 4
              │            │
              └─────┬──────┘
                    │  leak rate = 2 units/sec
                    ▼
```

### Behaviour
- **No bursting above capacity.** If 11 requests arrive simultaneously into a capacity-10 bucket, the 11th is rejected.
- **Outflow is smooth** (constant rate). Downstream sees a steady stream — protects fragile backends.
- Conceptually dual to token bucket: TB tracks *budget*, LB tracks *backlog*.

### Example
`capacity=10, leak_rate=2/sec`. Bucket starts empty.

| Time | Request | Water before | Water after | Verdict |
|---|---|---|---|---|
| t=0.0 | R1  | 0  | 1  | ALLOWED |
| t=0.0 | R2  | 1  | 2  | ALLOWED |
| ...  | ... | ... | ... | ... |
| t=0.0 | R10 | 9  | 10 | ALLOWED |
| t=0.0 | R11 | 10 | 10 | BLOCKED *(overflow)* |
| t=0.5 | R12 | 9.0 | 10.0 | ALLOWED *(leaked 1 unit in 0.5s)* |

### When to use
- **Traffic shaping** in front of a fragile downstream (DB writes, payment gateway).
- When you need to **enforce a strict max sustained rate** with bounded queue depth.

### Token Bucket vs. Leaky Bucket (the classic confusion)

| | Token Bucket | Leaky Bucket |
|---|---|---|
| What's in the bucket? | Tokens (budget) | Water (pending work) |
| Idle behaviour | Bucket fills up | Bucket drains to empty |
| Burst on full bucket? | **Yes** — fire instantly | **No** — burst beyond capacity is rejected |
| Output shape | Bursty when budget exists | Always smooth |
| Used by | API gateways (AWS, Stripe) | Network routers, traffic shaping |

---

## 3. Fixed Window

### Mental model
Divide time into **fixed buckets** of `W` seconds (e.g., aligned to clock minutes). Each bucket has a counter. Each request increments the counter for the current bucket. If the counter exceeds `limit`, reject.

```
   window: [00:00 ─ 00:60) [01:00 ─ 02:00) [02:00 ─ 03:00) ...
   counter:      87                34                0
                 ^ limit = 100
```

### Behaviour
- **Trivial to implement**: just `(current_window, count)` per key.
- **Boundary problem**: with `limit=100, window=60s`, a client can fire 100 requests at `t=59.999` and another 100 at `t=60.001` → **200 requests in 2ms**, double the intended rate.

### Example
`limit=10, window=60s`. Window resets at every minute boundary.

| Time | Window | Count before | Count after | Verdict |
|---|---|---|---|---|
| 12:00:05 | [12:00, 12:01) | 0  | 1  | ALLOWED |
| ...      | [12:00, 12:01) | ... | ... | ... |
| 12:00:30 | [12:00, 12:01) | 9  | 10 | ALLOWED |
| 12:00:31 | [12:00, 12:01) | 10 | 10 | BLOCKED |
| 12:01:00 | [12:01, 12:02) | 0  | 1  | ALLOWED *(reset)* |

### When to use
Coarse throttling where exact precision doesn't matter (e.g., "roughly 1000 req/min per IP"). Cheapest and simplest.

---

## 4. Sliding Window (Log)

### Mental model
For each key, keep a **deque of timestamps** of the most recent allowed requests. On each request, **evict timestamps older than W seconds**, then check `len(deque) < limit`.

```
   window = last 60 seconds, limit = 10
   deque: [t-58s, t-45s, t-30s, t-22s, t-10s, t-3s, t-1s]
           ↑ evicted on next call when it falls out of window
```

### Behaviour
- **Exact**: enforces "at most `limit` requests in any rolling W-second interval" — no boundary cheat.
- **O(limit) memory** per key (stores up to `limit` timestamps).
- More expensive than the others; use when correctness matters (e.g., login attempts, anti-abuse).

### Example
`limit=5, window=60s`.

| Time | Timestamps in window before | Action | Verdict |
|---|---|---|---|
| 12:00:00 | [] | append, len=1 | ALLOWED |
| 12:00:10 | [00] | append, len=2 | ALLOWED |
| 12:00:20 | [00, 10] | append, len=3 | ALLOWED |
| 12:00:30 | [00, 10, 20] | append, len=4 | ALLOWED |
| 12:00:40 | [00, 10, 20, 30] | append, len=5 | ALLOWED |
| 12:00:50 | [00, 10, 20, 30, 40] | len ≥ 5 | **BLOCKED** |
| 12:01:01 | evict 00 → [10, 20, 30, 40], append | ALLOWED |

Compare with fixed window: at the boundary, a fixed-window limiter would allow `limit` fresh requests *plus* the ones already counted in the previous window — sliding window correctly rejects until old entries truly age out.

### When to use
- **Login attempts / brute-force protection.**
- **Anti-abuse limits** where the boundary doubling of fixed window is unacceptable.

---

Are you doing security/quota enforcement
(login attempts, OTP, daily quota)?
   │
   ├── YES → SLIDING WINDOW (exact count, no bursts, audit trail)
   │
   └── NO → Is the protected resource fragile / bursty-sensitive
            (DB writes, payment gateway, email, downstream API)?
              │
              ├── YES → LEAKY BUCKET (smooth outflow, traffic shaping)
              │
              └── NO → Are real users bursty by nature
                       (dashboards, multi-tab apps, API consumers)?
                         │
                         ├── YES → TOKEN BUCKET (allow bursts, scale)
                         │
                         └── NO  → FIXED WINDOW (cheapest, "good enough")

---

## File layout

```
rate_limiter/
├── __main__.py                                  # demo: bursts against all 4 limiters
├── enums/
│   └── rate_limiter_type.py                     # RateLimiterType enum
├── factories/
│   └── rate_limiter_factory.py                  # builds limiters from type + kwargs
├── interfaces/
│   └── rate_limiter.py                          # RateLimiter.allow_request(user_id)
├── models/
│   ├── token_bucket.py
│   ├── leaky_bucket.py
│   ├── fixed_window.py
│   └── sliding_window.py
└── strategies/
    ├── token_bucket_rate_limiter.py
    ├── leaky_bucket_rate_limiter.py
    ├── fixed_window_rate_limiter.py
    └── sliding_window_rate_limiter.py
```

## Factory usage

```python
from factories.rate_limiter_factory import RateLimiterFactory
from enums.rate_limiter_type import RateLimiterType

# With defaults (100 req/60s):
limiter = RateLimiterFactory.create(RateLimiterType.TOKEN_BUCKET)

# With custom parameters via **kwargs:
limiter = RateLimiterFactory.create(
    RateLimiterType.TOKEN_BUCKET,
    capacity=10,
    refill_rate=2.0,
)

limiter = RateLimiterFactory.create(
    RateLimiterType.LEAKY_BUCKET,
    capacity=10,
    leak_rate=2.0,
)

limiter = RateLimiterFactory.create(
    RateLimiterType.FIXED_WINDOW,
    limit=10,
    window_size_seconds=60,
)

limiter = RateLimiterFactory.create(
    RateLimiterType.SLIDING_WINDOW,
    limit=10,
    window_size_seconds=60,
)

allowed = limiter.allow_request("user-123")
```

## Trade-offs at a glance

| Concern | Token Bucket | Leaky Bucket | Fixed Window | Sliding Window |
|---|---|---|---|---|
| Allows bursts | yes (up to capacity) | no | at boundary only | no |
| Smooth outflow | no | yes | no | no |
| Memory per key | O(1) | O(1) | O(1) | O(limit) |
| Boundary accuracy | high | high | **low (2× spike)** | **exact** |
| Implementation cost | low | low | very low | medium |

## Thread-safety

All limiters use:
- A `Lock` around the per-key state map for safe lazy initialization (double-checked locking).
- A per-key `Lock` on each bucket/window for the critical section of `allow_request`.

## How to extend

| Add… | Change |
|---|---|
| **Distributed (Redis)** | New `RedisTokenBucketRateLimiter` using `INCR` + `EXPIRE` or a Lua script |
| **Tiered limits** (per-user + per-endpoint) | Compose limiters; allow only if all return `True` |
| **Retry-after header** | Return `(allowed, retry_after_seconds)` instead of `bool` |
| **Injected clock** | Replace `time.time()` with an `IClock` for deterministic testing |

## Out of scope

- Distributed coordination across multiple processes.
- Persistence — buckets reset on process restart.
- Eviction of idle keys — the per-user maps grow unbounded.
