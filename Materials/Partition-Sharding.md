**Partitioning** and **sharding** both mean splitting data into smaller pieces, but they are used slightly differently.

**Partitioning** is the general idea:

> Split a large dataset into smaller logical pieces.

**Sharding** is a specific kind of partitioning:

> Split data across multiple machines/nodes/databases.

So:

```text
All sharding is partitioning.
Not all partitioning is sharding.
```

## Partitioning

Partitioning can happen inside the same database/server.

Example: an `orders` table is huge, so we split it by month:

```text
orders_2026_01
orders_2026_02
orders_2026_03
```

The database may still be one logical database, but internally the table is divided into partitions.

### Why partition?

- Improve query performance
- Make large tables easier to manage
- Archive/drop old data faster
- Reduce index size per partition
- Improve maintenance operations

Example query:

```sql
SELECT *
FROM orders
WHERE order_date >= '2026-01-01'
  AND order_date < '2026-02-01';
```

If the table is partitioned by `order_date`, the database can scan only the January partition.

This is called **partition pruning**.

## Sharding

Sharding means partitions are distributed across multiple machines.

Example:

```text
Shard 1 -> users 1 to 10 million
Shard 2 -> users 10 million to 20 million
Shard 3 -> users 20 million to 30 million
```

Or hash-based:

```text
shard = hash(user_id) % number_of_shards
```

Example:

```text
User 123 -> Shard 2
User 456 -> Shard 1
User 789 -> Shard 3
```

### Why shard?

- One database cannot handle all traffic
- One database cannot store all data
- Write throughput is too high
- Need horizontal scaling
- Need isolate tenants/customers/regions

## Partitioning vs Sharding

| Concept | Partitioning | Sharding |
|---|---|---|
| Meaning | Split data into smaller parts | Split data across machines |
| Scope | Can be within one database | Usually across multiple databases/nodes |
| Goal | Manageability and query performance | Horizontal scalability |
| Example | Partition orders by month | Put users on different DB servers |
| Complexity | Moderate | Higher |
| Cross-part queries | Easier | Harder |
| Failure handling | Usually one DB system manages it | App/database cluster must handle distributed concerns |

## Common Partitioning Strategies

### 1. Range Partitioning

Split by ranges.

Example:

```text
orders_2026_01
orders_2026_02
orders_2026_03
```

Good for:

- Time-series data
- Logs
- Orders
- Events
- Historical data

Pros:

- Easy to query by range
- Easy to archive old data
- Partition pruning works well

Cons:

- Hot partition risk

Example hot partition:

```text
All new writes go to current month partition
```

### 2. Hash Partitioning

Use a hash function.

```text
partition = hash(user_id) % 16
```

Good for:

- Even distribution
- User/account-based data
- High write volume

Pros:

- Spreads load evenly
- Avoids obvious hot ranges

Cons:

- Range queries become harder
- Rebalancing can be painful

### 3. List Partitioning

Partition by known values.

Example:

```text
US customers
EU customers
APAC customers
```

Good for:

- Region
- Country
- Business unit
- Tenant category
- Status

Pros:

- Easy to understand
- Good for regional/data residency logic

Cons:

- Uneven partition sizes if one region dominates

### 4. Composite Partitioning

Combine strategies.

Example:

```text
Partition by region first
Then by month
```

Or:

```text
Partition by tenant
Then hash by user_id
```

Good for complex large systems.

## Common Sharding Strategies

### 1. Hash-Based Sharding

```text
shard = hash(user_id) % N
```

Good for even distribution.

Problem: changing `N` reshuffles many keys.

Better version: **consistent hashing**, where adding/removing nodes moves only part of the data.

### 2. Range-Based Sharding

```text
Shard 1: user_id 1 - 1M
Shard 2: user_id 1M - 2M
Shard 3: user_id 2M - 3M
```

Good for range queries.

Problem: some ranges can become hot.

### 3. Geo-Based Sharding

```text
US users -> US shard
EU users -> EU shard
India users -> India shard
```

Good for:

- Low latency
- Data residency
- Regional compliance

Problem:

- Global queries are harder
- Users moving regions can be tricky
- Some regions may be much larger

### 4. Tenant-Based Sharding

```text
Customer A -> Shard 1
Customer B -> Shard 2
Customer C -> Shard 3
```

Common in SaaS systems.

Problem:

- Large tenants can dominate a shard
- Need tenant migration/rebalancing strategy

## Choosing a Shard Key

The **shard key** decides where data lives.

Good shard key:

- High cardinality
- Evenly distributed
- Used often in queries
- Stable over time
- Avoids hot partitions

Examples:

Good:

```text
user_id
account_id
tenant_id + hash(user_id)
```

Risky:

```text
created_at
country
status
is_active
```

Why risky?

- `created_at`: all new writes hit newest partition/shard
- `country`: one country may dominate
- `status`: too few values
- `is_active`: only true/false, terrible distribution

## Hot Partition / Hot Shard

A hot partition happens when one partition gets too much traffic.

Examples:

- Celebrity account gets millions of reads
- Viral product page
- Current timestamp partition receives all writes
- One large tenant dominates a shard
- One region has most users

Fixes:

- Cache hot keys
- Split hot partition
- Add random suffix
- Use adaptive partitioning
- Special-case celebrity/high-volume users
- Use read replicas
- Use consistent hashing
- Move large tenants to dedicated shards

## Cross-Shard Problems

Sharding makes some things harder.

### 1. Cross-Shard Query

Example:

```sql
SELECT COUNT(*)
FROM orders
WHERE created_at >= '2026-01-01';
```

If orders are spread across 100 shards, you may need to query all shards and merge results.

### 2. Cross-Shard Transaction

Example:

```text
Transfer money from user A on shard 1
to user B on shard 7
```

This is much harder than a transaction inside one database.

### 3. Joins Across Shards

If `orders` and `users` are on different shards, joins become expensive.

Fix:

- Co-locate related data by shard key
- Denormalize
- Use async pipelines
- Use materialized views
- Avoid cross-shard joins in hot paths

## Interview Answer

You can say:

> Partitioning means splitting data into smaller logical pieces, often inside one database, for performance and manageability. Sharding is partitioning across multiple machines to scale storage and throughput horizontally. The hardest part is choosing the right partition or shard key because it affects load distribution, query patterns, hot partitions, rebalancing, and cross-shard operations.