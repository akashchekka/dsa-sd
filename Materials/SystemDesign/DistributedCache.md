---
title: Distributed Cache System Design (Planet Scale)
description: Interview notes on designing a planet-scale distributed cache, covering node internals, sharding, replication, multi-region invalidation, hard problems, and consensus-based failover with Raft and etcd
---

## Requirements

### Functional requirements

* `get(key)`, `set(key, value, expiry)`, `delete(key)`
* Keys expire automatically after their expiry time.
* When memory is full, the cache evicts the least useful data.

### Non-functional requirements

* **Very low latency:** Under 1 ms within a datacenter, and a few ms at the
  slowest end.
* **Massive scale:** Users on every continent, and hundreds of millions of
  requests per second worldwide.
* **Highly available:** Losing a machine, or even a whole region, must not take
  the product down.
* **Eventual consistency is acceptable:** The cache may be slightly stale for a
  short time.

> [!IMPORTANT]
> Confirm with the interviewer that **the cache is not the source of truth**.
> If cached data is lost, it can be rebuilt from the database. That one
> assumption simplifies the whole design.

## Rough estimates

Assumptions:

* 1 billion daily users
* 100 million cache reads per second worldwide, with about 10:1 reads to writes
* 10 regions around the world
* Average value size of 1 KB

| What                          | Calculation               | Result                         |
|-------------------------------|---------------------------|--------------------------------|
| Reads per region              | 100M / 10                 | **10M reads/sec**              |
| Hot data per region           | 10 billion keys x 1 KB    | **~10 TB**                     |
| Usable memory per machine     | -                         | ~100 GB                        |
| Machines for memory           | 10 TB / 100 GB            | **~100 machines**              |
| With 3 copies of each piece   | 100 x 3                   | **~300 machines per region**   |
| Throughput check              | 10M / 300 machines        | **~33k reads/sec per machine** |

One machine easily handles 100k+ reads per second, so **memory, not request
rate, decides the machine count.**

## High-level architecture

```text
        Users (worldwide)
             |
     +-------+--------+   routed to nearest region
     v                v
 +----------- Region: Asia -------------+   +---- Region: US ----+
 | App servers                          |   |   (same layout)    |
 |  +- cache client library             |   +--------------------+
 |       | knows which shard owns key   |
 |       v                              |
 | +--------+ +--------+ +--------+     |
 | |Shard 1 | |Shard 2 | |Shard N |     |  each shard = 1 leader + 2 replicas
 | |L  R  R | |L  R  R | |L  R  R |     |
 | +--------+ +--------+ +--------+     |
 |       ^                              |
 | Config service: shard map,           |
 | health checks, failover              |
 |                                      |
 | Database (source of truth)           |
 +--------------------------------------+
```

There are three main pieces:

* **Cache nodes:** In-memory key-value servers.
* **Client library:** Lives inside each app server and decides which node to
  call.
* **Config service:** Knows which nodes are alive and which shard owns which
  keys.

## Inside one cache node

### Storage: hash map plus eviction list

* A **hash map** gives O(1) lookup by key.
* A **doubly linked list** tracks usage order, for **least recently used (LRU)**
  eviction:
  * On every read, move the item to the front.
  * When memory is full, remove items from the back.
* Both operations are O(1).

### Expiry: two methods together

* **Lazy check:** On `get`, if the key has expired, delete it and return a miss.
* **Background cleanup:** Every 100 ms, sample some random keys and delete the
  expired ones. This removes expired keys that nobody reads anymore.

Scanning all keys would be too slow, so the cleanup samples.

### Concurrency

* **Option A:** A single thread per CPU core, with the data split across cores.
  There are no locks, so it's very fast.
* **Option B:** A multi-threaded server that splits the hash map into many
  segments, each with its own lock. That reduces contention.
* Avoid a single global lock.

### Memory

* Allocate memory in fixed-size chunks, grouped by value size, to avoid
  fragmentation.
* Set a hard memory limit. Evict before the limit is reached, never crash.

## Sharding: splitting data across nodes

### Why not `hash(key) % N`

When N changes from 100 to 101, **almost every key moves** to a different node.
The hit rate drops to near zero, and the database gets flooded.

### Consistent hashing

* Picture a **ring** of hash values.
* Each node sits at several points on the ring.
* A key goes to the **first node clockwise** from its hash.
* When a node is added or removed, **only about 1/N of the keys move**.

**Virtual nodes:** Each physical machine takes about 100 to 200 points on the
ring. That spreads load evenly, and when a machine dies its keys spread across
many machines instead of one neighbor.

### Who does the routing

| Option             | How                                                         | Trade-off                                                     |
|--------------------|-------------------------------------------------------------|---------------------------------------------------------------|
| **Client library** | The app knows the ring and calls the right node directly.   | Fastest, with no extra hop, but every client needs the map.   |
| **Proxy layer**    | Apps call a proxy, which forwards the request.              | Simple clients, but an extra hop and more machines to run.    |

At planet scale, pick the **client library**, because every millisecond counts.
The client fetches the shard map from the config service and refreshes it on
changes.

## Replication

Each shard has **1 leader and 2 replicas**, placed in **different availability
zones**, which are separate buildings within the region.

* **Writes** go to the leader, which copies them to the replicas
  **asynchronously**. Writes stay fast, and losing a few writes is acceptable
  because this is a cache.
* **Reads** can go to the leader or the replicas, which spreads read load.

## Caching patterns: how apps use the cache

