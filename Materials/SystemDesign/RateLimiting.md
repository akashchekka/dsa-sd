---
title: Distributed Rate Limiter System Design
description: Interview notes on designing a distributed rate limiter, covering algorithms, atomic Redis checks, token leasing, hot keys, failure handling, multi-region limits, and Redis Cluster resharding
---

## Requirements

### Functional requirements

* Limit how many requests a client can make in a time period, for example 100
  requests per minute per user.
* Limits apply to different keys: user ID, API key, IP address, or a
  combination like "user + endpoint".
* Different rules for different endpoints and plans. A free plan gets 100 per
  minute, and a paid plan gets 10,000.
* When a client goes over the limit, reject with **HTTP 429 Too Many Requests**
  and tell them when to retry.
* Rules can change without redeploying.

### Non-functional requirements

* **Very low added latency:** It runs in front of every request, so it should
  add about 1 ms at most.
* **Highly available:** If the rate limiter breaks, it must not take the
  product down.
* **Global limits across many servers:** 100 per minute total, not 100 per
  server.
* **Approximately accurate is fine:** Letting 102 through instead of 100 is
  acceptable. Wrongly blocking good users is worse.

> [!IMPORTANT]
> Say this early: "The limiter runs on every request, so it must be fast and
> must never become the reason the product is down. I'll trade a little
> accuracy for speed and availability."

## Rough estimates

Assumptions: 100M users, 1M requests per second at peak, about 2 rules per
user.

| What                       | Calculation                | Result                           |
|----------------------------|----------------------------|----------------------------------|
| Limit checks per second    | 1 per request              | **1M/sec**                       |
| Active counters            | 100M users x 2 rules       | 200M keys                        |
| Memory per counter         | key + 2 numbers + overhead | ~100 bytes                       |
| Total memory               | 200M x 100 bytes           | **~20 GB**                       |
| Store nodes for throughput | 1M / ~100k ops per node    | **~10 nodes, ~30 with replicas** |

The data is small and fits in memory. The challenge is **1M very fast checks
per second**, done correctly across many servers.

## Where the rate limiter lives

```text
 Clients
    |
    v
 CDN / edge firewall        <- layer 1: per-IP limits, blocks attacks (DDoS)
    |
    v
 API gateway                <- layer 2: per-user / per-API-key limits (main design)
    |  "allowed?" ---> Rate limit store (Redis Cluster)
    v
 Services                   <- layer 3: protect expensive resources
                               (e.g. "max 5 report exports per hour per tenant")
```

| Option                                   | Pros                                             | Cons                                       |
|------------------------------------------|--------------------------------------------------|--------------------------------------------|
| In the client                            | No server cost                                   | **Can't be trusted.** Clients can bypass it. |
| In the API gateway                       | One place for all services, blocks traffic early | The gateway must know all rules            |
| Inside each service (library or sidecar) | Can use business context                         | Every team must adopt it                   |

Choice: the API gateway for general limits, plus a shared library for services
that need special limits. Both use the same store and rule format.

## Choosing the algorithm

| Algorithm                  | How it works                                                              | Pros                                   | Cons                                                          |
|----------------------------|---------------------------------------------------------------------------|----------------------------------------|---------------------------------------------------------------|
| **Fixed window**           | Count requests per clock minute, reset at :00                             | Simplest, one counter                  | Burst at the edge: 100 at 0:59 and 100 at 1:00 is 200 in 2 sec |
| **Sliding log**            | Store a timestamp per request, count those in the last 60 sec             | Exact                                  | Memory heavy: one entry per request                           |
| **Sliding window counter** | Current minute's count + previous minute's count x overlap fraction       | Smooth, only 2 counters                | Slight approximation                                          |
| **Token bucket**           | Bucket refills at a steady rate, each request takes a token, empty = reject | Allows short bursts, only 2 numbers  | Needs careful refill math                                     |
| **Leaky bucket**           | Requests enter a queue that drains at a fixed rate                        | Perfectly smooth output                | Adds waiting, bursts get delayed                              |

