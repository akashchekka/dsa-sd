# Databases — FAANG Interview Guide

## Table of Contents
- [Storage Engines & Internals](#storage-engines--internals)
- [Indexing](#indexing)
- [B-Trees & LSM Trees](#b-trees--lsm-trees)
- [Query Processing & Optimization](#query-processing--optimization)
- [Transactions & Concurrency Control](#transactions--concurrency-control)
- [Log-Structured Storage & WAL](#log-structured-storage--wal)
- [Replication](#replication)
- [Partitioning / Sharding](#partitioning--sharding)
- [Consistency Models](#consistency-models)
- [CAP Theorem & PACELC](#cap-theorem--pacelc)
- [SQL vs NoSQL](#sql-vs-nosql)
- [Key-Value Stores](#key-value-stores)
- [Document Stores](#document-stores)
- [Column-Family Stores](#column-family-stores)
- [Graph Databases](#graph-databases)
- [Caching Layer](#caching-layer)
- [Data Modeling & Schema Design](#data-modeling--schema-design)
- [Distributed DB Concepts](#distributed-db-concepts)
- [Common Data Structures Used in DBs](#common-data-structures-used-in-dbs)
- [Common Interview Questions](#common-interview-questions)

---

## Storage Engines & Internals

A storage engine is the component of a database that is responsible for how data is stored, retrieved, and managed on disk (and in memory). Understanding storage engines is crucial because they dictate the performance characteristics of every read and write your application makes.

### How Data Lives on Disk

Databases don't read or write individual bytes — they operate in **pages** (also called blocks), typically 4–16 KB in size. Every time the DB needs a single row, it reads an entire page from disk into memory. This is because disk I/O is orders of magnitude slower than memory access, and reading a whole page amortizes the seek cost.

A **heap file** is the simplest way to organize pages — it's just an unordered collection of pages where each page holds rows/tuples. When you insert a row, the DB finds any page with free space and writes it there.

Inside each page, most databases use a **slotted page layout**:

```
┌──────────────────────────────────────────┐
│ Page Header (free space pointer, flags)  │
├──────────────────────────────────────────┤
│ Slot Array → [offset1, offset2, ...]     │
│                                          │
│           ← free space →                 │
│                                          │
│ ... [Record 2] [Record 1]               │
└──────────────────────────────────────────┘
```

The slot array grows from the top down, records grow from the bottom up. This allows variable-length records while keeping a fixed pointer (slot number) that other pages can reference. If a record moves within a page, only its slot entry needs updating — external references (from indexes) remain valid.

### Two Dominant Storage Paradigms

At the highest level, there are two fundamentally different approaches to how a storage engine organizes data on disk. Almost every production database you'll encounter uses one of these:

| Aspect | B-Tree (Update-in-place) | LSM-Tree (Append-only) |
|---|---|---|
| Write path | Random write to a specific page | Sequential append to memtable → flush to SSTable |
| Read path | O(log N) tree traversal | Check memtable → bloom filters → SSTables |
| Write amplification | Higher (random I/O, page rewrites) | Lower (sequential I/O, but compaction adds writes) |
| Compaction | Page splits and merges | Background merge-sort of SSTables |
| Use cases | OLTP (PostgreSQL, MySQL/InnoDB) | Write-heavy (RocksDB, Cassandra, LevelDB) |

**Key insight for interviews**: B-Trees are optimized for reads (stable, predictable read latency), while LSM-Trees are optimized for writes (all writes become sequential I/O). The trade-off is that LSM reads may need to check multiple levels of SSTables, and background compaction can cause latency spikes.

### Row-Store vs Column-Store

How you *arrange* data within pages matters just as much as which tree structure you use:

**Row-store** (PostgreSQL, MySQL): All columns of a single row are stored together on the same page. This is ideal for **OLTP** workloads where you frequently read or write entire rows (e.g., `SELECT * FROM users WHERE id = 42`).

```
Page: [row1: id=1, name="Alice", age=30] [row2: id=2, name="Bob", age=25] ...
```

**Column-store** (ClickHouse, Redshift, Parquet): Each column is stored in a separate file/segment. This is ideal for **OLAP** workloads where you scan millions of rows but only need a few columns (e.g., `SELECT AVG(age) FROM users`).

```
Column file "age": [30, 25, 35, 28, 22, 31, ...]   ← sequential read, fits in cache
Column file "name": ["Alice", "Bob", "Charlie", ...]
```

Column stores also enable much better **compression** because values in the same column tend to be similar. Common techniques include run-length encoding (for repeated values), dictionary encoding (for low-cardinality columns), and delta encoding (for sorted/monotonic data like timestamps).

Some systems are **hybrid** — for example, SQL Server lets you add columnstore indexes alongside a row-store table, giving you OLTP and OLAP capabilities on the same data.

---

## Indexing

Without indexes, answering a query like `SELECT * FROM orders WHERE customer_id = 42` requires scanning every single page in the table — a **full table scan**. Indexes are auxiliary data structures that let the database jump directly to the rows that match your query.

### B+ Tree Index (most common)

The B+ tree is the workhorse index of relational databases. It's a balanced tree where:

```
              [30 | 70]                    ← Internal node (keys only, for routing)
             /    |     \
      [10|20]  [40|50|60]  [80|90]         ← Leaf nodes (keys + row pointers)
        ↔          ↔          ↔            ← Doubly-linked list for range scans
```

**Why B+ trees are so effective:**

1. **High fan-out**: Each node is sized to match a disk page (e.g., 8 KB) and can hold hundreds or thousands of keys. This means a tree with 4 billion entries is only ~4 levels deep.
2. **All data is in leaves**: Internal nodes hold only keys for routing, so they're compact and often cached in memory. The leaves hold keys plus pointers to the actual rows (either a heap file tuple ID or the full row in a clustered index).
3. **Leaf-level linked list**: Leaves are linked together, so once you find the start of a range, you can scan sequentially — no need to traverse back up the tree.
4. **Balanced by construction**: All leaves are at the same depth, guaranteeing O(log N) lookups.

**Example**: Finding `customer_id = 42` in a table with 100 million rows, using a B+ tree with fan-out 500:
- Level 0 (root): 1 page → covers all 100M rows
- Level 1: ~500 pages
- Level 2: ~250,000 pages  
- Level 3: ~125M leaf entries

That's **3 page reads** to find one row out of 100 million. Without the index, you'd need to scan potentially millions of pages.

```sql
-- PostgreSQL: Create a B+ tree index
CREATE INDEX idx_orders_customer ON orders (customer_id);

-- Composite index (leftmost prefix rule applies)
CREATE INDEX idx_orders_cust_date ON orders (customer_id, order_date);
-- ✅ Works for: WHERE customer_id = 42
-- ✅ Works for: WHERE customer_id = 42 AND order_date > '2024-01-01'
-- ❌ Does NOT work for: WHERE order_date > '2024-01-01' (alone)
```

### B-Tree vs B+ Tree

In interviews, people sometimes say **B-Tree** and **B+ Tree** interchangeably, but they are not exactly the same.

Also, **B-Tree** is the correct term. If someone says **B- Tree**, they usually mean B-Tree, not "B minus tree".

| Aspect | B-Tree | B+ Tree |
|---|---|---|
| Data placement | Keys and row pointers/data can be stored in internal nodes and leaf nodes. | Internal nodes store only routing keys; actual row pointers/data live in leaf nodes. |
| Internal nodes | Can contain searchable data. | Used only to guide the search path. |
| Leaf nodes | May or may not be linked. | Usually linked together for fast ordered scans. |
| Equality lookup | Fast O(log N). | Fast O(log N). |
| Range queries | Good, but scanning may require more tree traversal. | Excellent because linked leaves can be scanned sequentially. |
| Fan-out | Lower if internal nodes store more payload. | Higher because internal nodes are compact. |
| Tree height | Balanced and short. | Often shorter/wider for the same data volume. |
| Common database use | Conceptually important and used in some systems. | Very common for relational database indexes. |

**Why databases often prefer B+ trees:**

- Internal nodes are small, so more routing keys fit in each page.
- The tree has high fan-out, so fewer page reads are needed.
- All records/pointers are at the leaf level, giving predictable lookup paths.
- Linked leaves make range scans efficient.

Example range query:

```sql
SELECT *
FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31';
```

With a B+ tree on `order_date`, the database navigates to the first matching leaf page and then walks the linked leaf pages until the end of the range.

**Interview summary:**

> A B-Tree is a balanced multi-way search tree. A B+ Tree is a database-friendly variant where internal nodes only route searches and all row pointers/data are stored in linked leaf nodes. B+ Trees are especially strong for range queries, which is why they are widely used for relational database indexes.

### Hash Index

A hash index uses a hash function to map keys directly to storage locations — giving **O(1) average-case lookups** but **no support for range queries** or ordering. It's like a dictionary/hashmap on disk.

```
hash(key) → bucket → [key, pointer to row]
```

Hash indexes are primarily used for:
- In-memory indexes (e.g., hash joins during query execution)
- Specialized equality-only lookups (PostgreSQL supports hash indexes but B-tree is almost always preferred)

### Other Index Types

Different access patterns require different index structures. Here's what to know:

| Type | How It Works | Use Case |
|---|---|---|
| **Bitmap Index** | One bit per row, per distinct value. Combine with AND/OR/NOT bitwise ops. | Low-cardinality columns (status, gender). Fast multi-column filtering in OLAP. |
| **GiST / R-Tree** | Hierarchical bounding boxes for spatial data. | "Find all restaurants within 5km" — geometric/geographic queries. |
| **GIN (Generalized Inverted)** | Maps each element to a list of rows containing it. | Full-text search (`to_tsvector`), JSONB containment (`@>`), array queries. |
| **Bloom Filter** | Probabilistic bitmap — can say "definitely not here" or "maybe here." | LSM-Tree reads: skip SSTables that definitely don't contain the key. |
| **Skip List** | Layered linked list with O(log N) search. Probabilistic balancing. | In-memory sorted structures: Redis sorted sets, memtables in some LSM implementations. |

```sql
-- PostgreSQL GIN index for full-text search
CREATE INDEX idx_articles_fts ON articles USING gin(to_tsvector('english', body));

-- Query using the GIN index
SELECT title FROM articles
WHERE to_tsvector('english', body) @@ to_tsquery('database & optimization');
```

### Clustered vs Non-Clustered Index

This distinction is about whether the index controls the **physical order** of the table data:

**Clustered index**: The table rows are physically sorted and stored according to the index key. There can be only **one** clustered index per table (you can only sort data one way). In MySQL/InnoDB, the primary key IS the clustered index — leaf pages of the B+ tree contain the actual row data.

```
Clustered B+ Tree (InnoDB):
    Leaf page: [pk=1, name="Alice", age=30] [pk=2, name="Bob", age=25] ...
    → The leaf IS the table. No separate heap file.
```

**Non-clustered index**: A separate B+ tree where leaf nodes contain the indexed column value plus a pointer back to the actual row. The row could be in a heap file (PostgreSQL) or in the clustered index (MySQL).

```
Non-clustered index on "name":
    Leaf: [name="Alice" → pk=1] [name="Bob" → pk=2]
    → Must do a second lookup (heap fetch or primary key lookup) to get full row.
```

**Covering index**: A non-clustered index that includes all columns the query needs, so the DB can answer the query from the index alone without fetching the actual row:

```sql
-- Covering index: includes email for lookups, name as included column
CREATE INDEX idx_users_covering ON users (email) INCLUDE (name);

-- This query uses index-only scan (no heap fetch needed)
SELECT name FROM users WHERE email = 'alice@example.com';
```

---

## B-Trees & LSM Trees

These two data structures underpin nearly every database in production. Understanding their internals — and the trade-offs between them — is essential for interviews.

### B-Tree Internals

A B-tree stores data in **fixed-size pages** (typically matching the OS page size, e.g., 4 KB or 16 KB). Each page is either an internal node or a leaf node. Here's what happens during key operations:

**Writes (Update-in-Place)**:
1. Traverse from root to the target leaf page.
2. If the key exists, update the value in place.
3. If the key is new and the leaf has room, insert into the sorted position.
4. If the leaf is **full**, perform a **page split**: create a new page, distribute keys evenly, and push the median key up to the parent.

```
Before split (leaf full):       After split:
[10 | 20 | 30 | 40]           [10 | 20]  [30 | 40]
                                    ↑
                               Parent gets key 30
```

**Reads**: Walk the tree from root → internal nodes → leaf. At each level, binary-search within the page to find the right child pointer. With a fan-out of 500, a tree with 500^4 = 62.5 billion entries is only 4 levels deep.

**Deletions**: Remove the key from the leaf. If the leaf becomes less than half full, it may **merge** with a sibling or **redistribute** keys with a neighbor to maintain balance.

**Critical supporting structures**:

- **Write-Ahead Log (WAL)**: Before modifying any B-tree page, the change is first written to a sequential log file. If the database crashes mid-write (e.g., during a page split that modifies two pages), the WAL can replay the change to restore consistency.
- **Buffer pool / page cache**: An in-memory cache of frequently accessed pages. The DB reads from the buffer pool first and only goes to disk on a cache miss. Eviction is typically LRU or clock-based.

### LSM-Tree Internals

LSM trees take a radically different approach: instead of modifying data in place, they **append** every write to an in-memory buffer and periodically flush it to disk as a sorted, immutable file.

```
Client writes key=42, value="hello"
        │
        ▼
┌─────────────────────┐
│   Memtable           │  ← In-memory sorted structure (skip list or red-black tree)
│   (sorted by key)    │     All writes go here first. Also written to WAL for durability.
└────────┬────────────┘
         │ When memtable reaches size threshold (e.g., 64 MB), flush to disk
         ▼
┌─────────────────────┐
│   SSTable Level 0    │  ← Sorted String Table: immutable, sorted file on disk
│   (newly flushed)    │     May overlap with other L0 SSTables
└────────┬────────────┘
         │ Background compaction: merge-sort overlapping SSTables
         ▼
┌─────────────────────┐
│   SSTable Level 1    │  ← Each level is ~10× larger than the previous
│   (no key overlaps)  │     Keys are partitioned across SSTables at this level
└────────┬────────────┘
         ▼
    Level 2, 3, ... N
```

**Read path** (this is where LSM gets complex):

1. Check the memtable (in-memory, fast).
2. Check each SSTable level, starting from newest. For each SSTable:
   a. Check the **Bloom filter** — if it says "no," skip this file entirely.
   b. Check the **sparse index** — find the approximate position in the file.
   c. Read the data block and search for the key.
3. Return the first (newest) match found.

**Compaction strategies** — this is how the DB reclaims space and keeps reads efficient:

| Strategy | How It Works | Trade-offs |
|---|---|---|
| **Size-tiered (STCS)** | Merge SSTables of similar size together when there are enough of them. | Simple, good write throughput. Higher space amplification (may temporarily use 2× the data size during compaction). |
| **Leveled (LCS)** | Each level has a strict size limit (~10× the previous). Compaction merges one SSTable from level N with overlapping SSTables in level N+1. | Better read performance (fewer files to check), less space amplification. But more write amplification. |

**Tombstones and deletes**: You can't remove a key from an immutable file. Instead, the DB writes a special "tombstone" marker. During compaction, when the tombstone meets the original entry, both are discarded.

### The Three Amplification Factors

Every storage engine makes trade-offs along these three axes:

```
                    B-Tree          LSM-Tree
Write Amplification  Higher           Lower
 (total disk writes   (random I/O,     (sequential I/O,
  per app write)       page rewrites)   but compaction adds writes)

Read Amplification   Lower            Higher
 (disk reads          (single tree      (check memtable + multiple
  per app read)        traversal)        SSTable levels)

Space Amplification  Lower            Higher
 (disk space /        (no redundant    (duplicate keys across levels
  actual data size)    copies)          until compacted)
```

**Interview rule of thumb**: If the workload is write-heavy (logging, time-series, IoT), lean toward LSM. If it's read-heavy with complex queries (OLTP, user-facing), lean toward B-tree.

---

## Query Processing & Optimization

When you type a SQL query, it goes through a surprisingly sophisticated pipeline before any data is actually read. Understanding this pipeline helps you debug slow queries and reason about database performance.

### Query Lifecycle

```
┌────────┐    ┌────────┐    ┌────────┐    ┌──────────────┐    ┌───────────┐    ┌──────────┐
│  SQL   │ →  │ Parser │ →  │  AST   │ →  │    Binder    │ →  │  Logical  │ →  │ Physical │ → Results
│ String │    │        │    │        │    │(resolve names│    │   Plan    │    │   Plan   │
└────────┘    └────────┘    └────────┘    │ check types) │    │(Optimizer)│    │(Executor)│
                                          └──────────────┘    └───────────┘    └──────────┘
```

1. **Parser**: Converts the SQL string into an Abstract Syntax Tree (AST). Checks syntax.
2. **Binder/Analyzer**: Resolves table and column names, checks types, verifies permissions.
3. **Logical Plan**: Represents the query as a tree of relational algebra operators (Scan, Filter, Join, Project, Aggregate). This is *what* needs to happen, not *how*.
4. **Optimizer**: Transforms the logical plan into an efficient physical plan. This is the "brain" of the query engine.
5. **Physical Plan / Executor**: Chooses concrete algorithms (which join algorithm, which scan method) and executes them.

### Join Algorithms — The Big Three

Joins are the most expensive operation in SQL, and interviewers love asking about join algorithms:

**Nested Loop Join** — the simplest approach:

```python
# Pseudocode: O(N × M) — bad for large tables, great with an index on inner
for row_outer in outer_table:          # N rows
    for row_inner in inner_table:      # M rows
        if row_outer.key == row_inner.key:
            emit(row_outer, row_inner)

# With index on inner: O(N × log M) — much better
for row_outer in outer_table:
    row_inner = index_lookup(inner_table, row_outer.key)  # O(log M)
    if row_inner:
        emit(row_outer, row_inner)
```

**Hash Join** — the go-to for equality joins:

```python
# Phase 1: BUILD — hash the smaller table into a hash table
hash_table = {}
for row in smaller_table:              # O(N)
    hash_table[row.key] = row

# Phase 2: PROBE — scan the larger table and look up matches
for row in larger_table:               # O(M)
    if row.key in hash_table:          # O(1) average
        emit(row, hash_table[row.key])

# Total: O(N + M) time, O(N) memory for hash table
```

If the smaller table doesn't fit in memory, the optimizer uses **Grace Hash Join**: partition both tables by hash value, write partitions to disk, then join matching partitions one at a time.

**Sort-Merge Join** — great when inputs are already sorted:

```python
# Phase 1: SORT both inputs (skip if already sorted, e.g., from index scan)
sorted_left = sort(left_table)         # O(N log N)
sorted_right = sort(right_table)       # O(M log M)

# Phase 2: MERGE — like merging two sorted arrays
i, j = 0, 0
while i < len(sorted_left) and j < len(sorted_right):
    if sorted_left[i].key == sorted_right[j].key:
        emit(sorted_left[i], sorted_right[j])
        j += 1
    elif sorted_left[i].key < sorted_right[j].key:
        i += 1
    else:
        j += 1
```

| Algorithm | Time Complexity | Memory | Best When |
|---|---|---|---|
| **Nested Loop** | O(N × M) | O(1) | Small inner table, or index available on inner |
| **Hash Join** | O(N + M) | O(min(N,M)) | Equality joins, one table fits in memory |
| **Sort-Merge Join** | O(N log N + M log M) | O(N + M) | Both inputs already sorted, or result needs to be sorted |

### The Cost-Based Optimizer

The optimizer doesn't just pick the right join algorithm — it also decides:
- **Join order**: Which tables to join first. For N tables, there are N! possible orderings.
- **Access method**: Sequential scan vs. index scan vs. index-only scan.
- **Whether to materialize** intermediate results or pipeline them.

To make these decisions, the optimizer relies on **statistics** about the data:

```sql
-- PostgreSQL: See table-level stats
SELECT relname, reltuples, relpages FROM pg_class WHERE relname = 'orders';

-- Column-level stats: distinct values, null fraction, most common values
SELECT * FROM pg_stats WHERE tablename = 'orders' AND attname = 'status';
```

The optimizer estimates **cardinality** (how many rows each step will produce) at every node of the plan tree. If the estimates are wrong (stale statistics, correlated columns), the optimizer may choose a terrible plan.

```sql
-- See the optimizer's plan and compare estimates to reality
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 42 AND status = 'shipped';

-- Output (look for "rows=X" estimated vs "actual rows=Y"):
-- Seq Scan on orders  (cost=0.00..35811.00 rows=1 width=48) (actual rows=5000 ...)
--                                              ^^^                       ^^^^
--                                          estimated=1              actual=5000  ← BAD estimate!
```

### Key Optimizer Concepts

**Predicate pushdown**: Move filter conditions as close to the data source as possible. Instead of scanning the entire table and then filtering, apply the filter during the scan.

```sql
-- Before pushdown (conceptual):  Scan orders → Join with customers → Filter status='shipped'
-- After pushdown:                 Scan orders WHERE status='shipped' → Join with customers
```

**Projection pushdown**: Only read the columns you actually need. In a column store, this means reading fewer column files. In a row store, the impact is smaller but still relevant for I/O.

**Join reordering**: Place the smaller table as the build side in a hash join. The optimizer uses cardinality estimates to determine which table is smaller.

---

## Transactions & Concurrency Control

A transaction is a group of operations that should execute as a single, indivisible unit. Even if the database crashes or multiple users are writing at the same time, transactions ensure data remains correct.

### ACID Properties

These four properties define what "correct" means for a transaction:

| Property | What It Guarantees | How It's Implemented |
|---|---|---|
| **Atomicity** | Either ALL operations in the transaction succeed, or NONE do. If the DB crashes mid-transaction, partial changes are rolled back. | Write-ahead log (WAL) with undo records. On crash, replay the log and undo incomplete transactions. |
| **Consistency** | The database moves from one valid state to another. All constraints (foreign keys, unique, check) are satisfied after the transaction. | Enforced by the DB engine (constraints, triggers) and application logic. |
| **Isolation** | Concurrent transactions don't see each other's intermediate states. Each transaction behaves *as if* it were the only one running. | Locking protocols (2PL), multi-version concurrency control (MVCC), or serializable snapshot isolation (SSI). |
| **Durability** | Once a transaction is committed, its changes survive any subsequent crash (power failure, disk failure, etc.). | WAL is flushed to disk (fsync) before reporting commit success. Replication adds another layer of durability. |

### Isolation Levels

Not all applications need full isolation. Stronger isolation means more overhead (more locking, more aborts). SQL defines four levels:

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Lost Update | Performance |
|---|---|---|---|---|---|
| **Read Uncommitted** | ✅ possible | ✅ | ✅ | ✅ | Fastest |
| **Read Committed** | ❌ prevented | ✅ | ✅ | ✅ | Good — default in PostgreSQL, Oracle |
| **Repeatable Read** | ❌ | ❌ | ✅ (some DBs prevent) | ❌ | Moderate — default in MySQL/InnoDB |
| **Serializable** | ❌ | ❌ | ❌ | ❌ | Slowest |

What each anomaly means, with concrete examples:

**Dirty read**: Transaction A modifies a row but hasn't committed. Transaction B reads that modified row. If A rolls back, B has read data that never existed.

```sql
-- Transaction A                    -- Transaction B
BEGIN;
UPDATE accounts SET balance = 0
  WHERE id = 1;
                                    BEGIN;
                                    SELECT balance FROM accounts WHERE id = 1;
                                    -- Reads 0 (dirty!) even though A hasn't committed
ROLLBACK;                           -- A rolled back; the 0 was never real
```

**Non-repeatable read**: Transaction B reads a row, Transaction A modifies and commits it, Transaction B re-reads and gets a different value.

**Phantom read**: Transaction B runs a range query, Transaction A inserts a new row that matches the range, Transaction B re-runs the query and sees a new row that wasn't there before.

**Write skew**: The subtlest anomaly. Two transactions read overlapping data, make independent decisions, and write non-overlapping data, violating an application invariant. Only prevented at Serializable.

```sql
-- Example: Hospital requires at least 1 doctor on-call
-- Doctor Alice and Doctor Bob are both on-call

-- Transaction A (Alice)             -- Transaction B (Bob)
BEGIN;                               BEGIN;
SELECT count(*) FROM on_call;        SELECT count(*) FROM on_call;
-- count = 2, safe to leave          -- count = 2, safe to leave
DELETE FROM on_call                  DELETE FROM on_call
  WHERE doctor = 'Alice';             WHERE doctor = 'Bob';
COMMIT;                              COMMIT;
-- Result: ZERO doctors on-call! Invariant violated.
```

### Locking & MVCC

Databases use two main approaches to enforce isolation:

**Two-Phase Locking (2PL)** — the pessimistic approach:

Every transaction must acquire a lock before reading or writing any data. The protocol has two phases:

```
Growing Phase                    Shrinking Phase
──────────────── ─ ─ ─ ─ ─ ─ ─  ───────────────────
Acquire locks,                   Release locks,
never release any                never acquire new ones
                  Lock Point
                  (all locks held)
```

Lock types:
- **Shared (S) lock**: For reads. Multiple transactions can hold shared locks on the same resource.
- **Exclusive (X) lock**: For writes. Only one transaction can hold this; blocks all other locks.

2PL guarantees serializability but has two major problems:
1. **Deadlocks**: Transaction A holds lock on row 1, waits for lock on row 2. Transaction B holds lock on row 2, waits for lock on row 1. Neither can proceed. Solutions: deadlock detection (wait-for graph), timeouts, or prevention schemes (wound-wait, wait-die).
2. **Low concurrency**: Readers block writers, writers block readers.

**Multi-Version Concurrency Control (MVCC)** — the optimistic approach:

Instead of locking, the DB keeps **multiple versions** of each row. Each transaction sees a consistent **snapshot** of the database as of its start time.

```
Time    Row (id=1)
──────────────────────────────────────────────
t=100   version 1: {name="Alice", txn_id=100}     ← created by txn 100
t=200   version 2: {name="Alicia", txn_id=200}    ← updated by txn 200
t=300   version 3: {name="Alisha", txn_id=300}    ← updated by txn 300

Transaction started at t=150 sees → version 1 (txn 100 committed before t=150)
Transaction started at t=250 sees → version 2 (txn 200 committed before t=250)
```

Key benefit: **readers never block writers, and writers never block readers**. Each just sees its own consistent snapshot. Old versions are cleaned up by a garbage collector (VACUUM in PostgreSQL) once no active transaction can see them.

MVCC is used by PostgreSQL, MySQL/InnoDB, Oracle, and CockroachDB.

**Serializable Snapshot Isolation (SSI)** — best of both worlds:

SSI starts with MVCC snapshot isolation and adds **conflict detection** at commit time. It tracks which rows each transaction read and checks for dependency cycles. If a cycle is detected, one transaction is aborted and retried. This gives you serializable isolation without the blocking overhead of 2PL. Used by PostgreSQL (SERIALIZABLE level) and CockroachDB.

---

## Log-Structured Storage & WAL

The Write-Ahead Log is arguably the single most important component for database reliability. The principle is simple: **before modifying any data page, first write the intended change to a sequential log file and fsync it to disk.**

### Write-Ahead Log (WAL)

Here's the lifecycle of a transaction from the WAL's perspective:

```
1. Transaction begins
   → WAL: <BEGIN T1>

2. Row is modified
   → WAL: <T1, table=orders, row=42, old={status:"pending"}, new={status:"shipped"}>
   → Dirty page in buffer pool is updated (but NOT flushed to disk yet)

3. More modifications...
   → WAL: <T1, table=inventory, row=7, old={qty:100}, new={qty:99}>

4. Transaction commits
   → WAL: <COMMIT T1>
   → WAL file is fsync'd to disk          ← THIS is what makes it durable
   → Return "success" to the client

5. Eventually (maybe seconds or minutes later)
   → Background writer flushes dirty data pages to disk
   → This is called "checkpointing"
```

Why this works: if the database crashes at any point before step 4, the transaction was never committed — on restart, the undo log rolls back any partial changes. If it crashes after step 4 but before step 5, the data pages on disk are stale but the WAL has the complete record — the redo log replays the changes.

**Log Sequence Number (LSN)**: Every WAL record gets a monotonically increasing LSN. Each data page also stores the LSN of the last WAL record that modified it. During recovery, if a page's LSN is less than a WAL record's LSN, that change needs to be replayed.

**Checkpointing**: Periodically, the DB flushes all dirty pages to disk and records the current LSN as a checkpoint. This limits how far back recovery needs to scan the WAL. Without checkpointing, recovery could take hours after a long-running database accumulates a massive WAL.

### ARIES Recovery Algorithm

ARIES (Algorithms for Recovery and Isolation Exploiting Semantics) is the gold standard recovery algorithm used by most relational databases. It has three phases:

```
Crash occurs at time T
Last checkpoint was at time C

WAL: ─────[Checkpoint C]───────────[Crash T]
              │                         │
              ▼                         ▼
Phase 1: ANALYSIS (scan C → T)
    - Build a "dirty page table" (which pages were modified)
    - Build an "active transaction table" (which txns were in-flight)

Phase 2: REDO (scan from earliest dirty page's LSN → T)
    - Replay ALL logged changes (committed AND uncommitted)
    - Bring the database to the exact state at crash time

Phase 3: UNDO (scan backwards)
    - Roll back all transactions that were active at crash time
    - Write "compensation log records" (CLRs) so undo is itself recoverable
```

**Key insight**: ARIES redoes everything first (including uncommitted transactions), then undoes just the uncommitted ones. This approach is simpler and more correct than trying to selectively redo only committed changes.

---

## Replication

Replication means keeping copies of the same data on multiple machines. There are three motivations:

1. **High availability**: If one machine dies, another has the data and can keep serving requests.
2. **Read scalability**: Spread read traffic across multiple replicas.
3. **Latency**: Place replicas geographically close to users.

### Replication Topologies

**Single-leader (master-slave)**: One node accepts writes (the leader), then replicates changes to followers. The simplest and most common setup.

```
Clients ──write──→ [Leader]
                     │  │
              replicate  replicate
                     │  │
                     ▼  ▼
                [Follower 1]  [Follower 2]
                     ↑            ↑
Clients ──read──────┘────────────┘
```

**Synchronous vs. asynchronous replication**:
- **Synchronous**: Leader waits for follower(s) to confirm before acknowledging the write. Guarantees no data loss but adds latency.
- **Asynchronous**: Leader acknowledges immediately after writing locally. Faster, but if the leader crashes, recently committed writes may be lost.
- **Semi-synchronous**: Wait for at least one follower (common compromise).

**Multi-leader**: Multiple nodes accept writes. Each leader replicates to all others. Used for multi-datacenter deployments (one leader per datacenter). The big challenge is **conflict resolution** — what happens when two leaders modify the same row simultaneously?

**Leaderless**: Any node can accept reads and writes. The client sends writes to multiple replicas and reads from multiple replicas. Popularized by Amazon's Dynamo paper. Used by Cassandra and Riak.

### Replication Mechanisms

| Method | How | Pros | Cons |
|---|---|---|---|
| **Statement-based** | Ship the SQL statements (`UPDATE orders SET...`) | Simple | Non-deterministic functions (`NOW()`, `RAND()`) produce different results on replicas |
| **WAL shipping** | Ship the raw WAL bytes to followers | Exact byte-level copy | Tightly coupled to storage engine version — can't replicate between different versions |
| **Logical (row-based)** | Ship the row-level changes (`INSERT row {id=1, ...}`) | Engine-independent, can replicate across versions | Slightly more overhead to decode |

### Quorum Reads/Writes

In leaderless replication, consistency is achieved through quorums:

```
N = total replicas (e.g., 3)
W = write quorum (e.g., 2) — write must succeed on W replicas
R = read quorum (e.g., 2)  — read from R replicas, take newest

Rule: W + R > N  →  read and write quorums overlap → guaranteed to read latest write

Example with N=3, W=2, R=2:
    Write goes to nodes A, B, C → succeeds on A, B (W=2 met)
    Read from nodes B, C → B has latest, C has stale
    → Client takes newest value from B ✓
```

**Sloppy quorum**: When the designated replicas are unavailable, write to any W available nodes and use **hinted handoff** to deliver the data to the correct nodes later. Increases availability at the cost of consistency.

### Conflict Resolution

When two nodes accept conflicting writes (multi-leader or leaderless), you need a strategy:

- **Last-Write-Wins (LWW)**: Use timestamps; highest timestamp wins. Simple but can silently lose data.
- **Custom merge function**: Application-specific logic (e.g., union of sets, take the longer string).
- **CRDTs**: Data structures that mathematically guarantee convergence without coordination. Examples: G-Counter (grow-only counter), OR-Set (observed-remove set).

---

## Partitioning / Sharding

When a single node can't hold all your data or handle all your traffic, you split the data across multiple nodes. Each node is responsible for a **partition** (also called a shard).

### Partitioning Strategies

**Range-based partitioning**: Assign key ranges to partitions.

```
Partition 1: keys A–M
Partition 2: keys N–Z

✅ Great for range queries: "SELECT * WHERE name BETWEEN 'Alice' AND 'Charlie'"
   → only hits Partition 1
❌ Risk of hotspots: if most names start with 'S', Partition 2 is overloaded
```

**Hash-based partitioning**: Hash the key and assign to a partition based on the hash.

```
partition = hash(key) % num_partitions

✅ Even distribution (assuming good hash function)
❌ Range queries are expensive — must scatter to ALL partitions
```

**Consistent hashing**: Arrange partitions on a hash ring. Each key maps to the next clockwise partition. Adding/removing a node only redistributes keys near that node.

```
         Node A
        /      \
   Node D      Node B    ← Hash ring
        \      /
         Node C

Key "user:42" → hash → lands between B and C → assigned to C
Add Node E between B and C → only some of C's keys move to E
```

| Strategy | Pros | Cons |
|---|---|---|
| **Range-based** | Efficient range queries | Hotspots on skewed data |
| **Hash-based** | Even distribution | No efficient range queries |
| **Consistent hashing** | Minimal data movement on topology changes | Implementation complexity, need virtual nodes for balance |
| **Compound (Cassandra-style)** | Hash first part (partition placement), sort by second part (within-partition order) | Must design schema around query patterns |

```sql
-- Cassandra compound key example
CREATE TABLE messages (
    chat_id UUID,          -- partition key (hashed → determines node)
    sent_at TIMESTAMP,     -- clustering key (sorted within partition)
    sender TEXT,
    body TEXT,
    PRIMARY KEY (chat_id, sent_at)  -- compound: (partition_key, clustering_key)
);

-- Efficient: reads all messages for one chat in time order
SELECT * FROM messages WHERE chat_id = ? ORDER BY sent_at;

-- Inefficient: requires scatter-gather across ALL partitions
SELECT * FROM messages WHERE sender = 'Alice';
```

### Secondary Indexes in Partitioned DBs

Secondary indexes are tricky in a partitioned database because the index key may not align with the partition key:

**Local index (document-partitioned)**: Each partition maintains its own index covering only its local data.
```
Partition 1: data A–M, local index on "color"
Partition 2: data N–Z, local index on "color"

Query: WHERE color = 'red' → must check BOTH partitions (scatter-gather)
```

**Global index (term-partitioned)**: The index itself is partitioned (e.g., colors A–M on one node, N–Z on another).
```
Index partition 1: colors A–M → pointers to data across all partitions
Index partition 2: colors N–Z → pointers to data across all partitions

Query: WHERE color = 'red' → hits only index partition 2
Write: must update the global index partition that owns the indexed value (cross-partition)
```

### Rebalancing Strategies

When you add or remove nodes, data must be redistributed:

- **Fixed number of partitions**: Create many more partitions than nodes (e.g., 1000 partitions for 10 nodes = 100 per node). When you add a node, move some partitions to it. Simple and predictable.
- **Dynamic splitting**: Start with one partition, split when it gets too large (like HBase and MongoDB). Adapts to data size automatically.
- **Never use `hash(key) % N`**: Adding one node changes the assignment of almost every key, causing massive data movement.

---

## Consistency Models

In a distributed system, "consistency" has a very specific (and different) meaning from ACID consistency. It's about what values a read can return when multiple copies of the data exist.

| Model | Guarantee | Example |
|---|---|---|
| **Linearizability** | Every read returns the value of the most recent completed write. The system behaves as if there's a single copy of the data. | After a write of x=5 completes, ALL subsequent reads see 5. |
| **Sequential consistency** | All operations appear in some total order that respects the order within each individual process. | Process A's operations appear in order, Process B's appear in order, but the interleaving may vary. |
| **Causal consistency** | If operation A *could have influenced* operation B, everyone sees A before B. Concurrent (causally unrelated) operations can be seen in any order. | If I post a message and you reply, everyone sees my message before your reply. |
| **Eventual consistency** | If no new updates are made, all replicas will *eventually* converge to the same value. No guarantees about when or what intermediate states are visible. | DNS propagation: update a record, and it takes minutes/hours for all DNS servers to see the change. |

**Linearizability** is the strongest guarantee and is needed for:
- Leader election (only one leader at a time)
- Unique constraints (no two users with the same username)
- Distributed locks with fencing tokens

It can be achieved via single-leader replication with synchronous reads from the leader, or consensus algorithms (Raft, Paxos).

---

## CAP Theorem & PACELC

### CAP Theorem

The CAP theorem states that during a **network partition** (when some nodes can't communicate), a distributed system must choose between:

- **Consistency (C)**: Every read gets the latest write or an error. (Linearizability.)
- **Availability (A)**: Every request gets a non-error response, but the data might be stale.

```
Network partition occurs: Node A can't talk to Node B

Option 1 — Choose Consistency (CP):
    Node A refuses to answer reads because it can't verify
    it has the latest data. Returns an error.
    → Correct but unavailable.

Option 2 — Choose Availability (AP):
    Node A answers with whatever data it has, even if it's stale.
    → Available but possibly inconsistent.
```

> **Important nuance for interviews**: CAP is about behavior **during** a partition. It is NOT saying "pick two out of three." In normal operation (no partition), you can have both consistency and availability. The question is only: what happens when the network breaks?

### PACELC — The More Nuanced Framework

CAP only describes the partition case. PACELC extends it:

- If **P**artition → choose **A**vailability or **C**onsistency
- **E**lse (normal operation) → choose **L**atency or **C**onsistency

| System | P → A or C? | E → L or C? | Explanation |
|---|---|---|---|
| **PostgreSQL** | PC | EC | Unavailable if leader is down. Consistent reads with higher latency (synchronous replication). |
| **Cassandra** | PA | EL | Stays available during partitions (eventual reads). Low latency in normal operation (tunable quorum). |
| **MongoDB** | PC | EC | Requires primary for writes. Consistent reads from primary. |
| **DynamoDB** | PA | EL | Stays available. Eventual consistency by default (strong consistency optional with higher latency). |
| **CockroachDB** | PC | EC | Raft-based consensus. Strong consistency always, higher latency. |

---

## SQL vs NoSQL

This isn't a religious debate — it's an engineering trade-off. The right choice depends on your data shape, query patterns, and scale requirements.

| Dimension | SQL (Relational) | NoSQL |
|---|---|---|
| **Data model** | Tables with rows and columns. Rigid schema (ALTER TABLE to change). | Varies: documents (JSON), key-value, wide-column, graph. Schema-on-read. |
| **Query language** | Declarative SQL. Powerful joins, aggregations, subqueries. | API-specific. Usually no joins (or limited). |
| **Transactions** | Full ACID across multiple rows/tables. | Varies: some support single-document ACID (MongoDB), some have no transactions. |
| **Scaling** | Primarily vertical (bigger machine). Horizontal with effort (Vitess, Citus, CockroachDB). | Designed for horizontal scale from the start. |
| **Best for** | Complex queries, relationships, strong consistency requirements. | High throughput, flexible/evolving schemas, massive horizontal scale. |

**When to choose SQL**: You have complex relationships, need joins, need multi-row transactions, your data has a well-defined schema, or you need strong consistency guarantees.

**When to choose NoSQL**: Your data is denormalized or self-contained (like a user profile document), you need to scale writes horizontally, your schema changes frequently, or you have extreme throughput requirements.

---

## Key-Value Stores

The simplest NoSQL model: every item is a key-value pair. Think of it as a giant distributed hash map.

### Examples: Redis, DynamoDB, Memcached, etcd

### Redis Internals — Data Structures Under the Hood

Redis is much more than a cache — it's an in-memory data structure server. Each Redis value type is backed by different internal structures depending on size:

| User-Facing Type | Small Size Implementation | Large Size Implementation | Typical Use Case |
|---|---|---|---|
| **String** | Embedded string or integer encoding | SDS (Simple Dynamic String) | Caching, counters (`INCR`), distributed locks |
| **List** | Listpack (compact, contiguous memory) | Quicklist (linked list of listpacks) | Message queues, activity feeds |
| **Hash** | Listpack | Hashtable (chaining) | Object storage (user profiles) |
| **Set** | Intset (sorted array of integers) | Hashtable | Tags, unique visitors, set operations |
| **Sorted Set** | Listpack | Skip list + Hashtable | Leaderboards, rate limiting, priority queues |
| **Stream** | Radix tree of listpacks | Same | Event sourcing, message streaming (like Kafka-lite) |

**Why Redis uses different encodings**: Small collections use compact, cache-friendly encodings (listpack) that minimize memory overhead. When the collection grows beyond a threshold (configurable), Redis transparently converts to a more scalable structure.

```python
# Redis skip list (Sorted Set internals) — conceptual structure
# Each element has a score (float) used for sorting

# Level 3:  HEAD ──────────────────────────── 90 ── NIL
# Level 2:  HEAD ──────── 30 ──────────────── 90 ── NIL
# Level 1:  HEAD ── 10 ── 30 ── 50 ── 70 ── 90 ── NIL

# Lookup "50": Start at top level, skip ahead, drop down when overshoot
# → O(log N) average, like a balanced BST but simpler to implement
```

### DynamoDB Internals

DynamoDB's architecture is based on the Amazon Dynamo paper, with significant enhancements:

```
Client request (GetItem, PutItem)
        │
        ▼
┌──────────────────┐
│  Request Router   │  ← Stateless. Knows the partition map.
│  (front-end)      │     Determines which partition owns the key.
└────────┬─────────┘
         │
         ▼
   hash(partition_key) → Partition ID → Storage Node
         │
         ▼
┌──────────────────┐
│  Storage Node     │  ← B-tree indexed by sort key within each partition
│  (3 replicas)     │     One leader + 2 followers per partition
│  Leader: ──────── │     All writes go to leader, replicated via Paxos
│  Follower 1: ──── │     Eventually consistent reads: any replica
│  Follower 2: ──── │     Strongly consistent reads: leader only
└──────────────────┘
```

Key design decisions:
- **Partition key**: Hashed to determine which partition stores the item. Choose a high-cardinality attribute to avoid hot partitions.
- **Sort key**: Within a partition, items are sorted by this key (B-tree). Enables efficient range queries within a partition.
- **Adaptive capacity**: If one partition gets more traffic (hot partition), DynamoDB automatically splits it and rebalances.

---

## Document Stores

Document stores organize data as **documents** — typically JSON (or binary JSON like BSON). Each document is self-contained and can have a different structure, making the schema flexible.

### Examples: MongoDB, CouchDB, Firestore

### MongoDB Internals

**Storage engine — WiredTiger** (default since MongoDB 3.2):
- Uses a **B-tree** variant for on-disk storage.
- Supports **snappy** and **zlib/zstd compression** at the page level.
- Implements **MVCC** with document-level concurrency control — multiple readers and one writer per document can operate concurrently.
- **Journaling**: WAL equivalent. Writes are logged to a journal before being applied. Enabled by default.

**Documents are BSON (Binary JSON)**:
```json
// BSON supports more types than JSON: dates, binary, ObjectId, Decimal128
{
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "name": "Alice",
    "orders": [
        {"product": "Widget", "qty": 3, "date": ISODate("2024-01-15")},
        {"product": "Gadget", "qty": 1, "date": ISODate("2024-02-20")}
    ]
}
```

**Replication — Replica Sets**:
```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Primary   │ ──→ │ Secondary 1   │     │ Secondary 2   │
│ (writes)  │ ──→ │ (async repl)  │     │ (async repl)  │
└──────────┘     └──────────────┘     └──────────────┘
     ↑                                        │
     └── If primary fails, election ───────────┘
         (Raft-like protocol, majority vote)
```

**Sharding architecture**:
```
Client ──→ [mongos Router] ──→ [Config Servers (metadata)]
                │
          ┌─────┴──────┐
          ▼            ▼
    [Shard 1]     [Shard 2]      ← Each shard is a replica set
    (Replica Set) (Replica Set)

Shard key → hash or range → determines which chunk → placed on which shard
Chunks auto-split when they exceed the configured size (default 128 MB)
Balancer process migrates chunks between shards to maintain even distribution
```

---

## Column-Family Stores

Column-family stores organize data into rows, but within each row, columns are grouped into **column families** and stored together. They're optimized for write-heavy workloads with high throughput.

### Examples: Cassandra, HBase, ScyllaDB

### Cassandra Internals

Cassandra's write and read paths illustrate LSM-tree principles in a distributed setting:

**Write path**:
```
Client write
    │
    ▼
[Coordinator Node]  ← Any node can be coordinator (peer-to-peer, no master)
    │
    ├──→ [Replica 1]  ──→  1. Append to Commit Log (WAL, sequential write)
    │                       2. Write to Memtable (in-memory, sorted)
    │                       3. Return ACK
    │
    ├──→ [Replica 2]  ──→  Same process
    │
    └──→ [Replica 3]  ──→  Same process

Coordinator waits for W replicas to ACK (W = consistency level, e.g., QUORUM = 2)
When Memtable is full → flush to SSTable on disk (immutable, sorted)
Background compaction merges SSTables
```

**Read path**:
```
Client read
    │
    ▼
[Coordinator] ──→ sends read requests to R replicas
    │
    Each replica checks:
    1. Memtable (newest data, in memory)
    2. Row cache (if enabled)
    3. Bloom filter for each SSTable (skip if key definitely not present)
    4. Partition index → find SSTable offset
    5. Compression offset map → locate exact data block
    6. Read and decompress the data block

Coordinator compares responses from R replicas, returns newest value
If replicas disagree → triggers read repair (background consistency fix)
```

**Gossip protocol**: Nodes exchange state information (alive/dead, load, schema version) by periodically picking a random node and sharing their knowledge. This means every node eventually knows about every other node — no central coordinator needed.

**Anti-entropy with Merkle trees**: To detect data inconsistencies between replicas, Cassandra builds a hash tree (Merkle tree) over each partition's data. Two replicas compare their Merkle tree roots — if they match, all data is consistent. If not, they traverse down the tree to find exactly which partitions differ, minimizing data transfer.

### Data Modeling in Cassandra

Cassandra data modeling is **query-driven**, not relationship-driven. You design your tables to answer specific queries efficiently, even if it means duplicating data:

```sql
-- Design for the query: "Get all messages in a chat room, ordered by time"
CREATE TABLE messages_by_chat (
    chat_id UUID,
    sent_at TIMESTAMP,
    user_id UUID,
    message TEXT,
    PRIMARY KEY ((chat_id), sent_at)
    --          ↑ partition key   ↑ clustering key (sorted within partition)
) WITH CLUSTERING ORDER BY (sent_at DESC);

-- Design for the query: "Get all messages by a specific user"
CREATE TABLE messages_by_user (
    user_id UUID,
    sent_at TIMESTAMP,
    chat_id UUID,
    message TEXT,
    PRIMARY KEY ((user_id), sent_at)
) WITH CLUSTERING ORDER BY (sent_at DESC);

-- Same data, two tables, each optimized for a different query
-- Application writes to BOTH tables (denormalization)
```

---

## Graph Databases

Graph databases store data as **nodes** (entities) and **edges** (relationships), making them ideal for highly connected data where the relationships are as important as the data itself.

### Examples: Neo4j, Amazon Neptune, JanusGraph

### Native vs Non-Native Graph Storage

**Native graph storage** (Neo4j): Nodes and relationships are stored as linked structures on disk. Each node record physically contains a pointer to its first relationship, and each relationship contains pointers to the next relationship of each connected node.

```
Node Record (fixed size, ~15 bytes):
┌─────────┬──────────────────┬───────────────────┐
│ in-use  │ first_relationship│ first_property    │
│ flag    │ pointer           │ pointer           │
└─────────┴──────────────────┴───────────────────┘

Relationship Record (fixed size, ~34 bytes):
┌─────────┬────────┬──────────┬──────────────┬──────────────┐
│ start   │ end    │ rel type │ next_rel of  │ next_rel of  │
│ node_id │ node_id│          │ start node   │ end node     │
└─────────┴────────┴──────────┴──────────────┴──────────────┘
```

This enables **index-free adjacency**: traversing from one node to its neighbors is a constant-time pointer chase, regardless of the total graph size. In a relational database, the same operation would require an index lookup on a join table.

**Non-native graph** (JanusGraph): Uses a relational or key-value store underneath (e.g., Cassandra, HBase). Relationship traversal requires index lookups, which is slower for deep traversals but can leverage the scalability of the underlying store.

### Query Language: Cypher

```cypher
-- Find friends-of-friends who like the same movies as me
MATCH (me:User {name: 'Alice'})-[:FRIENDS_WITH]->(friend)-[:FRIENDS_WITH]->(fof)
WHERE NOT (me)-[:FRIENDS_WITH]->(fof) AND me <> fof
WITH fof, collect(friend.name) AS mutual_friends

MATCH (me:User {name: 'Alice'})-[:LIKES]->(movie:Movie)<-[:LIKES]-(fof)
RETURN fof.name, mutual_friends, collect(movie.title) AS shared_movies
ORDER BY size(shared_movies) DESC
LIMIT 10
```

**When to choose a graph database**:
- Many-to-many relationships that are difficult to model with foreign keys
- Variable-depth traversals (friends of friends of friends...)
- Relationship-centric queries ("who is connected to whom and how?")
- Examples: social networks, fraud detection rings, recommendation engines, knowledge graphs

**When NOT to choose a graph database**:
- Simple CRUD with well-defined relationships (relational DB is simpler)
- Aggregations over large datasets (OLAP / column store is better)
- Simple key-value lookups (key-value store is faster)

---

## Caching Layer

Caching sits between your application and database, storing frequently accessed data in memory to reduce database load and latency. The challenge isn't implementing a cache — it's **keeping it consistent** with the database.

### Cache Patterns

**Cache-Aside (Lazy Loading)** — the most common pattern:

```python
def get_user(user_id):
    # 1. Check cache first
    user = cache.get(f"user:{user_id}")
    if user is not None:
        return user  # Cache hit!

    # 2. Cache miss — read from database
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)

    # 3. Populate cache for next time
    cache.set(f"user:{user_id}", user, ttl=3600)  # expire in 1 hour
    return user

def update_user(user_id, new_data):
    db.query("UPDATE users SET ... WHERE id = %s", user_id)
    cache.delete(f"user:{user_id}")  # Invalidate, don't update (safer)
```

| Pattern | How It Works | Pros | Cons |
|---|---|---|---|
| **Cache-aside** | App manages cache: check → miss → read DB → populate cache | Simple, app controls caching logic | Cache miss = slow (DB roundtrip). Potential stale data. |
| **Read-through** | Cache itself reads from DB on a miss (transparent to app) | Simpler app code | Cache library must know about DB |
| **Write-through** | Every write goes to cache AND DB synchronously | Cache always consistent | Higher write latency (two writes per operation) |
| **Write-behind (write-back)** | Write to cache, async write to DB later | Very fast writes | Risk of data loss if cache crashes before DB write |
| **Write-around** | Write to DB only, cache populated on reads | No cache churn from writes | Cache miss after every write |

### Eviction Policies

When the cache is full, which entries should be removed?

```python
# LRU (Least Recently Used) — most common
# Keep track of access order, evict the item that hasn't been accessed the longest
# Implementation: HashMap + Doubly Linked List → O(1) get, O(1) put

class LRUCache:
    def get(self, key):
        if key in self.map:
            self.move_to_front(key)    # Mark as recently used
            return self.map[key]
        return None

    def put(self, key, value):
        if len(self.map) >= self.capacity:
            self.evict_from_back()     # Remove least recently used
        self.map[key] = value
        self.add_to_front(key)
```

| Policy | When to Evict | Best For |
|---|---|---|
| **LRU** | Least recently accessed item | General purpose, recency-based access |
| **LFU** | Least frequently accessed item | Stable popularity patterns (video CDNs) |
| **TTL** | After a fixed time period | Data with known staleness tolerance |
| **Random** | Random item | When access patterns are unpredictable; avoids pathological LRU cases |

### Cache Invalidation — The Hard Part

There are only two hard things in computer science: cache invalidation and naming things. Here are the common problems and solutions:

**Thundering herd**: A popular cache entry expires, and hundreds of concurrent requests simultaneously hit the database to reload it.
```
Solution: Use a mutex/lock so only one request fetches from DB while others wait.
           Or use "probabilistic early expiration" — randomly refresh before TTL.
```

**Stale reads**: Cache has old data because the DB was updated but the cache wasn't invalidated.
```
Solution: Event-driven invalidation using Change Data Capture (CDC).
           When a row changes in the DB, a CDC event triggers cache invalidation.
```

**Cold start**: Cache is empty after deployment/restart, all requests hit the database.
```
Solution: Cache warming — pre-populate the cache with hot data before going live.
```

### Redis Persistence

Redis is in-memory but can persist data to disk using two mechanisms:

**RDB (Snapshotting)**: Periodically fork the process and write the entire dataset to a binary file. The fork uses copy-on-write, so the parent can continue serving requests.

**AOF (Append-Only File)**: Log every write command to a file. On restart, replay the file. More durable (can fsync every second or every command) but the file grows larger.

**Hybrid** (recommended): Load the RDB snapshot for fast startup, then replay only the AOF tail for recent writes.

---

## Data Modeling & Schema Design

### Normalization

Normalization eliminates data redundancy by organizing tables so that each fact is stored in exactly one place. The normal forms build on each other:

| Normal Form | Rule | Example Violation |
|---|---|---|
| **1NF** | Every column holds atomic (indivisible) values. No repeating groups. | A "phone_numbers" column containing "555-1234, 555-5678" |
| **2NF** | 1NF + every non-key column depends on the **entire** primary key (no partial dependencies). | In a table with PK (student_id, course_id), if "student_name" depends only on student_id. |
| **3NF** | 2NF + no non-key column depends on another non-key column (no transitive dependencies). | "city" → "zip_code" → "state". State depends on zip_code, not on the PK directly. |
| **BCNF** | Every determinant is a candidate key. Stronger than 3NF. | If a non-candidate-key column functionally determines another column. |

```sql
-- Unnormalized (violation of 1NF):
-- orders(id, customer, items: "Widget×3, Gadget×1")

-- Normalized to 3NF:
CREATE TABLE customers (id INT PRIMARY KEY, name TEXT, email TEXT);
CREATE TABLE orders (id INT PRIMARY KEY, customer_id INT REFERENCES customers(id), order_date DATE);
CREATE TABLE order_items (order_id INT REFERENCES orders(id), product_id INT, quantity INT);
```

### Denormalization

In practice, normalized schemas require expensive joins at read time. **Denormalization** intentionally adds redundancy to avoid joins:

```sql
-- Normalized: requires JOIN to get customer name with order
SELECT o.id, c.name, o.total
FROM orders o JOIN customers c ON o.customer_id = c.id;

-- Denormalized: customer_name is duplicated in orders table
SELECT id, customer_name, total FROM orders;
-- ✅ Faster read (no join)
-- ❌ Must update customer_name in orders table when customer changes
```

When to denormalize:
- Read-heavy workloads where join cost is unacceptable
- NoSQL databases that don't support joins
- Data warehouses / OLAP (Star/Snowflake schema)
- Microservices where data lives in different services

### Star Schema (OLAP / Data Warehousing)

```
               ┌────────────┐
               │ dim_product │
               │ - product_id│
               │ - name      │
               │ - category  │
               └──────┬─────┘
                      │
┌────────────┐  ┌─────┴──────┐  ┌────────────┐
│ dim_date   ├──┤ fact_sales  ├──┤ dim_store  │
│ - date_id  │  │ - date_id  │  │ - store_id │
│ - year     │  │ - product_id│  │ - city     │
│ - quarter  │  │ - store_id │  │ - state    │
│ - month    │  │ - qty      │  └────────────┘
└────────────┘  │ - revenue  │
                └─────┬──────┘
                      │
               ┌──────┴─────┐
               │ dim_customer│
               │ - cust_id  │
               │ - name     │
               │ - segment  │
               └────────────┘
```

- **Fact table**: Records events/measurements (one row per sale). Contains foreign keys to dimensions and numeric measures.
- **Dimension tables**: Descriptive, relatively small tables that provide context (who, what, when, where).
- **Snowflake schema**: Same concept, but dimension tables are further normalized (e.g., dim_product → dim_category).

---

## Distributed DB Concepts

### Consensus Algorithms

When multiple nodes must agree on a value (who is the leader? is this transaction committed?), they need a consensus algorithm.

**Raft** — designed for understandability:

```
State machine: each node is in one of three states:
    Follower → Candidate → Leader

Step 1: Leader Election
    - All nodes start as Followers with a randomized election timeout
    - If a Follower doesn't hear from the Leader before timeout, it becomes a Candidate
    - Candidate increments its term and requests votes from all nodes
    - If it receives majority votes → becomes Leader
    - If it hears from a Leader with equal/higher term → reverts to Follower

Step 2: Log Replication
    - Leader receives client writes and appends to its log
    - Leader sends AppendEntries RPCs to all Followers
    - When majority of Followers acknowledge → entry is committed
    - Leader notifies Followers that entry is committed
    - Followers apply the committed entry to their state machine

Step 3: Safety
    - A Candidate can only win if its log is at least as up-to-date as the majority
    - This ensures the Leader always has all committed entries
```

**Paxos** (theoretical foundation): More general but harder to understand. Involves Proposers, Acceptors, and Learners. Multi-Paxos adds a leader for efficiency.

### Distributed Transactions

**Two-Phase Commit (2PC)**:

```
                    Coordinator
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     Participant A  Participant B  Participant C

Phase 1 — PREPARE:
    Coordinator → all participants: "Can you commit?"
    Each participant: acquire locks, write to WAL, respond YES or NO

Phase 2 — COMMIT or ABORT:
    If ALL say YES → Coordinator logs COMMIT, tells everyone to commit
    If ANY says NO  → Coordinator logs ABORT, tells everyone to abort

Problem: If Coordinator crashes after sending PREPARE but before COMMIT/ABORT,
         participants are stuck holding locks, waiting forever.
         This is the "blocking" problem of 2PC.
```

**Saga Pattern** — for microservices (where 2PC is impractical):

```
Book Flight → Book Hotel → Charge Payment

If "Charge Payment" fails:
    → Compensating action: Cancel Hotel booking
    → Compensating action: Cancel Flight booking

Each step is a local transaction. If a step fails,
execute compensating transactions for all completed steps (in reverse order).
```

### Clock & Ordering in Distributed Systems

In a distributed system, there is no global clock. Different nodes have different wall-clock times, which can drift. How do you determine the order of events?

**Lamport timestamps**: A simple logical counter. Increment on each event; on receiving a message, set your counter to max(local, received) + 1. Gives a total order, but if A < B, you can't tell if A causally preceded B or if they were concurrent.

**Vector clocks**: Each node maintains a vector of counters (one per node). Enables detection of **concurrent** events: if neither vector dominates the other, the events are concurrent.

```
Node A: [A:2, B:0, C:0]    ← A has seen 2 of its own events
Node B: [A:1, B:3, C:1]    ← B has seen 1 of A's events, 3 of its own, 1 of C's

Compare: A's clock is NOT ≥ B's clock (A:2 > A:1, but B:0 < B:3)
         B's clock is NOT ≥ A's clock (B:3 > B:0, but A:1 < A:2)
         → These events are CONCURRENT
```

**TrueTime (Google Spanner)**: Uses GPS receivers and atomic clocks in every datacenter to provide a time API that returns an interval `[earliest, latest]` instead of a single timestamp. The true time is guaranteed to be within this interval. Spanner uses this to implement **external consistency** — if transaction A commits before transaction B starts, then A's timestamp is guaranteed to be less than B's.

---

## Common Data Structures Used in DBs

Understanding which data structures databases use — and why — is a powerful signal in interviews:

| Data Structure | Where It's Used | Why This Structure |
|---|---|---|
| **B+ Tree** | Primary/secondary indexes (PostgreSQL, MySQL, SQLite) | High fan-out → short tree → few disk reads. Leaf linked list → fast range scans. |
| **LSM Tree** | Write-optimized engines (RocksDB, LevelDB, Cassandra) | All writes sequential → high write throughput. Trade read speed for write speed. |
| **Skip List** | Redis sorted sets, memtables in LSM | O(log N) search with simpler implementation than balanced BSTs. Lock-free variants possible. |
| **Hash Table** | In-memory indexes, hash joins, Redis dictionaries | O(1) average lookup. No ordering but fastest for equality checks. |
| **Bloom Filter** | LSM reads (RocksDB, Cassandra, HBase) | Tiny memory footprint. "Definitely not here" in O(k) time, avoiding expensive disk reads. |
| **Cuckoo Filter** | Alternative to Bloom filter | Supports deletion (Bloom doesn't). Better space efficiency at low false positive rates. |
| **Red-Black Tree** | In-memory ordered maps, some memtable implementations | Self-balancing BST with O(log N) guaranteed operations. |
| **Radix Tree / Trie** | Redis streams, in-memory key indexes | Prefix-based operations. Memory-efficient for keys with common prefixes. |
| **Merkle Tree** | Anti-entropy repair (Cassandra, DynamoDB, IPFS) | Efficiently compare large datasets by comparing tree roots → O(log N) to find differences. |
| **R-Tree** | Spatial indexes (PostGIS, MongoDB geospatial) | Hierarchical bounding boxes for multi-dimensional range queries. |
| **Bitmap** | Bitmap indexes, column stores (Apache Druid, Roaring Bitmaps) | Extremely fast set operations (AND/OR/NOT) on low-cardinality data. |
| **Ring Buffer** | WAL segments, circular log buffers | Fixed-size, wrap-around buffer for sequential writes. No allocation overhead. |
| **Min-Heap** | Query scheduling, Top-K queries, merge step in external sort | O(1) access to minimum, O(log N) insert/remove. Used in K-way merge of SSTables. |
| **Count-Min Sketch** | Approximate frequency counting (stream processing) | Sublinear space. Answers "approximately how many times has X appeared?" |
| **HyperLogLog** | Approximate cardinality estimation (Redis `PFCOUNT`) | Count unique items using only ~12 KB regardless of cardinality. Error ~0.81%. |

---

## Common Interview Questions

### Design / Conceptual

**1. How does a B+ tree index speed up queries?**

The B+ tree has a very high fan-out (hundreds of keys per node), so even billions of rows produce a tree only 3-4 levels deep. Each level requires one disk read, and leaf nodes are linked for efficient range scans. So a point lookup costs O(log_B N) disk reads, and a range scan costs O(log_B N + K/B) where K is the number of results and B is the page size.

**2. B-Tree vs LSM-Tree — when do you choose which?**

B-Trees have stable, predictable read latency (single tree traversal) but writes are random I/O (update-in-place). LSM-Trees turn all writes into sequential I/O (append to memtable, flush to SSTable) but reads may need to check multiple SSTables. Choose B-Tree for read-heavy OLTP (PostgreSQL, MySQL). Choose LSM for write-heavy workloads (time-series, logging, Cassandra).

**3. Explain MVCC and why it matters.**

MVCC keeps multiple versions of each row, tagged with transaction IDs. Readers see a snapshot at their start time, so they never block writers and writers never block readers. This dramatically improves concurrency compared to locking. The trade-off is garbage collection (old versions must be cleaned up) and storage overhead.

**4. What happens when you run a SQL query end-to-end?**

Parse the SQL string → bind table/column names and check types → generate a logical plan (relational algebra) → optimize using statistics and cost estimation → generate a physical plan with concrete algorithms → execute the plan using the buffer pool and indexes → return results.

**5. Explain write-ahead logging and crash recovery.**

Before any data page is modified, the change is written to a sequential WAL and fsync'd. If the DB crashes, the WAL is replayed on startup: redo all committed changes, undo all uncommitted changes (ARIES algorithm). Checkpointing periodically flushes dirty pages so recovery doesn't have to replay the entire WAL.

**6. How does sharding work? How do you choose a shard key?**

Data is partitioned across nodes by a shard key. Good shard keys have: high cardinality (many distinct values for even distribution), are used in most queries (to avoid scatter-gather), and don't create hotspots (avoid monotonically increasing keys like auto-increment ID with range partitioning). Hash the key for even distribution, or use range partitioning if you need range queries on the shard key.

**7. Explain the CAP theorem with a real-world example.**

During a network partition (e.g., US-East can't talk to US-West), you choose: Consistency (refuse requests to the isolated datacenter until the partition heals) or Availability (keep serving both datacenters with potentially stale/divergent data). PostgreSQL chooses CP — the isolated followers can't become leader, so writes are unavailable. Cassandra chooses AP — both sides keep accepting writes, and conflicts are resolved later.

### Practical Scenarios

**8. A query that used to be fast is now slow. How do you debug it?**

```sql
-- Step 1: Run EXPLAIN ANALYZE to see the actual execution plan
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ;

-- Look for:
-- • Sequential scans on large tables (missing index?)
-- • Estimated rows vs actual rows mismatch (stale statistics? Run ANALYZE.)
-- • Nested loop joins on large tables (should be hash join?)
-- • High buffer reads (working set doesn't fit in memory?)

-- Step 2: Check for lock contention
SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';

-- Step 3: Check if statistics are stale
ANALYZE table_name;
-- Then re-run EXPLAIN ANALYZE
```

**9. Design a distributed cache.**

Use consistent hashing to distribute keys across cache nodes (minimal reshuffling when nodes are added/removed). Use the cache-aside pattern. Set TTLs for all entries. Handle thundering herd with a mutex on cache population. Add replication for availability. Monitor hit rate — below 90% suggests the cache is too small or access patterns are too random.

**10. How would you handle hot partitions?**

Add a random suffix to the partition key (e.g., `user_id + random(0,9)`) to spread writes across 10 partitions — but now reads must scatter-gather across all 10. Alternatively, use application-level caching for hot keys, or use a database with adaptive partitioning (DynamoDB automatically splits hot partitions).

---

## Quick Reference: When to Use What

| Scenario | DB Type | Examples |
|---|---|---|
| Complex queries + ACID + joins | Relational | PostgreSQL, MySQL, CockroachDB |
| High write throughput, time-series | LSM-based / Wide-column | Cassandra, ScyllaDB, TimescaleDB |
| Flexible schema, document-centric | Document | MongoDB, Firestore, CouchDB |
| Low-latency key-value lookups | Key-Value | Redis, DynamoDB, Memcached |
| Highly connected data, traversals | Graph | Neo4j, Neptune, JanusGraph |
| Analytics, columnar scans | Column store / OLAP | ClickHouse, BigQuery, Redshift |
| Full-text search | Inverted index | Elasticsearch, OpenSearch |
| Coordination / config / leader election | Consensus-based | etcd, Zookeeper |