| Pattern                    | How                                                                                                                         | When                                   |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Cache-aside** (default)  | Read the cache. On a miss, read the database and fill the cache. On a write, update the database and **delete** the cache key. | Most read-heavy systems                |
| **Write-through**          | Write the cache and the database together.                                                                                  | Reads right after writes must be fresh |
| **Write-behind**           | Write the cache, and update the database later.                                                                             | High write volume, some loss risk OK   |

**Why delete instead of update on write?** If two writers update the cache in
different orders, the cache can end up holding the older value forever.
Deleting is safer, because the next read loads the fresh value.

## Planet scale: multiple regions

The key decision: **each region has its own independent cache cluster.** Do
**not** replicate the cache synchronously across continents. A round trip from
India to the US takes about 200 ms, which would destroy the sub-millisecond
goal.

### Keeping regions consistent with invalidation

```text
 Write in US region
       |
       v
  Database (US) --> change log --> message stream --> invalidator in each region
                                                          |
                                                          v
                                                 delete key from local cache
```

* Every database change produces an event.
* An **invalidator service** in every region reads these events and **deletes**
  the affected keys from its local cache.
* The next read in that region gets a miss and loads the fresh value.
* Stale data lasts at most a few hundred milliseconds, which is acceptable for a
  cache.

**Why invalidate instead of copying values across regions?**

* Each region only keeps data its own users actually read.
* Cross-region traffic stays small, because a key is tiny compared to a value.

### Region failure

* Global routing sends users to the next nearest region.
* That region's cache is **cold** for those users, so the database sees a burst
  of traffic. Protect it with request coalescing and rate limiting.
* Optionally, pre-warm a backup region with the most popular keys.

## The hard problems

### 1. Hot keys

**Problem:** One celebrity post gets millions of reads per second, all hitting
**one shard**.

**Fixes:**

* **Small local cache in the app server** for very hot keys, holding them for a
  few seconds. Most reads never leave the server.
* **Copies of the hot key:** Store it as `post:123#1` to `post:123#10` on
  different shards, and have each reader pick one at random.
* **Detect hot keys** by counting requests per key on each node and flagging
  the top ones.

### 2. Cache stampede (thundering herd)

**Problem:** A popular key expires, and 10,000 requests miss at once and **all
hit the database**.

**Fixes:**

* **Request coalescing:** Only one request loads from the database, and the
  others wait for its result.
* **Lock or lease:** The first requester gets a short lock to rebuild the key,
  while others briefly get the stale value or wait.
* **Early refresh:** Refresh popular keys in the background a little before they
  expire.

### 3. Mass expiry (avalanche)

**Problem:** Many keys were set at the same time with the same expiry, so they
all expire together.

**Fix:** Add **random jitter** to expiry times. Instead of exactly 1 hour, use
1 hour plus or minus 5 minutes.

### 4. Lookups for missing data (penetration)

**Problem:** Requests for keys that **don't exist in the database** always miss
the cache, so they always hit the database. Attackers can abuse this.

**Fixes:**

* **Cache the "not found" result** with a short expiry.
* Use a **compact "might exist" filter** (a Bloom filter) in front of the
  database to reject keys that definitely don't exist.

### 5. Stale data race

**Problem:**

1. Reader A misses and reads the **old** value from the database.
2. Writer B updates the database and deletes the cache key.
3. Reader A now writes the **old** value into the cache, and it stays stale.

**Fix:** Use **leases or version numbers.** On a miss, the cache gives the
reader a token. A delete invalidates outstanding tokens. When the reader tries
to fill the cache with an invalid token, the write is rejected.

### 6. Large values

* Store very large values (several MB) in blob storage and cache a pointer.
* Or split them into chunks. Large values block network and memory and hurt
  everyone's latency.

### 7. Adding or removing nodes (resharding)

* Consistent hashing moves only about 1/N of the keys.
* Add nodes **gradually**, and optionally copy the affected keys to the new node
  before switching traffic, so the hit rate doesn't drop.

### 8. Cold start

* A fresh cluster with an empty cache would send all traffic to the database.
* **Warm it up** by replaying recent popular keys, or by shifting traffic
  gradually: 1%, then 10%, then 100%.

## Failover: who decides a new leader

There are three ways to handle failover.

### Option 1: Consensus in the control plane (recommended)

```text
   Config service = 5 machines running consensus (majority vote)
   +- stores: shard map, leader of each shard, epoch numbers
   +- decides failover
              | heartbeats / health checks
     +--------+--------+
  Shard 1  Shard 2  Shard N     <- cache nodes: simple, fast, async replication
```

* **Consensus runs only on small metadata:** which node leads which shard. That
  changes rarely.
* **The cache data path has no voting.** A write goes to the leader, completes,
  and is copied to replicas in the background.
* Failover means the consensus cluster **agrees by majority** to promote a
  replica and increments the shard's **epoch number**.

### Option 2: Nodes vote among themselves (peer-to-peer)

* Cache nodes constantly **gossip** about each other's health.
* If a **majority** of nodes agree a leader is dead, they promote one of its
  replicas. Redis Cluster works this way.

**Pros:**

* No external system to run.

**Cons:**

* **Gossip traffic grows** with the cluster. It works for hundreds of nodes, but
  gets harder with thousands.
* Failure detection is **slower**, because news spreads node to node.
* Clients still need the shard map, so they learn it from the nodes, which is
  messier.
* Cache nodes do two jobs, serving data and running elections, so the code is
  more complex.

### Option 3: Consensus per shard (on every write)

* The 3 copies of each shard run their own consensus, such as Raft.
* **Every write waits until a majority (2 of 3) confirms it.**
* Leader election is built in.