### Sliding window counter example

Limit 100 per minute. It's 15 seconds into the current minute. The previous
minute had 80 requests, and the current minute has 30.

```text
estimate = 30 + 80 x (45/60) = 30 + 60 = 90   -> under 100, allow
```

### Choice: token bucket

Real users are bursty (opening an app fires 10 calls at once). A token bucket
allows short bursts while enforcing the average rate, and it needs only two
values per key: tokens left and last refill time. The sliding window counter is
an equally good choice when the requirement is strictly "N per minute".

Capacity 10, refill of 1 token per second:

```text
time 0s:   tokens = 10. Burst of 10 requests -> all allowed, tokens = 0
time 0.5s: request -> tokens = 0 + 0.5 refill = 0.5 -> REJECT
time 3s:   tokens = 0 + 3 = 3 -> request allowed, tokens = 2
```

Refill is calculated lazily when a request arrives:
`tokens = min(capacity, tokens + elapsed x rate)`. No background timer is
needed.

## The distributed problem: keeping counts correct

With one server, the counter lives in memory. With 100 gateway servers, a
user's requests land on different servers, so the count must be shared.

### Option A: each server limits locally (limit / N)

* With 100 servers and a limit of 1,000, each server allows 10.
* Load isn't spread evenly, and N changes as servers scale. A user hitting one
  server gets blocked at 10 while others sit idle.
* Too inaccurate on its own, but useful as a fallback.

### Option B: a central shared store (main design)

All servers check and update the counter in **Redis**, sharded by key.

### The race condition

```text
Tokens left for user 42 = 1

Server A: read tokens -> 1          Server B: read tokens -> 1
Server A: 1 > 0, allow, write 0     Server B: 1 > 0, allow, write 0
Result: 2 requests allowed with only 1 token
```

"Read, then decide, then write" across the network isn't safe. **Make the whole
check one atomic operation inside Redis** with a small Lua script. Redis runs
each script start to finish without interruption.

```lua
-- KEYS[1] = "rl:{user42}:api"   ARGV = capacity, refill_per_sec
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])
local t        = redis.call('TIME')
local now      = t[1] + t[2] / 1e6           -- use Redis clock, not app server clocks

local b       = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens  = tonumber(b[1]) or capacity
local ts      = tonumber(b[2]) or now

tokens = math.min(capacity, tokens + (now - ts) * rate)
local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end

redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', KEYS[1], math.ceil(capacity / rate) * 2)  -- idle keys clean themselves up
return {allowed, tokens}
```

Points to call out:

* One network round trip per check, about 0.5 to 1 ms in the same datacenter.
* Use the Redis clock, not the app server's. App server clocks drift, which
  breaks the refill math.
* Every key has an expiry, so inactive users don't hold memory forever.
* For a fixed or sliding window, `INCR` plus `EXPIRE` is already atomic.

### Sharding the store

* Use **Redis Cluster**, which spreads keys across nodes by hashing the key.
* All data for one rate-limit key lives on one node, so the script stays
  atomic.
* Each shard has a replica in another zone for failover.
* Losing a few counts during failover is fine. At worst a user gets a few extra
  requests for a few seconds.

## Rules and configuration

Rules live in a config service (a small database with an admin UI), not in
code.

```yaml
- name: free-plan-api
  match: { plan: free, endpoint: "/api/*" }
  key: user_id
  algorithm: token_bucket
  capacity: 20
  refill_per_sec: 1.67        # ~100 per minute
- name: login-attempts
  match: { endpoint: "/login" }
  key: ip
  limit: 5 per minute
  on_store_failure: fail_closed
```

* Gateways cache rules in memory and receive pushed updates when rules change.
  Never fetch rules per request.
* A request may match several rules (per IP, per user, per endpoint). Reject if
  any rule says no.
* **Shadow mode:** A new rule first only logs what it would block. Turn it on
  for real once the numbers look right. This prevents an outage from a bad
  rule.

## What the client sees

```text
HTTP 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1696320060
Retry-After: 12
```

