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

## Q: How to achieve High Availability and High Consistency in distributed systems? (FAANG)

### The core tension — CAP & PACELC
- **CAP:** during a network **Partition**, choose **C** (reject/stale-error) or **A** (serve stale, reconcile later).
  - **CP:** ZooKeeper, etcd, Spanner, HBase. **AP:** Cassandra, DynamoDB, Riak.
- **PACELC:** if **P**artition → A or C; **E**lse (normal) → **L**atency or **C**onsistency. (Consistency costs latency even without failures.)

### High Availability — how
- **Replication** across nodes/AZs/regions; **redundancy** (active-active / active-passive).
- **Automatic failover** via leader election (Raft/Paxos) + health checks.
- **Sharding** (one shard's failure ≠ whole system), **load balancing**, **geo-distribution**.
- **Graceful degradation:** stale cache, read-only mode, circuit breakers, retries w/ backoff + jitter.
- Measured in **nines** (99.99% ≈ 52 min/yr downtime).

### High Consistency — how
- **Consensus (Paxos/Raft):** quorum agrees on an ordered log (etcd, Spanner).
- **Quorum reads/writes:** with N replicas, **W + R > N** guarantees read overlaps latest write (tunable).
- **Strong/linearizable** reads, **synchronous replication**, **2PC/3PC** for atomic cross-node commits (slow, blocking).
- Spectrum: Strong → Linearizable → Sequential → Causal → Read-your-writes → Eventual.

### Getting *both* (engineering around CAP)
- **Quorum tuning (W+R>N):** Dynamo/Cassandra — strong-ish + highly available.
- **Raft replicated state machine:** consistent + available while a **majority quorum** survives.
- **Spanner + TrueTime:** global strong consistency *and* HA (canonical example).
- **CRDTs / conflict resolution:** AP systems converge automatically.
- **Tiered:** strong for critical paths (payments, inventory), eventual for the rest (feeds, likes).

### Interview framing
1. State **CAP/PACELC** trade-off. 2. Ask: **strong or eventual** for this feature? 3. Pick quorum / consensus / leaderless+CRDT. 4. Discuss failure modes (partition, failover, **split-brain** fenced by quorum/leases). 5. Mention degradation + SLOs.

**Rule:** Can't beat CAP under a partition, but **quorums + consensus + per-feature consistency choices** let you be highly available *and* strongly consistent in the common case.

---

## Q: Redundancy & failover (active-active vs active-passive, health checks, leader election)?

**Redundancy** = keep multiple copies of a component so no single point of failure (SPOF). Failover = how you use them.

### Active-Active vs Active-Passive
| | Active-Active | Active-Passive |
|---|---|---|
| Traffic | All nodes serve | Only primary serves |
| Utilization | High | Standby idle |
| Failover | Instant (others live) | Promote standby (delay) |
| Complexity | High (data sync/conflicts) | Lower |
| Example | App servers behind LB, multi-region DB | Primary DB + hot standby, Redis Sentinel |

### Health checks
- Continuously probe nodes (HTTP/TCP heartbeat). Missed checks → node declared dead → removed from rotation / triggers failover. Without them you can't detect failure.

### Automatic leader election (Raft / Paxos)
- When the primary dies, **who becomes new primary?** Two leaders = **split-brain** (conflicting writes).
- **Consensus (Raft/Paxos):** nodes vote, a **majority quorum** must agree → only **one** leader elected → no split-brain. New leader has up-to-date log → no committed data lost.
- **Raft** = popular/understandable (etcd, Consul). **Paxos** = classic/harder (Spanner, Chubby).
- Quorum rule: on a split, only the **majority** side can elect a leader & accept writes; minority steps down.

**Rule:** Redundancy = spare copies, health checks = detect failure, **consensus leader election = safely promote exactly one new leader** (no split-brain) → real HA.

---

## Q: Availability "nines" — downtime numbers (2 to 5 nines)?

| Availability | Nines | Downtime / year | Downtime / month |
|---|---|---|---|
| 99% | two 9s | ~3.65 days | ~7.2 hours |
| 99.9% | three 9s | ~8.76 hours | ~43.8 min |
| 99.99% | four 9s | ~52.6 min | ~4.38 min |
| 99.999% | five 9s | ~5.26 min | ~26 sec |

- Each extra **9 cuts downtime by 10×**.
- **3 nines** ≈ common SaaS baseline; **4 nines** ≈ serious cloud target; **5 nines** ≈ telecom gold standard (expensive).
- Formula: $\text{Availability} = \frac{MTBF}{MTBF + MTTR}$ → improve by failing less (**↑MTBF**) or recovering faster (**↓MTTR**); fast failover mainly cuts MTTR.

**Memory hook:** 2→**3.65 days**, 3→**8.8 hrs**, 4→**52 min**, 5→**5 min** (each step ÷10).

---

## Q: How are Linearizability and Distributed Transactions (2PC/3PC) achieved?

### Strong Consistency / Linearizability
Every op appears to take effect **instantly at one point**; all clients see the **same real-time order**; a completed write is visible to **all** later reads.

**How:**
- **Single leader** serializes all writes into a total order; reads go to leader or up-to-date followers.
- **Consensus + quorum (Raft/Paxos):** leader replicates to a **majority** before ack. Reads also touch a majority → **W + R > N** guarantees overlap with the latest write.
- **Leases/fencing:** time-bound leader lease stops a stale old leader serving reads.
- **Spanner TrueTime:** GPS+atomic clocks; waits out clock-uncertainty window → globally linearizable.
- **Cost:** every op needs a majority round-trip → higher latency; minority side can't serve under partition (CP).

### Distributed Transactions — 2PC
Atomic all-or-nothing across multiple nodes, driven by a **coordinator**:
1. **Prepare (vote):** "can you commit?" Participants lock rows, log, reply Yes/No.
2. **Commit/Abort:** all Yes → commit; any No → abort.
- **Problems:** **blocking** (coordinator crash after votes → participants stuck holding locks), **slow** (sync round-trips + locks), coordinator is a **SPOF**.

### 3PC
Adds a **pre-commit** phase + timeouts → **non-blocking** (participants can decide via timeout if coordinator dies). But more latency and **still breaks under partitions** → rarely used.

### Modern alternatives
- **Saga:** local transactions + **compensating actions**, no global locks → eventual consistency (microservices).
- **Consensus commit:** Spanner runs 2PC **over Paxos groups** → no single-coordinator SPOF.

| Concept | How | Cost |
|---|---|---|
| Linearizability | Leader + quorum (W+R>N), leases, TrueTime | High latency, CP |
| 2PC | Coordinator: prepare→commit | Blocking, slow, SPOF |
| 3PC | + pre-commit + timeouts | More latency, fails on partition |
| Saga | Local txns + compensation | Eventual consistency |

**Rule:** Strong consistency = **single order via leader + majority quorum** (pay latency). Atomic cross-node = **2PC** (simple but blocking) or **Sagas** (non-blocking, eventually consistent).

---

## Q: What is the Saga pattern?

Manages a **distributed transaction across microservices without 2PC/global locks**. A saga = a **sequence of local transactions**, each with a **compensating action** to undo it if a later step fails → **eventual consistency**.

### Example: Place Order
| Step | Local txn | Compensation |
|---|---|---|
| 1 | Create order (pending) | Cancel order |
| 2 | Reserve inventory | Release inventory |
| 3 | Charge payment | Refund payment |
| 4 | Schedule shipping | Cancel shipping |

Payment fails → run compensations for steps 2 & 1.

### Two coordination styles
- **Choreography (event-driven):** no coordinator; each service listens for an event, does its step, emits the next. Simple, loosely coupled, but hard to track/debug at scale.
- **Orchestration (centralized):** an orchestrator tells each service what to do and triggers compensations on failure. Clear control flow, but orchestrator is an extra component (must be HA).

### Key properties
- Compensations + steps must be **idempotent** (replays on failure); some actions can't be undone perfectly (sent email → send apology).
- **No isolation** → others can see intermediate state; mitigate with **semantic locks / status flags** (order = PENDING).
- Built on **durable messaging** (Kafka + outbox) so events aren't lost.

### Saga vs 2PC
| | Saga | 2PC |
|---|---|---|
| Consistency | Eventual | Strong (atomic) |
| Locks | None | Holds locks across phases |
| Blocking | Non-blocking | Blocks on coordinator crash |
| Isolation | None (semantic locks) | Yes |
| Fit | Microservices, long workflows | Single transaction boundary |

**Rule:** Saga trades **atomicity + isolation** for **availability + no distributed locks**, via **local commits + compensating undos**. Orchestration for complex flows, choreography for simple; make every step **idempotent**.

---

## Q: What to use in production for strong consistency?

You don't hand-roll Paxos — pick proven tech and configure it.

### Coordination / metadata (consensus backbone)
- **etcd** (Raft, backs Kubernetes), **ZooKeeper** (ZAB), **Consul** (Raft) — leader election, distributed locks, config, service discovery. Small critical state, not bulk data.

### Strongly-consistent databases
- **Spanner / Cloud Spanner** — global strong consistency via **TrueTime** (gold standard).
- **CockroachDB / YugabyteDB** — open-source Spanner-like, Raft per range, serializable SQL.
- **PostgreSQL / MySQL** — single-node ACID; scale with **synchronous replication** for HA + consistency.

### Tunable-consistency DBs (configure for strong)
- **DynamoDB:** `ConsistentRead=true`; Transactions API for ACID.
- **Cassandra:** **`QUORUM` read + `QUORUM` write (W+R>N)** → strong; `LOCAL_QUORUM` per region.
- **MongoDB:** `writeConcern: majority` + `readConcern: majority/linearizable`, read from primary.

### Decision guide
| Need | Use |
|---|---|
| Locks / leader election / config | etcd / ZooKeeper / Consul |
| Global-scale SQL + strong | Spanner / CockroachDB |
| Single-region ACID | PostgreSQL/MySQL (sync replication) |
| KV at scale, strong reads | DynamoDB (`ConsistentRead`) |
| Wide-column, tunable | Cassandra (`QUORUM`) |
| Document store | MongoDB (`majority`) |

### Practical guidance
- Apply strong consistency **only on critical paths** (payments, inventory, balances, uniqueness); eventual for feeds/likes/analytics.
- Helpers: **single-writer/leader per entity, idempotency keys, optimistic concurrency (version/CAS), outbox + transactions**.

**Rule:** Use **etcd/ZooKeeper** for coordination, **Spanner/CockroachDB** for strong SQL at scale, or **tune quorums** (Cassandra QUORUM, DynamoDB ConsistentRead, Mongo majority) — and apply strong consistency **selectively**.

---

## Q: How do you achieve strong consistency? (simple)

**One line:** Funnel all writes through a **single agreed order** and make every read see a **majority** of replicas → a read can never miss the latest write.

### 3 core mechanisms
1. **Single leader:** all writes go through one leader → strict order, no conflicting concurrent writes.
2. **Majority quorum (Raft/Paxos):** confirm a write only after a majority store it; reads also consult a majority → **W + R > N** guarantees overlap with the latest write.
3. **Synchronous replication:** ack only **after** replicas persist — never from one node's memory.

### Safety nets
- **Leader leases / fencing** → stale old leader can't keep serving (no split-brain).
- **Synchronized clocks (Spanner TrueTime)** → for global strong consistency.

**Trade-off:** every op needs a coordination round-trip → **higher latency**; minority side refuses to serve under partition (CP).

**Mental model:** *one leader + majority agreement + don't ack until replicated.*

---

## Q: Explain Raft and Paxos quorum.

**Consensus** = make a cluster agree on a single ordered log despite failures. **Quorum (majority)** makes it safe.

### Quorum — the foundation
$$\text{quorum} = \lfloor N/2 \rfloor + 1$$
| N | Quorum | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

**Why it works:** any two majorities **always overlap** in ≥1 node → a new leader's majority includes a node that saw the last write (no data loss), and only **one** leader can win (no split-brain). Use **odd** sizes (3/5/7).

### Raft (built for understandability)
- **Roles:** Follower / Candidate / Leader; time split into **terms** (≤1 leader each).
- **Leader election:** on election timeout a follower becomes Candidate, requests votes; a **majority** → Leader. Randomized timeouts avoid split votes.
- **Log replication:** writes go to leader → `AppendEntries` to followers → committed once a **majority** ack.
- **Safety:** only a candidate with an up-to-date log can win → committed entries never overwritten.
- Used by: **etcd, Consul, CockroachDB, TiKV**.

### Paxos (the original, harder)
- **Roles:** Proposer / Acceptor / Learner. Basic Paxos = 2 phases:
  1. **Prepare/Promise:** proposer's number `n` gets a majority promise.
  2. **Accept/Accepted:** majority accepts value → **chosen**.
- **Multi-Paxos** chains it into a log with a stable leader. Used by: **Chubby, Spanner, Cassandra LWT**.

### Raft vs Paxos
| | Raft | Paxos |
|---|---|---|
| Design | Understandable, prescriptive | Theoretical, flexible |
| Leader | Strong, explicit | Optional (Multi-Paxos) |
| Adoption | etcd, Consul, CockroachDB | Chubby, Spanner |

Both need a **majority quorum**, tolerate `⌊N/2⌋` failures, are **CP** (halt writes if majority unreachable).

**Rule:** Both achieve agreement via a **majority quorum**; overlapping majorities → one leader, no lost data — at the cost of halting writes when a majority is unreachable.

---

## Q: Paxos looks like 2PC — what's the difference?

Both have a two-phase "propose → commit" shape, but solve **different problems**. The key difference: **2PC needs ALL participants; Paxos needs only a MAJORITY.**

### Different problems
- **2PC = atomic commit** across **different** resources (DB1, DB2, DB3 each hold *different* data) → **all must agree** to commit.
- **Paxos = consensus/replication** across **replicas** of the *same* data → only **enough (majority)** must agree.

### Why it matters
- **2PC:** one crashed/No participant → abort. Coordinator crashes mid-decision → participants **stuck holding locks** (blocking, not fault-tolerant). Coordinator is a **SPOF**.
- **Paxos:** value chosen on **majority** accept; tolerates `⌊N/2⌋` failures. Dead proposer → another takes over → **never permanently blocks**.

### Summary
| | 2PC | Paxos |
|---|---|---|
| Purpose | Atomic commit across **different** resources | Agree on a value across **replicas** |
| Agreement | **All** participants | **Majority** quorum |
| Fault tolerance | None | Tolerates `⌊N/2⌋` failures |
| Blocking? | Yes | No |

**In practice they combine:** Spanner runs **2PC across shards, each shard a Paxos group** → 2PC participants are themselves replicated/fault-tolerant, removing the SPOF.

**Rule:** 2PC asks *"can **everyone** commit?"* (blocks); Paxos asks *"can a **majority** agree?"* (fault-tolerant).

---

## Q: How does Spanner combine 2PC + Paxos? (removing 2PC's SPOF)

The trick is **layering**: Paxos solves "don't lose a node," 2PC solves "commit atomically across shards."

### The structure
- Data is split into **shards**. Each shard is **NOT one server** — it's replicated across 3–5 machines forming a **Paxos group** (1 leader + followers).
```
        2PC  ← atomicity ACROSS shards (horizontal)
       /    \
  Shard A   Shard B
    |          |
  Paxos     Paxos   ← HA/durability WITHIN each shard (vertical)
 (A1,A2,A3)(B1,B2,B3)
```
- **Paxos (vertical):** keeps each shard alive/consistent despite machine failures.
- **2PC (horizontal):** glues shard leaders together for atomic multi-shard transactions.

### Why it kills 2PC's blocking weakness
- **Plain 2PC:** a participant is one server; if it crashes after voting "yes," everyone is stuck holding locks (it held the only copy of its state).
- **Spanner:** each 2PC participant/coordinator is a **whole Paxos group**. If the leader (A1) dies mid-commit, **Paxos promotes A2** which already has the replicated prepare/commit log → new leader **resumes the 2PC**. No single machine's death can block it → **SPOF gone**.

**Rule:** **Paxos makes each participant fault-tolerant; 2PC makes the transaction atomic.** Together = atomic *and* highly-available distributed transactions.

---

## Q: Is Raft a different thing altogether (vs Paxos)?

**No — Raft solves the exact same problem as Paxos.** It's an alternative **consensus algorithm**, not a different category. Both = "replicas agree on an ordered log via majority quorum."

- Both use a **leader + majority quorum**, tolerate `⌊N/2⌋` failures, are **CP**, prevent split-brain/data loss.
- They're **interchangeable**: Spanner uses **Paxos** per shard; **CockroachDB/TiDB** build the same thing using **Raft** per shard.

### Why Raft exists
Paxos is notoriously hard to understand/implement. Raft (2014) = *"consensus made understandable"* — same guarantees, clearer structure.

| | Paxos | Raft |
|---|---|---|
| Philosophy | Theoretical, flexible | Practical, prescriptive |
| Leader | Optional (Multi-Paxos adds one) | Strong, explicit from start |
| Structure | One abstract primitive | Split: election + log replication + safety |
| Used by | Chubby, Spanner, Cassandra LWT | etcd, Consul, CockroachDB, TiKV |

### Mental grouping
- **{Paxos, Raft} = consensus** (majority, fault-tolerant, replicas of *same* data).
- **2PC = atomic commit** (unanimous, blocking, *different* resources) — the odd one out.

**Rule:** Raft ≠ new category — it's a **friendlier Paxos**. Anywhere Paxos fits (e.g. Spanner shards), Raft can replace it (e.g. CockroachDB).

---

## Q: How to achieve BOTH high availability and high consistency? (practical mechanisms)

CAP says no perfect C+A *during a partition*, but partitions are rare/brief → goal = **strong consistency + HA in the common case**, degrade only the minority side during a real partition.

### The core trick: consensus-replicated state machine (Raft/Paxos)
- **Consistency:** writes go through one leader, committed only after a **majority** ack → single ordered log, linearizable reads.
- **Availability:** leader dies → surviving majority **auto-elects a new leader in ms** → keeps serving.
- → As long as a **majority is alive**, you get both. (etcd, Spanner, CockroachDB.)

### 5 building blocks
1. **Replication + majority quorum (W+R>N):** copies = availability, majority = consistency.
2. **Automatic failover (leader election):** no manual recovery → failure barely dents availability.
3. **Odd clusters across AZs (3/5):** one zone down still leaves a majority alive.
4. **Sync replication to the quorum (not all):** majority ack = durable + consistent without one slow node blocking (2PC needs ALL → blocks).
5. **Sharding:** each shard its own consensus group → failure/hot-spot isolated, scales (Spanner = 2PC across shards, Paxos within).

### Practical guidance
- **Tier consistency:** strong (consensus/quorum) for payments/inventory/balances; eventual for feeds/likes/analytics.
- Keep services **stateless**, push state into a consensus store.
- Honest trade-off: strong consistency costs **latency** (majority round-trip); minority side stops serving under partition.

**Rule:** "Both" = **consensus-replicated state (Raft/Paxos) + majority quorum + multi-AZ sharding + auto-failover**, applied **selectively** to data that truly needs it.

---