**Pros:**

* It has the strongest guarantee: **a confirmed write is never lost.**
* No external coordinator is needed.

**Cons:**

* **Every write is slower**, because it waits for a second machine.
* More CPU and network per write.
* **It's overkill for a cache.** Losing a few writes during failover only causes
  a few cache misses.

**Where it fits:** Databases and stores that are the source of truth, such as
CockroachDB, TiKV, and etcd itself.

### Comparison of failover options

| Point                       | 1. Consensus in config service | 2. Nodes vote (gossip) | 3. Consensus per shard  |
|-----------------------------|--------------------------------|------------------------|-------------------------|
| Write latency               | Fastest (async copy)           | Fast                   | Slower (wait for majority) |
| Lost writes on failover     | A few (OK for a cache)         | A few                  | None                    |
| Failure detection speed     | Fast                           | Slower at large scale  | Fast                    |
| Works with thousands of nodes | Yes                          | Gossip gets heavy      | Yes                     |
| Extra system to run         | Yes (small cluster)            | No                     | No                      |
| Cache node complexity       | Simple                         | Higher                 | Highest                 |
| Best for                    | **Large caches**               | Small or medium caches | Databases, source of truth |

### Why Option 1 for planet scale

1. **Consensus where it's cheap:** Leadership changes are rare and small, so
   voting on them costs almost nothing.
2. **No consensus where it's expensive:** Millions of cache writes per second
   stay fast with async copies.
3. **One source of truth for the shard map:** Clients need it anyway, and they
   get it from one consistent place.
4. **Simple cache nodes:** They only store and serve data, and simple nodes
   fail less.
5. **The cache can afford to lose a few writes:** The database is the source of
   truth.

## Deep dive: Raft in the config service

There are **two separate groups of machines**, and Raft runs **only inside the
small one**.

```text
 +---------------- CONTROL PLANE (rarely changes) -----------------+
 |  Config service: 5 machines running Raft among THEMSELVES       |
 |   C1 (Raft leader)   C2   C3   C4   C5                          |
 |   Stores: shard map, leader of each shard, epochs, leases       |
 +--------------^-------------------------------+------------------+
                | heartbeats / lease renewals   | shard map updates
                | (every 1-2 sec)               v
 +--------------+---- DATA PLANE (millions of req/sec) ------------+
 |  Cache shards (NO Raft here)                                    |
 |   Shard 1: Leader A --async copy--> Replica B, Replica C        |
 |   Shard 2: Leader D --async copy--> Replica E, Replica F        |
 |   ...                                                           |
 |  App servers (client library) --get/set--> shard leaders        |
 +-----------------------------------------------------------------+
```

``` text
 Region Asia                         Region US
 +----------------------------+      +----------------------------+
 | etcd: 5 nodes across 3 zones|     | etcd: 5 nodes across 3 zones|
 | Controller x3 (1 active)    |     | Controller x3 (1 active)    |
 | Cache shards + API servers  |     | Cache shards + API servers  |
 +----------------------------+      +----------------------------+
          independent  <------ no shared etcd ------>  independent
```

* **Cache nodes never vote.** They only report health and obey decisions.
* **App requests never touch the config service.** They go straight to cache
  nodes.

### How Raft works inside the config service

Raft lets 5 machines **behave like one reliable machine**, even if 2 fail.

#### One leader among the config machines

* One config machine, say C1, is the **Raft leader**. The others are followers.
* All changes go through the Raft leader.
* Raft has a **term**, which is like an election round. Each election increments
  the term.

#### Writing a change: the majority rule

Suppose the Raft leader records "Shard 1's leader is now B":

```text
Step 1: C1 appends the change to its log
Step 2: C1 sends it to C2, C3, C4, C5
Step 3: C2 and C3 reply "saved"  ->  C1 + C2 + C3 = 3 of 5 = MAJORITY
Step 4: Change is COMMITTED. C1 applies it and tells others to apply it.
```

* Once a majority saves the change, it's **permanent**. Any future Raft leader
  must come from that majority, so it's guaranteed to have the change.
* With 5 machines, any 2 can fail and the service still works.
* **Use odd sizes.** 3 machines tolerate 1 failure and 5 tolerate 2, while 4
  still only tolerates 1.

#### If the Raft leader dies

* Followers stop hearing from C1. After a random timeout of about 150 to 300 ms,
  a follower, say C3, starts an **election** and asks for votes.
* If C3 gets **3 votes out of 5**, it becomes the new Raft leader with a higher
  term.
* A machine only votes for a candidate whose log is **at least as up to date**
  as its own, so no committed change is lost.

### What the config service stores

```text
/shards/1   -> { leader: A, replicas: [B, C], epoch: 12 }
/shards/2   -> { leader: D, replicas: [E, F], epoch: 5 }
/nodes/A    -> { address: 10.0.1.5, zone: zone-1, lease_expires: 20:03:24 }
/nodes/B    -> { address: 10.0.2.7, zone: zone-2, replication_offset: 98,450 }
...
```

* **Shard map:** Which nodes hold which part of the hash ring.
* **Leader per shard**, plus an **epoch**, a version number that increments on
  each leader change.
* **Lease per node:** The node is considered alive until this time, unless it
  renews.
* **Replication offset:** How up to date each replica is.

### How cache nodes and clients interact with it

**Cache nodes renew a lease:**

* Every 2 seconds, each cache node sends a heartbeat: "I'm alive. Here's my
  replication offset."
* The config service extends that node's lease to 10 seconds from now.
* **A shard leader may only accept writes while its lease is valid.** That rule
  is what prevents split brain.