* Clients retry after the given time, with exponential backoff and random
  jitter, so they don't all retry at the same moment.
* Rejected requests are usually dropped. Background jobs that must eventually
  run go into a queue and are processed at the allowed rate (leaky bucket
  style).

## The hard problems

### 1. Latency: avoid a network call on every request

At very high volume, even 1 ms per request adds up. Gateways can hold some
state locally. There are two different techniques, and they behave very
differently.

#### Technique A: token leasing (recommended)

* A gateway only holds state for **keys it's seeing traffic for right now**,
  not every user in the region. The local table uses LRU eviction.
* When a request for user 42 arrives and the gateway has no tokens for user 42,
  it **synchronously** asks Redis: "give me up to 5 tokens for user 42."
* The Lua script subtracts them from the shared bucket right away. Those tokens
  now belong to this gateway.
* The next 4 requests for user 42 on this gateway are decided from memory.
* Leftover tokens expire after about 1 second and aren't written back.

```text
Redis bucket for user42: 100 tokens

Gateway A: "take 5"  -> Redis: 100 -> 95. Gateway A holds 5 locally.
Gateway B: "take 5"  -> Redis: 95  -> 90. Gateway B holds 5 locally.
Gateway A spends 3, then its lease expires -> 2 tokens wasted.
```

**It never overshoots**, because every token is removed from Redis before it's
spent. The only error is undershoot: wasted tokens mean the user gets slightly
fewer requests.

#### Technique B: local counting with async sync

* The gateway counts locally and pushes "user 42 used 7 more" to Redis every
  100 ms.
* Cheaper, but it **can overshoot**, because during those 100 ms no gateway
  knows what the others did.

#### When leasing actually helps

A user's requests normally spread across all gateways. If 100 gateways each
grab 5 tokens, a user with a limit of 100 per minute is drained in one burst.

* **Small limits (like 100 per minute):** Don't lease. Make one Redis call per
  request. These users send few requests, so the cost is low.
* **Large limits (like 50,000 per second for a tenant):** Lease. Even 100
  gateways x 50 tokens is a tiny fraction of the limit.
* **Key-based routing:** The load balancer hashes the API key so one customer's
  traffic lands on a small group of gateways instead of all of them. Fewer
  gateways share each key, so fewer tokens are wasted.

> [!TIP]
> "Gateways lease small batches of tokens per active key, removed from Redis up
> front, so it never overshoots. I only lease for high-limit keys, where the
> saved Redis calls matter."

### 2. Hot keys

**Problem:** One big customer has a limit of 50,000 requests per second, all on
one Redis key, so one node gets hammered.

**Fixes:**

* Split the key into `tenantX#0` to `tenantX#9`, each with a limit of 5,000.
  Each request picks one at random, which spreads the load across nodes.
* Token leasing helps most here, because high limits allow large leases with
  tiny relative error.

### 3. Redis is down or slow

This is the most important decision. Every check has a short timeout, about
5 ms.

| Strategy                   | Behavior                                         | Use for                                                     |
|----------------------------|--------------------------------------------------|-------------------------------------------------------------|
| **Fail open**              | If the store can't answer, allow the request     | Most APIs. Availability matters more than exact limits.     |
| **Fail closed**            | If the store can't answer, reject the request    | Security limits: login attempts, OTP sends, password resets |
| **Fall back to local limits** | Switch to in-memory per-server limits (limit / N) | Best default: protects backends without blocking everyone |

Choice: fail open with a local fallback limiter, and fail closed only for
security rules. A **circuit breaker** stops calling Redis for a few seconds
after repeated failures, so a sick Redis isn't hammered further.

> [!IMPORTANT]
> "The rate limiter exists to protect the system. If it fails in a way that
> blocks all traffic, it becomes the outage."

### 4. Multiple regions

A global limit with every check crossing continents adds 100+ ms, which isn't
acceptable.

