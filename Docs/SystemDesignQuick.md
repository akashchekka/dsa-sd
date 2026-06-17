# System Design — Quick Revision

---

## Q: All that I need to know about Kafka

**What it is:** A distributed, append-only **commit log** for streaming events. Producers write, consumers read, messages are stored durably and replayed by offset. Used to decouple services, stream events, and handle high throughput.

### Core concepts
- **Topic:** Named stream, split into **partitions**.
- **Partition:** Ordered, append-only log. **Order guaranteed only within a partition**, not across topic.
- **Offset:** Sequential message ID in a partition (the bookmark).
- **Producer:** Writes events; partition chosen by key hash (same key → same partition → ordered).
- **Consumer / Consumer Group:** Each partition is read by **exactly one** consumer in a group → parallelism = number of partitions.
- **Broker:** A Kafka server; cluster = many brokers.
- **Controller:** Manages metadata + leader election. Newer Kafka uses **KRaft** (no ZooKeeper).

### Replication & durability
- Each partition has a **leader** + **follower replicas** (`replication.factor`, usually 3).
- **ISR (In-Sync Replicas):** replicas caught up to leader; new leader elected from ISR on failure.
- `min.insync.replicas=2` + `acks=all` → no acknowledged data loss.

### Delivery guarantees
| Guarantee | How |
|---|---|
| At-most-once | Commit offset before processing (may lose) |
| **At-least-once** (default) | Commit after processing (may duplicate → need idempotent consumer) |
| Exactly-once (EOS) | Idempotent producer + transactions |

### Producer essentials
- `acks`: `0` (fire-forget), `1` (leader only), `all` (safest).
- `enable.idempotence=true` → no duplicate writes on retry.
- Batching (`linger.ms`, `batch.size`) + compression for throughput. **Key** decides partition → ordering.

### Consumer essentials
- **Pull-based.** Commit offset manually after success (safer than auto-commit).
- `auto.offset.reset`: `earliest` (replay all) / `latest` (only new).
- **Rebalancing:** partitions reassigned when consumers join/leave (briefly pauses consumption).

### Retention & replay
- Kept by **time** (`retention.ms`) or **size** (`retention.bytes`) — not deleted on read.
- **Log compaction:** keeps only latest value per key (state/changelog topics).
- Replay = seek to older offset/timestamp → reprocess.

### When to use / avoid
- **Use:** event streaming, log aggregation, decoupling microservices, high throughput, replay/audit.
- **Avoid:** simple request/response, small task queues (use RabbitMQ/SQS), strict global ordering.

### Kafka vs RabbitMQ
| Kafka | RabbitMQ |
|---|---|
| Log retained, replayable | Message removed on ack |
| Pull-based, consumer groups | Push-based, smart broker |
| Huge throughput, ordered per partition | Flexible routing, lower throughput |

**Golden rules:** Order is **per-partition**. Parallelism = **partition count**. Default is **at-least-once** → make consumers **idempotent**. Durability = **replication + `acks=all` + `min.insync.replicas`**.

> Producer hashes a key to pick a partition inside a topic → message is appended to that partition's log → each consumer group reads all partitions independently, splitting partitions among its consumers.

---

## Q: What if Kafka fails?

Kafka survives most failures through **replication**. Design producers/consumers to tolerate broker downtime.

- **Broker dies:** Each partition has a leader + replicas. A new leader is auto-elected from in-sync replicas (ISR). Set `replication.factor=3`, `min.insync.replicas=2`, `acks=all` → no acknowledged data loss.
- **Producer can't reach Kafka:** Use retries + `enable.idempotence=true` (no dupes/loss). For full outages use the **Outbox pattern** — write the event to your DB in the same transaction, a relay publishes it later.
- **Consumer crashes:** Resumes from last committed **offset** → no loss. Make consumers **idempotent** (at-least-once delivery).
- **Whole cluster down:** Mitigate with **multi-AZ/region** replication (MirrorMaker) and **backpressure** in upstream services.

| Failure | Mitigation |
|---|---|
| Single broker | `replication.factor≥3`, `acks=all` |
| Producer can't publish | Retries + idempotence, Outbox pattern |
| Consumer crash | Resume from offset, idempotent consumer |
| Full outage | Multi-AZ/region, Outbox in DB |