**Clients watch the shard map:**

* At startup, each client library downloads the shard map.
* It **subscribes to changes**, and the config service pushes updates.
* Client requests go **directly to cache nodes** using the local copy of the
  map.

### Failover step by step

Shard 1's leader A crashes at 20:03:00.

```text
20:03:00  Leader A crashes. Last heartbeat was at 20:02:58.
          Writes to Shard 1 fail; clients retry or treat as cache miss.

20:03:08  Config service: "A's lease expired (no renewal for 10 sec)."

20:03:08  Config Raft leader picks the most up-to-date replica:
          B offset = 98,450   C offset = 98,300   -> choose B

20:03:08  Config writes through Raft (needs 3 of 5 to agree):
          /shards/1 -> { leader: B, replicas: [C], epoch: 13 }

20:03:08  Change committed. Config notifies:
          -> B: "You are leader of Shard 1, epoch 13"
          -> C: "Follow B now, epoch 13"
          -> All clients: "Shard map updated, Shard 1 leader = B"

20:03:09  Clients send Shard 1 requests to B. Service restored.

Later     A restarts -> registers -> config makes it a REPLICA of B,
          it copies data from B. (Or a brand-new node replaces it.)
```

**Why choose the most up-to-date replica?** Replication is async, so replicas
may be slightly behind. Picking the highest offset **loses the fewest writes**.

### The tricky case: the leader isn't dead, just cut off

A network problem separates A from the config service, but **some clients can
still reach A**.

```text
20:03:00  Network cut: A can't reach config service.
          A keeps serving clients (its lease is valid until 20:03:08).

20:03:06  A notices: "I can't renew my lease."
          A STOPS accepting writes on its own at 20:03:06
          (A uses a slightly SHORTER deadline than the config service,
           to be safe against clock differences).

20:03:08  Config's view: A's lease expired -> promote B (epoch 13).

Result:   A stopped at :06, B started at :08 -> never two leaders at once.
```

Two safety mechanisms work together:

1. **Lease, self-fencing:** An old leader **stops by itself** when it can't
   renew. It doesn't need to be told.
2. **Epoch, rejecting stale messages:**
   * Every request and replication message carries the epoch.
   * If old A comes back and sends replication data with epoch 12, B and C
     reject it because they're on epoch 13.
   * If a client with an old map writes to A, A replies "I'm not the leader.
     Refresh your map." The client fetches the new map and retries on B.

> [!NOTE]
> Safety comes from **leases and epochs**, not from perfectly detecting
> failures. Even if the config service wrongly thinks A is dead, the worst case
> is a few seconds of unavailability for one shard, never two leaders.

**Avoiding false alarms:** Use health checks from several zones, and fail over
only when a majority agree the leader is unreachable. Redis Sentinel uses this
quorum idea.

### What if the config service has problems

| Situation                         | Effect                                                                                 |
|-----------------------------------|----------------------------------------------------------------------------------------|
| 1 or 2 config machines die        | No effect. Raft still has a majority (3 of 5).                                         |
| Config Raft leader dies           | A new Raft leader is elected in under 1 second. A few heartbeats may be delayed.       |
| Whole config service is down      | **Cache reads and writes keep working** with the last shard map. Only failover and adding nodes pause. |

When the config service is fully down, nobody can renew leases. To avoid every
leader fencing itself and freezing writes, nodes keep serving as long as they
can't reach config **and** haven't been told they were replaced. A 5-machine
Raft cluster spread across 3 zones rarely fails completely.

### Why this split works

| Point                    | Config service (Raft)                          | Cache nodes (no Raft)               |
|--------------------------|------------------------------------------------|-------------------------------------|
| Traffic                  | Hundreds of small writes/sec (heartbeats)      | Millions of reads/writes/sec        |
| Data size                | KBs to MBs (metadata)                          | TBs (cached values)                 |
| Needs strong agreement?  | Yes, two leaders would be a disaster           | No, a few lost writes are OK        |
| Cost of Raft             | Cheap (small, rare writes)                     | Expensive (would slow every write)  |

### Using etcd as the config service

Yes, the config service can be an **etcd cluster**. etcd runs Raft internally
and is usually deployed as 3 or 5 nodes. It already has what we need:

* **Leases with a time limit:** Cache node heartbeats.
* **Watches:** Push shard map changes to clients.
* **Transactions:** Update the shard leader and epoch only if the current epoch
  matches, so two promotions can't collide.

Kubernetes uses etcd for exactly this kind of cluster metadata. ZooKeeper and
Consul are common alternatives.

### Failover controller: who acts on an expired lease

etcd only **stores data**. It runs no custom logic. Something must watch for
expired leases and perform the promotion. That's the **failover controller**.

* **One controller for the whole cluster, not one per shard.** It watches all
  shards in etcd and promotes whichever leader fails.
* Run **2 or 3 copies** for safety. Only one is active, chosen with an
  **etcd lock**.
* When it sees a leader's key disappear, it:
  1. Picks the replica with the **highest replication offset**.
  2. Tells that replica to become the leader.
  3. Tells the other replicas to follow the new leader.
  4. Updates `/shards/N` in etcd **inside a transaction**: "only if the epoch is
     still 12, set the leader to B and the epoch to 13." Two controllers can
     never both promote.
  5. Clients watching etcd get the new map and switch to B.

In an interview, draw etcd and the controller as **one box**: "Config service =
etcd + failover logic."

### How cache nodes talk to etcd: built-in vs sidecar

