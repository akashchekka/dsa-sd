---
title: Horizontally Scaling SQL and NoSQL Databases (100M RPS)
description: Interview notes on scaling SQL and NoSQL databases horizontally to 100 million requests per second, covering sharding, caching, Vitess, per-shard transaction limits, and NoSQL partitioning trade-offs
---

## Table of contents

* [The core idea](#the-core-idea)
* [Part 1: Scaling databases to 100M RPS](#part-1-scaling-databases-to-100m-rps)
* [Part 2: Vitess](#part-2-vitess)
* [Part 3: Maximum open transactions per shard](#part-3-maximum-open-transactions-per-shard)
* [Part 4: NoSQL at millions of QPS](#part-4-nosql-at-millions-of-qps)
* [Interview summaries](#interview-summaries)

## The core idea

> [!IMPORTANT]
> 100 million API requests per second is **not** 100 million database
> operations per second. Sending every request to a database is neither
> practical nor necessary. The design must remove most database traffic
> through caching, precomputation, batching, and asynchronous processing.

At this scale, the challenge is not choosing SQL versus NoSQL. The challenge
is **reducing database traffic** and **keeping every operation local to one
partition**.

## Part 1: Scaling databases to 100M RPS

### Capacity math

Assumptions:

* 100 million API requests per second
* 1 KB average request
* 90% reads, 10% writes

| What                         | Calculation        | Result                          |
|------------------------------|--------------------|---------------------------------|
| Incoming data                | 100M x 1 KB        | **~100 GB/sec**                 |
| Data per day (no replicas)   | 100 GB x 86,400    | **~8.64 PB/day**                |
| Writes if all reach storage  | 100M x 10%         | **10M writes/sec**              |

The first design goal is reducing how many requests reach the database. For
example:

| Layer                                        | Traffic remaining   |
|----------------------------------------------|---------------------|
| Incoming traffic                             | 100M RPS            |
| CDN or edge cache (90% hit rate)             | 10M RPS             |
| Regional cache (90% hit rate)                | 1M RPS              |
| Application cache and request coalescing     | 300K to 700K RPS    |
| Database                                     | Manageable load     |

These numbers are illustrative. Real capacity must come from benchmarks.

### High-level architecture

```text
Clients
   |
Anycast DNS / Global Load Balancer
   |
CDN and Edge Cache
   |
Regional Load Balancers
   |
Stateless Application Servers
   |
Request Router / Shard Router
   |
+-------------------------------+
| Cache Cluster                 |
| Redis / Memcached / Local     |
+-------------------------------+
   |
+-------------------------------+
| Database Shards               |
| Shard 0 | Shard 1 | ... | N   |
+-------------------------------+
   |
Event Log / Queue
   |
Asynchronous Workers, Analytics and Search
```

Use multiple geographic regions. Each region serves nearby users instead of
sending every request across the world.

### Partition the data

Horizontal scaling comes mainly from **partitioning**, also called
**sharding**. Each server stores only part of the data.

Range partitioning:

```text
userId 1 to 1M       -> Shard 1
userId 1M to 2M      -> Shard 2
userId 2M to 3M      -> Shard 3
```

Hash partitioning spreads load more evenly:

```text
partition = hash(userId) % numberOfLogicalPartitions
```

Do not map keys directly to physical servers. Use many **logical
partitions**, and map them to servers:

```text
userId -> logical partition -> physical database node
```

For example, 16,384 logical partitions spread across 500 physical nodes. Adding
capacity means moving some logical partitions, not rehashing every key. A shard
directory or a consistent-hashing ring stores the mapping.

#### Choosing the partition key

A good partition key has:

* High cardinality (many distinct values)
* Even traffic distribution
* Queries that usually target one partition
* No predictable hot partitions
* Stable ownership

| Good keys      | Poor keys                                       |
|----------------|-------------------------------------------------|
| `user_id`      | Current date                                    |
| `tenant_id`    | Country alone                                   |
| `account_id`   | Status such as `ACTIVE`                         |
| `device_id`    | Sequential IDs without hashing                  |
|                | Celebrity or globally popular object IDs        |

> [!TIP]
> Choose the partition key from **access patterns**, not only from how evenly
> the data is spread.

### Scaling SQL option A: application-level sharding

Run many independent SQL databases. Each shard has:

* One primary for writes
* Several read replicas
* Its own local indexes
* Backups and change logs

```text
Application receives userId
        |
Shard router determines shard
        |
Query is sent directly to that shard (primary + replicas)
```

| Advantages                                   | Challenges                                  |
|----------------------------------------------|---------------------------------------------|
| Uses mature databases (PostgreSQL, MySQL)    | Cross-shard joins are expensive             |
| Strong transactions within one shard         | Cross-shard transactions are difficult      |
| Failures stay isolated to one shard          | Rebalancing requires moving data            |
| Capacity can be added gradually              | Global unique constraints are difficult     |
|                                              | Schema migrations must run on every shard   |

> [!IMPORTANT]
> Keep business transactions inside one shard whenever possible.

Store all data belonging to one customer on the same shard (customer, orders,
payments, addresses). A customer operation then uses a normal local SQL
transaction.

For workflows that span shards, use:

* Event-driven processing
* Idempotency keys
* Saga workflows
* Transactional outbox
* Reconciliation jobs

Avoid distributed transactions on the critical path at this scale.

### Scaling SQL option B: distributed SQL

Distributed SQL systems partition and replicate tables automatically.
Examples include Spanner, CockroachDB, and YugabyteDB.

```text
SQL API
   |
Distributed query and transaction layer
   |
Replicated data partitions
```

| Advantages                        | Trade-offs                                        |
|-----------------------------------|---------------------------------------------------|
| Familiar SQL query model          | Distributed transactions add network latency      |
| Automatic partitioning            | Cross-partition queries remain expensive          |
| Strong consistency                | Poor partition keys still create hotspots         |
| Built-in replication and failover | Operational complexity does not disappear         |
| Cross-node transactions           | Global consistency requires coordination          |

Distributed SQL makes sharding easier to manage. It does not remove the limits
of distributed systems.

### Scaling NoSQL

Many NoSQL databases partition data natively:

```text
partition = hash(partitionKey)

Partition 42:
    Leader:  Node A
    Replica: Node B
    Replica: Node C
```

| Advantages                              | Trade-offs                                     |
|-----------------------------------------|------------------------------------------------|
| High write throughput                   | Limited or no joins                            |
| Built-in partition distribution         | Data is often duplicated                       |
| Adding nodes is straightforward         | Queries must be designed in advance            |
| Tunable consistency in many systems     | Secondary indexes can be expensive             |
| Fast key-based lookups                  | Cross-partition operations are costly          |
| Fits denormalized records               | Eventual consistency affects app behavior      |

Model data around queries. Instead of normalized `users`, `orders`,
`order_items`, and `products` tables, store what one query needs together:

```text
Partition key: customerId
Sort key:      orderTimestamp

{
  orderId,
  customerId,
  items,
  total,
  status
}
```

This duplicates some data, but a single partition lookup answers the query.
Part 4 covers NoSQL scaling in depth.

### Replication versus sharding

Replication and sharding solve different problems:

* Sharding divides the workload across servers.
* Replication copies each shard for availability and extra read capacity.

```text
Shard 1 -> Primary + 2 replicas
Shard 2 -> Primary + 2 replicas
Shard 3 -> Primary + 2 replicas
```

Read replicas help with reports, profile reads, product reads, and other
queries that tolerate slightly stale data. They do **not** scale writes,
because every replica must apply every write.

> [!WARNING]
> Watch replication lag. A user who updates a record and immediately reads from
> a replica might see old data. Fix this with read-from-primary after a write,
> session consistency, version tokens, or short-lived sticky routing.

### Cache aggressively

At 100M RPS, caching is part of the data architecture, not an optional
optimization.

| Layer                       | Where                   | Notes                                                 |
|-----------------------------|-------------------------|-------------------------------------------------------|
| L1: process-local cache     | Inside each app server  | Fastest, no network call, can be stale across servers |
| L2: regional cache          | Shared cache cluster    | Handles millions of requests, shields the database    |
| L3: CDN or edge cache       | Closest to users        | Best for public or rarely changing content            |

Cache protections:

* Use **request coalescing** (single flight) so one request rebuilds an expired
  key while the others wait for it.
* Add **TTL jitter** (`TTL = baseTTL + randomJitter`) so millions of keys do not
  expire at once.
* Use **stale-while-revalidate** to return slightly stale data while refreshing
  in the background.
* Use **negative caching** to remember "not found" results briefly.
* **Replicate hot keys** across several cache nodes instead of one.

```text
1,000,000 requests for one expired key
        |
Single-flight lock
        |
1 database query
```

### Process writes asynchronously

Not every write needs to reach the database before responding. The
synchronous path does only what is required to respond safely:

```text
Request
   |
Validate and authenticate
   |
Write event to a durable log
   |
Return "accepted"
   |
Consumers update databases, indexes, and analytics
```

The durable log absorbs traffic bursts and lets consumers process at a steady
rate. Use batching, backpressure, idempotent consumers, retry queues,
dead-letter queues, and per-key ordering where needed.

Example: do not run this 100 million times per second for view counts:

```sql
UPDATE videos
SET views = views + 1
WHERE video_id = ?;
```

Instead:

1. Record compact view events.
2. Aggregate counts in memory.
3. Flush increments in batches.
4. Reconcile totals periodically.

Millions of individual writes become a small number of batched writes.

### Prevent hot partitions

Balance partitions by **request rate**, not only by data size. If a celebrity
with 100 million followers uses `partitionKey = celebrityId`, one partition
receives nearly all the load.

| Technique              | How it works                                                         |
|------------------------|----------------------------------------------------------------------|
| Write sharding         | `celebrityId + hash(requestId) % 1000`, then merge buckets on read   |
| Time bucketing         | `entityId + hourBucket` (the current bucket can still get hot)       |
| Replicate hot reads    | Copy popular, unchanging data to many cache nodes, regions, and edges |
| Dedicated partitions   | Move very hot tenants or keys to isolated capacity                   |

### Avoid scatter-gather queries

```sql
SELECT *
FROM orders
WHERE status = 'PENDING';
```

Without the partition key, this query must go to every shard. With 1,000
shards, one client request becomes 1,000 database requests.

Instead:

* Maintain a dedicated index table keyed by status.
* Build materialized views asynchronously.
* Use a search system.
* Precompute feeds.
* Run global analytics outside the serving database.

> [!TIP]
> On the serving path, aim for **one request to one partition**. A small, fixed
> number of partitions is acceptable. Unbounded fan-out is dangerous.

### Estimate the shard count

Use measured sustainable throughput, not vendor maximums:

```text
Required shards = Peak database ops per second / Safe ops per shard
```

Then add room for replication overhead, failover, rebalancing, growth, hot-key
imbalance, and 30 to 50% headroom.

```text
Database traffic:        1,000,000 ops/sec
Safe shard capacity:        20,000 ops/sec
Base shard count:               50
Target utilization:             60%
Adjusted shard count:      ~84 shards
```

If one node fails, its replicas must absorb its traffic without overloading.
Benchmark with realistic record sizes, indexes, read/write ratio, durability
settings, consistency level, replication factor, request distribution, and hot
keys.

### SQL versus NoSQL decision

| Requirement                       | SQL                      | NoSQL              |
|-----------------------------------|--------------------------|--------------------|
| Complex relationships and joins   | Strong                   | Limited            |
| Multi-record transactions         | Strong                   | Often limited      |
| Flexible, denormalized records    | Possible                 | Strong fit         |
| Key-based high throughput         | With sharding            | Strong fit         |
| Automatic partitioning            | Distributed SQL          | Common             |
| Ad hoc queries                    | Strong                   | Often weaker       |
| Strong global consistency         | Distributed SQL          | Depends on system  |
| Very high write ingestion         | Harder                   | Often strong       |

At this scale, the answer is usually **both**, each for the data it fits:

* SQL for payments, accounts, and transactional state
* Key-value storage for sessions and profiles
* Wide-column storage for activity streams
* A search engine for text search and filtering
* Object storage for large content
* An event log for ingestion
* A data warehouse for analytics

### Multi-region strategy

| Approach                    | How it works                                | Trade-off                                          |
|-----------------------------|---------------------------------------------|----------------------------------------------------|
| Single writer per key       | `userId -> home region -> shard`            | Simple and consistent, but remote writes are slower |
| Active-active writes        | Any region accepts writes                   | Low write latency, but needs conflict resolution   |

Active-active adds conflict resolution, clock ordering, duplicate request
handling, and global uniqueness problems. Choose it only when the business
needs it.

### Reliability requirements

At 100M RPS, failures happen all the time. The design needs:

* Per-shard circuit breakers
* Rate limiting and load shedding
* Backpressure and bounded queues
* Timeouts and idempotency keys
* Automated failover
* Point-in-time recovery and regular backup restore tests
* Regional evacuation (moving all traffic out of a failing region)

Monitor averages **and** skew:

* Requests per partition
* p50, p95, and p99 latency
* Cache hit rate
* Replication lag
* Queue age
* Throttled requests
* Hot-key frequency
* Rebalancing progress
* Storage and index growth

## Part 2: Vitess

### What Vitess is

**Vitess is a sharding and clustering layer that runs in front of MySQL.** To
the application, many MySQL servers look like one large MySQL database.
Vitess handles:

* Routing each query to the correct shard
* Connection pooling
* Resharding without downtime
* Replica management and failover
* Online schema changes

YouTube built Vitess around 2010, when its MySQL databases outgrew single
servers. It is now a graduated CNCF project. Slack, GitHub, Shopify, HubSpot,
and others run it, and PlanetScale's managed database is built on it.

> [!NOTE]
> In one line: Vitess automates application-level MySQL sharding so the
> application does not manage shards itself.

### Vitess architecture

```text
              Application (MySQL driver / gRPC)
                          |
          +---------------+---------------+
          |               |               |
       VTGate          VTGate          VTGate        <- stateless query routers
          |               |               |
          +-------+-------+-------+-------+
                  |               |
         Topology Service (etcd / ZooKeeper)          <- shard map and metadata
                  |
     +------------+------------+------------+
     |            |            |            |
  Shard -80    Shard 80-     ...         Shard N
  +--------+   +--------+
  |VTTablet|   |VTTablet|     <- sidecar next to each MySQL instance
  | MySQL  |   | MySQL  |
  |primary |   |primary |
  +--------+   +--------+
  replicas     replicas
```

| Component            | Role                                                                                                      |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| **VTGate**           | Stateless proxy that speaks the MySQL protocol. Parses each query and routes it to the right shards. Scales like a web server. |
| **VTTablet**         | Runs next to every MySQL instance. Pools connections, enforces limits and timeouts, merges identical in-flight reads. |
| **Topology service** | Stores the keyspace and shard layout and which instance is primary.                                       |
| **VTOrc**            | Detects a failed primary and promotes a replica.                                                          |
| **VReplication**     | Streams data between shards. Powers resharding, table moves, and materialized views.                      |

### How Vitess shards data

* A **keyspace** is a logical database. It can be unsharded or split into many
  shards.
* A **VIndex** maps a column value to a **keyspace ID**, for example
  `hash(customer_id)`.
* Each shard owns a **range** of keyspace IDs.

```text
customer_id = 9182
      |
hash VIndex
      |
keyspace_id = 0xA3...
      |
falls in range 80-C0
      |
Shard 80-C0
```

A query with the sharding key goes to **one shard** (the fast path):

```sql
SELECT * FROM orders WHERE customer_id = 9182;
```

A query without it goes to **every shard** and VTGate merges the results:

```sql
SELECT * FROM orders WHERE status = 'PENDING';
```

To avoid that scatter, add a **lookup VIndex**: a secondary index table that
maps the column back to the shard.

### Resharding

When a shard gets too large or too hot, split it:

```text
Shard 80-  ->  Shard 80-C0  +  Shard C0-
```

VReplication copies the data and keeps it in sync while traffic continues. The
final cutover typically takes only seconds, and the application needs no code
changes.

### Can Vitess handle millions of concurrent transactions

**Yes for single-shard work. Use caution for cross-shard work.** First,
separate three different numbers:

| Metric                              | Meaning                                    | Millions possible?                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------------|
| Client connections                  | Open connections from app servers          | **Yes.** VTGate multiplexes them onto a small pool of MySQL connections.          |
| Throughput (QPS/TPS)                | Queries or transactions per second         | **Yes**, if most stay in one shard. Slack has reported peaks above 2M QPS.        |
| Simultaneously open transactions    | Transactions in progress at the same time  | **Only if they are short.** Each one holds a real MySQL connection until commit.  |

#### Why connection pooling matters

MySQL uses one thread per connection, so a few thousand connections already
cause problems on one server.

```text
1,000,000 client connections
        |
     VTGates
        |
VTTablet pools (~hundreds per MySQL instance)
        |
     MySQL
```

Simple reads borrow a connection and return it immediately. **Inside a
transaction, the connection is pinned** until commit or rollback and cannot be
shared.

#### Little's Law for open transactions

```text
Open transactions = Throughput x Transaction duration
```

Short transactions:

```text
Throughput:        1,000,000 transactions/sec
Average duration:  5 ms
Open at once:      1,000,000 x 0.005 = 5,000

Across 200 shards  ->  ~25 open transactions per shard  (easy)
```

Long transactions (for example, a network call inside the transaction):

```text
1,000,000 x 2 sec = 2,000,000 open transactions  (system collapses)
```

> [!IMPORTANT]
> Millions of transactions per second is possible only when each transaction is
> short. Never make remote calls while a database transaction is open.

### Vitess transaction modes

| Mode                          | Behavior                                                                                                         |
|-------------------------------|------------------------------------------------------------------------------------------------------------------|
| Single-shard                  | Full MySQL ACID guarantees. Fast and safe. The design goal.                                                      |
| `MULTI` (default, cross-shard)| Best effort. Commits shards one after another. A failure partway through can leave a **partial commit**.         |
| `TWOPC` (cross-shard)         | Two-phase commit for atomicity. Slower, and readers can briefly see a partial state. Maturity depends on version. |
| `SINGLE`                      | Rejects any transaction that touches more than one shard. Useful to enforce good design.                         |

Production pattern:

1. Put related data on the same shard by choosing the right sharding key (for
   example, shard `customers`, `orders`, and `payments` by `customer_id`).
2. Keep business transactions single-shard.
3. Handle rare cross-shard workflows with sagas, a transactional outbox, and
   idempotency keys instead of distributed transactions.

### When to use Vitess

Use Vitess when:

* You already run MySQL and are reaching the limits of one server.
* Most queries can be keyed by one entity (user, tenant, or customer).
* You want to keep SQL and existing tooling while scaling horizontally.
* You need online resharding and online schema changes.

Avoid it, or consider alternatives, when:

* The workload depends on many cross-shard joins or transactions.
* You need strict global serializability across all data. Distributed SQL
  (Spanner, CockroachDB) fits better.
* You use PostgreSQL. Vitess supports only MySQL; Citus is a common Postgres
  option.
* The data fits on one server with replicas. Vitess adds complexity you do not
  need yet.

## Part 3: Maximum open transactions per shard

There is **no fixed number**. Practical rule of thumb for one MySQL primary:

| Open transactions  | What it means                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| Tens to about 200  | Healthy zone. Most well-run shards stay here.                                 |
| A few hundred      | Workable only if transactions are short and rarely touch the same rows.      |
| 1,000 or more      | Warning zone. Latency usually rises sharply from lock waits, CPU, or memory. |

For reference, Vitess ships with a **transaction pool of only 20 per tablet**
by default (`queryserver-config-transaction-cap`). Production teams usually
raise it to a few hundred after benchmarking.

### Open versus active transactions

| State                                         | Cost                                                  |
|-----------------------------------------------|-------------------------------------------------------|
| Actively running a query                      | Uses CPU and disk I/O                                 |
| Open but idle (waiting on the app)            | Holds a connection, holds locks, blocks undo cleanup  |

### What limits concurrency

#### CPU limits active transactions

A database server does useful work on only a few threads at a time:

```text
Useful active concurrency ≈ 2 to 4 x CPU cores

32-core server -> ~64 to 128 truly active transactions
```

Above that, threads mostly wait on CPU scheduling and internal latches.
Throughput stops rising and latency climbs.

#### Locks limit hot rows

If 500 transactions update the same row, they run one at a time, no matter how
many cores the server has. Hot rows limit concurrency more than hardware does.

#### Undo logs limit long-running transactions

InnoDB keeps old row versions until the oldest open transaction finishes. One
transaction left open for minutes can:

* Grow the undo history without limit (the history list length)
* Slow every read that must skip old row versions
* Eventually degrade the whole shard

> [!WARNING]
> The duration of the longest transaction often matters more than the total
> number of transactions.

#### Memory limits connection count

Each MySQL connection uses its own memory for session buffers, sorts, and
temporary tables. Thousands of connections can consume several gigabytes and
compete with the buffer pool that caches data.

### From concurrency to throughput

```text
Max TPS per shard = Transaction slots / Average transaction duration
```

| Slots | Avg duration | Theoretical max TPS |
|------:|-------------:|--------------------:|
|   200 |         2 ms |             100,000 |
|   200 |         5 ms |              40,000 |
|   200 |        50 ms |               4,000 |
|   200 |          1 s |                 200 |

In practice, write-heavy shards usually reach their limit at roughly 10,000 to
50,000 small write transactions per second. Disk sync on commit, replication,
and lock contention set that limit before the slot count does. Read-heavy
shards can go much higher. These are planning estimates only.

> [!TIP]
> Shortening transactions increases throughput more than adding transaction
> slots.

### How to size a shard

1. Measure the average and p99 transaction duration under realistic load.
2. Benchmark one shard. Raise concurrency until p99 latency rises sharply, then
   use about 60 to 70% of that point as the safe limit.
3. Set the pool size (for example, the Vitess transaction cap) to that safe
   limit. Extra requests should queue or fail fast instead of overloading
   MySQL.
4. Calculate the shard count:

   ```text
   Shards = Peak TPS / Safe TPS per shard  (+ 30 to 50% headroom)
   ```

5. Add guardrails:
   * Set a transaction timeout (for example, 1 to 5 seconds).
   * Alert on long-running transactions and undo history growth.
   * Never make network calls inside an open transaction.

## Part 4: NoSQL at millions of QPS

**Yes, NoSQL databases scale to millions of QPS horizontally**, as long as the
data model fits the database.

| System                   | Reported scale                                                                      |
|--------------------------|-------------------------------------------------------------------------------------|
| Amazon DynamoDB          | AWS reported more than **100 million requests/sec** during Prime Day peaks          |
| Apache Cassandra         | Apple has described **more than 75,000 nodes**; Netflix reports millions of writes/sec |
| Redis / Memcached        | Millions of operations/sec for caches and session storage                           |

### Why NoSQL scales out more easily

| Design choice                          | Why it helps                                                                   |
|----------------------------------------|--------------------------------------------------------------------------------|
| Built-in partitioning                  | Tables are spread across nodes by hashing the partition key automatically.    |
| No joins                               | Each request reads one partition on a few nodes.                               |
| Few cross-partition transactions       | No coordination or waiting on locks held by other nodes.                       |
| Leaderless replication (Cassandra)     | Any replica accepts writes, so no single primary per shard bottlenecks writes. |
| LSM-tree storage                       | Writes go to memory and flush sequentially, making writes fast.               |
| Tunable consistency                    | Choose how many replicas must respond, trading consistency for speed.          |
| Asynchronous connection handling       | No thread per connection, so many clients are cheap.                           |

> [!NOTE]
> NoSQL removes the features that need coordination between nodes: joins,
> global transactions, and global indexes. Without coordination, adding a node
> adds capacity almost linearly.

### How a request flows (Cassandra-style)

```text
Request: get user 9182
     |
Client driver hashes the partition key
     |
token = hash(9182) -> belongs to Node C
     |
Replication factor 3 -> Nodes C, D, E hold copies
     |
Consistency level QUORUM -> wait for 2 of 3 replicas
     |
Return result
```

To add capacity, add nodes. Each new node takes over part of the token ring,
and data streams to it in the background.

Consistency rule:

```text
R + W > N   ->   reads see the latest write

N = 3, W = 2, R = 2  ->  2 + 2 > 3  ✓  strong reads
N = 3, W = 1, R = 1  ->  1 + 1 < 3  ✗  fastest, eventually consistent
```

### NoSQL capacity math

Assume 10 million QPS of database traffic, 80% reads, 20% writes, and
replication factor 3:

```text
Reads:   8M/s at QUORUM -> 2 replicas each   -> 16M replica reads/s
Writes:  2M/s, stored on all 3 replicas      ->  6M replica writes/s
Total work on nodes                          -> ~22M operations/s
```

With about 25,000 safe operations per second per node (a common Cassandra
planning figure; ScyllaDB and similar engines can do more):

```text
22,000,000 / 25,000   ≈ 880 nodes
+ 30 to 50% headroom  ≈ 1,150 to 1,300 nodes
```

> [!IMPORTANT]
> Replication multiplies the work. Size the cluster on replica-level operations,
> not client requests.

### NoSQL limits that remain

#### Per-partition throughput ceiling

The cluster scales, but each partition key lives on a fixed set of replicas.
DynamoDB limits each partition to about **3,000 reads and 1,000 writes per
second**. A cluster can serve 100M QPS while one celebrity's row is throttled.

Fixes:

* Write sharding: `key = celebrityId#bucket(0..N)`, merge buckets on read
* Cache hot reads in front of the database
* Batch counters in memory and flush periodically

#### Queries must use the partition key

```text
Good:  orders WHERE customer_id = 9182   -> 1 partition
Bad:   orders WHERE status = 'PENDING'   -> every partition
```

Secondary indexes in many NoSQL systems either query every node or update
asynchronously. At scale, **write the data twice**, into a second table keyed
by the other access pattern.

#### Transactions are limited and expensive

| System    | Transaction support                                                                  |
|-----------|--------------------------------------------------------------------------------------|
| DynamoDB  | Up to 100 items per transaction, at about twice the cost of normal operations        |
| Cassandra | Lightweight transactions use Paxos with several round trips, so they are much slower |
| MongoDB   | Multi-document transactions work, but across shards they need coordination           |

Use them rarely. For multi-item workflows, prefer idempotent writes,
conditional updates, and sagas.

#### Large partitions

A partition that grows forever, such as one row per user holding every event,
causes slow reads, compaction pressure, and uneven nodes. Bucket by time, for
example `userId#2026-10`.

#### Eventual consistency

With weaker consistency, a user might not immediately see their own update. Use
read-your-writes routing, version numbers, or QUORUM where correctness matters.

#### Background work competes with traffic

LSM databases regularly **compact** files and **repair** replicas, which uses
disk and CPU. Clusters near full capacity see p99 latency spikes during
compaction or repair. Keep headroom.

### Sharded SQL (Vitess) versus NoSQL

|                              | Sharded SQL (Vitess)                  | NoSQL (Cassandra / DynamoDB)                  |
|------------------------------|---------------------------------------|-----------------------------------------------|
| Horizontal scaling           | Yes, by resharding                    | Yes, partitioning is built in                 |
| Single-key reads and writes  | Fast                                  | Fast                                          |
| Write throughput             | Limited by one primary per shard      | Very high (leaderless writes, LSM storage)    |
| Transactions                 | Full ACID within a shard              | Limited and expensive                         |
| Joins and flexible queries   | Yes, within a shard                   | No, design one table per query                |
| Schema                       | Fixed                                 | Flexible                                      |
| Best fit                     | Payments, orders, accounts            | Feeds, sessions, events, metrics, profiles    |

## Interview summaries

### Summary: scaling to 100M RPS

> To support 100 million requests per second, I would not send 100 million
> operations to a database. I would use edge and regional caches to remove most
> reads, partition data using a high-cardinality key, replicate each partition
> for availability, and route each request to one shard. SQL data would use
> application sharding or distributed SQL, while high-volume key-based workloads
> would use partitioned NoSQL storage. Writes that do not need immediate
> consistency would go into a durable event log and be batched asynchronously. I
> would design for hot keys, avoid cross-shard transactions and scatter-gather
> queries, and keep enough spare capacity to survive node or regional failures.

### Summary: Vitess

> Vitess is a sharding layer for MySQL that YouTube built. VTGate routes queries
> using a VIndex on the sharding key, VTTablet pools connections and protects
> each MySQL instance, and VReplication lets us reshard online. It can serve
> millions of queries and transactions per second, as Slack and YouTube do, but
> only if the sharding key keeps each transaction on one shard and transactions
> stay short. By Little's Law, open transactions equal throughput times
> duration, and every open transaction holds a real MySQL connection. So I would
> co-locate related data on one shard, keep transactions in the low
> milliseconds, avoid scatter queries with lookup VIndexes, and handle
> cross-shard workflows asynchronously with sagas.

### Summary: open transactions per shard

> A shard has no fixed maximum. The limit comes from CPU for active transactions
> (about 2 to 4 times the core count), lock contention on hot rows, undo-log
> growth from long transactions, and memory per connection. A healthy MySQL
> primary runs tens to a couple of hundred concurrent transactions, which is why
> the Vitess default pool is only 20. By Little's Law, 200 slots at 5 ms give
> about 40,000 TPS per shard, so I focus on keeping transactions short instead
> of adding slots. I find the real limit by benchmarking, cap the pool there,
> and add shards for more throughput.

### Summary: NoSQL at millions of QPS

> NoSQL databases scale to millions of QPS horizontally; DynamoDB has served
> over 100 million requests per second at Amazon. They scale well because they
> remove features that need coordination between nodes: joins, global
> transactions, and global indexes. Each request goes to one partition and its
> replicas. The limits remain real. Every partition has its own throughput
> ceiling, so hot keys need write sharding or caching. Queries without the
> partition key fan out to every node, so I denormalize into one table per
> access pattern. Replication multiplies the work, so I size the cluster on
> replica operations with headroom for compaction and failures. For data that
> needs strong transactions, such as payments, I still use sharded SQL. For
> high-volume key-based data, I use NoSQL.
