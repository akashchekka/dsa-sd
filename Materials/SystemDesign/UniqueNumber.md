---
title: Distributed Unique Number Generator
description: Interview notes on generating unique IDs across many servers, covering rejected options, range allocation, and time + machine + counter IDs
---

## Requirements

Clarify these with the interviewer first:

* **Unique:** No two IDs are ever the same, across all servers.
* **Numeric and compact:** Fits in 64 bits, so it is cheap to store and index.
* **Roughly ordered by time (ask):** Later IDs are usually larger. This helps
  database inserts and sorting.
* **High throughput:** For example, 10,000 to 1 million IDs per second.
* **Highly available:** ID generation is never a single point of failure.
* **Low latency:** Well under a millisecond, ideally with no network call.

## Initial options and why they don't work

### 1. Database auto-increment

A single database hands out 1, 2, 3, and so on.

* **Single point of failure:** If the database is down, nobody gets IDs.
* **Bottleneck:** Every ID needs a database write, which can't reach very
  high throughput.
* **Latency:** Every ID costs a network round trip.

### 2. Multiple databases with a step

With two databases, A gives 1, 3, 5 and B gives 2, 4, 6. Each starts at a
different offset and increments by the number of databases.

* **Hard to scale:** Adding a third database changes the step, so every
  existing database has to be reconfigured.
* **Not time-ordered:** A busy database runs ahead of a quiet one, so ID 1001
  from A may be older than ID 500 from B.
* **Still a network call per ID.**

### 3. Random UUID

Each server generates a random 128-bit value on its own.

* **Too large:** 128 bits instead of 64 bits, which costs more storage and
  memory.
* **Not ordered:** Random values make poor database index keys, because inserts
  land all over the index and cause page splits.
* **Not numeric:** Some systems need a plain number.
* It is unique and needs no coordination, so it is fine when size and ordering
  don't matter.

### 4. Central counter service

One service holds a counter in memory and hands out the next number on request.

* **Single point of failure and bottleneck:** It's the same problem as the
  database auto-increment.
* **Network call per ID:** At 1 million requests per second, this alone
  overwhelms the service.

The common problem with options 1, 2, and 4 is **coordinating on every ID**.
The two approaches below avoid that.

## Approach 1: Range allocation

Instead of asking a central place for **one** ID at a time, each server asks
for a **whole block** of IDs, then hands them out from memory.

Analogy: a bank gives each teller a booklet of 1,000 numbered receipts. The
teller only calls head office when the booklet runs out.

### How it works

There's one small central store, usually a single database table:

| key      | next_available |
|----------|----------------|
| order_id | 5001           |

1. Server A starts and asks for a block of 1,000. It gets **5001 to 6000**, and
   `next_available` moves to **6001**.
2. Server B starts and asks for a block. It gets **6001 to 7000**, and
   `next_available` moves to **7001**.
3. Each server hands out IDs **from memory** with a local counter (5001, 5002,
   ...). There's no network call.
4. When Server A runs out, it asks for another block and gets **7001 to 8000**.

The store never gives the same block twice, so IDs are unique across servers.

### Claiming a block safely

Two servers may ask at the same moment, so the read and the update must happen
in **one atomic step**:

```sql
UPDATE id_ranges
SET next_available = next_available + 1000
WHERE key = 'order_id'
RETURNING next_available - 1000 AS block_start;
```

The database row lock makes sure only one server gets each block.

### Server-side logic

```python
def next_id():
    with lock:
        if current >= block_end:
            block_start = claim_block_from_db(size=1000)
            current, block_end = block_start, block_start + 1000
        id = current
        current += 1
        return id
```

### Scaling to 1 million requests per second

The key point: **the central database never sees 1 million requests per
second.** It only sees one request per block.

```text
Database calls per second = Total IDs per second / Block size
```

| Block size | Database calls/sec at 1M rps | A block lasts (whole fleet) |
|------------|------------------------------|-----------------------------|
| 1,000      | 1,000                        | 1 ms                        |
| 10,000     | 100                          | 10 ms                       |
| 100,000    | 10                           | 100 ms                      |
| 1,000,000  | 1                            | 1 second                    |

With 100,000-ID blocks, the database handles about **10 calls per second**.
With 20 app servers at about 50,000 rps each, each server needs a new block
roughly every 2 seconds.

