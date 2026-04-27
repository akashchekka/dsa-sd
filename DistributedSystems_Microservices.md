# Distributed Systems and Microservices Interview Guide

## Table of Contents

- [How to Use This Guide](#how-to-use-this-guide)
- [Distributed Systems Big Picture](#distributed-systems-big-picture)
- [Core Vocabulary](#core-vocabulary)
- [Networking Fundamentals](#networking-fundamentals)
- [Latency, Throughput, and Tail Latency](#latency-throughput-and-tail-latency)
- [Scalability Fundamentals](#scalability-fundamentals)
- [Load Balancing](#load-balancing)
- [Caching](#caching)
- [Databases in Distributed Systems](#databases-in-distributed-systems)
- [Replication](#replication)
- [Partitioning and Sharding](#partitioning-and-sharding)
- [Consistency Models](#consistency-models)
- [CAP and PACELC](#cap-and-pacelc)
- [Consensus and Coordination](#consensus-and-coordination)
- [Transactions and Distributed Transactions](#transactions-and-distributed-transactions)
- [Event-Driven Architecture](#event-driven-architecture)
- [Message Queues and Streams](#message-queues-and-streams)
- [Microservices Fundamentals](#microservices-fundamentals)
- [Microservices Communication Patterns](#microservices-communication-patterns)
- [Service Discovery and API Gateway](#service-discovery-and-api-gateway)
- [Resilience Patterns](#resilience-patterns)
- [Data Management in Microservices](#data-management-in-microservices)
- [Observability](#observability)
- [Deployment and Operations](#deployment-and-operations)
- [Security in Distributed Systems](#security-in-distributed-systems)
- [Performance and Capacity Planning](#performance-and-capacity-planning)
- [System Design Interview Framework](#system-design-interview-framework)
- [Common FAANG-Style System Design Problems](#common-faang-style-system-design-problems)
- [Regular Interview Questions](#regular-interview-questions)
- [Tricky Interview Questions](#tricky-interview-questions)
- [Scenario-Based Questions](#scenario-based-questions)
- [Microservices Anti-Patterns](#microservices-anti-patterns)
- [Quick Revision Notes](#quick-revision-notes)

---

## How to Use This Guide

This guide is designed for interviews at companies like FAANG, Uber, Microsoft, Stripe, Airbnb, LinkedIn, and other large-scale engineering organizations.

For interview preparation, focus on three layers:

1. **Concepts**: CAP, consistency, replication, sharding, consensus, queues, caching, microservices boundaries.
2. **Tradeoffs**: Every design decision has cost, latency, reliability, correctness, operational, and complexity tradeoffs.
3. **Communication**: In interviews, clearly state assumptions, ask clarifying questions, estimate scale, and explain why you choose one design over another.

Most strong distributed systems answers sound like this:

> "Given the requirement for low latency and high availability, I would choose asynchronous replication and eventual consistency for this path, but for payments or inventory reservation I would isolate the strongly consistent workflow and use idempotency plus transactional guarantees."

---

## Distributed Systems Big Picture

A **distributed system** is a collection of independent computers that appears to users as a single coherent system.

Examples:

- Search engine
- Payment system
- Ride-sharing platform
- Social network feed
- Online marketplace
- Messaging app
- Video streaming system
- Cloud storage service
- Banking platform
- Large-scale analytics pipeline

### Why Distributed Systems Exist

Single-machine systems eventually hit limits:

- CPU limit
- Memory limit
- Disk limit
- Network limit
- Availability limit
- Geographic latency limit
- Operational blast radius limit

Distributed systems solve these by spreading work across many machines, regions, databases, caches, queues, and services.

### The Hard Part

Distributed systems are difficult because failures are partial.

In a single process, either the process is running or it crashed. In a distributed system:

- One service may be healthy while another is down.
- One region may be unreachable.
- A request may succeed but the response may be lost.
- A database write may commit but the client may time out.
- Two replicas may disagree.
- Clocks may not agree.
- Messages may be delayed, duplicated, reordered, or dropped.

### Core Principle

The central challenge is this:

> How do we build systems that remain correct, available, and understandable when machines, networks, and people fail?

---

## Core Vocabulary

| Term | Meaning |
|---|---|
| Node | A machine, process, or server participating in the system. |
| Cluster | Group of nodes working together. |
| Replica | Copy of data or service instance. |
| Leader/Primary | Node responsible for coordinating writes or decisions. |
| Follower/Secondary | Node that replicates data from leader. |
| Quorum | Minimum number of nodes needed to make a decision. |
| Partition | Network split where some nodes cannot communicate with others. |
| Shard | Horizontal partition of data. |
| Replication | Keeping copies of data on multiple nodes. |
| Consistency | Whether reads observe correct/latest data according to a model. |
| Availability | System continues serving requests despite failures. |
| Durability | Data survives crashes or restarts. |
| Idempotency | Repeating an operation has the same effect as doing it once. |
| Backpressure | Slowing producers when consumers cannot keep up. |
| Circuit breaker | Stop calling an unhealthy dependency temporarily. |
| Tail latency | High-percentile latency such as p95/p99. |
| SLO | Service Level Objective, target reliability/latency goal. |
| SLA | Service Level Agreement, external commitment. |
| RPO | Recovery Point Objective, acceptable data loss window. |
| RTO | Recovery Time Objective, acceptable recovery time. |

---

## Networking Fundamentals

Distributed systems communicate over networks. Network behavior dominates system behavior at scale.

### TCP vs UDP

| Feature | TCP | UDP |
|---|---|---|
| Connection | Connection-oriented | Connectionless |
| Reliability | Reliable delivery | Best effort |
| Ordering | Ordered bytes | No ordering guarantee |
| Congestion control | Built-in | Application responsibility |
| Use cases | HTTP, databases, RPC, APIs | DNS, video, gaming, telemetry, QUIC base |

Most backend services use TCP through HTTP, gRPC, database drivers, or message brokers.

### HTTP/1.1 vs HTTP/2 vs gRPC

| Protocol | Key Idea | Best For |
|---|---|---|
| HTTP/1.1 | Text-based request/response, limited multiplexing | Public APIs, browser compatibility |
| HTTP/2 | Multiplexed streams over one connection | Lower latency, many concurrent requests |
| gRPC | Binary RPC over HTTP/2 using Protocol Buffers | Internal service-to-service communication |

### Common Network Failure Modes

- Connection timeout
- Read timeout
- DNS failure
- TLS handshake failure
- Packet loss
- Slow network path
- Load balancer misrouting
- Connection pool exhaustion
- Half-open connection
- Network partition

### Interview Tip

When an interviewer asks, "What can go wrong in this service call?", do not just say "the service can fail." Say:

- The request may never arrive.
- The request may arrive twice because of retries.
- The server may process it but response may be lost.
- The client may time out and retry, causing duplicate side effects.
- The dependency may be slow, causing thread pool exhaustion.
- DNS or load balancer behavior may route to unhealthy hosts.

---

## Latency, Throughput, and Tail Latency

### Latency

Latency is the time taken to complete one operation.

Examples:

- API request takes 80 ms.
- Database query takes 12 ms.
- Cache lookup takes 1 ms.

### Throughput

Throughput is the number of operations completed per unit time.

Examples:

- 10,000 requests per second.
- 5 million messages per minute.

### Tail Latency

Tail latency is high-percentile latency.

| Metric | Meaning |
|---|---|
| p50 | 50% of requests are faster than this. Median latency. |
| p95 | 95% of requests are faster than this. |
| p99 | 99% of requests are faster than this. |
| p999 | 99.9% of requests are faster than this. |

Tail latency matters because user-facing flows often call many services. If one request fans out to 20 services, the probability of hitting one slow dependency becomes high.

### Example

If each dependency has 99% chance of being fast, and a request calls 20 dependencies:

```
Probability all are fast = 0.99^20 = 0.817
```

So about 18% of requests may experience at least one slow dependency.

### Causes of Tail Latency

- Garbage collection pauses
- Noisy neighbors
- Lock contention
- Queue buildup
- Slow disk I/O
- Network retransmission
- Cache miss
- Cold start
- Database compaction
- Large fanout
- Retry storms

### Reducing Tail Latency

- Timeouts
- Hedged requests
- Circuit breakers
- Caching
- Load shedding
- Bulkheads
- Async processing
- Reduce fanout
- Use p95/p99 metrics, not averages

---

## Scalability Fundamentals

Scalability is the ability of a system to handle increased load.

### Vertical Scaling

Add more resources to one machine.

Examples:

- More CPU
- More RAM
- Faster disk
- Larger database instance

Pros:

- Simpler architecture
- Fewer distributed systems problems
- Good early-stage choice

Cons:

- Hardware limits
- Expensive at high scale
- Single-machine failure risk

### Horizontal Scaling

Add more machines.

Examples:

- More stateless API servers
- More database shards
- More Kafka partitions
- More worker nodes

Pros:

- Better fault tolerance
- Can scale very large
- Supports geographic distribution

Cons:

- More operational complexity
- Requires partitioning, routing, coordination
- More consistency challenges

### Stateless vs Stateful Scaling

| Type | Scaling Difficulty | Examples |
|---|---|---|
| Stateless | Easier | API servers, web servers, compute workers |
| Stateful | Harder | Databases, queues, caches, search indexes |

Stateless services can usually sit behind a load balancer. Stateful services require replication, partitioning, backups, failover, and consistency decisions.

---

## Load Balancing

Load balancing distributes traffic across multiple backend instances.

### Why Load Balancing Matters

- Increases availability
- Improves throughput
- Prevents one server from being overloaded
- Enables rolling deployments
- Supports health checks

### Common Algorithms

| Algorithm | How It Works | Good For |
|---|---|---|
| Round robin | Send requests in order to each server | Similar servers, simple traffic |
| Weighted round robin | More traffic to stronger servers | Mixed capacity servers |
| Least connections | Send to server with fewest active connections | Long-lived connections |
| Least response time | Prefer fastest responding server | Latency-sensitive services |
| Consistent hashing | Route same key to same node | Caches, sticky routing, sharded systems |
| Random | Choose random healthy server | Simple and surprisingly effective |

### L4 vs L7 Load Balancing

| Type | Layer | Routes By | Example |
|---|---|---|---|
| L4 | Transport | IP and port | TCP load balancer |
| L7 | Application | HTTP path, headers, host, cookies | API gateway, reverse proxy |

### Sticky Sessions

Sticky sessions send the same user to the same server.

Pros:

- Useful when session state is stored locally.

Cons:

- Uneven load
- Harder failover
- Bad fit for stateless microservices

Better approach: store session state in shared storage such as Redis, database, or signed tokens.

---

## Caching

Caching stores frequently accessed data closer to the consumer.

### Why Cache?

- Lower latency
- Reduce database load
- Improve throughput
- Survive dependency slowness
- Reduce cost

### Cache Locations

| Cache Type | Example |
|---|---|
| Browser cache | Static files, images, scripts |
| CDN | Global edge cache for media/static content |
| API gateway cache | Cache API responses |
| Application cache | In-memory local cache |
| Distributed cache | Redis, Memcached |
| Database cache | Buffer pool, query cache |

### Cache Patterns

#### Cache-Aside

Application checks cache first. On miss, reads database and populates cache.

```
read(key):
  value = cache.get(key)
  if value exists:
      return value
  value = db.get(key)
  cache.set(key, value, ttl)
  return value
```

Most common pattern.

#### Read-Through

Application reads from cache. Cache itself loads from database on miss.

#### Write-Through

Write goes to cache and database synchronously.

Pros: cache stays fresh.

Cons: higher write latency.

#### Write-Behind

Write goes to cache first, database update happens asynchronously.

Pros: low write latency.

Cons: risk of data loss if cache fails before persistence.

### Cache Invalidation

Cache invalidation is hard because stale data can cause incorrect behavior.

Common strategies:

- TTL expiration
- Explicit delete on write
- Versioned keys
- Event-based invalidation
- Write-through updates
- Short TTL for sensitive data

### Cache Stampede

A cache stampede happens when many requests miss the cache at the same time and all hit the database.

Mitigations:

- Request coalescing
- Locks around recomputation
- Probabilistic early refresh
- Jittered TTLs
- Serve stale while revalidating
- Prewarming

### Tricky Cache Question

**Question:** If cache and database disagree, which one is correct?

**Answer:** Usually the database is the source of truth, but the real answer depends on the write pattern. In write-behind systems, cache may temporarily contain newer data than the database. In cache-aside systems, database is usually authoritative and cache is a performance optimization.

---

## Databases in Distributed Systems

Choosing the database is one of the most important system design decisions.

### OLTP vs OLAP

| Type | Purpose | Examples |
|---|---|---|
| OLTP | Online transactions, low-latency reads/writes | MySQL, PostgreSQL, DynamoDB, Spanner, CockroachDB |
| OLAP | Analytics over large datasets | BigQuery, Redshift, Snowflake, ClickHouse, Druid |

### SQL vs NoSQL

| Aspect | SQL | NoSQL |
|---|---|---|
| Schema | Structured | Flexible or semi-structured |
| Query | SQL, joins, transactions | Key-value, document, wide-column, graph |
| Consistency | Often strong by default | Often tunable/eventual |
| Scaling | Traditionally vertical, now can be distributed | Often designed for horizontal scale |
| Best for | Complex queries, relational integrity | Massive scale, flexible data, simple access patterns |

### Common Database Types

| Type | Examples | Good For |
|---|---|---|
| Relational | PostgreSQL, MySQL | Transactions, joins, strong consistency |
| Key-value | Redis, DynamoDB | Fast lookup by key |
| Document | MongoDB, Cosmos DB | JSON-like documents, flexible schema |
| Wide-column | Cassandra, HBase | High-write scale, time-series-like access |
| Search | Elasticsearch, OpenSearch | Full-text search |
| Graph | Neo4j, Neptune | Relationship-heavy queries |
| Time-series | InfluxDB, TimescaleDB | Metrics, IoT, events over time |
| Columnar OLAP | ClickHouse, BigQuery | Fast analytical scans |

### Interview Rule

Do not choose a database because it sounds modern. Choose based on access patterns.

Ask:

- What are the main reads?
- What are the main writes?
- Is strong consistency needed?
- Is cross-entity transaction needed?
- What is query shape?
- How much data?
- What is write rate?
- What is read rate?
- What are the latency goals?
- What is the failure tolerance?

---

## Replication

Replication stores copies of data on multiple nodes.

### Why Replicate?

- High availability
- Fault tolerance
- Read scaling
- Disaster recovery
- Geographic locality

### Leader-Follower Replication

One leader accepts writes. Followers replicate from leader.

Pros:

- Simpler conflict handling
- Stronger write ordering
- Common in relational databases

Cons:

- Leader bottleneck
- Failover complexity
- Replication lag

### Multi-Leader Replication

Multiple leaders accept writes.

Pros:

- Better write availability
- Useful across regions

Cons:

- Conflict resolution is hard
- Concurrent writes may conflict

### Leaderless Replication

Any replica can accept writes. Uses quorum reads/writes.

Examples: Dynamo-style systems, Cassandra-like designs.

Pros:

- High availability
- No single leader bottleneck

Cons:

- Read repair, hinted handoff, conflict resolution complexity

### Synchronous vs Asynchronous Replication

| Replication | Write Latency | Data Safety | Availability |
|---|---|---|---|
| Synchronous | Higher | Stronger | Lower during replica/network issues |
| Asynchronous | Lower | Possible data loss on failover | Higher |

### Replication Lag

Replication lag means followers are behind the leader.

Problems:

- User writes then reads stale data.
- Reports show old values.
- Failover may lose recent writes.

Solutions:

- Read-your-writes using leader reads for user session.
- Use monotonic reads by routing user to same replica.
- Track replication offset/version.
- Use synchronous replication for critical paths.

---

## Partitioning and Sharding

Partitioning splits data across machines.

### Why Shard?

- Dataset too large for one machine.
- Write throughput too high for one machine.
- Read traffic too large for one machine.
- Need isolation by tenant/region/customer.

### Sharding Strategies

| Strategy | How It Works | Pros | Cons |
|---|---|---|---|
| Range-based | Key ranges assigned to shards | Efficient range queries | Hot partitions possible |
| Hash-based | Hash(key) maps to shard | Even distribution | Range queries harder |
| Directory-based | Lookup service maps key to shard | Flexible | Directory can be bottleneck |
| Geo-based | Data partitioned by region | Low local latency | Cross-region queries harder |
| Tenant-based | Tenant/customer owns shard | Isolation | Large tenants can become hot |

### Hot Shard Problem

A hot shard receives disproportionate traffic.

Examples:

- Celebrity account in social media.
- Popular product during sale.
- Current timestamp partition in time-series DB.
- One large enterprise tenant.

Mitigations:

- Add random suffix/prefix to keys.
- Split hot partition.
- Use adaptive partitioning.
- Cache hot objects.
- Separate heavy tenants.
- Use write buffering.

### Rebalancing

Rebalancing moves data when shards are added/removed.

Challenges:

- Moving large data takes time.
- Traffic must keep flowing.
- Need dual reads/writes during migration.
- Avoid overloading network/disk.

Common approaches:

- Consistent hashing
- Virtual nodes
- Online migration with backfill
- Change data capture during migration
- Cutover after validation

---

## Consistency Models

Consistency defines what values reads are allowed to return.

### Strong Consistency

Reads always return the latest committed write.

Good for:

- Payments
- Inventory reservation
- Bank balances
- User permissions
- Uniqueness constraints

Cost:

- Higher latency
- Lower availability during network partitions
- More coordination

### Eventual Consistency

If no new writes happen, replicas eventually converge.

Good for:

- Likes count
- View count
- Search indexing
- Recommendations
- Analytics
- Feeds where slight delay is acceptable

Cost:

- Users may see stale data
- Conflicts may need resolution
- Harder mental model

### Read-Your-Writes Consistency

After a user writes, that same user sees their own write.

Example:

- You update your profile photo and immediately see the new photo.

Implementation:

- Route user reads to leader briefly.
- Track version/session token.
- Use sticky replica after replica catches up.

### Monotonic Reads

Once a user sees version 10, they should not later see version 8.

Implementation:

- Route user to same replica.
- Use version-aware reads.

### Causal Consistency

If event B depends on event A, everyone should see A before B.

Example:

- Comment reply should not appear before the parent comment.

### Linearizability

The strongest common consistency model. Operations appear to happen atomically in real-time order.

Good for:

- Locks
- Leader election
- Account balance updates
- Distributed coordination

Cost:

- Requires coordination/quorum/consensus
- Higher latency
- Lower availability during partitions

---

## CAP and PACELC

### CAP Theorem

CAP says that during a network partition, a distributed data system must choose between:

- **Consistency**: every read sees the latest correct write.
- **Availability**: every request receives a non-error response.
- **Partition tolerance**: system continues despite network split.

Because network partitions can happen, real distributed systems must tolerate partitions. So the practical tradeoff is usually **CP vs AP during partition**.

### CP Systems

Prefer consistency over availability during partition.

Examples:

- ZooKeeper
- etcd
- Consul in strong consistency mode
- Spanner-like systems for strongly consistent data

Behavior:

- May reject requests if quorum unavailable.
- Avoids returning incorrect/stale data for critical operations.

### AP Systems

Prefer availability over consistency during partition.

Examples:

- Dynamo-style systems
- Cassandra-style systems depending on quorum settings

Behavior:

- Accepts reads/writes during partition.
- Reconciles conflicts later.

### PACELC

CAP only talks about partitions. PACELC adds the normal-case tradeoff:

> If Partition occurs, choose Availability or Consistency; Else, choose Latency or Consistency.

Meaning:

- During partition: A vs C
- During normal operation: L vs C

This is often more useful in interviews because most of the time the system is not partitioned, but every request faces latency vs consistency tradeoffs.

---

## Consensus and Coordination

Consensus lets distributed nodes agree on a value despite failures.

### Why Consensus Is Needed

- Leader election
- Distributed locks
- Configuration management
- Membership tracking
- Strongly consistent metadata
- Transaction coordination

### Common Algorithms

| Algorithm | Notes |
|---|---|
| Paxos | Classic consensus algorithm, theoretically important, hard to understand/implement. |
| Raft | Easier-to-understand consensus algorithm used by etcd and others. |
| Zab | ZooKeeper atomic broadcast protocol. |

### Raft Basic Idea

Raft has:

- Leader
- Followers
- Candidates
- Terms
- Log replication
- Majority quorum

Writes go through the leader. A write is committed when replicated to a majority.

### Quorum

For N replicas, quorum is usually:

```
floor(N / 2) + 1
```

Examples:

- 3 nodes => quorum 2
- 5 nodes => quorum 3
- 7 nodes => quorum 4

### Split Brain

Split brain happens when two nodes believe they are leader.

Mitigation:

- Use quorum-based leader election.
- Use fencing tokens.
- Avoid manual failover without coordination.

### Fencing Token

A fencing token is a monotonically increasing number given to a lock holder or leader. Downstream systems reject stale tokens.

This prevents an old leader from continuing to write after it lost leadership.

---

## Transactions and Distributed Transactions

### ACID

| Property | Meaning |
|---|---|
| Atomicity | All or nothing. |
| Consistency | Transaction preserves invariants. |
| Isolation | Concurrent transactions do not interfere incorrectly. |
| Durability | Committed data survives crashes. |

### Isolation Levels

| Level | Prevents | Allows |
|---|---|---|
| Read uncommitted | Almost nothing | Dirty reads |
| Read committed | Dirty reads | Non-repeatable reads, phantom reads |
| Repeatable read | Dirty and non-repeatable reads | Phantom reads in some systems |
| Serializable | All major anomalies | Lower concurrency/higher cost |

### Two-Phase Commit (2PC)

2PC coordinates a transaction across multiple systems.

Steps:

1. Prepare phase: coordinator asks participants if they can commit.
2. Commit phase: if all agree, coordinator tells everyone to commit.

Problems:

- Blocking if coordinator fails.
- Holds locks across services.
- Poor availability.
- Operationally fragile.

### Saga Pattern

A saga breaks a distributed transaction into local transactions with compensating actions.

Example order saga:

1. Create order.
2. Reserve inventory.
3. Charge payment.
4. Schedule shipment.

If payment fails:

1. Cancel payment attempt.
2. Release inventory.
3. Mark order failed.

### Choreography vs Orchestration

| Style | How It Works | Pros | Cons |
|---|---|---|---|
| Choreography | Services react to events | Loose coupling | Hard to understand global flow |
| Orchestration | Central orchestrator coordinates steps | Clear control flow | Orchestrator can become central dependency |

### Idempotency

Idempotency is critical because retries create duplicate requests.

Example:

```
POST /payments
Idempotency-Key: abc-123
```

If the same key is sent twice, the server returns the same result instead of charging twice.

---

## Event-Driven Architecture

Event-driven systems communicate by publishing events.

### Event

An event is a fact that something happened.

Examples:

- `OrderCreated`
- `PaymentCaptured`
- `DriverAssigned`
- `UserSignedUp`
- `InventoryReserved`

### Benefits

- Loose coupling
- Async processing
- Better scalability
- Better resilience
- Natural audit trail
- Easier fanout to multiple consumers

### Challenges

- Eventual consistency
- Duplicate events
- Out-of-order events
- Schema evolution
- Debugging complexity
- Poison messages
- Backpressure

### Event Notification vs Event-Carried State Transfer

| Type | Description |
|---|---|
| Event notification | Event says something happened; consumer calls source for details. |
| Event-carried state | Event includes enough data for consumer to update local state. |

Tradeoff:

- Notification keeps events small but increases coupling and extra calls.
- Event-carried state reduces calls but duplicates data and requires schema management.

---

## Message Queues and Streams

### Queue vs Stream

| Feature | Queue | Stream |
|---|---|---|
| Message consumption | Usually one consumer processes each message | Multiple consumers can read same event log |
| Retention | Message often deleted after ack | Events retained for time/size |
| Ordering | Usually per queue or partition | Per partition |
| Replay | Limited | Natural replay supported |
| Examples | SQS, RabbitMQ, Azure Service Bus | Kafka, Kinesis, Event Hubs, Pulsar |

### At-Most-Once, At-Least-Once, Exactly-Once

| Delivery | Meaning | Risk |
|---|---|---|
| At-most-once | Message delivered zero or one time | Data loss |
| At-least-once | Message delivered one or more times | Duplicates |
| Exactly-once | Effect happens exactly once | Hard; often means idempotent processing plus transactions |

### Kafka Basics

| Concept | Meaning |
|---|---|
| Topic | Named event stream. |
| Partition | Ordered append-only log within a topic. |
| Offset | Position in partition. |
| Consumer group | Group of consumers sharing partitions. |
| Broker | Kafka server. |
| Producer | Publishes events. |
| Consumer | Reads events. |

### Ordering in Kafka

Kafka guarantees ordering within a partition, not across all partitions.

If order matters for a key, use the same partition key.

Example:

- All events for `orderId=123` should use `orderId` as partition key.

### Poison Message

A poison message repeatedly fails processing.

Mitigation:

- Retry with backoff
- Dead-letter queue
- Alerting
- Manual inspection
- Skip after max attempts if safe

### Backpressure

Backpressure prevents producers from overwhelming consumers.

Approaches:

- Consumer lag monitoring
- Rate limiting producers
- Auto-scaling consumers
- Buffering
- Load shedding
- Bounded queues

---

## Microservices Fundamentals

A **microservice** is an independently deployable service organized around a business capability.

### Microservices Are Not Just Small Services

A good microservice has:

- Clear ownership
- Business boundary
- Independent deployment
- Own data model or database boundary
- Explicit API/event contract
- Observability
- Operational maturity

### Monolith vs Microservices

| Aspect | Monolith | Microservices |
|---|---|---|
| Deployment | One deployable unit | Many independently deployable services |
| Development | Simple initially | More coordination and tooling |
| Scaling | Scale whole app | Scale hot services independently |
| Data | Shared database common | Database-per-service preferred |
| Failure | One bug can affect entire app | Failures can be isolated but network failures increase |
| Transactions | Easier local transactions | Distributed consistency challenges |
| Observability | Simpler | Requires tracing, metrics, logs |

### When Microservices Make Sense

- Multiple teams need independent ownership.
- Different parts scale differently.
- Clear business domains exist.
- Deployment speed is blocked by monolith size.
- Organizational maturity supports distributed operations.

### When Microservices Are a Bad Idea

- Small team
- Unclear domain boundaries
- Early product discovery
- Weak observability
- Weak DevOps maturity
- Need simple transactional consistency everywhere

### Interview Tip

Do not automatically say microservices are better. Strong answers mention that a modular monolith is often better until team size, scale, or deployment constraints justify microservices.

---

## Microservices Communication Patterns

### Synchronous Communication

Examples:

- REST
- gRPC
- GraphQL

Pros:

- Simple mental model
- Immediate response
- Good for request/response flows

Cons:

- Tight runtime coupling
- Cascading failures
- Higher tail latency
- Requires timeouts/retries/circuit breakers

### Asynchronous Communication

Examples:

- Kafka events
- SQS messages
- RabbitMQ queues
- Azure Service Bus

Pros:

- Loose coupling
- Better resilience
- Smooth traffic spikes
- Good for background workflows

Cons:

- Eventual consistency
- Debugging is harder
- Duplicate/out-of-order handling required

### REST vs gRPC

| Aspect | REST | gRPC |
|---|---|---|
| Format | JSON usually | Protobuf binary |
| Performance | Good, human-readable | Faster, smaller payloads |
| Browser support | Native | Requires proxy for browsers |
| Contract | OpenAPI optional | Protobuf required |
| Streaming | Limited | Built-in streaming |
| Best for | Public APIs | Internal service-to-service APIs |

### GraphQL

GraphQL lets clients request exactly the fields they need.

Good for:

- Frontend aggregation
- Mobile clients
- Avoiding over-fetching/under-fetching

Risks:

- Query complexity attacks
- N+1 backend calls
- Caching complexity
- Authorization complexity

---

## Service Discovery and API Gateway

### Service Discovery

Service discovery helps services find each other dynamically.

Patterns:

- Client-side discovery: client queries registry and chooses instance.
- Server-side discovery: load balancer/proxy queries registry.

Examples:

- Kubernetes service DNS
- Consul
- Eureka
- etcd-backed systems

### API Gateway

An API gateway is the entry point for clients.

Responsibilities:

- Routing
- Authentication
- Authorization
- Rate limiting
- TLS termination
- Request/response transformation
- Aggregation
- Caching
- Observability

### API Gateway vs Load Balancer

| Component | Purpose |
|---|---|
| Load balancer | Distributes traffic among instances. |
| API gateway | Manages API-level concerns such as auth, routing, quotas, transformations. |

### Backend for Frontend (BFF)

BFF is a gateway tailored for a specific frontend, such as mobile or web.

Use when:

- Mobile and web need different payloads.
- Frontend needs aggregation across many services.
- Client-specific logic should not pollute core services.

---

## Resilience Patterns

Distributed systems must assume dependencies fail.

### Timeout

Every network call should have a timeout.

Bad:

```
call dependency and wait forever
```

Good:

```
call dependency with 200 ms timeout
fallback or fail gracefully
```

### Retry

Retries help with transient failures.

Rules:

- Retry only safe/idempotent operations or use idempotency keys.
- Use exponential backoff.
- Add jitter.
- Limit max attempts.
- Do not retry overload errors aggressively.

### Circuit Breaker

Stops calling a failing dependency temporarily.

States:

- Closed: calls allowed.
- Open: calls blocked, fallback used.
- Half-open: small number of trial calls.

### Bulkhead

Isolates resources so one dependency cannot exhaust everything.

Examples:

- Separate thread pools per dependency.
- Separate connection pools.
- Separate queues.

### Rate Limiting

Controls request rate.

Algorithms:

- Token bucket
- Leaky bucket
- Fixed window
- Sliding window

### Load Shedding

Drop lower-priority work when overloaded.

Examples:

- Reject optional analytics calls.
- Return cached/stale data.
- Disable expensive personalization.

### Hedged Requests

Send a duplicate request to another replica if the first is slow.

Pros:

- Reduces tail latency.

Cons:

- Increases load.
- Must be safe for idempotent reads or carefully controlled.

---

## Data Management in Microservices

### Database per Service

Each service owns its data.

Pros:

- Loose coupling
- Independent schema changes
- Clear ownership
- Different services can choose different databases

Cons:

- Joins across services are hard
- Transactions across services are hard
- Eventual consistency required
- Data duplication may happen

### Shared Database Anti-Pattern

Multiple services directly read/write same database schema.

Problems:

- Tight coupling
- Hard schema migrations
- Ownership confusion
- Services can bypass business rules
- Hidden dependencies

### Data Duplication Is Often Intentional

In microservices, duplication may be acceptable if it improves autonomy.

Example:

- Order service stores `customerId` and customer snapshot fields like shipping name/address at time of order.
- Customer service owns current customer profile.

### CQRS

Command Query Responsibility Segregation separates writes from reads.

| Side | Purpose |
|---|---|
| Command/write model | Validates and changes state. |
| Query/read model | Optimized for reads. |

Useful when:

- Read and write patterns differ significantly.
- Need denormalized read models.
- Complex event-driven projections exist.

### Event Sourcing

Store events as source of truth instead of only current state.

Example account events:

- `AccountCreated`
- `MoneyDeposited`
- `MoneyWithdrawn`

Current balance is derived by replaying events.

Pros:

- Full audit history
- Temporal queries
- Rebuild projections

Cons:

- More complex
- Event schema evolution
- Debugging and replay correctness

---

## Observability

Observability answers: what is happening, why, and where?

### Three Pillars

| Pillar | Purpose |
|---|---|
| Logs | Detailed event records. |
| Metrics | Numeric time-series such as latency/error rate. |
| Traces | End-to-end request path across services. |

### Important Metrics

| Metric | Why It Matters |
|---|---|
| QPS/RPS | Traffic volume. |
| Error rate | Reliability. |
| p50/p95/p99 latency | User experience and tail behavior. |
| Saturation | CPU, memory, disk, network, queue depth. |
| Consumer lag | Streaming/queue processing health. |
| Cache hit rate | Cache effectiveness. |
| DB connection pool usage | Bottleneck detection. |

### Golden Signals

Google SRE golden signals:

- Latency
- Traffic
- Errors
- Saturation

### Distributed Tracing

Tracing follows a request across services.

Example:

```
Client -> API Gateway -> Order Service -> Payment Service -> Database
```

Each step creates a span. All spans belong to one trace.

### Correlation ID

A correlation ID is passed across services so logs can be joined.

Example header:

```
X-Correlation-Id: req-123
```

---

## Deployment and Operations

### Deployment Strategies

| Strategy | Description | Risk |
|---|---|---|
| Rolling deployment | Replace instances gradually | Moderate |
| Blue-green | Two environments, switch traffic | Low, but expensive |
| Canary | Small traffic percentage first | Low with good monitoring |
| Shadow traffic | Send copy of production traffic to new version | Good for testing, no user impact |

### Kubernetes Basics

| Concept | Meaning |
|---|---|
| Pod | Smallest deployable unit. |
| Deployment | Manages replica pods. |
| Service | Stable network identity/load balancing for pods. |
| Ingress | External HTTP routing. |
| ConfigMap | Non-secret configuration. |
| Secret | Sensitive configuration. |
| HPA | Horizontal Pod Autoscaler. |

### Autoscaling

Scale based on:

- CPU
- Memory
- Queue length
- Request rate
- Custom business metric
- Kafka consumer lag

### Safe Rollout Checklist

- Health checks
- Readiness checks
- Metrics dashboards
- Error budget awareness
- Rollback plan
- Feature flags
- Database migration plan
- Backward-compatible API changes

---

## Security in Distributed Systems

### Authentication vs Authorization

| Term | Meaning |
|---|---|
| Authentication | Who are you? |
| Authorization | What are you allowed to do? |

### Common Security Controls

- TLS everywhere
- OAuth2/OIDC for user identity
- JWT validation
- mTLS for service-to-service identity
- Secrets management
- Principle of least privilege
- Rate limiting
- Audit logs
- Input validation
- Data encryption at rest
- Data encryption in transit

### Zero Trust

Zero trust means do not automatically trust traffic because it is inside the network.

Every service call should be authenticated, authorized, encrypted, and observable.

### Common Distributed Security Risks

- Over-permissive service accounts
- Leaked API keys
- Missing tenant isolation
- Broken object-level authorization
- Insecure direct service access bypassing gateway
- Unvalidated internal events
- Secrets in logs
- Replay attacks

---

## Performance and Capacity Planning

### Back-of-the-Envelope Estimation

Interviewers expect rough estimates.

Example:

```
100 million daily active users
Each user makes 20 reads/day
Total reads/day = 2 billion
Reads/sec average = 2B / 86,400 = ~23K RPS
Peak = 3x average = ~70K RPS
```

### Storage Estimate Example

```
1 billion events/day
Each event = 1 KB
Daily storage = 1 TB/day
Retention = 365 days
Raw storage = 365 TB
With replication factor 3 = ~1.1 PB
```

### Capacity Planning Questions

- What is average QPS?
- What is peak QPS?
- What is read/write ratio?
- What is object size?
- What is retention period?
- What is replication factor?
- What are p95/p99 latency targets?
- What is acceptable data loss?
- What is acceptable downtime?

---

## System Design Interview Framework

Use this structure in interviews.

### 1. Clarify Requirements

Ask:

- Who are the users?
- What are core features?
- What is out of scope?
- What consistency is required?
- What latency is expected?
- What scale are we designing for?
- What availability target matters?

### 2. Estimate Scale

Estimate:

- DAU/MAU
- QPS
- Storage
- Bandwidth
- Cache size
- Number of partitions

### 3. Define APIs

Example:

```
POST /orders
GET /orders/{id}
POST /payments
GET /users/{id}/feed
```

### 4. Data Model

Define major entities and access patterns.

### 5. High-Level Design

Draw components:

- Client
- CDN
- Load balancer
- API gateway
- Services
- Databases
- Cache
- Queue/stream
- Workers
- Search/indexing

### 6. Deep Dive

Pick the hard parts:

- Consistency
- Scaling
- Failure handling
- Hot partitions
- Data model
- Cache invalidation
- Queue semantics
- Rate limiting

### 7. Reliability and Operations

Discuss:

- Monitoring
- Alerts
- Rollback
- Data backup
- Disaster recovery
- Security

---

## Common FAANG-Style System Design Problems

### 1. Design URL Shortener

Core topics:

- Unique ID generation
- Base62 encoding
- Read-heavy workload
- Cache popular URLs
- DB sharding by short code
- Analytics async pipeline

Tricky part:

- Avoid collisions and handle custom aliases.

### 2. Design Twitter/X Feed

Core topics:

- Fanout on write vs fanout on read
- Celebrity users
- Timeline cache
- Ranking
- Eventual consistency
- Graph service

Tricky part:

- Hybrid fanout: precompute for normal users, pull celebrity posts at read time.

### 3. Design Uber Ride Matching

Core topics:

- Location updates
- Geospatial indexing
- Driver-rider matching
- Real-time dispatch
- Low latency
- High availability

Tricky part:

- Race conditions when multiple riders match same driver.

### 4. Design WhatsApp/Messenger

Core topics:

- WebSocket connections
- Message queues
- Offline delivery
- Ordering per conversation
- Push notifications
- End-to-end encryption

Tricky part:

- Exactly-once user-visible delivery is usually implemented with idempotent message IDs and acknowledgments, not magic network exactly-once.

### 5. Design Distributed Rate Limiter

Core topics:

- Token bucket
- Redis counters
- Sliding window
- Local + global limits
- Consistency vs latency

Tricky part:

- Strong global limits require coordination; approximate limits scale better.

### 6. Design Payment System

Core topics:

- Idempotency keys
- Ledger
- Strong consistency
- Auditability
- Reconciliation
- Webhooks
- Retries

Tricky part:

- Never model money as just updating balances without immutable ledger entries.

### 7. Design Search Autocomplete

Core topics:

- Trie or prefix index
- Ranking
- Caching
- Personalization
- Freshness

Tricky part:

- Hot prefixes like `a`, `i`, `the` need caching and precomputation.

### 8. Design Notification System

Core topics:

- Fanout
- User preferences
- Template service
- Push/email/SMS providers
- Retries and DLQ
- Rate limits

Tricky part:

- Provider may accept request but fail delivery later, so delivery tracking is async.

### 9. Design Distributed Cache

Core topics:

- Consistent hashing

- Replication
- Eviction
- TTL
- Hot keys
- Rebalancing

Tricky part:

- Node failure changes key mapping; virtual nodes reduce disruption.

### 10. Design Hotel Booking

Core topics:

- Inventory availability
- Reservation hold
- Payment
- Expiry
- Strong consistency for final booking

Tricky part:

- Availability search can be eventually consistent; booking confirmation must prevent double booking.

---

## Regular Interview Questions

### Q1: What is a distributed system?

A distributed system is a group of independent computers that communicate over a network and coordinate to appear as one system to users.

### Q2: Why are distributed systems hard?

Because failures are partial. Networks can drop, delay, duplicate, or reorder messages. Clocks differ. Nodes can crash independently. Data replicas can disagree. Retried operations can create duplicates.

### Q3: What is horizontal scaling?

Adding more machines or instances to handle more load. Stateless services scale horizontally more easily than stateful services.

### Q4: What is replication?

Replication stores copies of data on multiple nodes to improve availability, fault tolerance, and read scalability.

### Q5: What is sharding?

Sharding splits data horizontally across multiple nodes so each node owns a subset of data.

### Q6: What is eventual consistency?

Eventual consistency means replicas may temporarily disagree, but if no new writes occur, they eventually converge to the same value.

### Q7: What is CAP theorem?

During a network partition, a distributed system must choose between consistency and availability. Since partitions can happen, systems are often described as CP or AP under partition.

### Q8: What is a quorum?

A quorum is the minimum number of nodes required to perform an operation or make a decision, usually majority: `floor(N / 2) + 1`.

### Q9: What is idempotency and why is it important?

Idempotency means repeated execution has the same effect as one execution. It is important because retries can duplicate requests.

### Q10: What is a circuit breaker?

A circuit breaker prevents repeated calls to a failing dependency, allowing the system to fail fast and recover instead of cascading failure.

### Q11: What is a saga?

A saga is a sequence of local transactions across services. If a step fails, compensating actions undo previous steps where possible.

### Q12: What is the difference between queue and stream?

A queue usually delivers a message to one consumer and deletes it after acknowledgment. A stream keeps an ordered log that multiple consumers can independently read and replay.

### Q13: Why use API gateway?

API gateway centralizes routing, authentication, authorization, rate limiting, TLS termination, request transformation, and observability for client-facing APIs.

### Q14: What is service discovery?

Service discovery lets services find healthy instances of other services dynamically, often using DNS, registry, or service mesh.

### Q15: Why is shared database between microservices bad?

It tightly couples services, makes schema changes risky, bypasses service ownership, and creates hidden dependencies.

### Q16: What is CQRS?

CQRS separates write models from read models so each can be optimized independently.

### Q17: What is event sourcing?

Event sourcing stores all changes as immutable events and derives current state by replaying those events.

### Q18: What are p95 and p99 latency?

p95 means 95% of requests are faster than that value. p99 means 99% are faster. They show tail latency better than averages.

### Q19: What is backpressure?

Backpressure is a mechanism to slow producers when consumers or downstream systems cannot keep up.

### Q20: What is dead-letter queue?

A dead-letter queue stores messages that failed processing after retries so they can be inspected or reprocessed later.

---

## Tricky Interview Questions

### Q1: A client sends a payment request, the server processes it, but the client times out. Should the client retry?

Yes, but only with an idempotency key. The server should store the result for that key and return the same result on retry. Without idempotency, retrying may double-charge.

### Q2: Is exactly-once delivery possible?

Exactly-once message delivery over an unreliable network is not generally guaranteed in the simple sense. Production systems usually achieve exactly-once effects through idempotent processing, deduplication keys, transactions, and careful offset management.

### Q3: If Kafka guarantees ordering, why can messages still appear out of order?

Kafka guarantees order only within a partition. If related events are sent to different partitions, global order is not guaranteed. Retries and multiple producers can also create surprising ordering unless keys and producer settings are designed carefully.

### Q4: Why can retries make an outage worse?

Retries add extra load to an already failing dependency. If every client retries immediately, the dependency receives a retry storm and recovery becomes harder. Use exponential backoff, jitter, retry budgets, and circuit breakers.

### Q5: Why is average latency misleading?

Averages hide tail latency. A system with 50 ms average may still have many users seeing 2 second p99 latency, especially when requests fan out to many dependencies.

### Q6: In a leader-follower database, why might a user not see their own update?

The write goes to the leader, but the read is served from a follower with replication lag. Solve with read-your-writes routing, version tokens, or reading from leader for a short window.

### Q7: Can caching break correctness?

Yes. Stale cache values can expose old permissions, incorrect inventory, old prices, or outdated configuration. Critical data often needs short TTLs, explicit invalidation, or bypassing cache.

### Q8: Why is distributed locking dangerous?

Locks can expire while a process is paused, causing two owners. Network partitions can create false assumptions. Use fencing tokens and prefer designing idempotent operations when possible.

### Q9: Why is two-phase commit not common between microservices?

It blocks on coordinator failure, holds locks across services, reduces availability, and couples services tightly. Sagas and eventual consistency are often preferred.

### Q10: If a service is stateless, does it mean it has no data?

No. Stateless means the service instance does not store session-specific state locally between requests. It can still read/write external databases, caches, or queues.

### Q11: What happens if you shard by user ID in a social network feed?

User data distributes well, but celebrity users can create hot keys and fanout problems. Feed design may need hybrid fanout and special handling for high-follower accounts.

### Q12: Why can adding more servers make performance worse?

More servers can increase coordination overhead, cache misses, network traffic, lock contention, database pressure, or queue contention. Bottlenecks often move instead of disappearing.

### Q13: What is the problem with using timestamps for ordering events?

Distributed clocks are not perfectly synchronized. Clock skew can reorder events incorrectly. Use logical clocks, sequence numbers, database-generated versions, or per-key ordering through streams.

### Q14: Why is health check design tricky?

If health checks are too shallow, unhealthy instances receive traffic. If too strict, instances may be killed during transient dependency failures, causing cascading failure. Separate liveness and readiness checks.

### Q15: If Redis is down, should your system fail open or fail closed?

Depends on use case. For caching product data, fail open by reading database. For rate limiting or authorization, fail closed may be safer. Strong answers depend on risk.

### Q16: Why is global uniqueness hard at scale?

Central ID generation can become a bottleneck or single point of failure. Distributed ID generation must handle ordering, collisions, clock skew, and region/node identifiers.

### Q17: How can a database commit succeed but the caller think it failed?

The database commits, but the network response is lost or the client times out. This is why idempotency and read-after-timeout verification are important.

### Q18: Why should you avoid synchronous chains of many microservices?

They multiply latency and failure probability. One slow dependency slows the entire request. Prefer aggregation carefully, async workflows, caching, and reducing fanout.

### Q19: What if an event consumer processes an event successfully but fails before committing offset?

The event will be processed again. Consumer logic must be idempotent or store processing state transactionally with side effects.

### Q20: Why is multi-region active-active hard?

Because writes can happen concurrently in different regions, creating conflicts. Strong consistency across regions adds latency. Eventual consistency requires conflict resolution and careful user experience.

### Q21: Can a system be both highly available and strongly consistent?

Yes during normal operation, depending on design. But during a network partition, CAP says you must choose whether to preserve availability or strong consistency for affected operations.

### Q22: What is a hidden coupling in microservices?

Services may appear independent but are coupled through shared database schemas, event formats, synchronized deployments, common libraries, or undocumented behavior expectations.

### Q23: Why are distributed systems often designed for at-least-once instead of exactly-once?

At-least-once is easier and more reliable under failure. Duplicates are handled with idempotency. At-most-once risks data loss, and exactly-once is expensive and limited.

### Q24: What is the difference between deduplication and idempotency?

Deduplication detects duplicate requests/events and suppresses repeats. Idempotency makes repeat execution safe even if it reaches business logic again.

### Q25: Why can a cache with 99% hit rate still overload a database?

At very high scale, 1% miss rate can still be huge. Also synchronized expiry can create bursts. Example: 1 million RPS with 99% hit rate still means 10,000 RPS to database.

---

## Scenario-Based Questions

### Scenario 1: Design a Distributed Rate Limiter

Expected discussion:

- Token bucket or sliding window.
- Redis for centralized counters.
- Local in-memory counters for low latency.
- Approximate global limits for scale.
- Per-user, per-IP, per-API key dimensions.
- Fail open vs fail closed decision.
- Hot key mitigation for large customers.

Tricky follow-up:

> How do you rate limit across multiple regions?

Answer:

Strong global accuracy requires cross-region coordination and higher latency. Many systems use regional limits plus periodic global reconciliation, or allocate quota per region.

### Scenario 2: Design Uber Driver Location Tracking

Expected discussion:

- Drivers send location updates every few seconds.
- Use geospatial indexing such as geohash, S2, H3, or grid cells.
- Store latest location in memory/Redis-like system.
- Stream updates for analytics.
- Match riders with nearby available drivers.
- Need low latency and approximate freshness.

Tricky follow-up:

> What if two riders are matched to the same driver?

Answer:

Use a driver state transition with conditional update/compare-and-set. Only one match can change driver from `available` to `assigned`. Others retry with next candidate.

### Scenario 3: Design Payment Processing

Expected discussion:

- Idempotency key for payment creation.
- Immutable ledger.
- Payment state machine.
- External provider integration.
- Webhook handling.
- Reconciliation jobs.
- Strong consistency for ledger entries.

Tricky follow-up:

> Provider times out but later sends success webhook. What happens?

Answer:

Payment remains pending until webhook or reconciliation confirms final state. State transitions must be idempotent and monotonic so success/failure updates do not corrupt ledger.

### Scenario 4: Design Notification System

Expected discussion:

- Notification API accepts request.
- Queue for async processing.
- User preferences service.
- Template rendering.
- Provider adapters for email/SMS/push.
- Retry with backoff.
- DLQ for failures.
- Deduplication to avoid spam.

Tricky follow-up:

> How do you prevent sending the same notification twice?

Answer:

Use a deterministic notification ID or idempotency key based on user, template, event, and business entity. Store send attempts and final status.

### Scenario 5: Design Inventory Reservation

Expected discussion:

- Search availability can be eventually consistent.
- Reservation must be strongly consistent.
- Use conditional update: reserve if available quantity > 0.
- Reservation hold expires after TTL.
- Payment completion confirms reservation.
- Failed payment releases reservation.

Tricky follow-up:

> Why not just cache inventory count?

Answer:

Cache is fine for browsing, but final reservation needs authoritative consistency to avoid overselling.

### Scenario 6: Design News Feed

Expected discussion:

- Follow graph.
- Fanout on write for normal users.
- Fanout on read for celebrities.
- Timeline cache.
- Ranking service.
- Eventual consistency acceptable.
- Media stored separately in object storage/CDN.

Tricky follow-up:

> What happens when a celebrity posts?

Answer:

Do not push to millions of followers synchronously. Store celebrity post separately and merge into feed at read time or through async limited fanout.

### Scenario 7: Design Chat Messaging

Expected discussion:

- WebSocket gateway.
- Conversation service.
- Message store.
- Per-conversation ordering.
- Offline delivery.
- Push notifications.
- Read receipts.
- Idempotent client message IDs.

Tricky follow-up:

> User sends message, reconnects, and retries. How avoid duplicate messages?

Answer:

Client generates message ID. Server stores messages with unique constraint on conversation ID + client message ID. Retry returns existing message.

### Scenario 8: Design Search Indexing Pipeline

Expected discussion:

- Source database emits CDC events.
- Events go to stream.
- Indexer consumes and updates search index.
- Search is eventually consistent.
- Rebuild pipeline for full reindex.
- Dead-letter and retry handling.

Tricky follow-up:

> What if updates arrive out of order?

Answer:

Use per-entity version numbers or timestamps from authoritative source. Indexer ignores older versions.

---

## Microservices Anti-Patterns

### Distributed Monolith

Services are separate deployments but tightly coupled.

Symptoms:

- Must deploy many services together.
- Synchronous chains everywhere.
- Shared database.
- Shared domain models across services.
- One service failure breaks all flows.

### Chatty Services

One user request causes too many small service calls.

Fixes:

- API aggregation
- BFF
- Batch APIs
- Denormalized read models
- Caching

### Shared Database

Multiple services own the same schema.

Fix:

- Define ownership.
- Expose APIs/events.
- Migrate tables gradually.

### Wrong Service Boundaries

Services split by technical layer instead of business capability.

Bad:

- UserControllerService
- UserBusinessLogicService
- UserDatabaseService

Better:

- Identity service
- Billing service
- Order service
- Catalog service

### Too Much Synchronous Communication

Every service depends on every other service at request time.

Fix:

- Async events
- Local read models
- Caching
- Reduce fanout

### No Observability

Microservices without tracing and metrics are painful to debug.

Minimum requirement:

- Structured logs
- Correlation IDs
- Metrics
- Distributed tracing
- Dashboards
- Alerts

---

## Quick Revision Notes

- Distributed systems are hard because failures are partial.
- Stateless services scale more easily than stateful services.
- Tail latency matters more than average latency.
- Replication improves availability but introduces consistency tradeoffs.
- Sharding improves scale but introduces routing, rebalancing, and hot shard issues.
- Strong consistency costs coordination and latency.
- Eventual consistency improves availability and latency but complicates correctness.
- CAP matters during partitions; PACELC also considers normal latency vs consistency tradeoffs.
- Consensus is used for leader election, locks, metadata, and coordination.
- 2PC is usually avoided in microservices; sagas are more common.
- Idempotency is mandatory for reliable retries.
- Queues smooth bursts; streams support replay and multiple consumers.
- Kafka ordering is per partition, not global.
- Microservices should be split by business capability, not technical layer.
- Database-per-service improves ownership but requires eventual consistency patterns.
- API gateways handle client-facing cross-cutting concerns.
- Circuit breakers, retries, timeouts, bulkheads, and backpressure prevent cascading failure.
- Observability requires logs, metrics, and traces.
- A cache with high hit rate can still overload a database at large scale.
- Payment systems need immutable ledgers, idempotency, reconciliation, and auditability.
- Search, feeds, analytics, and notifications often accept eventual consistency.
- Inventory reservation, payments, permissions, and uniqueness often need stronger consistency.

---

## Final Interview Mindset

In senior system design interviews, there is rarely one perfect answer. Interviewers want to see whether you can reason about tradeoffs.

Good answers include:

- Clear requirements
- Reasonable scale estimates
- Explicit consistency choices
- Failure handling
- Operational concerns
- Security and observability
- Simple design first, then scale bottlenecks

When stuck, say:

> "The key tradeoff here is availability versus consistency. For this user-facing read path I would optimize for low latency and eventual consistency, but for the money/inventory/permission path I would isolate a strongly consistent workflow."

That sentence alone covers a lot of what FAANG-style interviewers are looking for.