A **sidecar**: a separate small program
running next to the cache server. Whether you need one depends on whether you
can change the cache server's code.

```text
Off-the-shelf Redis:                 Your own cache server:
+----------------------+             +-----------------------------+
| Machine              |             | Machine                     |
|  [Redis] <-> [Agent] |--> etcd     |  [Cache server process      |--> etcd
|  (can't     (talks   |             |    - serves get/set         |
|   change)   to etcd) |             |    - thread: renew lease    |
+----------------------+             |    - thread: watch role ]   |
                                     +-----------------------------+
  2 programs                           1 program, same work
```

#### Built into the node (use this in a "design a distributed cache" interview)

You're writing the cache server yourself, so the agent's job becomes **a
background thread inside the same process**. The same work happens, just
inside the node instead of beside it.

```python
# runs inside the cache server process, in a background thread
lease = etcd.lease(ttl=10)
etcd.put(f"/nodes/{me}", my_address, lease=lease)

while True:
    ok = lease.refresh()              # heartbeat
    if not ok:
        stop_accepting_writes()       # self-fence: lease lost
    sleep(2)

# another thread watches my role
for event in etcd.watch(f"/shards/{my_shard}"):
    update_role(event.leader, event.epoch)   # become leader or follow new leader
```

* The node **creates and renews its own lease** and **watches its own role**.
* It understands epochs, so it can reject stale requests directly.
* There's no extra process to run.

#### Sidecar agent (when using off-the-shelf Redis)

**Redis can't talk to etcd by itself.** Redis is a server that waits for
clients. It has no etcd client built in, and it has no idea what a lease or an
epoch is. Its code can't be changed, so a separate agent bridges the gap.

```text
 +------------------- etcd cluster (Raft, 3-5 nodes) -------------------+
 |  /shards/1 -> {leader: A, replicas: [B, C], epoch: 12}               |
 |  /nodes/A  -> alive (lease 10s)   /nodes/B -> alive   /nodes/C ...   |
 +------^--------------------^-----------------------+------------------+
        | keep lease alive   | keep lease alive      | watch for changes
        |                    |                       v
 +------+-------+    +-------+------+       +------------------+
 | Machine A    |    | Machine B    |       | Failover         |
 | Redis leader |    | Redis replica|       | controller       |
 | + Agent      |    | + Agent      |       | (watches etcd,   |
 +--------------+    +--------------+       |  promotes)       |
                                            +------------------+
 App servers: client library reads shard map from etcd (watch),
              sends get/set directly to Redis leaders.
```

**What the agent does:**

* Every second, it checks the local Redis with `PING` and reads its replication
  offset from `INFO replication`.
* **If Redis is healthy,** it renews the etcd lease and publishes the offset.
* **If Redis is unhealthy,** it stops renewing, so the lease expires.

```python
lease = etcd.lease(ttl=10)
etcd.put(f"/nodes/{me}", info, lease=lease)
while True:
    if redis_is_healthy():
        lease.refresh()                       # heartbeat
        etcd.put(f"/nodes/{me}/offset", redis_offset(), lease=lease)
    sleep(1)
```

**etcd's role:** etcd doesn't actively receive heartbeats. It **expires the
lease** when renewals stop and deletes the node's key. That deletion is an
event the controller reacts to.

**What the controller does with Redis:** It sends `REPLICAOF NO ONE` to the
chosen replica to make it the leader, sends `REPLICAOF <new leader>` to the
other replicas, and updates the shard map in etcd with the epoch check.

**Use plain Redis with replication, not Redis Cluster mode.** Redis Cluster has
its **own brain**: nodes gossip, vote, promote replicas, and redirect clients
with "MOVED". Adding etcd on top creates **two brains**:

```text
Leader A looks slow.
  Redis Cluster's vote:  promote replica B
  etcd controller:       promote replica C   (it saw a different offset)
Result: Redis tells clients "go to B", etcd shard map says "go to C"
        -> clients bounce between them, writes split, data inconsistent
```

There must be **one source of truth** for the leader. With plain Redis, Redis
only stores and replicates data, and etcd plus the controller decide everything
else.

**The fencing gap:** Redis doesn't understand leases or epochs, so it can't
fence itself. Handle that in three ways:

* **The agent fences Redis:** If it can't renew the lease, it makes local Redis
  refuse writes (pause writes or switch to read-only) before the lease runs
  out.
* **Built-in Redis safety net:** `min-replicas-to-write 1` with
  `min-replicas-max-lag 10` makes a leader refuse writes if it can't reach any
  replica, so an isolated old leader stops accepting writes.
* **Clean up on return:** When the old leader comes back, its agent sees in
  etcd that it's no longer the leader and runs `REPLICAOF <new leader>`.

#### Other ways to connect nodes to etcd

* **Controller checks the nodes (pull model):** The controller (several copies
  in different zones) pings every Redis directly and writes health into etcd.
  This is how Redis Sentinel works. Nothing is installed on Redis machines, but
  the checkers do all the work and Redis can't fence itself, so you rely on
  `min-replicas-to-write`.
* **Kubernetes:** The kubelet on every machine already acts as the agent. It
  health-checks Redis and reports status to the Kubernetes API, which stores it
  in etcd. A Redis operator acts as the controller.

| Way                     | Who talks to etcd                   | When to use                              |
|-------------------------|-------------------------------------|------------------------------------------|
| Built into the node     | The cache node itself               | You design the cache (interview default) |
| Sidecar agent           | A small process beside Redis        | Off-the-shelf Redis, outside Kubernetes  |
| Controller checks nodes | The controller, after pinging nodes | No changes to nodes, like Sentinel       |
| Kubernetes              | The kubelet, plus an operator       | Redis running on Kubernetes              |