#### Bottlenecks and fixes

1. **Load on the central database**
   * Use large blocks.
   * Better: **adjust block size automatically.** Each server aims for a block
     that lasts about 1 minute. If the last block ran out in 10 seconds, request
     a bigger one. If it lasted 10 minutes, request a smaller one.
2. **Waiting when a block runs out**
   * **Keep two buffers:** a current block and a standby block.
   * When the current block is about 20% used, fetch the next one in the
     background.
   * When the current block runs out, switch to the standby block instantly.
     Requests never wait on the database.
3. **Lock contention inside one server**
   * Use an **atomic increment**, which is a single CPU instruction, instead of
     a heavy lock. It handles tens of millions of operations per second.
   * If it's still hot, give each thread its own small sub-block.
4. **Network cost, if the generator is a separate service**
   * Run the generator as a **library inside each app server**, so there's no
     network call.
   * Or let clients **request IDs in batches**, for example 100 per call.
     That's 10,000 calls per second instead of 1 million.
5. **Central database goes down**
   * The two buffers act as a cushion. Two blocks of about 1 minute each give
     every server 1 to 2 minutes of runway.
   * Run the database with a **replica and automatic failover**, which usually
     takes seconds.
6. **One hot row in the database**
   * At about 10 updates per second, this isn't a real problem.
   * At extreme scale, split the number space across several rows on separate
     databases. For example, database 1 hands out blocks in the lower half and
     database 2 in the upper half.
7. **Wasted IDs when servers crash**
   * A crash can lose up to one block of IDs.
   * This doesn't matter: 64 bits hold about 9 quintillion values. At 1 million
     per second, that lasts about 290,000 years.

#### Architecture

```text
              +-----------------------------------+
              | Central database (+ replica)      |
              | id_ranges: next_available         |
              | ~10 block requests/sec            |
              +-----------------^-----------------+
                                | fetch block in background
          +---------------------+---------------------+
          |                     |                     |
   +------+-------+      +------+-------+      +------+-------+
   | App server 1 |      | App server 2 | ...  | App server 20|
   | current blk  |      | current blk  |      | current blk  |
   | standby blk  |      | standby blk  |      | standby blk  |
   | atomic ++    |      | atomic ++    |      | atomic ++    |
   +--------------+      +--------------+      +--------------+
     ~50k rps each, all generated in memory = 1M rps total
```

### Pros and cons of range allocation

**Pros:**

* It's very simple to build and explain.
* IDs are small, plain numbers.
* It's very fast, because almost every ID is generated in memory.
* It doesn't depend on clocks.

**Cons:**

* **Gaps:** If a server crashes mid-block, the unused IDs are lost.
* **Not time-ordered across servers:** Server A may issue 5002 after Server B
  issued 6001. Within one server, IDs do increase.
* **Central dependency:** The store is needed whenever a block runs out.
  Prefetching reduces this risk but doesn't remove it.
* **Guessable:** Sequential IDs shouldn't be exposed publicly, for example in
  URLs.

## Approach 2: Time + machine + counter

Each server builds the ID **itself, with no coordination per request**, by
packing three pieces into one 64-bit number. This is the idea behind Twitter's
Snowflake IDs.

### Bit layout

```text
| 1 bit  |      41 bits        |  10 bits   |   12 bits    |
| unused |  timestamp (ms)     | machine id |  sequence    |
```

* **1 bit, unused:** Always 0, so the number stays positive.
* **41 bits, timestamp:** Milliseconds since a custom start date (for example,
  2024-01-01). This gives about **69 years**.
* **10 bits, machine ID:** Up to **1,024** generator servers.
* **12 bits, sequence:** A counter that resets every millisecond. This allows
  **4,096 IDs per millisecond per machine**, about 4 million per second.

**Why it's unique:** A collision would need the same millisecond, the same
machine, and the same sequence number, and the design never allows that.

**Why it's time-ordered:** The timestamp is in the highest bits, so newer IDs
are bigger numbers.

### Generation logic

