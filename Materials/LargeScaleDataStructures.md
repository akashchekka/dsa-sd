## Overview

Large-scale systems combine several data structures. Each is selected for a specific access pattern such as exact lookup, range scanning, prefix search, scheduling, partitioning, or approximate counting.

A data structure is usually local to one process or storage node. Replication, sharding, consensus, and failover turn these local structures into a distributed system.

> [!IMPORTANT]
> Big-O complexity is only the starting point. At scale, memory layout, disk access, network round trips, contention, write amplification, cache locality, and recovery behavior often matter more.

## Quick Reference

| Data structure        | Primary purpose                           | Used in                                           |
|-----------------------|-------------------------------------------|---------------------------------------------------|
| Hash table            | Expected `O(1)` key lookup                | Caches, sessions, deduplication, metadata         |
| B+ tree               | Ordered lookup and range scans            | Relational databases and file systems             |
| LSM tree              | High write throughput                     | Cassandra, RocksDB, LevelDB                       |
| Append-only log       | Sequential durable writes and replay      | Kafka, database WAL, event sourcing               |
| Skip list             | Sorted in-memory data                     | Redis sorted sets and LSM memtables               |
| Trie or radix tree    | Prefix matching                           | Autocomplete, routing, and IP lookup              |
| Heap                  | Minimum, maximum, and top-K selection      | Schedulers, ranking, and retry queues             |
| Queue or deque        | Work buffering and distribution           | Job processing and work stealing                  |
| Ring buffer           | Fixed-memory event transport              | Logging, network I/O, low-latency pipelines       |
| Inverted index        | Term-to-document lookup                   | Elasticsearch, OpenSearch, and search engines     |
| Bitmap                | Fast set operations                       | Analytics, permissions, and audience filtering    |
| Consistent hash ring  | Assign keys to nodes                      | Distributed caches, databases, and routing        |
| Merkle tree           | Compare replicas efficiently              | Anti-entropy repair and integrity verification    |
| Graph or DAG          | Relationships and dependencies            | Social graphs, workflows, and build systems       |
| Spatial index         | Geographic candidate search               | Maps, ride sharing, and delivery systems          |
| Probabilistic summary | Memory-efficient approximate answers      | Analytics, storage engines, and abuse detection   |

## Hash Tables

Hash tables are used when a system needs fast exact lookup by key.

Examples:

* Cache key to cached object
* User ID to active session
* Request ID to idempotency result
* Connection ID to WebSocket connection
* Object ID to metadata

Tradeoffs:

* No natural ordering
* Resizing can create latency spikes
* Poor hash functions can cause collisions
* Unbounded keys can exhaust memory

## B+ Trees

B+ trees keep keys ordered and store many keys in each disk page.

They support:

* Exact lookup
* Range queries
* Sorting
* Prefix ranges
* Sequential traversal

A query such as the following benefits from a B+ tree index:

```sql
SELECT *
FROM orders
WHERE user_id = 123
  AND created_at >= '2026-08-01'
ORDER BY created_at;
```

B+ trees are effective for read-heavy databases because their high branching factor minimizes disk reads. Their main costs are random writes, page splits, and index maintenance.

## LSM Trees

Log-Structured Merge trees optimize sustained write throughput.

```text
Write
  -> Write-ahead log
  -> Ordered in-memory memtable
  -> Immutable SSTable files
  -> Background compaction
```

Common components include:

* Write-ahead log for durability
* Skip list or ordered tree for the memtable
* Immutable sorted files on disk
* Sparse indexes for locating blocks
* Bloom filters for avoiding unnecessary file reads
* Compaction for merging files and removing old versions

LSM trees make writes sequential, but introduce compaction, read amplification, write amplification, and less predictable latency.

## Append-Only Logs

An append-only log writes records sequentially and assigns them increasing offsets.

Uses include:

* Kafka partitions
* Database write-ahead logs
* Event sourcing
* Change data capture
* Replication streams
* Audit trails

Logs provide efficient writes and replay. They require segment indexes, retention policies, compaction, and replication to remain manageable.

## Skip Lists

A skip list maintains sorted elements using multiple probabilistic linked-list levels.

Expected complexity:

* Search: $O(\log n)$
* Insert: $O(\log n)$
* Delete: $O(\log n)$

Redis combines a hash table and skip list for large sorted sets:

* Hash table for direct member lookup
* Skip list for score ordering and range queries

## Tries and Radix Trees