**Used in practice:** Patroni does this for PostgreSQL with etcd (an agent per
node holds a leader key with an expiry time). Codis, a sharded Redis system,
stored its shard map in ZooKeeper or etcd. Redis operators on Kubernetes follow
the same pattern.

### Practical choices for failover with Redis

| Point            | Redis Cluster (built-in)                     | Redis Sentinel                                      | etcd + agent + controller                              |
|------------------|----------------------------------------------|-----------------------------------------------------|--------------------------------------------------------|
| How failover works | Redis nodes gossip and vote                | Separate Sentinel processes watch Redis and vote    | Agent renews an etcd lease, controller promotes on expiry |
| Sharding         | Built in (16,384 slots)                      | None, you shard in the client or a proxy            | You build it, with the shard map in etcd               |
| Extra systems    | None                                         | Sentinel processes                                  | etcd, agents, controller                               |
| Effort           | Lowest                                       | Low                                                 | Highest (custom code)                                  |
| Flexibility      | Low                                          | Medium                                              | Highest (custom placement, many clusters, own rules)   |
| Scale limit      | Gossip gets heavy around 1,000 nodes         | Each Sentinel group watches a few leaders           | Scales well, etcd only holds metadata                  |

* **Default:** Redis Cluster, or a managed service.
* **Small setup without sharding:** Sentinel.
* **Planet scale or custom needs:** etcd-based control.

### Presenting the etcd design in an interview

It's a valid, well-known pattern (Kafka with ZooKeeper, HBase, Vitess, Patroni,
Kubernetes with etcd). How you present it matters most:

* **Match the question:**
  * "Design a distributed cache": present cache nodes plus a coordination
    service (etcd or ZooKeeper) for membership and failover. "Just use Redis"
    can sound like dodging the question.
  * "Design a feed / URL shortener / ...": say "Redis Cluster or a managed
    cache" and move on.
* **Start simple, escalate with a reason:** Redis Cluster is enough for
  millions of rps in one region. Move to etcd only for thousands of nodes or
  hundreds of clusters.
* **Draw three boxes:** config service (etcd + failover logic), cache nodes
  (renew their own lease), and clients (watch the shard map). Discuss Raft
  internals, sidecars, or `REPLICAOF` only if asked.
* **Name the trade-off:** It's an extra system and custom code, only worth it at
  large scale.
* **Avoid these mistakes:** putting the config service on the request path,
  using consensus on every cache write, or spending all the time on Raft
  instead of hot keys, stampedes, and multi-region.

## Failure scenarios

| Failure                       | What happens                       | Mitigation                                                                   |
|-------------------------------|------------------------------------|------------------------------------------------------------------------------|
| One node dies                 | Its keys are briefly unavailable.  | A replica is promoted within seconds.                                        |
| A whole zone dies             | About a third of the nodes are lost. | Replicas in other zones take over.                                         |
| A whole region dies           | Users go to another region.        | Spare capacity, coalescing protects the database, optional pre-warming.      |
| Cache cluster is slow         | App latency rises.                 | Short timeouts (a few ms). Treat a timeout as a miss or **fail fast**.       |
| Database overloaded by misses | Failures can cascade.              | Rate limits, coalescing, and serving stale values while the database recovers. |

## What to monitor

* **Hit rate:** The most important number. A sudden drop means trouble.
* **Latency:** Median and the slowest 1% of requests.
* **Eviction rate and memory usage:** Tell you when to add capacity.
* **Hot keys:** The top keys by requests.
* **Replication lag** and **failover events**.

## FLOW

Here's the failover flow, start to finish:

1. **The sidecar sends heartbeats.** The sidecar next to each cache node keeps renewing that node's lease in etcd.
2. **The leader fails.** Leader A of shard 2 goes down, so its sidecar stops renewing.
3. **The lease expires.** etcd automatically revokes A's lease and deletes `/nodes/A`.
4. **etcd reports the fact.** It pushes a `DELETE /nodes/A` event to the controller, which is watching.
5. **The controller decides.** It looks up the slot map, sees that A led shard 2, and picks the replica with the highest offset, B.
6. **The controller updates etcd safely.** In one transaction it sets `shard2 → leader: B, epoch: 12 → 13`, but only if the epoch is still 12.
7. **The controller assigns roles.** It tells B "you're the leader, epoch 13" and C "follow B."
8. **etcd pushes the change to clients.** Every client watching gets the new map with epoch 13 and updates its local copy.
9. **Clients ignore older updates.** Any late message with a lower epoch is discarded.
10. **Stale clients get rejected.** A client still on epoch 12 that sends to A gets a timeout or a reject. If it sends to B, B replies "stale epoch."
11. **Stale clients fix themselves.** They re-read the map from etcd and retry on B.
12. **The old leader steps down.** If A comes back, it sees epoch 13 with leader B in etcd and rejoins as a replica of B.

This is the full lifecycle of one region's cache. Every region runs the same setup independently.

## Cast of characters

| Component | Role in one line |
|---|---|
| **etcd** (5 nodes across 3 zones) | **Remembers.** It stores the slot map, shard leaders, epochs, and node leases. It runs no logic. |
| **Controller** (3 copies, 1 active) | **Decides.** It assigns slots, picks leaders, handles failover, and rebalances. |
| **Cache nodes** (with a built-in etcd client, or a sidecar for Redis) | **Store and serve data.** They renew their lease and follow the role they're given. |
| **Client library** (inside every API server) | **Routes.** It keeps a copy of the map, hashes keys, and sends requests directly to the right node. |
| **Database** | **Source of truth.** The cache is only a copy. |