| Option                              | How                                                                          | Trade-off                                                       |
|-------------------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Split the limit per region** (default) | 1,000/min globally becomes 600 for the US and 400 for Europe, by traffic share | Fast and simple. A traveling or failed-over user may hit the limit early. |
| **Local counts + async sync**       | Each region counts locally and shares totals with others every second       | Closer to a true global limit. Can overshoot by ~1 sec of traffic. |
| **Route users to a home region**    | Each user's requests always go to one region                                 | Accurate, but slow for users far from home                      |

#### How do you route to a home region without knowing the user

Before a request reaches a server, **nobody knows who the user is.** DNS or
anycast sends it to the nearest region. The identity (API key or login token)
is only readable after TLS is terminated at that region's edge. So home-region
routing only works if the region can be found from the request itself.

| Approach                       | How                                                                                     | Used when                                                 |
|--------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------|
| **Region-specific URLs**       | Customers pick a region at signup and call `api.eu.example.com` or `api.us.example.com` | B2B and SaaS APIs, often for data residency laws          |
| **Region inside the credential** | The API key looks like `eu_live_8f3k...`, or the login token contains `region: eu`. The edge reads it and forwards the request. | One URL, but a home region is still needed |
| **Lookup table at the edge**   | A small, globally replicated, read-only map `api_key -> home region`, cached in memory  | Old keys don't carry region info                          |
| **No home region**             | Each region enforces its own share of the limit                                         | Anonymous traffic, IP-based limits, consumer apps         |

**The cost:** a user in Asia whose home is the US pays a cross-ocean hop on
every request, not only on the limit check. Forwarding only the check is no
better, since the check is the slow part.

Recommendation:

* **Default:** per-region limits. Each region gets a share of the global limit,
  and no routing is needed.
* **Anonymous traffic:** limit by IP, per region. There's no user, so there's
  no home region.
* **Strict global limits for paying tenants:** region-specific URLs or a region
  prefix in the key. Those customers usually live in one region anyway.

### 5. Accuracy details to mention

* **Retries count too.** A client retrying failed requests burns its own limit,
  which is usually intended.
* **Failed requests:** Decide whether a request rejected by the backend (like a
  500 error) costs a token. Usually yes, because it still used resources.
* **Multiple rules per request:** Checking 3 rules means 3 updates. Run them in
  one script call or one pipelined round trip to keep latency flat.

## Deep dive: Redis Cluster when nodes are added or removed

### Hash slots, not direct key-to-node mapping

* Redis Cluster has a fixed **16,384 slots.**
* Every key maps to a slot: `slot = CRC16(key) mod 16384`.
* Each primary node owns ranges of slots, for example node A owns 0 to 5460.
* Nodes and clients keep a **slot map**: slot to node.

```text
key "rl:{user42}:api" -> CRC16("user42") -> slot 9,301 -> owned by Node B
```

A key never changes slot. **Only the slot's owner changes.** That gives the
same benefit as consistent hashing: when nodes change, only keys in the moved
slots move.

### Adding a node

1. The new node joins with zero slots. Nothing moves automatically.
2. An operator or a managed service runs a **rebalance**, which moves some
   slots from existing nodes to the new one, one slot at a time.
3. For each slot being moved:
   * The source marks the slot `MIGRATING` and the target marks it `IMPORTING`.
   * Keys are copied over in small batches and deleted from the source.
4. Requests during the move:
   * If the key is still on the source, the source answers normally.
   * If the key has already moved, the source replies `ASK`, meaning "go to the
     target for this one request." The client retries there without updating
     its map.
5. When the slot is fully moved, ownership is updated and spread to all nodes
   through the cluster's internal gossip.
6. A client with an old map gets `MOVED`, meaning "this slot now lives on
   Node D." It updates its slot map and goes there from then on.

```text
Client --get slot 9301--> Node B
Node B: "MOVED 9301 10.0.0.9:6379"
Client updates its map, retries on Node D, and uses Node D next time
```

### Removing a node

* First move all its slots to other nodes, using the same migration.
* Once it owns no slots, remove it from the cluster.
* A **crash** isn't a removal. The crashed primary's replica is promoted
  automatically by a majority vote among the primaries.