**Rule:** Never assume Kafka is up. Decouple writes with the **Outbox pattern**, make consumers **idempotent**, tune **replication + acks**.

---

## Q: How do consumers replay events using offsets to recover missed notifications?

Kafka **keeps messages** (doesn't delete on read). Each message has a permanent **offset**, so consumers can rewind to an earlier offset and **reprocess** missed events.

- **Why it works:** Messages stay within the **retention window** (`retention.ms`, e.g. 7 days). The committed offset is just a bookmark.
- **How to replay:** Seek to an earlier offset — `seek()`, `seekToBeginning()`, by timestamp, or `--reset-offsets` CLI. A new consumer group with `auto.offset.reset=earliest` re-reads the whole topic.
- **Safety (must be idempotent):** Replay can process a message twice. Dedupe by a unique key (`event_id`) so you recover missed notifications **without sending duplicates**.
- **Patterns:** Dead Letter Topic for failed events; commit offset **only after** a successful send (so a crash mid-send replays it).

**Rule:** Replay = **seek to offset** (recovery) + **idempotent dedupe** (safety).

---

## Q: Redis vs Memcached

Both are in-memory key-value stores used for **caching**. Memcached is a simple, fast cache; Redis is a richer data-structure store with persistence and replication.

| Feature | **Redis** | **Memcached** |
|---|---|---|
| Data types | Strings, hashes, lists, sets, sorted sets, streams, geo | Strings only |
| Persistence | Yes — RDB snapshots + AOF log | None (lost on restart) |
| Replication / HA | Yes — replicas + Sentinel + Cluster | No built-in replication |
| Sharding | Built-in (Redis Cluster) | Client-side only |
| Threading | Mostly single-threaded (I/O threads in 6+) | Multi-threaded (scales on cores) |
| Eviction | Many policies (LRU, LFU, TTL, random) | LRU only |
| Extras | Pub/Sub, transactions, Lua scripts, atomic ops | None |
| Max value size | 512 MB | 1 MB (default) |

### When to use which
- **Redis:** need data structures, persistence, replication/HA, pub/sub, atomic ops, rate limiting, leaderboards, queues, or larger values.
- **Memcached:** need a simple **multi-threaded** cache for small key-value pairs at very high throughput, no durability needed.

**Rule:** Default to **Redis** (more features, persistence, HA). Pick **Memcached** only for a pure, simple, multi-core caching layer.

---

## Q: What if Redis fails?

Plan for node failure, data loss, and how the app behaves when Redis is unreachable.

### 1. Single node crash (in-memory data lost)
- **Persistence** softens this:
  - **RDB:** periodic snapshots → fast restart, loses writes since last snapshot.
  - **AOF:** logs every write → less loss (`appendfsync everysec` ≈ 1s), slower.
  - Best durability = **AOF + RDB together**. Pure in-memory = full loss on restart (OK if just a cache).

### 2. High availability (auto-failover)
- **Sentinel:** monitors master + replicas, auto-promotes a replica on failure, updates clients (needs **quorum**).
- **Redis Cluster:** sharded data; each shard has master + replicas with built-in failover.
- Replication is **async** → a few writes can be lost during failover.

### 3. App-side resilience (Redis unreachable)
- **Cache-aside fallback:** on miss/error, read from the **source DB** → app degrades, doesn't crash.
- **Timeouts + circuit breaker:** fail fast to DB instead of hanging.
- **Cache stampede:** mass cache loss floods the DB → use request coalescing, jittered TTLs, warm-up.

### 4. Consistency risk
- Async replication → promoted replica may miss the master's last writes.
- `min-replicas-to-write` forces master to reject writes if too few replicas in sync (consistency over availability).

| Failure | Mitigation |
|---|---|
| Node crash, data lost | AOF + RDB persistence |
| Master down | Sentinel / Cluster auto-failover |
| Redis unreachable | Cache-aside fallback to DB, timeouts, circuit breaker |
| Mass cache loss | Request coalescing, jittered TTLs, warm-up |

**Rule:** If Redis is a **cache** → fall back to the **DB** gracefully. If a **datastore** → use **Sentinel/Cluster + AOF** for HA/durability, accept a tiny async-replication loss window.

---

## Q: Trade-offs with Redis?

Redis is fast and flexible, but speed comes with real costs.

- **Memory cost (RAM-bound):** Everything in RAM → expensive, capacity-limited vs disk. Large data needs sharding or eviction.
- **Durability vs performance:** Pure in-memory = fast but loses data on crash. AOF/RDB add durability but cost I/O latency; even AOF `everysec` loses ~1s of writes.
- **Consistency vs availability:** Async replication → failover can **lose recent writes**. Forcing sync (`min-replicas-to-write`) cuts availability.
- **Single-threaded core:** One slow command (`KEYS *`, big `SORT`) **blocks everything**; CPU work doesn't scale across cores on one node.
- **Scaling complexity:** Vertical scaling hits a RAM ceiling. Cluster adds horizontal scale but brings resharding and **cross-slot/multi-key limits**.
- **Operational overhead:** HA (Sentinel/Cluster), eviction tuning, fragmentation, persistence config all need care.
- **Not a full DB:** No joins or complex SQL-like queries. Best as cache / fast-access layer, not primary store for complex relational data.

| Trade-off | Cost |
|---|---|
| In-memory speed | High RAM cost, size limits |
| Persistence | I/O overhead, small loss window |
| Async replication | Possible write loss on failover |
| Single-threaded | One slow command blocks all |
| Cluster scaling | Resharding + multi-key limits |

**Rule:** Redis trades **durability, consistency, and rich querying** for **raw speed and simplicity**. Design around RAM limits, async replication, and single-threaded execution.

---

## Q: What is the Geo data type in Redis?

Redis **Geo** stores and queries geospatial data (lat/long) — used for "find nearby" features like ride-sharing, food delivery, store locators.

### How it works
- **Not a separate type** — built on a **Sorted Set (ZSET)**.
- Coordinates are encoded into a **52-bit Geohash** stored as the sorted-set **score** → O(log N) inserts/queries, reuses ZSET commands.

### Core commands
| Command | Purpose |
|---|---|
| `GEOADD key lon lat member` | Add a location |
| `GEOSEARCH ... BYRADIUS r unit` | Find members within a radius |
| `GEOSEARCH ... BYBOX w h unit` | Find members within a box |
| `GEODIST key m1 m2 unit` | Distance between two members |
| `GEOPOS key member` | Get lon/lat of a member |
| `GEOHASH key member` | Get geohash string |

```bash
GEOADD drivers 77.5946 12.9716 "driver:1"
GEOSEARCH drivers FROMLONLAT 77.5946 12.9716 BYRADIUS 5 km ASC
# → nearby drivers sorted by distance
```

### Use cases & limits
- **Use:** nearby drivers/restaurants/users, geofencing, location recommendations.
- **Limits:** in-memory (RAM cost), pole/meridian edge cases, only radius/box (no polygons → use PostGIS), no per-member TTL.

**Rule:** Redis Geo = a **Sorted Set with geohash scores** for fast radius/box "find nearby" queries. Use PostGIS for advanced geospatial analysis.

---

## Q: Load Balancing

A **load balancer (LB)** distributes traffic across servers for **availability, scalability, and reliability**, hiding backend failures and enabling horizontal scaling.

### Layers
| Type | Layer | Routes by | Notes |
|---|---|---|---|
| **L4 (Transport)** | TCP/UDP | IP + port | Fast, no payload inspection |
| **L7 (Application)** | HTTP | URL, headers, cookies, path | Smart routing, SSL termination, slower |

### Algorithms
- **Round Robin:** rotate evenly. **Weighted RR:** bigger servers get more.
- **Least Connections:** fewest active connections (good for long-lived requests).
- **Least Response Time:** fastest server.
- **IP Hash / Consistent Hashing:** same client → same server (stickiness, cache locality).

### Key mechanisms
- **Health checks:** ping backends; remove unhealthy, re-add when healthy.
- **Sessions:** prefer **stateless servers + session in Redis/DB** over **sticky sessions** (affinity causes uneven load, breaks on server loss).
- **LB redundancy:** LB must not be a SPOF → active-passive/active-active with virtual IP (keepalived) or managed LB (AWS ELB/ALB/NLB).

### Types
- **Software:** Nginx, HAProxy, Envoy. **Hardware:** F5, Citrix. **DNS/GSLB:** cross-region geo-routing.

**Rule:** Use **L4** for raw speed, **L7** for content-based routing. Prefer **stateless servers + external session store**, run **health checks**, and make the **LB itself redundant**.

---