## Phase 1: Bootstrapping the cluster

**Step 1. Start etcd.**
- Bring up 5 etcd machines across 3 zones. They elect their own Raft leader.
- etcd is empty at this point.

**Step 2. Start the controller.**
- 3 controller copies start, and they compete for an **etcd lock**. One wins and becomes active, and the other two wait as standbys.
- The active controller writes the fixed config: `total_slots = 65,536`. This number never changes.

**Step 3. Start the cache nodes, for example 300 nodes.**
- Each node **creates a lease** in etcd (for example, 5 seconds) and registers itself:
  ```
  /nodes/A -> { addr: 10.0.1.5, zone: 1, memory: 100GB }   (attached to lease)
  ```
- Each node then **keeps renewing its lease** in the background. This is the heartbeat.
- Nodes start with **no role**. They wait for the controller to assign one.

**Step 4. The controller builds shards and assigns slots.**
- The controller watches `/nodes/`, sees 300 live nodes, and groups them into **100 shards of 3**, placing each shard's nodes in **3 different zones**.
- In each shard, it chooses one **leader** and two **replicas**, and sets the **epoch to 1**.
- It splits the 65,536 slots evenly, about 655 per shard.
- It writes everything to etcd in one transaction:
  ```
  /slotmap/shard1 -> { slots: [0-654],    leader: A, replicas: [B, C], epoch: 1 }
  /slotmap/shard2 -> { slots: [655-1309], leader: D, replicas: [E, F], epoch: 1 }
  ...
  /slotmap/version -> 1
  ```

**Step 5. Nodes learn their roles.**
- Each node **watches its own shard entry** in etcd.
- A sees "I'm leader of shard 1, epoch 1."
- B and C see "We're replicas of shard 1." They connect to A and start replicating.

**Step 6. API servers start.**
- Each API server's client library **downloads the full slot map** from etcd. It's only a few KB.
- It **watches `/slotmap/`**, so any future change is pushed to it.

The cluster is now ready, and etcd will not be touched again by normal requests.

## Phase 2: Reading and writing data

**Step 7. A read: `get("user:123")`.**
```
Client library (all in memory, nanoseconds):
  slot   = hash("user:123") % 65536  = 1000
  shard  = slot 1000 -> shard2
  target = shard2 leader D (or a replica E/F for reads)
  send GET (epoch 1) directly to D
```
- **Hit:** D returns the value in about 1 ms.
- **Miss:** The API reads the **database**, then calls `set` to fill the cache (cache-aside).

**Step 8. A write: the user updates their profile.**
1. The API **updates the database** first.
2. The API **deletes** the cache key `user:123`. The request goes to **leader D**, because writes and deletes are leader-only.
3. D checks: "Am I the leader, and is my lease still valid?" If yes, it deletes the key.
4. D copies the delete to E and F **asynchronously**.
5. The next read misses and loads the fresh value from the database.

**Step 9. Expiry and eviction happen on each node.**
- Keys expire after their expiry time. Expired keys are removed when someone reads them, and also by a background sampler.
- When memory is full, the node evicts the least recently used keys.

**Note:** etcd and the controller were **not involved at all** in phase 2. They're only for coordination.

## Phase 3: Adding a node (scaling out)

The cluster is getting full, so we add 3 new nodes (X, Y, and Z) to form a new **shard 101**.

**Step 10. New nodes register.**
- X, Y, and Z create leases and register under `/nodes/`, just like in step 3.

**Step 11. The controller notices and plans the move.**
- The controller is watching `/nodes/`, so etcd **pushes** the 3 new registrations to it.
- It creates shard 101 with leader X and replicas Y and Z, in different zones.
- It plans to take **a few slots from each existing shard**, about 650 slots in total, so every shard ends up equal again.

**Step 12. Move one slot at a time, for example slot 500 from shard 1 to shard 101.**
```
a) Controller -> etcd:  slot 500 = MIGRATING (shard1 -> shard101)
b) Leader A copies all keys of slot 500 to X
   (A keeps keys grouped by slot, so it can list them quickly)
c) During copy:
     - A still serves slot 500 keys it has
     - for keys already moved, A replies "ask shard101"
d) Copy done -> Controller -> etcd (transaction):
     slot 500 -> shard101, /slotmap/version 1 -> 2
e) etcd pushes the new map to every client library
f) A deletes its copy of slot 500's keys
```

**Step 13. Clients adjust.**
- Most clients update through the **watch** within milliseconds.
- A client with a stale map sends a request for slot 500 to A. A replies "**not my slot, refresh your map**," and the client re-reads etcd and retries on X.

**Key point:** Only about 1% of the keys move, and they move a few slots at a time in the background. There's no downtime and only a small drop in hit rate.

Removing a node works the same way in reverse: the controller moves that shard's slots to other shards, then removes it.

## Phase 4: A leader fails (failover)

Leader D of shard 2 crashes.

**Step 14. The heartbeat stops.**
- D stops renewing its lease.

**Step 15. etcd expires the lease.**
- After about 5 seconds with no renewal, etcd **expires the lease automatically** and deletes `/nodes/D`.
- etcd **pushes a `DELETE /nodes/D` event** to the controller. etcd only reports the fact. It doesn't decide anything.

**Step 16. The controller decides.**
- The controller looks up D in the slot map: "D was the **leader** of shard 2."
- It compares the replicas' replication offsets: E = 98,450 and F = 98,300, so it picks **E**.