```python
def next_id():
    now = current_time_ms()
    if now < last_timestamp:
        raise ClockMovedBackwardsError
    if now == last_timestamp:
        sequence = (sequence + 1) & 4095    # 12 bits
        if sequence == 0:                   # used all 4096 this millisecond
            now = wait_until_next_ms(last_timestamp)
    else:
        sequence = 0
    last_timestamp = now
    return ((now - CUSTOM_EPOCH) << 22) | (machine_id << 12) | sequence
```

The function must be thread-safe, so it runs under a lock or uses an atomic
operation.

### Architecture

```text
  App servers --> ID generator (library inside each app, OR a small service)
                        |
                        +-- at startup only: get a unique machine ID
                            from a coordination store
```

* **Library:** No network call, so it's the fastest option.
* **Separate service:** Easier to manage and upgrade, but every ID costs a
  network call.

### Edge cases

1. **Assigning unique machine IDs**
   * At startup, a server claims a free number from 0 to 1023 in a shared store
     (a database table or a configuration service) and holds it with a lease
     that it renews regularly.
   * If the server dies, the lease expires and the number can be reused.
2. **The clock moves backwards** (for example, after a clock sync correction)
   * For a small jump of a few milliseconds, wait until the clock catches up.
   * For a large jump, refuse to generate IDs and raise an alert.
   * Configure clock sync to adjust slowly instead of jumping.
3. **More than 4,096 requests in one millisecond**
   * Wait for the next millisecond, which costs at most 1 ms.
   * If this happens often, use fewer machine bits and more sequence bits.
4. **Server restarts within the same millisecond**
   * On startup, wait a few milliseconds, or save the last-used timestamp to
     disk.
5. **The 69 years run out**
   * Choose the custom start date close to launch, and plan a migration well
     in advance.

### Scaling to 1 million requests per second

* There's no central call per ID, so throughput scales with the number of
  servers.
* One machine can produce about 4 million IDs per second, so a handful of
  servers covers 1 million rps.
* For more than 1,024 servers or several datacenters, split the 10 machine bits
  into 5 datacenter bits and 5 machine bits, or rebalance the bits.

### Pros and cons of time + machine + counter

**Pros:**

* IDs are roughly sorted by time across all servers.
* There's no central dependency per request. A coordination store is only
  needed at startup.
* It's very fast and scales horizontally.

**Cons:**

* **Depends on clocks:** It's sensitive to clock drift and clocks moving
  backwards.
* **Only roughly ordered:** Clock differences between machines mean an ID
  created a few milliseconds later can be slightly smaller.
* **Reveals information:** Anyone can decode the creation time and the machine
  from an ID.
* IDs are large 64-bit numbers.

## Comparison

| Point                 | Range allocation         | Time + machine + counter       |
|-----------------------|--------------------------|--------------------------------|
| Central dependency    | Yes, once per block      | Only for a machine ID at start |
| Time-ordered          | Only within each server  | Roughly, across servers        |
| Depends on clocks     | No                       | Yes                            |
| ID size               | Small numbers            | Large 64-bit numbers           |
| Gaps                  | Yes, on a crash          | Yes, always                    |
| Complexity            | Very simple              | Moderate                       |
| 1M rps                | Large blocks + prefetch  | Natural, about 4M/sec/machine  |

## Which one to pick

* **Need unique, compact numbers, but not time ordering:** Use **range
  allocation**. It's simpler and has no clock problems.
* **Need IDs roughly sorted by time** (feeds, time-based queries, efficient
  index inserts): Use **time + machine + counter**.
* **Need strict ordering with no gaps** (for example, invoice numbers): Use a
  single database sequence and accept lower throughput. It's a different
  requirement.

## Interview summary

> Generating an ID through a central database or counter on every request
> is a bottleneck and a single point of failure. UUIDs avoid coordination, but
> they're 128 bits and unordered. So I'd pick one of two approaches.
> **Range allocation**: each server reserves a block of IDs from a central
> table and hands them out from memory. With 100,000-ID blocks, 1 million rps
> means only about 10 database calls per second, and prefetching the next block
> means requests never wait.
> **Time + machine + counter**: each server packs the current time, its unique
> machine number, and a per-millisecond counter into 64 bits. It needs no
> per-request coordination and gives time-sorted IDs, but I have to handle
> clock drift and machine ID assignment.
> If time ordering matters, I choose the second approach. Otherwise, I choose
> range allocation for its simplicity.
