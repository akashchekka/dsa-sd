# System Design — Quick Revision

## Table of Contents

- [Q: All that I need to know about Kafka](#q-all-that-i-need-to-know-about-kafka)
- [Q: What if Kafka fails?](#q-what-if-kafka-fails)
- [Q: How do consumers replay events using offsets to recover missed notifications?](#q-how-do-consumers-replay-events-using-offsets-to-recover-missed-notifications)
- [Q: What if Redis fails?](#q-what-if-redis-fails)
- [Q: Trade-offs with Redis?](#q-trade-offs-with-redis)
- [Q: Load Balancing](#q-load-balancing)
- [Q: How to achieve High Availability and High Consistency in distributed systems? (FAANG)](#q-how-to-achieve-high-availability-and-high-consistency-in-distributed-systems-faang)
- [Q: Redundancy & failover (active-active vs active-passive, health checks, leader election)?](#q-redundancy--failover-active-active-vs-active-passive-health-checks-leader-election)
- [Q: Availability "nines" — downtime numbers (2 to 5 nines)?](#q-availability-nines--downtime-numbers-2-to-5-nines)
- [Q: How are Linearizability and Distributed Transactions (2PC/3PC) achieved?](#q-how-are-linearizability-and-distributed-transactions-2pc3pc-achieved)
- [Q: What is the Saga pattern?](#q-what-is-the-saga-pattern)
- [Q: What to use in production for strong consistency?](#q-what-to-use-in-production-for-strong-consistency)
- [Q: How do you achieve strong consistency? (simple)](#q-how-do-you-achieve-strong-consistency-simple)
- [Q: Explain Raft and Paxos quorum.](#q-explain-raft-and-paxos-quorum)
- [Q: How does Spanner combine 2PC + Paxos? (removing 2PC's SPOF)](#q-how-does-spanner-combine-2pc--paxos-removing-2pcs-spof)
- [Q: Is Raft a different thing altogether (vs Paxos)?](#q-is-raft-a-different-thing-altogether-vs-paxos)
- [Q: How to achieve BOTH high availability and high consistency? (practical mechanisms)](#q-how-to-achieve-both-high-availability-and-high-consistency-practical-mechanisms)
- [The catch: reads can still be stale](#the-catch-reads-can-still-be-stale)
- [Bottom line](#bottom-line)
- [Q: All I need to know about Cassandra (HLD interview)](#q-all-i-need-to-know-about-cassandra-hld-interview)
- [Q: Is Cassandra for write-heavy and Postgres/MySQL for read-heavy?](#q-is-cassandra-for-write-heavy-and-postgresmysql-for-read-heavy)
- [Q: Any DB that excels at write-heavy AND read-heavy with scaling and strong transactional consistency?](#q-any-db-that-excels-at-write-heavy-and-read-heavy-with-scaling-and-strong-transactional-consistency)
- [Q: Do Spanner / CockroachDB use Raft/Paxos + 2PC/3PC for strong consistency?](#q-do-spanner--cockroachdb-use-raftpaxos--2pc3pc-for-strong-consistency)
- [Q: Consistency in SQL?](#q-consistency-in-sql)
- [Quick Revision: B+ Trees, InnoDB vs PostgreSQL](#quick-revision-b-trees-innodb-vs-postgresql)
- [Q: Are quorum read/write and Raft the same thing?](#q-are-quorum-readwrite-and-raft-the-same-thing)
- [Q: Which DBs use Quorum R/W vs Raft vs Paxos?](#q-which-dbs-use-quorum-rw-vs-raft-vs-paxos)

---

## Q: All that I need to know about Kafka

**What it is:** Distributed, append-only **commit log** for streaming events. Producers write, consumers read by offset; messages stored durably and replayable. Decouples services, handles high throughput.

### Core concepts
- **Topic:** Named stream split into **partitions**.
- **Partition:** Ordered append-only log. **Order guaranteed only within a partition.**
- **Offset:** Sequential message ID in a partition (the bookmark).
- **Producer:** Partition chosen by key hash (same key → same partition → ordered).
- **Consumer group:** Each partition read by **exactly one** consumer in a group → parallelism = partition count.
- **Broker:** A Kafka server; cluster = many brokers.
- **Controller:** Metadata + leader election. Newer Kafka = **KRaft** (no ZooKeeper).

### Replication & durability
- Each partition: **leader** + **follower replicas** (`replication.factor`, usually 3).
- **ISR (In-Sync Replicas):** replicas caught up to leader; new leader elected from ISR on failure.
- `min.insync.replicas=2` + `acks=all` → no acknowledged data loss.

### Delivery guarantees
| Guarantee | How |
|---|---|
| At-most-once | Commit offset before processing (may lose) |
| **At-least-once** (default) | Commit after processing (may duplicate → need idempotent consumer) |
| Exactly-once (EOS) | Idempotent producer + transactions |

### Producer essentials
- `acks`: `0` fire-forget / `1` leader only / `all` safest. `enable.idempotence=true` → no duplicate writes on retry.
- Batching (`linger.ms`, `batch.size`) + compression for throughput. **Key decides partition → ordering.**

### Consumer essentials
- **Pull-based;** commit offset manually after success. `auto.offset.reset`: `earliest` (replay all) / `latest` (only new).
- **Rebalancing:** partitions reassigned when consumers join/leave (briefly pauses).

### Retention & replay
- Kept by **time** (`retention.ms`) or **size** (`retention.bytes`) — not deleted on read.
- **Log compaction:** keeps latest value per key. **Replay** = seek to older offset/timestamp.

### When to use / avoid
- **Use:** event streaming, log aggregation, decoupling microservices, high throughput, replay/audit.
- **Avoid:** simple request/response, small task queues (RabbitMQ/SQS), strict global ordering.

### Kafka vs RabbitMQ
| Kafka | RabbitMQ |
|---|---|
| Log retained, replayable | Message removed on ack |
| Pull-based, consumer groups | Push-based, smart broker |
| Huge throughput, ordered per partition | Flexible routing, lower throughput |

**Golden rules:** Order **per-partition**. Parallelism = **partition count**. Default **at-least-once** → make consumers **idempotent**. Durability = **replication + `acks=all` + `min.insync.replicas`**.

> Producer hashes key → picks partition → appends to that partition's log → each consumer group reads all partitions independently, splitting them among its consumers.

>  Kafka is a replayable, partitioned commit log — producers hash a key to a partition, consumers read independently by offset, order holds only within a partition, and durability comes from replication with `acks=all` + `min.insync.replicas`. Because it defaults to at-least-once, correctness hinges on making consumers idempotent.

---

## Q: What if Kafka fails?

Kafka survives most failures via **replication**; design clients to tolerate broker downtime.

- **Broker dies:** new leader auto-elected from ISR. `replication.factor=3`, `min.insync.replicas=2`, `acks=all` → no acknowledged loss.
- **Producer can't reach Kafka:** retries + `enable.idempotence=true`. Full outage → **Outbox pattern** (write event to DB in same txn, relay publishes later).
- **Consumer crashes:** resumes from last committed **offset**; make consumers **idempotent** (at-least-once).
- **Whole cluster down:** **multi-AZ/region** replication (MirrorMaker) + **backpressure** upstream.

| Failure | Mitigation |
|---|---|
| Single broker | `replication.factor≥3`, `acks=all` |
| Producer can't publish | Retries + idempotence, Outbox pattern |
| Consumer crash | Resume from offset, idempotent consumer |
| Full outage | Multi-AZ/region, Outbox in DB |

**Rule:** Never assume Kafka is up. Decouple writes with the **Outbox pattern**, make consumers **idempotent**, tune **replication + acks**.

>  Kafka tolerates most failures through partition replication and ISR-based leader election; the engineering job is to assume it can still go down — retry idempotently, decouple writes via the Outbox pattern, resume consumers from committed offsets, and replicate across AZs/regions.

---

## Q: How do consumers replay events using offsets to recover missed notifications?

Kafka **keeps messages** (not deleted on read); permanent **offset** lets consumers rewind and reprocess.

- **Why it works:** messages stay within the **retention window** (`retention.ms`); committed offset is just a bookmark.
- **How:** seek to earlier offset — `seek()`, `seekToBeginning()`, by timestamp, or `--reset-offsets`. New group + `auto.offset.reset=earliest` re-reads whole topic.
- **Safety:** replay can double-process → dedupe by unique key (`event_id`).
- **Patterns:** Dead Letter Topic for failures; commit offset **only after** a successful send.

**Rule:** Replay = **seek to offset** + **idempotent dedupe**.

>  Because Kafka retains messages independently of consumption, recovery is just rewinding to an older offset and reprocessing; the only requirement is idempotent dedupe so replayed events don't produce duplicate side effects.

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

>  Redis failures span lost in-memory data (softened by AOF+RDB), write loss on async failover (Sentinel/Cluster), and unreachability; treat it as a cache that gracefully falls back to the DB, and only lean on it as a datastore when you accept a small replication-loss window.

---

## Q: Trade-offs with Redis?

- **Memory (RAM-bound):** all in RAM → expensive, size-limited; large data needs sharding/eviction.
- **Durability vs performance:** in-memory fast but loses data on crash; AOF/RDB add I/O latency; AOF `everysec` loses ~1s.
- **Consistency vs availability:** async replication → failover can **lose recent writes**; forcing sync (`min-replicas-to-write`) cuts availability.
- **Single-threaded core:** one slow command (`KEYS *`, big `SORT`) **blocks everything**; no multi-core scaling per node.
- **Scaling:** vertical hits a RAM ceiling; Cluster adds horizontal scale but brings resharding + **cross-slot/multi-key limits**.
- **Ops overhead:** HA (Sentinel/Cluster), eviction tuning, fragmentation, persistence config.
- **Not a full DB:** no joins/complex queries — cache / fast-access layer, not primary relational store.

| Trade-off | Cost |
|---|---|
| In-memory speed | High RAM cost, size limits |
| Persistence | I/O overhead, small loss window |
| Async replication | Possible write loss on failover |
| Single-threaded | One slow command blocks all |
| Cluster scaling | Resharding + multi-key limits |

**Rule:** Redis trades **durability, consistency, and rich querying** for **raw speed and simplicity**. Design around RAM limits, async replication, and single-threaded execution.

>  Redis buys raw speed by keeping everything in RAM and running single-threaded, which is exactly why it trades away durability, strong consistency, unlimited size, and rich querying — design around those limits rather than fighting them.

---

## Q: Load Balancing

A **load balancer (LB)** distributes traffic for **availability, scalability, reliability**; hides backend failures, enables horizontal scaling.

### Layers
| Type | Layer | Routes by | Notes |
|---|---|---|---|
| **L4 (Transport)** | TCP/UDP | IP + port | Fast, no payload inspection |
| **L7 (Application)** | HTTP | URL, headers, cookies, path | Smart routing, SSL termination, slower |

### Algorithms
- **Round Robin** / **Weighted RR** (bigger servers get more).
- **Least Connections** (good for long-lived requests). **Least Response Time** (fastest server).
- **IP Hash / Consistent Hashing:** same client → same server (stickiness, cache locality).

### Key mechanisms
- **Health checks:** ping backends; remove unhealthy, re-add when healthy.
- **Sessions:** prefer **stateless servers + session in Redis/DB** over **sticky sessions** (affinity causes uneven load, breaks on server loss).
- **LB redundancy:** not a SPOF → active-passive/active-active + virtual IP (keepalived) or managed LB (AWS ELB/ALB/NLB).

### Types
- **Software:** Nginx, HAProxy, Envoy. **Hardware:** F5, Citrix. **DNS/GSLB:** cross-region geo-routing.

**Rule:** **L4** for raw speed, **L7** for content-based routing. Prefer **stateless servers + external session store**, run **health checks**, make the **LB redundant**.

>  A load balancer is the front door that hides backend failures and enables horizontal scale — use L4 for raw throughput and L7 for content routing, keep servers stateless with an external session store, health-check backends, and make the balancer itself redundant so it isn't a SPOF.

---

## Q: How to achieve High Availability and High Consistency in distributed systems? (FAANG)

### The core tension — CAP & PACELC
- **CAP:** during a **Partition**, choose **C** (reject/stale-error) or **A** (serve stale, reconcile). CP: ZooKeeper, etcd, Spanner, HBase. AP: Cassandra, DynamoDB, Riak.
- **PACELC:** if **P** → A or C; **E**lse (normal) → **L**atency or **C**onsistency (consistency costs latency even without failures).

### High Availability — how
- **Replication** across nodes/AZs/regions; **redundancy** (active-active / active-passive).
- **Automatic failover** via leader election (Raft/Paxos) + health checks.
- **Sharding** (one shard's failure ≠ whole system), **load balancing**, **geo-distribution**.
- **Graceful degradation:** stale cache, read-only mode, circuit breakers, retries w/ backoff + jitter.
- Measured in **nines** (99.99% ≈ 52 min/yr).

### High Consistency — how
- **Consensus (Paxos/Raft):** quorum agrees on an ordered log (etcd, Spanner).
- **Quorum reads/writes:** **W + R > N** guarantees read overlaps latest write (tunable).
- **Strong/linearizable** reads, **synchronous replication**, **2PC/3PC** for atomic cross-node commits (slow, blocking).
- Spectrum: Strong → Linearizable → Sequential → Causal → Read-your-writes → Eventual.

### Getting *both* (engineering around CAP)
- **Quorum tuning (W+R>N):** Dynamo/Cassandra — strong-ish + highly available.
- **Raft state machine:** consistent + available while a **majority** survives.
- **Spanner + TrueTime:** global strong consistency *and* HA (canonical example).
- **CRDTs / conflict resolution:** AP systems converge automatically.
- **Tiered:** strong for critical paths (payments, inventory), eventual for the rest.

### Interview framing
State **CAP/PACELC** → ask **strong or eventual** for this feature? → pick quorum / consensus / leaderless+CRDT → discuss failure modes (partition, failover, **split-brain** fenced by quorum/leases) → mention degradation + SLOs.

**Rule:** Can't beat CAP under a partition, but **quorums + consensus + per-feature consistency choices** give HA *and* strong consistency in the common case.

>  CAP/PACELC frames the whole trade-off — you can't have both C and A during a partition (and even normally consistency costs latency), so you achieve availability through replication + failover + degradation and consistency through quorums/consensus, then apply strong consistency selectively per feature.

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
- Probe nodes (HTTP/TCP heartbeat); missed checks → node declared dead → removed from rotation / triggers failover.

### Automatic leader election (Raft / Paxos)
- Primary dies → who's next? Two leaders = **split-brain** (conflicting writes).
- **Consensus:** nodes vote, a **majority quorum** agrees → only **one** leader → no split-brain; new leader has up-to-date log → no committed loss.
- **Raft** (etcd, Consul) vs **Paxos** (Spanner, Chubby). On a split, only the **majority** side elects/writes; minority steps down.

**Rule:** Redundancy = spare copies, health checks = detect failure, **consensus election = promote exactly one leader** (no split-brain) → real HA.

>  High availability is spare copies plus a safe way to use them — health checks detect failure, and consensus-based leader election promotes exactly one new leader so redundancy never degenerates into split-brain.

---

## Q: Availability "nines" — downtime numbers (2 to 5 nines)?

| Availability | Nines | Downtime / year | Downtime / month |
|---|---|---|---|
| 99% | two 9s | ~3.65 days | ~7.2 hours |
| 99.9% | three 9s | ~8.76 hours | ~43.8 min |
| 99.99% | four 9s | ~52.6 min | ~4.38 min |
| 99.999% | five 9s | ~5.26 min | ~26 sec |

- Each extra **9 cuts downtime 10×**. 3 nines ≈ SaaS baseline; 4 ≈ serious cloud; 5 ≈ telecom gold (expensive).
- $\text{Availability} = \frac{MTBF}{MTBF + MTTR}$ → fail less (**↑MTBF**) or recover faster (**↓MTTR**); fast failover mainly cuts MTTR.

**Memory hook:** 2→**3.65 days**, 3→**8.8 hrs**, 4→**52 min**, 5→**5 min** (each step ÷10).

>  Availability is measured in nines, where each extra nine cuts downtime tenfold; since availability = MTBF/(MTBF+MTTR), you improve it by failing less often or — more practically — recovering faster via automatic failover.

---

## Q: How are Linearizability and Distributed Transactions (2PC/3PC) achieved?

### Strong Consistency / Linearizability
Every op appears to take effect **instantly at one point**; all clients see the **same real-time order**; a completed write is visible to **all** later reads.

- **Single leader** serializes writes into a total order; reads go to leader or up-to-date followers.
- **Consensus + quorum (Raft/Paxos):** leader replicates to a **majority** before ack; reads touch a majority → **W + R > N** overlap.
- **Leases/fencing:** stop a stale old leader serving reads.
- **Spanner TrueTime:** GPS+atomic clocks; wait out clock-uncertainty window → globally linearizable.
- **Cost:** majority round-trip → higher latency; minority can't serve under partition (CP).

### Distributed Transactions — 2PC
Atomic all-or-nothing via a **coordinator**:
1. **Prepare (vote):** participants lock rows, log, reply Yes/No.
2. **Commit/Abort:** all Yes → commit; any No → abort.
- **Problems:** **blocking** (coordinator crash → participants stuck holding locks), **slow**, coordinator = **SPOF**.

### 3PC
Adds a **pre-commit** phase + timeouts → **non-blocking**, but more latency and **still breaks under partitions** → rarely used.

### Modern alternatives
- **Saga:** local transactions + **compensating actions** → eventual consistency (microservices).
- **Consensus commit:** Spanner runs 2PC **over Paxos groups** → no single-coordinator SPOF.

| Concept | How | Cost |
|---|---|---|
| Linearizability | Leader + quorum (W+R>N), leases, TrueTime | High latency, CP |
| 2PC | Coordinator: prepare→commit | Blocking, slow, SPOF |
| 3PC | + pre-commit + timeouts | More latency, fails on partition |
| Saga | Local txns + compensation | Eventual consistency |

**Rule:** Strong consistency = **single order via leader + majority quorum** (pay latency). Atomic cross-node = **2PC** (simple but blocking) or **Sagas** (non-blocking, eventually consistent).

>  Linearizability means every read sees the latest write in one global order, achieved by funneling writes through a leader that commits on a majority quorum; atomic multi-node commits use 2PC (simple but blocking) or, in microservices, Sagas (non-blocking but eventually consistent).

---

## Q: What is the Saga pattern?

Distributed transaction across microservices **without 2PC/global locks**: a **sequence of local transactions**, each with a **compensating action** to undo it if a later step fails → **eventual consistency**.

### Example: Place Order
| Step | Local txn | Compensation |
|---|---|---|
| 1 | Create order (pending) | Cancel order |
| 2 | Reserve inventory | Release inventory |
| 3 | Charge payment | Refund payment |
| 4 | Schedule shipping | Cancel shipping |

Payment fails → run compensations for steps 2 & 1.

### Two coordination styles
- **Choreography (event-driven):** no coordinator; each service reacts to an event, does its step, emits the next. Simple, loosely coupled, hard to trace at scale.
- **Orchestration (centralized):** an orchestrator directs each step + triggers compensations. Clear control flow, but an extra (must-be-HA) component.

### Key properties
- Steps + compensations must be **idempotent** (replays); some actions can't fully undo (sent email → send apology).
- **No isolation** → intermediate state visible; mitigate with **semantic locks / status flags** (order = PENDING).
- Built on **durable messaging** (Kafka + outbox).

### Saga vs 2PC
| | Saga | 2PC |
|---|---|---|
| Consistency | Eventual | Strong (atomic) |
| Locks | None | Holds locks across phases |
| Blocking | Non-blocking | Blocks on coordinator crash |
| Isolation | None (semantic locks) | Yes |
| Fit | Microservices, long workflows | Single transaction boundary |

**Rule:** Saga trades **atomicity + isolation** for **availability + no distributed locks** via **local commits + compensating undos**. Orchestration for complex flows, choreography for simple; keep every step **idempotent**.

>  A Saga replaces a distributed transaction with a chain of local transactions plus compensating undos, trading atomicity and isolation for availability and no global locks — use orchestration for complex flows, choreography for simple ones, and keep every step idempotent.

---

## Q: What to use in production for strong consistency?

Don't hand-roll Paxos — pick proven tech and configure it.

### Coordination / metadata (consensus backbone)
- **etcd** (Raft, backs Kubernetes), **ZooKeeper** (ZAB), **Consul** (Raft) — leader election, locks, config, service discovery. Small critical state, not bulk data.

### Strongly-consistent databases
- **Spanner** — global strong consistency via **TrueTime** (gold standard).
- **CockroachDB / YugabyteDB** — open-source Spanner-like, Raft per range, serializable SQL.
- **PostgreSQL / MySQL** — single-node ACID; scale via **synchronous replication**.

### Tunable-consistency DBs (configure for strong)
- **DynamoDB:** `ConsistentRead=true`; Transactions API for ACID.
- **Cassandra:** **`QUORUM` read + write (W+R>N)** → strong; `LOCAL_QUORUM` per region.
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
- Strong consistency **only on critical paths** (payments, inventory, balances, uniqueness); eventual elsewhere.
- Helpers: **single-writer/leader per entity, idempotency keys, optimistic concurrency (version/CAS), outbox + transactions**.

**Rule:** **etcd/ZooKeeper** for coordination, **Spanner/CockroachDB** for strong SQL at scale, or **tune quorums** (Cassandra QUORUM, DynamoDB ConsistentRead, Mongo majority) — applied **selectively**.

>  In practice you don't implement consensus yourself — use etcd/ZooKeeper for coordination, Spanner/CockroachDB for strong SQL at scale, or tune quorums on Cassandra/DynamoDB/Mongo — and reserve strong consistency for the critical paths that truly need it.

---

## Q: How do you achieve strong consistency? (simple)

**One line:** Funnel all writes through a **single agreed order** and make every read see a **majority** → a read can never miss the latest write.

### 3 core mechanisms
1. **Single leader:** all writes ordered → no conflicting concurrent writes.
2. **Majority quorum (Raft/Paxos):** commit only after a majority stores it; reads consult a majority → **W + R > N** overlap.
3. **Synchronous replication:** ack only **after** replicas persist — never from one node's memory.

### Safety nets
- **Leader leases / fencing** → no stale leader serving (no split-brain).
- **Synchronized clocks (Spanner TrueTime)** → global strong consistency.

**Trade-off:** coordination round-trip → **higher latency**; minority refuses to serve under partition (CP).

**Mental model:** *one leader + majority agreement + don't ack until replicated.*

>  The essence of strong consistency is one leader ordering all writes, a majority persisting each write before it's acknowledged, and reads consulting a majority so they can never miss the latest write — paid for with a coordination round-trip of latency.

---

## Q: Explain Raft and Paxos quorum.

**Consensus** = a cluster agrees on a single ordered log despite failures. **Majority quorum** makes it safe.

### Quorum — the foundation
$$\text{quorum} = \lfloor N/2 \rfloor + 1$$
| N | Quorum | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

**Why it works:** any two majorities **overlap** in ≥1 node → a new leader's majority saw the last write (no loss), and only **one** leader can win (no split-brain). Use **odd** sizes (3/5/7).

### Raft (built for understandability)
- **Roles:** Follower / Candidate / Leader; time split into **terms** (≤1 leader each).
- **Election:** on timeout a follower becomes Candidate, requests votes; **majority** → Leader. Randomized timeouts avoid split votes.
- **Log replication:** writes → leader → `AppendEntries` → committed once a **majority** ack.
- **Safety:** only an up-to-date candidate can win → committed entries never overwritten.
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

**Rule:** Both agree via a **majority quorum**; overlapping majorities → one leader, no lost data — at the cost of halting writes when a majority is unreachable.

>  Consensus makes a cluster agree on one ordered log by requiring a majority quorum; because any two majorities overlap, exactly one leader can win and no committed entry is ever lost, at the price of halting writes when a majority is unreachable.

---

## Q: How does Spanner combine 2PC + Paxos? (removing 2PC's SPOF)

**Layering:** Paxos solves "don't lose a node," 2PC solves "commit atomically across shards."

### The structure
- Data split into **shards**; each shard is replicated across 3–5 machines as a **Paxos group** (1 leader + followers).
```
        2PC  ← atomicity ACROSS shards (horizontal)
       /    \
  Shard A   Shard B
    |          |
  Paxos     Paxos   ← HA/durability WITHIN each shard (vertical)
 (A1,A2,A3)(B1,B2,B3)
```
- **Paxos (vertical):** keeps each shard alive/consistent despite machine failures.
- **2PC (horizontal):** glues shard leaders for atomic multi-shard transactions.

### Why it kills 2PC's blocking weakness
- **Plain 2PC:** participant = one server; crash after "yes" → everyone stuck holding locks.
- **Spanner:** each participant is a **whole Paxos group**. Leader (A1) dies mid-commit → **Paxos promotes A2** (has the replicated prepare/commit log) → resumes the 2PC. No single death blocks it → **SPOF gone**.

**Rule:** **Paxos makes each participant fault-tolerant; 2PC makes the transaction atomic** → atomic *and* highly-available distributed transactions.

>  Spanner removes 2PC's blocking SPOF by making every transaction participant a Paxos group rather than a single server — Paxos keeps each shard alive (vertical), 2PC glues shard leaders for atomic multi-shard commits (horizontal), so a leader crash mid-commit is just a fast re-election.

---

## Q: Is Raft a different thing altogether (vs Paxos)?

**No — Raft solves the same problem as Paxos.** An alternative **consensus algorithm**: "replicas agree on an ordered log via majority quorum."

- Both: **leader + majority quorum**, tolerate `⌊N/2⌋` failures, **CP**, no split-brain/data loss.
- **Interchangeable:** Spanner uses **Paxos** per shard; CockroachDB/TiDB use **Raft** per shard.

### Why Raft exists
Paxos is hard to understand/implement. Raft (2014) = *"consensus made understandable"* — same guarantees, clearer structure.

| | Paxos | Raft |
|---|---|---|
| Philosophy | Theoretical, flexible | Practical, prescriptive |
| Leader | Optional (Multi-Paxos adds one) | Strong, explicit from start |
| Structure | One abstract primitive | Split: election + log replication + safety |
| Used by | Chubby, Spanner, Cassandra LWT | etcd, Consul, CockroachDB, TiKV |

### Mental grouping
- **{Paxos, Raft} = consensus** (majority, fault-tolerant, replicas of *same* data).
- **2PC = atomic commit** (unanimous, blocking, *different* resources) — the odd one out.

**Rule:** Raft ≠ new category — a **friendlier Paxos**. Anywhere Paxos fits (Spanner shards), Raft can replace it (CockroachDB).

>  Raft isn't a new category — it's a more understandable Paxos solving the identical problem (majority-quorum agreement over a replicated log); the real conceptual split is consensus (Raft/Paxos, majority, same data) versus 2PC (unanimous, blocking, different resources).

---

## Q: How to achieve BOTH high availability and high consistency? (practical mechanisms)

Partitions are rare/brief → goal = **strong consistency + HA in the common case**, degrade only the minority side during a real partition.

### The core trick: consensus-replicated state machine (Raft/Paxos)
- **Consistency:** writes through one leader, committed only after a **majority** ack → single ordered log, linearizable reads.
- **Availability:** leader dies → surviving majority **auto-elects a new leader in ms**.
- → Majority alive = both. (etcd, Spanner, CockroachDB.)

### 5 building blocks
1. **Replication + majority quorum (W+R>N):** copies = availability, majority = consistency.
2. **Automatic failover (leader election):** no manual recovery.
3. **Odd clusters across AZs (3/5):** one zone down still leaves a majority.
4. **Sync replication to the quorum (not all):** majority ack = durable + consistent without one slow node blocking (2PC needs ALL → blocks).
5. **Sharding:** each shard its own consensus group → isolated + scalable (Spanner = 2PC across, Paxos within).

### Practical guidance
- **Tier consistency:** strong for payments/inventory/balances; eventual for feeds/likes/analytics.
- Keep services **stateless**, push state into a consensus store.
- Trade-off: strong consistency costs **latency** (majority round-trip); minority stops serving under partition.

**Rule:** "Both" = **consensus-replicated state (Raft/Paxos) + majority quorum + multi-AZ sharding + auto-failover**, applied **selectively**.

>  You get both HA and strong consistency in the common case with a consensus-replicated state machine — a majority quorum spread over odd-numbered nodes across AZs, sharded for scale, with automatic failover — accepting that during a real partition only the majority side keeps serving.

### The catch: reads can still be stale

Naively serving a read from "the leader" is **not** automatically linearizable:

- **Stale leader problem:** a leader may have been deposed (network partition) but doesn't know it yet. Another leader was elected on the majority side. If the old leader answers a read from local state → it returns **stale data** → breaks linearizability.

Raft fixes this with one of:

| Technique | How it guarantees fresh reads |
|---|---|
| **ReadIndex** | Before replying, leader confirms it's still leader by exchanging a heartbeat round with a **majority**, then serves the read. |
| **Leader leases** | Time-bounded lease; within it the leader knows no other leader exists → can serve reads locally without a round-trip. |
| **Read through the log** | Treat the read as a log entry that must be committed → strongest, but slowest. |

### Bottom line

$$\text{Raft} + \text{leader reads via ReadIndex/lease} = \textbf{linearizable (strong)}$$

Raft's majority commit gives you a strongly-consistent **write order and durability out of the box**; you get strongly-consistent **reads only if you route them through the leader with ReadIndex or a lease**. That's exactly why your guide's rule holds: *one leader + majority agreement + don't ack until replicated* — plus **fence the leader** so stale reads can't sneak through.

Strong consistency isn't guaranteed by where the read is served — it's guaranteed by the follower synchronizing its apply progress to a leader-verified commit point first. The leader still anchors correctness (it certifies "I'm leader, here's the committed index"); the follower just serves the bytes once it's provably caught up.

---

## Q: All I need to know about Cassandra (HLD interview)

**One-liner:** Distributed, **wide-column, leaderless (masterless)** NoSQL for **high availability, linear horizontal scale, heavy writes**, across multiple DCs. **Dynamo (architecture) + BigTable (data model)**. **AP** with **tunable consistency**.

### Architecture — why it's HA
- **Leaderless / peer-to-peer:** every node equal, any node serves any request (as **coordinator**) → **no SPOF**.
- **Consistent hashing ring:** partitioned by hash of the **partition key**; each node owns token ranges. Add/remove nodes moves minimal data → **linear scale**.
- **Replication factor (RF):** each row on **N nodes** (usually 3), walking the ring; multi-DC aware (`NetworkTopologyStrategy`).
- **Gossip:** peer-to-peer failure/membership detection.
- **Hinted handoff:** replica down → coordinator stores a hint, replays on return.
- **Read repair + anti-entropy (Merkle trees):** background reconciliation keeps replicas convergent.

### Tunable consistency (the money topic)
Set per query via `W` (write) and `R` (read) levels: **W + R > N → strong consistency**.

| Level | Meaning |
|---|---|
| `ONE` | 1 replica acks — fast, weak |
| `QUORUM` | ⌊N/2⌋+1 replicas — strong if used for R & W |
| `LOCAL_QUORUM` | quorum **within local DC** — strong + avoids cross-DC latency (common in prod) |
| `ALL` | every replica — strongest, lowest availability |

- `QUORUM` R + `QUORUM` W → strong; `ONE`/`ONE` → eventual, max speed/availability.
- **Gold line:** *"AP by default, but `LOCAL_QUORUM` R+W gives strong-ish consistency without losing multi-DC availability."*

### Data model — query-first (biggest trap)
Model tables around **queries, not entities**. No joins; denormalize and duplicate freely.
- **Primary key = partition key + clustering columns.**
  - **Partition key** → which node (must be in `WHERE`); determines distribution.
  - **Clustering columns** → sort order **within** a partition.
- **Rules:** one table per query pattern; partition key with **high cardinality + even distribution** (avoid **hot partitions**); keep partitions bounded; writes are cheap → duplicate.

### Write & read path (LSM-tree)
- **Write:** commit log (durability) → **memtable** → flushed to immutable **SSTables**. No read-before-write → **very fast, append-only**.
- **Read:** merge memtable + SSTables by timestamp; **bloom filters** skip irrelevant SSTables.
- **Compaction:** merges SSTables, drops tombstones. **Conflict resolution = last-write-wins** by timestamp.

### Choose it when
Write-heavy + HA + horizontal scale + **known query patterns**: time-series/IoT/metrics, chat/message history, activity feeds, order/event history, catalogs, audit/fraud logs.

### Avoid it when
- No joins / ad-hoc queries / aggregations.
- Multi-key **transactions** (only slow Paxos-based **LWT** `IF NOT EXISTS` — use sparingly).
- Poor key → **hot partitions**; delete-heavy → **tombstone** read pain.
- Highly relational or low-scale apps (Postgres is simpler).

### 60-second interview framing
1. Why: high write throughput + HA + horizontal scale.
2. How: leaderless + consistent hashing → no SPOF, linear scale.
3. Model: table per query; partition key `X` (even distribution), clustering by `Y`.
4. Consistency: `LOCAL_QUORUM` R+W for strong-ish, or `ONE` for speed.
5. Trade-off: no joins/ad-hoc, weak multi-key txns — fine, access patterns known.

### Cassandra vs alternatives
| Need | Pick |
|---|---|
| HA + write-heavy + known queries | **Cassandra** |
| Managed/serverless on AWS | **DynamoDB** (same Dynamo lineage) |
| Strong consistency + SQL + txns | **Spanner / CockroachDB** |
| Rich queries/relations, moderate scale | **PostgreSQL** |
| Caching / ultra-low latency | **Redis** |

**Rule:** Cassandra = **Dynamo availability + BigTable model** → leaderless, consistent-hashing, tunable-consistency, write-optimized store you **model query-first**.

> "Cassandra is inherently optimized for writes through its LSM-tree storage engine. For reads, performance depends on schema design. We model tables around query patterns, choose a partition key that distributes data evenly and lets us locate the correct node quickly, and use clustering keys to keep data sorted within a partition. This avoids scans and makes reads efficient."

> The partition key identifies a logical partition. Cassandra hashes that key to determine which node stores the partition. Each node can store millions of partitions, so the number of partitions is much larger than the number of nodes.

---

## Q: Is Cassandra for write-heavy and Postgres/MySQL for read-heavy?

**Mostly right, but nuanced** — it's more about data model + scaling than a strict read/write split.

- **Cassandra → write-heavy + scale:** **LSM-tree** storage (append-only, no read-before-write), leaderless horizontal scaling, tunable consistency. Excels at high write throughput and HA.
- **PostgreSQL / MySQL → relational + complex reads:** **B-tree** storage, strong **ACID**, joins/aggregations/ad-hoc queries. Suit transactional and read-heavy workloads — though they scale reads well too (replicas), and can handle plenty of writes on a single node.

| | Cassandra | PostgreSQL / MySQL |
|---|---|---|
| Storage engine | LSM-tree (append-only) | B-tree |
| Strength | Write-heavy, HA, horizontal scale | Relational, ACID, complex reads/joins |
| Scaling | Leaderless, linear | Vertical + read replicas |
| Consistency | Tunable (AP default) | Strong (CP, ACID) |

**Rule:** Frame it as **"Cassandra = write-heavy + scale"** vs **"Postgres/MySQL = relational, consistent, complex reads"** — not a strict read-vs-write dichotomy.

>  It's directionally correct — Cassandra's LSM-tree and leaderless scaling make it write-heavy and highly scalable, while Postgres/MySQL's B-tree + ACID make them ideal for relational, consistent, complex-read workloads — but both relational engines scale reads well too, so it's really a data-model and scaling choice, not a pure read/write split.

---

## Q: Any DB that excels at write-heavy AND read-heavy with scaling and strong transactional consistency?

**No single DB is perfect at everything** (CAP/PACELC tradeoffs), but **NewSQL / distributed SQL** databases come closest.

| Database | Strengths | Notes |
|---|---|---|
| **Google Spanner** | Global horizontal scale, strong ACID, high read+write throughput | Gold standard; uses **TrueTime** (GPS + atomic clocks); GCP-locked |
| **CockroachDB** | Distributed SQL, strong consistency, scales reads + writes | Open-source, Spanner-inspired; Raft per range |
| **YugabyteDB** | Postgres-compatible, distributed, strong consistency | Horizontal scaling |
| **TiDB** | MySQL-compatible distributed SQL | Good for **HTAP** (transactional + analytical) |

**Trade-off:** they achieve this at the cost of **higher write latency** (consensus like Raft/Paxos + cross-shard 2PC) and **operational complexity** versus single-node Postgres or a purpose-built store like Cassandra.

**Rule:** Want scale + strong ACID + both read/write heavy → **distributed SQL (Spanner / CockroachDB / YugabyteDB / TiDB)**, accepting extra latency and ops overhead.

>  No database wins on every axis because of CAP/PACELC, but distributed SQL systems — Spanner, CockroachDB, YugabyteDB, TiDB — get closest to scalable, strongly-consistent read- and write-heavy workloads, paying for it with consensus-driven write latency and operational complexity.

---

## Q: Do Spanner / CockroachDB use Raft/Paxos + 2PC/3PC for strong consistency?

**Yes — a layered combination, but NOT 3PC** (3PC is largely theoretical, not used in production).

### Two distinct layers
1. **Replication / consensus (per shard/range)** → keeps replicas of a single data range consistent:
   - Spanner → **Paxos**
   - CockroachDB → **Raft**
2. **Distributed transactions (across shards/ranges)** → **2PC** coordinates atomic commit spanning multiple consensus groups.

### Ordering / isolation layer (the key differentiator)
- Spanner → **TrueTime** (GPS + atomic clocks) → external consistency / linearizability.
- CockroachDB → **Hybrid Logical Clocks (HLC)** → order transactions without special hardware.

| Layer | Purpose | Spanner | CockroachDB |
|---|---|---|---|
| Replica agreement | Keep a shard's replicas consistent | Paxos | Raft |
| Cross-shard atomicity | Atomic multi-shard commit | 2PC | 2PC (Parallel Commits) |
| Global ordering | Serializable / linearizable order | TrueTime | HLC |

**Rule:** **Paxos/Raft** for replica agreement, **2PC** for cross-shard atomicity, **TrueTime/HLC** for global ordering — CockroachDB also uses **Parallel Commits** to shave a 2PC round-trip.

>  Correct in spirit: both layer consensus (Paxos in Spanner, Raft in CockroachDB) for per-shard replica agreement with 2PC for cross-shard atomicity, plus a clock layer (TrueTime vs HLC) for global ordering — but nobody uses 3PC in production, and CockroachDB optimizes 2PC with Parallel Commits.

---

## Q: Consistency in SQL?

- Distributed consistency (multi-node SQL)

Single-node ACID relies on the above; across nodes SQL engines add:

Synchronous replication — commit only after replica(s) persist.
2PC — atomic commit across shards/databases.
Consensus (Raft/Paxos) — in distributed SQL (Spanner, CockroachDB) for a single ordered, linearizable log.

> SQL guarantees consistency by wrapping work in ACID transactions — enforcing constraints, isolating concurrent access via locking or MVCC, and using a write-ahead log for crash recovery — so the database only ever transitions between valid states.

--- 

## Quick Revision: B+ Trees, InnoDB vs PostgreSQL

### 1. B+ Tree Basics

| Concept                         | Explanation                                                                                           |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Every index is a B+ Tree**    | Each `CREATE INDEX` creates a separate B+ Tree.                                                       |
| **Why separate trees?**         | Each index is sorted on a different column(s). One tree cannot be sorted by both `name` and `salary`. |
| **One table, multiple indexes** | 1 table + 3 indexes = 3 independent B+ Trees.                                                         |
| **Leaf nodes**                  | Contain the information needed to fetch the row (actual row or pointer, depending on the database).   |
| **Internal nodes**              | Store only keys and child pointers for navigation.                                                    |

---

### 2. MySQL (InnoDB) vs PostgreSQL

| Feature                    | MySQL (InnoDB)                              | PostgreSQL                                    |
| -------------------------- | ------------------------------------------- | --------------------------------------------- |
| Table Storage              | **Clustered B+ Tree**                       | **Heap (separate table)**                     |
| Primary Key                | Clustered Index                             | Regular B+ Tree Index                         |
| Primary Key Leaf Nodes     | **Actual rows**                             | **TID (pointer to heap row)**                 |
| Secondary Index Leaf Nodes | Indexed key + **Primary Key**               | Indexed key + **TID**                         |
| Row Lookup                 | Secondary Index → Primary Key B+ Tree → Row | Index → Heap → Row                            |
| Heap                       | ❌ No (table is the clustered index)         | ✅ Yes                                         |
| Clustered Index            | ✅ Yes                                       | ❌ No (only `CLUSTER` command, not maintained) |

---

### 3. Secondary Index Lookup

| MySQL (InnoDB)                                                   | PostgreSQL                      |
| ---------------------------------------------------------------- | ------------------------------- |
| Secondary Index → Primary Key → Primary Key B+ Tree → Actual Row | Index → TID → Heap → Actual Row |

---

### 4. SQL Example

```sql
CREATE TABLE Employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    salary INT
);

CREATE INDEX idx_name ON Employees(name);

CREATE INDEX idx_salary ON Employees(salary);
```

Internally:

* **Primary Key** → One B+ Tree
* **idx_name** → Another B+ Tree
* **idx_salary** → Another B+ Tree

Each is **independent** and sorted by its own key.

---

### 5. Interview One-liners

| Topic                        | One-liner                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| B+ Tree                      | Internal nodes store only keys; leaf nodes store the actual row or a pointer to it.            |
| Every index                  | Every index is implemented as its own B+ Tree.                                                 |
| InnoDB                       | The clustered B+ Tree **is the table**; leaf nodes contain the full rows.                      |
| PostgreSQL                   | The table is a heap; B+ Tree leaf nodes contain a **Tuple ID (TID)** pointing to the heap row. |
| Secondary Index (InnoDB)     | Leaf nodes store the indexed key and the **primary key** of the row.                           |
| Secondary Index (PostgreSQL) | Leaf nodes store the indexed key and the **TID** of the row.                                   |

### Memory Trick

| Database       | Think of it as...                      |
| -------------- | -------------------------------------- |
| **InnoDB**     | **B+ Tree = Table**                    |
| **PostgreSQL** | **Heap = Table, B+ Tree = Lookup Map** |

---

## Q: Are quorum read/write and Raft the same thing?

They **share the same underlying idea (overlapping quorums)** but are **two different mechanisms operating at different layers** — one leaderless, one leader-based.

### Two separate mechanisms
| | Quorum R/W (Dynamo-style) | Raft |
|---|---|---|
| Category | **Leaderless** replication | **Leader-based** consensus |
| Coordinator | None — client writes to W nodes, reads from R | Single **leader** orders all writes |
| Quorum meaning | Tunable **W** and **R**, need `W + R > N` | Fixed **majority** (⌊N/2⌋+1) |
| Ordering | **No total order** (conflicts possible) | **Total order** (single log) |
| Conflicts | LWW / version vectors / CRDTs | Impossible — leader serializes |
| Result | Overlap → **strong-ish** | Overlap **+ ordering** → **linearizable** |
| Examples | Cassandra, DynamoDB, Riak | etcd, CockroachDB, Spanner, Consul |

### The shared foundation
Both rely on **"any two quorums intersect"**:
$$W + R > N \;\text{(Dynamo)} \qquad \text{majority} + \text{majority} \;\text{(Raft)}$$
That overlap is what guarantees a read can never miss the latest write.

### The difference: ordering
- **Quorum R/W alone** = overlap **without** ordering → two concurrent writes to the same key produce conflicting versions that get reconciled later (LWW / vector clocks / CRDTs). Not linearizable on its own.
- **Raft** adds a **leader-imposed total order** *before* the majority commits → no conflicts can exist → true linearizability.

### How they relate
- Quorum R/W is a **standalone replication strategy** — it runs with **no consensus algorithm at all** (Cassandra has no Raft leader).
- Raft **internally uses a majority quorum** for log replication, but wraps it with leader election + log ordering; reads get freshness via **ReadIndex/leader lease**, not a tunable `R`.
- They're **alternative points on the spectrum**, not layers you stack: pick **leaderless quorum** for availability + tunable consistency, or **Raft/Paxos** for a single ordered, linearizable history.

**Rule:** Same quorum math, different machinery — **quorum R/W = leaderless overlap** (strong-ish, tunable, conflicts possible) vs **Raft = leader + majority + total order** (linearizable). Choose one; you don't combine them.

> Quorum read/write and Raft are separate mechanisms that both exploit the same overlapping-quorum math. Quorum R/W is leaderless replication giving overlap without ordering (strong-ish, conflicts possible); Raft is leader-based consensus that uses a majority quorum plus a total order to give true linearizability. You pick one approach or the other — you don't stack them.

---

## Q: Which DBs use Quorum R/W vs Raft vs Paxos?


### Quorum Read/Write (leaderless, Dynamo-style)
- **Amazon DynamoDB** (the original Dynamo lineage)
- **Apache Cassandra**
- **ScyllaDB** (Cassandra-compatible)
- **Riak**
- **Voldemort** (LinkedIn, now retired)
- **Aerospike**
> By default writes propagate to replicas asynchronously (eventual consistency), but tuning W + R > N (e.g. QUORUM reads + writes) forces enough replicas to overlap synchronously, giving strong consistency.

> Configuration: The main configuration knobs are the replication factor N, the write quorum W, and the read quorum R. By adjusting W and R, we trade off consistency, latency, and availability. If we need strong quorum-based reads, we configure them so that W + R > N, ensuring every read quorum intersects every completed write quorum. For write-heavy or read-heavy workloads, we can bias the configuration by choosing a smaller W or a smaller R respectively, as long as the required consistency guarantees are met.

| Configuration                     |  N |  W |  R | `W + R > N` |
| --------------------------------- | -: | -: | -: | :---------: |
| Highest Availability              |  3 |  1 |  1 |      ❌      |
| Balanced / Strong Consistency     |  3 |  2 |  2 |      ✅      |
| **Write-optimized** (Fast Writes) |  3 |  1 |  3 |      ✅      |
| **Read-optimized** (Fast Reads)   |  3 |  3 |  1 |      ✅      |


### Raft (leader-based consensus)
- **etcd** (backs Kubernetes)
- **Consul** (HashiCorp)
- **CockroachDB** (Raft per range)
- **TiDB / TiKV**
- **YugabyteDB**
- **RethinkDB**
- **MongoDB** (Raft-*like* election protocol for replica sets)
- **Redis Raft** (module) / **RabbitMQ** quorum queues
> With Raft-powered DBs you get strong consistency out of the box, so there's no forced eventual consistency — but you can still opt into stale reads (follower/bounded-staleness reads, async cross-region replicas) when you want lower latency, and cross-shard reads need an extra ordering layer(2PC) to stay globally consistent.

> Raft within shards + 2PC across shards gives cross-region strong consistency (that's literally Spanner/CockroachDB), but you pay in WAN latency, longer lock windows, lower availability under partition, and complexity — so minimize it with geo-partitioning so most transactions stay single-region.

### Paxos (the other consensus family)
- **Google Spanner** (Paxos per shard)
- **Google Chubby**
- **Apache ZooKeeper** (ZAB — a Paxos-like protocol)
- **Cassandra LWT** (`IF NOT EXISTS` lightweight transactions use Paxos)

**Rule:** *Dynamo family = quorum R/W (Cassandra, DynamoDB, Riak); coordination + distributed SQL = Raft (etcd, Consul, CockroachDB); Google stack = Paxos (Spanner, Chubby, ZooKeeper).*

---

## Q. Scaling Writes?

**Scaling writes** in a distributed system is primarily about ensuring that incoming write requests are spread across multiple machines instead of overwhelming a single server. The first step is to choose a storage system that matches the workload—for example, a write-optimized distributed database such as Cassandra for high-ingestion workloads. Data is then horizontally partitioned (sharded) using a partition key so that different records are written to different nodes, allowing write throughput to grow simply by adding more machines to the cluster.

However, partitioning alone is not always sufficient. If a single record or key becomes extremely popular (for example, a viral post receiving millions of likes or an ad receiving millions of impressions), all writes may still be routed to the same partition, creating a **hotspot**. To eliminate this bottleneck, the system can shard the hot key itself by adding a salt or shard identifier, effectively distributing writes for that logical entity across multiple partitions. This ensures that no single node becomes overloaded while maintaining high write throughput.

For very large-scale systems, an additional buffering layer is often introduced. Instead of writing every request directly to the database, writes are first absorbed by a high-throughput cache, message queue, or log (such as Redis or Kafka). Background workers then batch, aggregate, or asynchronously persist these writes to the database. This reduces write amplification, smooths traffic spikes, improves resilience during bursts, and allows the database to process larger, more efficient batches rather than millions of individual write operations.

> **To scale writes in a distributed system, the goal is to avoid concentrating all write traffic on a single node or partition. This is typically achieved by horizontally scaling the storage layer, choosing a write-optimized database when appropriate, partitioning (sharding) data across multiple nodes using a well-designed partition key, and distributing hot keys across multiple shards if they become write hotspots. Systems may also buffer writes using caches or message queues and persist them asynchronously in batches to reduce pressure on the database. Together, these techniques increase write throughput, eliminate bottlenecks, and allow the system to scale horizontally as traffic grows.**

### For SQL databases

The first approach is still to **scale vertically** (more CPU, memory, faster disks). Once that reaches its limit, you **scale horizontally** by partitioning (sharding) the data across multiple database instances. Each shard owns a subset of the data based on a shard key (e.g., `customer_id`, `tenant_id`, or `region`). This distributes writes across multiple SQL servers instead of sending every write to a single database.

However, SQL databases also suffer from **hotspots**. If millions of writes target the same row (e.g., incrementing a "likes" counter), that row becomes a bottleneck due to row locks, index updates, transaction contention, and I/O. The same solution applies—**shard the hot data**. Instead of one counter row, maintain multiple counter rows (or buckets), distribute writes across them, and aggregate them when reading. The concept is identical to salting in NoSQL, although the implementation may use multiple rows or tables rather than partition keys.

For very high write throughput, SQL systems are also commonly combined with **asynchronous architectures**. Applications write to a queue (Kafka, RabbitMQ, etc.) or an in-memory store (Redis), and background workers batch inserts or updates into the SQL database. Batching drastically reduces transaction overhead, improves throughput, and smooths traffic spikes. This is especially useful for analytics events, logs, clickstreams, and counters where slight delays are acceptable.

### Interview summary

A good way to answer is:

> "The core principles of write scaling are the same for both SQL and NoSQL: distribute writes across multiple machines, avoid hotspots, and buffer or batch writes when possible. The difference is that NoSQL databases often provide built-in horizontal partitioning and are optimized for high write throughput, whereas SQL databases require explicit sharding strategies and must also account for transactions, row locking, and stronger consistency guarantees."

---

## Q. How do you scale writes while maintaining low latency?

> I would horizontally partition writes across multiple nodes using a well-chosen shard key to distribute load and reduce contention. For hot keys, I'd shard the key itself to eliminate hotspots. If the workload allows, I'd buffer writes through a cache or message queue and persist them asynchronously in batches. These techniques keep write latency low by preventing any single node from becoming overloaded. The trade-offs include increased operational complexity, more expensive cross-shard operations, and, when using asynchronous pipelines, eventual consistency instead of immediate durability.

---

## Q. Scaling Reads with Eventual and Strong Consistency

### **1. Scaling Reads with Eventual Consistency (Most Common)**

> Use **read replicas** and **distributed caches (Redis/CDN)** to distribute read traffic and reduce latency. Writes go to the primary, while reads are served from replicas or cache, providing excellent scalability at the cost of **possible stale reads due to replication lag or cache inconsistency**.

### **2. Scaling Reads with Strong Consistency**

> Serve reads from the **primary** or use **strongly consistent distributed databases** that rely on **synchronous replication, quorum reads/writes (`W + R > N`), or consensus protocols like Raft/Paxos**. This guarantees the latest committed data on every read but increases **read/write latency and coordination overhead**, reducing overall throughput compared to eventual consistency.

---

## Q. Caching Patterns

| Pattern                        | Explanation                                                                                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cache-Aside (Lazy Loading)** | Application checks the cache first. On a cache miss, it reads from the database, stores the result in the cache, and returns it. Most commonly used.                            |
| **Read-Through**               | Application always reads from the cache. On a cache miss, the cache itself fetches the data from the database, stores it, and returns it.                                       |
| **Write-Through**              | Application writes to the cache, and the cache synchronously writes the data to the database. Cache and DB stay consistent, but writes are slower.                              |
| **Write-Behind (Write-Back)**  | Application writes only to the cache. The cache asynchronously flushes changes to the database later. Faster writes, but risk of data loss if the cache fails before flushing.  |
| **Write-Around**               | Application writes directly to the database and skips the cache. The cache is populated only when the data is read later, avoiding cache pollution from rarely accessed writes. |

Easy way to remember:

Cache-Aside → App manages the cache.
Read-Through → Cache manages reads.
Write-Through → Cache writes to DB immediately.
Write-Behind → Cache writes to DB later.
Write-Around → Writes bypass the cache.