### What this means for the rate limiter

* **Keep each script on one slot.** A Lua script can only touch keys in one
  slot. Use **hash tags**: `rl:{user42}:api` and `rl:{user42}:login` both hash
  only `user42`, so they share a slot.
* Single-key checks move smoothly. At worst there's one extra round trip for an
  `ASK` redirect.
* Multi-key scripts can briefly fail with a `TRYAGAIN` error while their slot
  is half-moved. The client retries after a few milliseconds, or the limiter
  fails open.
* Losing a few counters during a move is harmless. A user might get a handful
  of extra requests.
* Managed services (Google Memorystore, AWS ElastiCache) rebalance slots for
  you when you resize the cluster.

## Final architecture

```text
 Clients
   |
   v
 CDN / WAF (per-IP limits, attack protection)
   |
   v
 +--------------------------------------------------+
 | API gateway servers                              |
 |  rate limit module:                              |
 |   1. match request to rules (in-memory cache)    |
 |   2. leased tokens available? -> decide locally  |
 |   3. else Lua script on Redis (5 ms timeout)     |
 |   4. Redis down? -> local fallback limiter       |
 +--------------------------------------------------+
   |  allowed               |  check              ^ rule updates pushed
   v                        v                     |
 Backend services     Redis Cluster          Config service
                      (sharded by slot,      (rules, admin UI,
                       replica per shard)     shadow mode)
   |
   v
 Metrics: allowed vs rejected per rule, Redis latency,
          fallback activations, top throttled keys
```

## Failure scenarios

| Failure                 | What happens                        | Mitigation                                                         |
|-------------------------|-------------------------------------|--------------------------------------------------------------------|
| One Redis node dies     | Keys on that shard briefly unavailable | Replica promoted in seconds. Fail open or local fallback meanwhile. |
| Whole Redis cluster down | No shared counts                   | Local per-server limits keep backends protected                    |
| Redis slow              | Request latency rises               | 5 ms timeout plus circuit breaker                                  |
| Bad rule pushed         | Good users blocked                  | Shadow mode first, plus fast rule rollback                         |
| Gateway server dies     | Its leased tokens are lost          | Harmless: users get slightly fewer requests for a moment           |
| Attack from many IPs    | Per-IP limits don't catch it        | Limits per user or API key, plus edge protection at the CDN        |

## What to monitor

* **Allowed vs rejected** per rule. A sudden jump can mean an attack or a bad
  rule.
* **Redis latency and errors.**
* **Fallback activations:** How often the local limiter takes over.
* **Top throttled keys:** Spot abusive clients, or customers who need a higher
  plan.

## Trade-offs to state clearly

* **Token bucket** allows realistic bursts while keeping the average rate.
  Sliding window counter fits strict per-minute limits.
* **Central Redis with atomic scripts** gives correct global counts for about
  1 ms per request.
* **Token leasing** cuts latency and load for high-limit keys, with slight
  undershoot and no overshoot.
* **Fail open by default** keeps the product up. **Fail closed** only where
  security demands it.
* **Per-region limits** avoid slow cross-continent checks at the cost of exact
  global accuracy.

## The answer in one paragraph

> "I'd put the rate limiter in the API gateway, with rules stored in a config
> service and cached in memory on each gateway. Each check runs a token bucket
> as one atomic Lua script in a Redis Cluster sharded by key, using the Redis
> clock so counts stay correct across hundreds of servers. To keep latency low,
> gateways lease small batches of tokens for high-limit keys and spend them
> locally, and hot keys are split across shards. If Redis is unavailable, the
> limiter falls back to local per-server limits and fails open, except for
> security rules like login attempts, which fail closed. Across regions, each
> region gets a share of the global limit, because cross-continent checks are
> too slow and the user's identity isn't known until the request reaches a
> region."

**Suggested 45-minute split:** 5 minutes requirements, 3 estimates, 5 placement
and algorithm choice, 20 on deep dives (race condition and atomic script,
latency, hot keys, failure handling, multi-region), and 5 on monitoring and
trade-offs.
