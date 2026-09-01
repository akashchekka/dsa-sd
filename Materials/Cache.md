---
description: Quick revision notes for caching, Redis, Dragonfly, and high-concurrency caches
---

# Cache - Quick Revision

## Table of Contents

- [Q: What if Redis fails?](#q-what-if-redis-fails)
- [Q: Trade-offs with Redis?](#q-trade-offs-with-redis)
- [Q: Does Redis Cluster use multiple CPU cores?](#q-does-redis-cluster-use-multiple-cpu-cores)
- [Q: What is Dragonfly and how does it differ from Redis?](#q-what-is-dragonfly-and-how-does-it-differ-from-redis)
- [Q: What is a high-concurrency cache?](#q-what-is-a-high-concurrency-cache)
- [Q: What is a cache stampede?](#q-what-is-a-cache-stampede)
- [Q: Caching Patterns](#q-caching-patterns)

---

## Q: What if Redis fails?

### 1. Single node crash (in-memory data lost)

- **RDB:** periodic snapshots → fast restart, loses writes since last snapshot.
- **AOF:** logs every write → less loss (`appendfsync everysec` ≈ 1s), slower.
- Best = **AOF + RDB**. Pure in-memory = full loss on restart (fine for a cache).

### 2. High availability (auto-failover)

- **Sentinel:** monitors master + replicas, auto-promotes a replica (needs **quorum**).
- **Redis Cluster:** sharded; each shard has master + replicas with built-in failover.
- Replication is **async** → a few writes lost during failover.

### 3. App-side resilience (Redis unreachable)

- **Cache-aside fallback:** on miss/error read source **DB** → degrade, don't crash.
- **Timeouts + circuit breaker:** fail fast instead of hanging.
- **Cache stampede:** mass loss floods DB → request coalescing, jittered TTLs, warm-up.

### 4. Consistency risk

- Async replication → promoted replica may miss last writes. `min-replicas-to-write` rejects writes if too few replicas in sync (consistency over availability).

| Failure | Mitigation |
|---|---|
| Node crash, data lost | AOF + RDB persistence |
| Master down | Sentinel / Cluster auto-failover |
| Redis unreachable | Cache-aside fallback to DB, timeouts, circuit breaker |
| Mass cache loss | Request coalescing, jittered TTLs, warm-up |

**Rule:** If Redis is a **cache** → fall back to the **DB** gracefully. If a **datastore** → use **Sentinel/Cluster + AOF** for HA/durability, accept a tiny async-replication loss window.

> Redis failures span lost in-memory data (softened by AOF+RDB), write loss on async failover (Sentinel/Cluster), and unreachability; treat it as a cache that gracefully falls back to the DB, and only lean on it as a datastore when you accept a small replication-loss window.

---

## Q: Trade-offs with Redis?

- **Memory (RAM-bound):** all in RAM → expensive, size-limited; large data needs sharding/eviction.
- **Durability vs performance:** in-memory fast but loses data on crash; AOF/RDB add I/O latency; AOF `everysec` loses ~1s.
- **Consistency vs availability:** async replication → failover can **lose recent writes**; forcing sync (`min-replicas-to-write`) cuts availability.
- **Single-threaded core:** one slow command (`KEYS *`, big `SORT`) **blocks everything**; no multi-core scaling per node.
- **Scaling:** vertical hits a RAM ceiling; Cluster adds horizontal scale but brings resharding + **cross-slot/multi-key limits**.
- **Ops overhead:** HA (Sentinel/Cluster), eviction tuning, fragmentation, persistence config.
- **Not a full DB:** no joins/complex queries → cache / fast-access layer, not primary relational store.

| Trade-off | Cost |
|---|---|
| In-memory speed | High RAM cost, size limits |
| Persistence | I/O overhead, small loss window |
| Async replication | Possible write loss on failover |
| Single-threaded | One slow command blocks all |
| Cluster scaling | Resharding + multi-key limits |

**Rule:** Redis trades **durability, consistency, and rich querying** for **raw speed and simplicity**. Design around RAM limits, async replication, and single-threaded execution.

> Redis buys raw speed by keeping everything in RAM and running single-threaded, which is exactly why it trades away durability, strong consistency, unlimited size, and rich querying. Design around those limits rather than fighting them.

---

## Q: Does Redis Cluster use multiple CPU cores?

Yes, **Redis Cluster uses multiple CPU cores in aggregate**, but it does so through multiple Redis processes rather than by executing all commands from one Redis process across every core.

Most commands in each Redis instance are executed sequentially by its main thread. Redis Cluster partitions keys across multiple instances, allowing those processes to execute commands concurrently on different CPU cores.

```text
4-core machine
├── Redis instance A → mostly Core 1
├── Redis instance B → mostly Core 2
├── Redis instance C → mostly Core 3
└── Redis instance D → mostly Core 4
```

Instances are not automatically bound to individual cores. The operating system schedules their threads across available cores unless CPU affinity or container CPU limits are configured. Redis Cluster also does not create instances automatically; the instances must be deployed and then configured as a cluster.

### Can a four-core machine run more than four instances?

Yes. Processes do not require dedicated cores, so a four-core machine can run more than four Redis instances:

```text
6 Redis instances
  ↓
4 physical CPU cores
  ↓
Instances compete for CPU time
```

For a CPU-bound workload, running more active master instances than available cores usually does not increase throughput. It can reduce performance through:

- CPU contention.
- Context switching.
- Memory pressure.
- Network contention.
- Less predictable latency.

More instances than cores can still be reasonable when some instances are lightly loaded replicas or their workloads spend significant time waiting on network I/O.

### Horizontal scaling distinction

- **Multiple instances on one machine:** process-level sharding that uses the machine's vertical CPU capacity.
- **Multiple instances across additional machines:** true horizontal scaling that adds capacity and fault isolation.

A single-machine Redis Cluster can be useful for development or CPU utilization, but it does not provide meaningful high availability. If the machine fails, every master and replica on it fails together. Production masters and replicas should be distributed across separate machines or availability zones.

**Rule:** Redis uses multiple cores by running **multiple sharded processes**. A machine may run more Redis instances than cores, but CPU-bound masters then compete for processing time, so benchmark the workload and reserve capacity for the OS, persistence, replication, and background work.

> Redis Cluster scales command processing across cores by distributing keys and requests among multiple single-threaded Redis processes; more processes than cores are allowed, but they share CPU time and do not add fault tolerance when they run on the same machine.

> Horizontal scaling distributes Redis instances across multiple machines, while multiple instances on each machine collectively use that machine’s CPU cores.

> Horizontal scaling adds machines and Redis instances; multiple instances collectively use the machines' cores, but one Redis instance does not ordinarily use all cores for command processing.

Redis Cluster
├── Machine A (4 cores)
│   ├── Redis instance 1 → main command thread uses ~1 core
│   ├── Redis instance 2 → main command thread uses ~1 core
│   └── Remaining CPU → OS, replication, persistence, networking
│
├── Machine B (4 cores)
│   ├── Redis instance 3 → ~1 core
│   └── Redis instance 4 → ~1 core
│
└── Machine C (4 cores)
    ├── Redis instance 5 → ~1 core
    └── Redis instance 6 → ~1 core

---

## Q: What is Dragonfly and how does it differ from Redis?

**Dragonfly is a complete in-memory database/server**, not a layer on top of Redis. It stores data, executes commands, expires and evicts keys, persists data, and supports replication itself.

### Redis client compatibility

Dragonfly implements the Redis wire protocol and many Redis commands. Existing Redis client libraries can therefore connect directly to a Dragonfly server:

```text
Redis deployment:
Application -> Redis client -> Redis server

Dragonfly deployment:
Application -> Redis client -> Dragonfly server
```

The Redis client is only the protocol-speaking library. Pointing its host and port to Dragonfly does not require a Redis server to run behind Dragonfly.

```python
from redis import Redis

client = Redis(host="dragonfly-host", port=6379)
client.set("user:1", "Akash")
print(client.get("user:1"))
```

### Multicore architecture

A process is not limited to one core. A single-threaded process can execute on only one core at a time, while a multithreaded process can run its threads concurrently on several cores.

Dragonfly is designed as a multithreaded, internally sharded process. It partitions keys among worker shards so one instance can use multiple CPU cores directly:

```text
One Dragonfly process on a 4-core machine
|-- Internal shard/thread 1 -> Core 1
|-- Internal shard/thread 2 -> Core 2
|-- Internal shard/thread 3 -> Core 3
`-- Internal shard/thread 4 -> Core 4
```

Redis and Dragonfly therefore use machine CPU differently:

| Redis | Dragonfly |
|---|---|
| One instance executes most commands on one main thread | One instance executes work across multiple threads |
| Multiple processes/shards use multiple command-processing cores | Internal shards use multiple cores within one process |
| Redis Cluster distributes keys across external instances | Dragonfly partitions keys among internal shards |

### Scaling model

- **Vertical scaling:** give one Dragonfly instance more CPU cores and RAM; it is designed to use that capacity directly.
- **Horizontal scaling:** deploy Dragonfly instances across multiple machines when one machine is insufficient or replicas are needed for availability.
- **Operational effect:** fewer processes may be required per machine than with Redis to use the same number of cores.

```text
Dragonfly deployment
|-- Machine A -> one multicore Dragonfly instance
|-- Machine B -> one multicore Dragonfly instance
`-- Machine C -> one multicore Dragonfly instance
```

### Hot-key limitation

Each key is owned by an internal shard. A hot key is not automatically split across all cores, so traffic concentrated on one key can still bottleneck its owning shard. Multicore scaling works best when requests are distributed across many keys.

### Compatibility caveat

Redis protocol compatibility does not guarantee identical behavior. Before migrating, verify:

- Commands used by the application.
- Lua scripts and transactions.
- Pub/Sub and Streams behavior.
- Persistence, recovery, replication, and failover semantics.
- Eviction policies and Redis module dependencies.

**Rule:** Dragonfly is an independent Redis-compatible in-memory database that uses multiple threads and internal shards to exploit multiple cores within one process; existing Redis clients can connect to it directly, but application and operational compatibility must still be tested.

> Redis commonly uses multiple processes or machines to exploit many command-processing cores, while one Dragonfly process uses multiple cores internally and can then be deployed or replicated across machines.

---

## Q: What is a high-concurrency cache?

A **high-concurrency cache** serves requests from many clients or application threads at the same time while maintaining low response times. It keeps frequently accessed data in memory so repeated requests avoid slower database or service calls.

```text
Thousands of clients
  ↓
Redis or Dragonfly
  ↓
product:123 → product details
```

### Key performance terms

- **Concurrency:** number of requests active at the same time.
- **Throughput:** number of requests completed per second.
- **Latency:** time required to complete one request.

A high-concurrency cache must sustain high throughput without latency increasing sharply as more clients connect.

### Common use cases

- User sessions and authentication tokens.
- Product, profile, and API response caching.
- Rate-limit counters and leaderboards.
- Frequently executed database query results.

### Redis vs Dragonfly

- **Redis:** uses an event-driven architecture for many connections, but executes most commands sequentially on its main thread. This gives simple atomic behavior and low latency, although one instance can become CPU-bound under extreme traffic.
- **Dragonfly:** distributes connections and command processing across multiple CPU threads. A single instance can use more cores directly and may provide higher throughput for highly parallel workloads.

Actual performance depends on command complexity, value size, network capacity, persistence settings, and key distribution.

### Common risks

- **Hot keys:** many requests target one key, concentrating load.
- **Cache stampede:** many clients simultaneously rebuild the same expired value.
- **Connection exhaustion:** clients open more connections than the cache can efficiently serve.
- **Uneven load:** poor key distribution overloads particular nodes or shards.

**Rule:** A high-concurrency cache handles many simultaneous requests with **high throughput and low latency**. Redis is usually sufficient, while Dragonfly can better exploit a large multi-core server for highly parallel traffic.

> A high-concurrency cache protects slower databases and services by serving frequently accessed data from memory; its effectiveness depends on keeping latency low under parallel load and controlling hot keys, stampedes, connection counts, and uneven distribution.

---

## Q: What is a cache stampede?

A **cache stampede** occurs when a popular cached item expires and many concurrent requests simultaneously miss the cache and query the database to rebuild it, potentially overwhelming the database.

```text
Popular key expires
  ↓
1,000 simultaneous cache misses
  ↓
1,000 identical database queries
  ↓
Database overload
```

### Prevention techniques

- **Request coalescing / single-flight:** only one request rebuilds the value; others wait.
- **Jittered TTLs:** add randomness to expiration times so many keys do not expire together.
- **Early refresh:** refresh popular values shortly before expiration.
- **Stale-while-revalidate:** serve slightly stale data while one request refreshes it.
- **Distributed locking:** allow only one application instance to rebuild the value.
- **Cache warming:** preload important values before traffic arrives.

### Example

A product page cached for 10 minutes receives 5,000 requests per second. When its cache entry expires, all requests may hit the database at once unless rebuilding is coordinated.

**Rule:** Let only **one request rebuild an expired value** while other requests wait or receive stale data, and use jittered TTLs to prevent many keys from expiring together.

> A cache stampede turns one expired hot key into a burst of identical database queries; prevent it with single-flight rebuilding, expiration jitter, early refresh, stale responses, locking, or cache warming.

---

## Q: Caching Patterns

| Pattern | Explanation |
|---|---|
| **Cache-Aside (Lazy Loading)** | Application checks the cache first. On a cache miss, it reads from the database, stores the result in the cache, and returns it. Most commonly used. |
| **Read-Through** | Application always reads from the cache. On a cache miss, the cache itself fetches the data from the database, stores it, and returns it. |
| **Write-Through** | Application writes to the cache, and the cache synchronously writes the data to the database. Cache and DB stay consistent, but writes are slower. |
| **Write-Behind (Write-Back)** | Application writes only to the cache. The cache asynchronously flushes changes to the database later. Faster writes, but risk of data loss if the cache fails before flushing. |
| **Write-Around** | Application writes directly to the database and skips the cache. The cache is populated only when the data is read later, avoiding cache pollution from rarely accessed writes. |

Easy way to remember:

- Cache-Aside → App manages the cache.
- Read-Through → Cache manages reads.
- Write-Through → Cache writes to DB immediately.
- Write-Behind → Cache writes to DB later.
- Write-Around → Writes bypass the cache.