Tries organize strings by shared prefixes. A radix tree compresses chains of single-child nodes to save memory.

Common uses:

* Search autocomplete
* URL routing
* Dictionary lookup
* IP longest-prefix matching
* Configuration path lookup

Operations take approximately $O(k)$, where $k$ is the key length, rather than depending directly on the number of stored keys.

## Heaps and Priority Queues

A heap efficiently exposes the minimum or maximum item.

Common uses:

* Job scheduling
* Earliest-deadline processing
* Delayed retries
* Top-K ranking
* Merging sorted streams
* Selecting nearest candidates

For top-K processing, a min-heap containing only $K$ elements avoids sorting the complete dataset.

## Queues, Deques, and Ring Buffers

Queues buffer work and decouple producers from consumers.

```text
Producer -> Bounded Queue -> Worker Pool
```

Large-scale systems should prefer bounded queues. An unbounded queue hides overload until memory is exhausted or queueing latency becomes unacceptable.

Deques are common in work-stealing schedulers:

* A worker consumes from its local end
* Idle workers steal tasks from the opposite end

Ring buffers use fixed-size circular arrays. They provide predictable memory usage, fewer allocations, and good CPU cache locality. They are used in network processing, logging, and low-latency event pipelines.

When producers catch consumers, the system needs an explicit policy:

* Block the producer
* Reject the event
* Spill to durable storage
* Overwrite old data when loss is acceptable

## Timing Wheels

A timing wheel groups timers into buckets representing time intervals. Advancing the wheel processes the bucket associated with the current interval.

Common uses:

* Connection timeouts
* Cache expiration
* Delayed retries
* Heartbeat deadlines
* Scheduled task execution

A timing wheel scales better than one global priority queue when a system manages millions of timers and does not need exact sub-millisecond ordering. The tradeoff is timer granularity.

## Inverted Indexes

An inverted index maps terms to documents.

```text
system -> doc1, doc5, doc8
design -> doc1, doc2, doc9
```

Search engines combine:

* Inverted indexes for term retrieval
* Compressed postings lists for storage efficiency
* Bitmaps for filters
* Heaps for top-K results
* Tries or finite-state structures for term lookup

The search index is generally a derived projection rather than the authoritative source of data.

## Bitmap Indexes

A bitmap represents set membership with bits. Boolean operations over machine words make intersection, union, and difference efficient.

Common uses:

* Analytics filters
* Audience segments
* Feature eligibility
* Access-control sets
* Search filters

A plain bitmap wastes space when identifiers are sparse. Compressed formats such as Roaring bitmaps work well for sparse or clustered integer sets.

## Consistent Hashing

Consistent hashing distributes keys among a changing set of nodes.

```text
hash(key) -> ring position -> next virtual node -> server
```

Adding or removing a node moves only part of the keyspace. Virtual nodes improve load distribution and allow machines to own different capacity shares.

Consistent hashing does not independently solve:

* Replication
* Node failure detection
* Hot keys
* Data migration
* Unequal load

These require replica placement, health detection, bounded-load routing, and sometimes key splitting.

## Merkle Trees

A Merkle tree stores hierarchical hashes.

Two replicas first compare root hashes. If the roots differ, they descend only through mismatched branches until they locate the divergent ranges.

Uses include:

* Replica synchronization
* Anti-entropy repair
* Distributed storage verification
* Content integrity checking

This avoids transferring every record merely to compare two large datasets.

## Graphs and DAGs

Graphs represent relationships:

* Users and friendships
* Roads and intersections
* Services and dependencies
* Accounts and suspicious transactions
* Products and recommendations

Directed acyclic graphs represent dependency-constrained workflows:

* Build systems
* Data pipelines
* Workflow engines
* Task orchestration
* Data lineage

A topological ordering determines when dependent tasks may execute.

## Version Vectors and CRDTs

Version vectors track the updates observed by each replica. They distinguish a version that causally follows another from versions created concurrently.

Conflict-free replicated data types (CRDTs) define merge operations that allow replicas to converge after independent updates. Their merge behavior is associative, commutative, and idempotent.

Common CRDT families include:

* Grow-only and positive-negative counters
* Grow-only, add-wins, and remove-wins sets
* Last-writer-wins registers
* Replicated sequences and maps

CRDTs permit coordination-free updates, but they add metadata and require application-specific conflict semantics.

## Spatial Indexes

Spatial structures narrow millions of geographic objects to a small candidate set.