**Step 17. The controller commits the change safely.**
```
etcd transaction:
  IF shard2.epoch == 1
  THEN shard2 -> { leader: E, replicas: [F], epoch: 2 }
```
- The epoch check guarantees that two controllers can't both promote someone.

**Step 18. Everyone follows.**
- **E** sees through its watch: "I'm leader, epoch 2." It starts accepting writes.
- **F** sees "follow E" and starts replicating from E.
- **Client libraries** receive the new map and send shard 2 writes to E.
- A **stale client** that sends to D with epoch 1 gets a timeout, refreshes its map, and retries on E.

**Step 19. During the roughly 5-second window:**
- **Reads** for shard 2 go to the replicas E and F, so they still work.
- **Writes** fail fast. The client skips caching, and the next read misses and goes to the database.
- **Deletes** are retried until E accepts them. The expiry time is the final safety net.

**Step 20. Repair.**
- The controller adds a new replica to shard 2 (a spare node, or D after it restarts). It copies data from E, or loads a snapshot and then catches up from E.
- If D comes back, it sees "epoch 2, leader E" in etcd and **rejoins as a replica**.

### The split-brain case: D isn't dead, just cut off from etcd

- D can't renew its lease, so it **stops accepting writes by itself** before the lease fully expires.
- The controller promotes E **only after** the lease expires, so the two never overlap.
- Any replication data D sends with **epoch 1** is rejected by E and F, which are on epoch 2.

## Phase 5: The controller itself fails

**Step 21.**
- The active controller dies, so its **etcd lock** (also tied to a lease) expires.
- A standby controller takes the lock and becomes active.
- It **reads the full state** from etcd (nodes, shards, and leaders) and fixes anything left half-done, for example a shard with no leader or a slot stuck in migration.
- Cache traffic is **not affected**, because clients and nodes don't depend on the controller from moment to moment.

If an **etcd machine** dies, the other 4 still have a majority and nothing changes. If **all of etcd** goes down, cache reads and writes keep working with the last known map. Only failover and rebalancing pause.

## Phase 6: Across regions

**Step 22.** A write in the US region updates the database. The change is replicated to the database copy in Asia.

**Step 23.** The **invalidator in Asia** reads the change log of **Asia's own database copy** and sends `delete user:123` to the Asia cache, using the same client-library routing.

**Step 24.** The next Asia read misses, reads the local Asia database copy (which is already updated), and refills the cache.

Each region has its **own etcd and controller**. Regions share only database changes, never cache state.

## The whole flow on one page

```
SETUP      nodes register (lease) -> controller groups into shards, assigns slots
           -> writes map to etcd -> nodes & clients watch it

REQUEST    client: hash(key)%65536 -> slot -> shard -> leader/replica -> direct call
           (etcd & controller NOT involved)

SCALE OUT  new node registers -> controller moves a few slots (MIGRATING -> copy -> commit)
           -> etcd pushes new map -> stale clients get "refresh map"

FAILOVER   heartbeat stops -> etcd expires lease, emits DELETE -> controller picks best replica
           -> etcd transaction (epoch+1) -> nodes & clients follow via watch

SAFETY     lease self-stop + epoch checks -> never two leaders accepting writes

REGIONS    one etcd + controller per region; DB change log drives cache invalidation
```

## 30-second interview version

> "Cache nodes register in etcd with a lease and keep renewing it. The controller groups them into shards of 3 across zones, assigns each shard a range of the 65,536 slots, picks leaders, and writes that map to etcd. Client libraries download the map, watch it, and route every request in memory: hash to slot, slot to shard, shard to leader. etcd is never on the request path. When I add nodes, the controller moves a few slots at a time and commits each move to etcd, and clients pick it up through their watch. When a leader dies, its lease expires, etcd pushes a delete event, and the controller promotes the most up-to-date replica with a higher epoch in one transaction. Leases and epochs ensure there's never two leaders accepting writes. Each region runs this independently, and database change events keep regions in sync."

## Interview summary

> "Each region runs its own cache cluster, so reads stay local and under a
> millisecond. Inside a region, data is split across nodes with **consistent
> hashing** and **virtual nodes**, and the client library routes directly to
> the right node. Each shard has a **leader and 2 replicas** in different zones
> with async replication. Apps use **cache-aside**, deleting keys on write.
> Across regions, a stream of database changes **invalidates** stale keys
> everywhere.
>
> Failover uses consensus in the **control plane**, not the data plane. A
> 5-node Raft cluster such as etcd stores the shard map and leader of each
> shard. Cache nodes renew a **lease**. When a lease expires, the config service
> promotes the most up-to-date replica with a higher **epoch**. Old leaders
> fence themselves when their lease runs out, and stale epochs are rejected.
>
> The real challenges are **hot keys** (local caching and copies),
> **stampedes** (request coalescing and leases), **mass expiry** (random
> jitter), and **stale-fill races** (version tokens). Since the database is the
> source of truth, losing cache data costs only latency, never correctness."

### Interview version for millions rps

> "For millions of rps in one region, I'd use **Redis Cluster**, ideally
> managed. Sizing comes to about 40 shards with 2 replicas each across 3 zones,
> which is well within its limits. It gives sharding, client-side routing, and
> automatic failover out of the box. On top of that, I'd add cache-aside,
> hot-key local caching, stampede protection, and expiry jitter. I'd only build
> a custom etcd-based control plane at planet scale, where the node count or
> multi-region needs outgrow Redis Cluster."