Common choices:

* Quadtree for adaptive two-dimensional partitioning
* R-tree for rectangles and overlapping regions
* Geohash for prefix-based geographic cells
* S2 for hierarchical spherical cells
* H3 for hexagonal geographic aggregation

Typical nearby search:

```text
Coordinates
  -> Spatial cell
  -> Current and neighboring cells
  -> Candidate objects
  -> Exact distance or ETA
  -> Ranked results
```

Spatial indexing generates candidates. An exact distance or road-network ETA calculation then ranks and filters those candidates.

## Probabilistic Data Structures

These structures trade exactness for significant memory savings.

| Structure        | Question answered                         | Error behavior                              |
|------------------|-------------------------------------------|---------------------------------------------|
| Bloom filter     | Is the item present?                      | False positives, but no false negatives     |
| Count-Min Sketch | How frequent is the item?                 | May overcount, but does not undercount       |
| HyperLogLog      | How many distinct items exist?            | Bounded cardinality estimation error        |

Examples:

* Bloom filter before expensive database or disk reads
* Count-Min Sketch for trending items and heavy hitters
* HyperLogLog for unique-user counting across shards

Probabilistic summaries are often mergeable, which allows each shard to maintain local state before a coordinator combines the results.

## Composite Designs in Real Systems

Production systems combine multiple structures because no single structure supports every operation efficiently.

### LSM Storage Engine

```text
WAL + skip-list memtable + SSTables + sparse indexes + Bloom filters
```

The WAL provides durability, the memtable serves recent data, SSTables store immutable sorted data, sparse indexes locate blocks, and Bloom filters avoid unnecessary file reads.

### Search Engine

```text
Trie + inverted index + compressed bitmaps + top-K heap
```

The trie locates terms, the inverted index retrieves documents, bitmaps apply filters, and the heap retains the highest-ranked results.

### Distributed Cache

```text
Hash table + eviction structure + frequency sketch + consistent hashing
```

The hash table performs lookup, the eviction structure controls memory, the sketch estimates popularity, and consistent hashing routes keys among cache nodes.

### Task Scheduler

```text
FIFO queue + priority heap + timing wheel + deduplication hash table
```

The queue buffers ready work, the heap orders priorities, the timing wheel manages delayed tasks, and the hash table prevents duplicate execution.

### Kafka-Style Broker

```text
Append-only segment log + sparse offset index + time index
```

The log stores events sequentially, while sparse indexes locate the segment position near a requested offset or timestamp.

### Large Sorted Set

```text
Hash table + skip list
```

The hash table provides direct member lookup, while the skip list supports rank and score-range queries.

### Replica Repair

```text
Partition map + per-range Merkle trees + version metadata
```

The partition map identifies ownership, Merkle trees locate divergent ranges, and version metadata determines which values need reconciliation.

## Choosing the Right Structure

Start with the dominant query instead of the technology name.

| Requirement                                  | Strong starting point                             |
|----------------------------------------------|---------------------------------------------------|
| Exact lookup by key                          | Hash table                                        |
| Ordered lookup and range scan                | B+ tree, ordered map, or skip list                |
| High sustained write rate                    | Append-only log or LSM tree                       |
| Prefix matching                              | Trie or radix tree                                |
| Next highest-priority or earliest item       | Heap or timing wheel                              |
| Full-text retrieval                          | Inverted index                                    |
| Fast intersection of large integer sets      | Compressed bitmap                                 |
| Partition assignment with little remapping   | Consistent hash ring                              |
| Efficient replica comparison                 | Merkle tree                                       |
| Dependency-constrained processing            | DAG                                               |
| Geographic candidate search                  | Quadtree, R-tree, S2, H3, or geohash              |
| Approximate membership, frequency, or count  | Bloom filter, Count-Min Sketch, or HyperLogLog    |

Then evaluate the operational costs:

* Does the structure fit in memory, and is its memory overhead predictable?
* Does it turn access into sequential I/O or random I/O?
* How much write, read, and space amplification does it create?
* Can it be partitioned without expensive cross-shard queries?
* Can replicas merge or compare state efficiently?
* What happens during resizing, rebalancing, compaction, and recovery?
* Is an approximate answer acceptable, and is its error one-sided or bounded?

## Interview Mental Model

> Choose the data structure from the access pattern, then explain how it will be bounded, partitioned, replicated, rebalanced, and recovered at scale.
