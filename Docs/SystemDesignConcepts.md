# System Design Concepts - Basic to Advanced

## Table of Contents

- [System Design Concepts - Basic to Advanced](#system-design-concepts---basic-to-advanced)
  - [Table of Contents](#table-of-contents)
  - [How to Read This Guide](#how-to-read-this-guide)
  - [What System Design Really Means](#what-system-design-really-means)
  - [The System Design Mindset](#the-system-design-mindset)
  - [Functional vs Non-Functional Requirements](#functional-vs-non-functional-requirements)
  - [Latency, Throughput, and Tail Latency](#latency-throughput-and-tail-latency)
    - [Average Latency](#average-latency)
    - [Percentiles](#percentiles)
  - [Scalability](#scalability)
    - [Vertical Scaling](#vertical-scaling)
    - [Horizontal Scaling](#horizontal-scaling)
    - [Scaling Compute vs Scaling Data](#scaling-compute-vs-scaling-data)
  - [Availability and Reliability](#availability-and-reliability)
  - [Fault Tolerance](#fault-tolerance)
    - [Timeout](#timeout)
    - [Retry](#retry)
    - [Circuit Breaker](#circuit-breaker)
    - [Bulkhead](#bulkhead)
    - [Graceful Degradation](#graceful-degradation)
  - [Client-Server Architecture](#client-server-architecture)
  - [DNS](#dns)
  - [CDN and Edge](#cdn-and-edge)
    - [Edge Computing](#edge-computing)
  - [Load Balancing](#load-balancing)
    - [L4 vs L7 Load Balancing](#l4-vs-l7-load-balancing)
    - [Algorithms](#algorithms)
    - [Health Checks](#health-checks)
  - [APIs](#apis)
    - [REST](#rest)
    - [gRPC](#grpc)
    - [GraphQL](#graphql)
      - [Risk 1: N+1 Backend Calls](#risk-1-n1-backend-calls)
      - [Risk 2: Query Complexity Attacks](#risk-2-query-complexity-attacks)
      - [Risk 3: Harder Caching](#risk-3-harder-caching)
      - [Risk 4: Authorization Complexity](#risk-4-authorization-complexity)
    - [Pagination](#pagination)
  - [Stateless and Stateful Services](#stateless-and-stateful-services)
  - [Synchronous and Asynchronous Processing](#synchronous-and-asynchronous-processing)
  - [Databases](#databases)
    - [Relational Databases](#relational-databases)
    - [NoSQL Databases](#nosql-databases)
    - [Database Selection Examples](#database-selection-examples)
  - [Data Modeling and Access Patterns](#data-modeling-and-access-patterns)
  - [Indexes](#indexes)
    - [Common Index Types](#common-index-types)
    - [Index Tradeoffs](#index-tradeoffs)
  - [Transactions](#transactions)
  - [Consistency](#consistency)
    - [Strong Consistency](#strong-consistency)
    - [Eventual Consistency](#eventual-consistency)
    - [Read-Your-Writes](#read-your-writes)
    - [Monotonic Reads](#monotonic-reads)
    - [Causal Consistency](#causal-consistency)
  - [CAP and PACELC](#cap-and-pacelc)
  - [Replication](#replication)
    - [Leader-Follower Replication](#leader-follower-replication)
    - [Multi-Leader Replication](#multi-leader-replication)
    - [Leaderless Replication](#leaderless-replication)
  - [Partitioning and Sharding](#partitioning-and-sharding)
    - [Hash-Based Sharding](#hash-based-sharding)
    - [Range-Based Sharding](#range-based-sharding)
    - [Geo Sharding](#geo-sharding)
    - [Hot Partitions](#hot-partitions)
  - [Caching](#caching)
    - [Cache-Aside](#cache-aside)
    - [Write-Through](#write-through)
    - [Write-Behind](#write-behind)
    - [Cache Invalidation](#cache-invalidation)
    - [Common Cache Problems](#common-cache-problems)
  - [Queues and Streams](#queues-and-streams)
    - [Queue](#queue)
    - [Stream](#stream)
    - [Delivery Semantics](#delivery-semantics)
  - [Idempotency and Retries](#idempotency-and-retries)
  - [Rate Limiting](#rate-limiting)
    - [Common Rate Limiting Algorithms Explained](#common-rate-limiting-algorithms-explained)
    - [1. Fixed Window Counter](#1-fixed-window-counter)
    - [2. Sliding Window Log](#2-sliding-window-log)
    - [3. Sliding Window Counter](#3-sliding-window-counter)
      - [Why This Is Better Than Fixed Window](#why-this-is-better-than-fixed-window)
      - [Simple Mental Picture](#simple-mental-picture)
      - [Another Example](#another-example)
    - [4. Token Bucket](#4-token-bucket)
    - [5. Leaky Bucket](#5-leaky-bucket)
    - [Token Bucket vs Leaky Bucket](#token-bucket-vs-leaky-bucket)
    - [Which Algorithm Should You Choose?](#which-algorithm-should-you-choose)
  - [Backpressure and Load Shedding](#backpressure-and-load-shedding)
  - [Search Systems](#search-systems)
    - [Inverted Index](#inverted-index)
    - [Ranking Signals](#ranking-signals)
    - [Freshness](#freshness)
  - [File and Media Storage](#file-and-media-storage)
  - [Real-Time Systems](#real-time-systems)
  - [Feed and Timeline Systems](#feed-and-timeline-systems)
    - [Fanout on Write](#fanout-on-write)
    - [Fanout on Read](#fanout-on-read)
    - [Hybrid Fanout](#hybrid-fanout)
  - [Notification Systems](#notification-systems)
  - [Payment and Ledger Systems](#payment-and-ledger-systems)
  - [Location-Based Systems](#location-based-systems)
    - [Latitude and Longitude](#latitude-and-longitude)
    - [Geohash](#geohash)
    - [S2 Cells](#s2-cells)
    - [H3 Hexagons](#h3-hexagons)
    - [Quadtrees](#quadtrees)
    - [Nearby Search](#nearby-search)
    - [Location Freshness](#location-freshness)
    - [Matching](#matching)
  - [Microservices](#microservices)
  - [Service Discovery and API Gateway](#service-discovery-and-api-gateway)
  - [Distributed Transactions and Sagas](#distributed-transactions-and-sagas)
    - [Saga](#saga)
  - [Outbox Pattern and CDC](#outbox-pattern-and-cdc)
  - [Consensus and Coordination](#consensus-and-coordination)
  - [Distributed Locks and Fencing Tokens](#distributed-locks-and-fencing-tokens)
  - [Ordering, Clocks, and Time](#ordering-clocks-and-time)
  - [Observability](#observability)
  - [Security and Privacy](#security-and-privacy)
  - [Multi-Region Design](#multi-region-design)
    - [Active-Passive](#active-passive)
    - [Active-Active](#active-active)
  - [Disaster Recovery](#disaster-recovery)
  - [Capacity Planning](#capacity-planning)
  - [Cost-Aware Design](#cost-aware-design)
  - [Common Tradeoff Patterns](#common-tradeoff-patterns)
  - [How to Think in Interviews](#how-to-think-in-interviews)

---

## How to Read This Guide

This document explains system design concepts from first principles. It is meant to be slower and more explanatory than an interview quick reference.

Use it in three passes:

1. Read the basic sections to build vocabulary.
2. Read the storage, consistency, caching, and queue sections to understand core architecture.
3. Read the advanced distributed systems sections to learn how large systems behave under failure.

System design is not about memorizing diagrams. It is about understanding tradeoffs.

---

## What System Design Really Means

System design is the process of deciding how software components work together to satisfy product requirements at a given scale.

A design usually answers these questions:

- What does the system need to do?
- How many users and requests must it handle?
- What data does it store?
- Which operations must be fast?
- Which operations must be correct?
- What happens when dependencies fail?
- How do we monitor and operate it?
- How do we keep it secure?
- How much complexity and cost are acceptable?

For a small app, the design may be simple:

```text
Client -> Server -> Database
```

For a large app, the design may include many components:

```text
Client -> DNS -> CDN -> Load Balancer -> API Services
                                      -> Cache
                                      -> Database
                                      -> Queue -> Workers
                                      -> Search Index
                                      -> Object Storage
```

The purpose of each component is to solve a specific problem. Do not add technology because it sounds advanced. Add it because the requirement needs it.

---

## The System Design Mindset

Good system design is disciplined tradeoff thinking.

You usually cannot optimize everything at once:

- Lower latency may require more caching and complexity.
- Stronger consistency may reduce availability or increase latency.
- More availability may require replication and failover.
- More durability may require extra writes and storage.
- More microservices may improve team autonomy but increase operational complexity.

The best design depends on the requirement.

For example:

- A payment system values correctness over speed.
- A social feed values low latency and availability over perfect freshness.
- A search index values fast reads but accepts delayed indexing.
- A chat system values low latency, ordering within conversations, and offline delivery.

Strong interview language:

> For this path, correctness matters more than latency, so I would keep it strongly consistent. For this other path, freshness is less critical, so eventual consistency is acceptable.

---

## Functional vs Non-Functional Requirements

Functional requirements describe what the system does.

Examples for a chat app:

- Send messages.
- Receive messages.
- Create group chats.
- Show message history.
- Send push notifications.

Non-functional requirements describe how the system behaves.

Examples:

- Low latency.
- High availability.
- Message durability.
- Security.
- Scalability.
- Observability.
- Data retention.
- Consistency guarantees.

Non-functional requirements often drive architecture more than features do.

Example:

If a chat app only needs to support 100 users, a single server and database might work. If it needs to support 500 million users globally, the system needs partitioning, replication, connection management, push notification infrastructure, monitoring, and failure recovery.

Interview mental model:

> Functional requirements define the product. Non-functional requirements define the architecture.

---

## Latency, Throughput, and Tail Latency

Latency is how long one operation takes.

Throughput is how many operations the system can handle per unit of time.

Example:

- A request that takes 120 ms has 120 ms latency.
- A service that handles 50,000 requests per second has 50,000 QPS throughput.

These are not the same thing. A system can handle many requests per second but still make some users wait too long.

### Average Latency

Average latency gives a rough idea, but it hides bad user experiences.

If 99 users get 50 ms responses and 1 user gets a 10 second response, the average may still look acceptable. But that one user had a terrible experience.

### Percentiles

Percentiles are more useful.

| Metric | Meaning |
|---|---|
| p50 | 50% of requests are faster than this. |
| p95 | 95% of requests are faster than this. |
| p99 | 99% of requests are faster than this. |

p95 and p99 are called tail latency.

Tail latency matters because large systems make many downstream calls.

```text
Request -> Service A -> Service B -> Service C -> Database
```

If any dependency is slow, the whole request becomes slow.

Common causes of tail latency:

- Cache misses
- Slow database queries
- Network retries
- Queue backlog
- Garbage collection pauses
- Lock contention
- Cold starts
- Overloaded dependency

Ways to improve latency:

- Use caching.
- Use CDN for static content.
- Add database indexes.
- Reduce network calls.
- Make independent calls in parallel.
- Move slow work to background jobs.
- Add timeouts and circuit breakers.
- Use smaller response payloads.

Interview mental model:

> Latency is user experience. Throughput is system capacity. Tail latency is what production users complain about.

---

## Scalability

Scalability means the system can handle increased load.

Load can increase in different dimensions:

- More users
- More requests per second
- More data
- More regions
- More background jobs
- More connections
- More search queries
- More writes

### Vertical Scaling

Vertical scaling means using a bigger machine.

Example:

- More CPU
- More RAM
- Faster disk
- Larger database instance

Pros:

- Simple
- No distributed coordination
- Good early-stage choice

Cons:

- Hardware limit
- Expensive at high scale
- Single failure domain

### Horizontal Scaling

Horizontal scaling means adding more machines.

Example:

```text
Load Balancer -> API Server 1
              -> API Server 2
              -> API Server 3
```

Pros:

- Scales further
- Better availability
- Can add capacity gradually

Cons:

- More operational complexity
- Requires load balancing
- Stateful systems require partitioning/replication

### Scaling Compute vs Scaling Data

Compute is usually easier to scale than data.

Stateless API servers can be copied many times. Databases are harder because they own durable state.

Interview mental model:

> Scale stateless compute horizontally. Scale stateful data with replication, partitioning, and careful access patterns.

---

## Availability and Reliability

Availability means the system is usable when users need it.

Reliability means the system continues to behave correctly over time.

Availability is often described as uptime percentage.

| Availability | Approx Downtime Per Year |
|---|---|
| 99% | 3.65 days |
| 99.9% | 8.76 hours |
| 99.99% | 52.6 minutes |
| 99.999% | 5.26 minutes |

A system can be technically up but unusable if requests timeout or return errors. So availability should be measured from the user's perspective.

Patterns that improve availability:

- Redundancy
- Replication
- Load balancing
- Health checks
- Failover
- Multi-region deployment
- Graceful degradation
- Circuit breakers
- Timeouts

Reliability requires correctness too.

Example:

A payment service that is always online but double-charges users is available but not reliable.

Interview mental model:

> Availability asks whether the system responds. Reliability asks whether it responds correctly.

---

## Fault Tolerance

Fault tolerance means the system continues working when parts fail.

Failures are normal in distributed systems:

- Server crashes
- Network timeouts
- Database failover
- Disk failure
- Bad deployments
- Queue backlog
- External provider outage
- Region outage

Common patterns:

### Timeout

Never wait forever for a dependency.

```text
API -> Payment Provider
```

If the provider does not respond in time, timeout and decide what to do next.

### Retry

Retry transient failures, but use backoff and jitter.

Bad retry behavior can overload a struggling dependency.

### Circuit Breaker

If a dependency is failing repeatedly, stop calling it temporarily.

This prevents cascading failures.

### Bulkhead

Isolate resources so one failing feature does not consume everything.

Example:

- Separate thread pool for payment calls.
- Separate queue for email jobs.
- Separate database connection pool for background jobs.

### Graceful Degradation

Keep core functionality working when optional features fail.

Examples:

- If recommendations fail, show popular items.
- If analytics fail, still process orders.
- If personalized feed fails, show cached feed.

Interview mental model:

> Design for failure before failure happens.

---

## Client-Server Architecture

The simplest architecture is:

```text
Client -> Server -> Database
```

The client sends requests. The server runs business logic. The database stores durable data.

This is enough for many small applications.

As the system grows, you add components to solve specific bottlenecks:

```text
Client
  -> DNS
  -> CDN
  -> Load Balancer
  -> API Servers
  -> Cache
  -> Database
  -> Queue
  -> Workers
  -> Object Storage
```

Each added component should have a reason:

- CDN reduces latency for static/media content.
- Load balancer distributes traffic.
- Cache reduces repeated database reads.
- Queue decouples slow work.
- Workers process background tasks.
- Object storage handles large files.

Interview mental model:

> Start simple, then add components when a requirement or bottleneck demands them.

---

## DNS

DNS maps a human-readable domain to an IP address.

Example:

```text
api.example.com -> 20.40.60.80
```

In system design, DNS can also help with:

- Geo routing
- Weighted routing
- Failover
- Blue-green deployments
- Routing users to nearest region

DNS has TTL, which controls how long clients and resolvers cache the answer.

Short TTL:

- Faster failover
- More DNS load

Long TTL:

- Less DNS load
- Slower failover

Interview mental model:

> DNS is the first routing layer users hit before reaching your application.

---

## CDN and Edge

A CDN stores content close to users.

Good CDN candidates:

- Images
- Videos
- CSS/JS
- Static pages
- Public downloadable files

Benefits:

- Lower latency
- Less origin server load
- Better global performance
- Better resilience during traffic spikes

Example:

```text
User in India -> CDN edge in India -> cached image
```

Without CDN, the user may fetch the image from a faraway region.

### Edge Computing

Edge computing runs small logic near users.

Examples:

- Redirects
- Authentication checks
- A/B routing
- Image resizing
- Request filtering

Tradeoff:

- Lower latency
- Harder debugging and deployment
- Limited runtime capabilities

Interview mental model:

> CDN caches content near users. Edge computing runs lightweight logic near users.

---

## Load Balancing

A load balancer distributes traffic across backend servers.

```text
Client -> Load Balancer -> Server 1
                        -> Server 2
                        -> Server 3
```

Why load balancers matter:

- Improve availability
- Improve scalability
- Remove unhealthy servers from traffic
- Support rolling deployments

### L4 vs L7 Load Balancing

| Type | Layer | Routes Based On |
|---|---|---|
| L4 | Transport | IP and port |
| L7 | Application | HTTP path, host, headers, cookies |

L4 is faster and simpler. L7 is more flexible.

### Algorithms

- Round robin
- Weighted round robin
- Least connections
- Least response time
- Random
- Consistent hashing

### Health Checks

Health checks decide whether an instance should receive traffic.

Liveness check:

> Is the process alive?

Readiness check:

> Can the process actually serve requests right now?

A service can be live but not ready. For example, it may be running but unable to connect to the database.

Interview mental model:

> Load balancers scale traffic, but health checks protect users from broken instances.

---

## APIs

APIs define how clients and services communicate.

Good APIs are:

- Simple
- Versioned
- Secure
- Stable
- Idempotent where needed
- Clear about errors
- Easy to paginate

### REST

REST models resources.

Example:

```http
POST /v1/orders
GET /v1/orders/{orderId}
PATCH /v1/orders/{orderId}
DELETE /v1/orders/{orderId}
```

REST is common for public APIs and CRUD-style operations.

### gRPC

gRPC uses strongly typed contracts and is common for internal service-to-service communication.

Good for:

- Low latency internal calls
- Strong schemas
- Streaming
- Polyglot services

### GraphQL

GraphQL lets clients request exactly the fields they need.

Good for:

- Frontend aggregation
- Mobile clients
- Avoiding over-fetching

Risks:

- N+1 backend calls
- Query complexity attacks
- Harder caching
- Authorization complexity

#### Risk 1: N+1 Backend Calls

GraphQL resolvers often fetch fields independently. If this is not designed carefully, one client query can accidentally create many backend/database calls.

Example query:

```graphql
query {
  users {
    id
    name
    orders {
      id
      total
    }
  }
}
```

Naive backend behavior:

```text
1 query to fetch users
1 query per user to fetch orders
```

If there are 100 users, the server may make 101 database calls. This is called the N+1 problem.

Why it is risky:

- Latency increases quickly.
- Database load increases unexpectedly.
- A harmless-looking query can become expensive at scale.
- Tail latency gets worse because many dependent calls must finish.

Common fixes:

- Batch requests using DataLoader-style batching.
- Use joins or bulk queries where appropriate.
- Preload common relationships.
- Add query planning and resolver-level performance monitoring.
- Put limits on nested collections.

Interview mental model:

> GraphQL gives clients flexibility, but the server must prevent one flexible query from becoming many hidden backend calls.

#### Risk 2: Query Complexity Attacks

GraphQL clients can send deeply nested or very broad queries.

Example risky query:

```graphql
query {
  users {
    posts {
      comments {
        author {
          followers {
            posts {
              comments {
                id
              }
            }
          }
        }
      }
    }
  }
}
```

Even if the query is valid, it may require huge amounts of CPU, memory, database work, or service calls.

Why it is risky:

- Attackers can create expensive queries cheaply.
- One request can consume too many backend resources.
- Deep recursion can overload services.
- It is harder to reason about cost than fixed REST endpoints.

Common fixes:

- Limit query depth.
- Limit query breadth.
- Assign cost scores to fields and reject expensive queries.
- Require pagination on list fields.
- Set server-side timeouts.
- Use persisted queries for public clients.
- Apply rate limits based on query cost, not only request count.

Interview mental model:

> In GraphQL, not all requests cost the same. Rate limiting only by request count is not enough.

#### Risk 3: Harder Caching

REST endpoints often map naturally to cache keys.

Example:

```http
GET /v1/products/123
```

This can be cached by URL, CDN, browser, gateway, or reverse proxy.

GraphQL usually sends many different queries to one endpoint:

```http
POST /graphql
```

Two clients may request the same object with different fields:

```graphql
query {
  product(id: "123") {
    id
    name
  }
}
```

```graphql
query {
  product(id: "123") {
    id
    name
    price
    reviews {
      rating
    }
  }
}
```

Why it is risky:

- CDN caching is less straightforward.
- Cache keys may need to include query text, variables, auth context, and selected fields.
- Personalized fields can make shared caching unsafe.
- Partial object updates are harder to invalidate correctly.

Common fixes:

- Use normalized client-side caching.
- Use persisted queries with stable IDs.
- Cache at resolver/data-loader layer.
- Cache common read-only queries.
- Keep authorization-sensitive data out of shared caches.
- Use clear TTL and invalidation strategies.

Interview mental model:

> REST often caches by URL. GraphQL often needs caching by query shape, variables, identity, and object identity.

#### Risk 4: Authorization Complexity

GraphQL lets clients choose fields and relationships. That means authorization cannot only happen at the endpoint level.

Example:

```graphql
query {
  user(id: "123") {
    id
    name
    email
    salary
    managerNotes
  }
}
```

A user may be allowed to see `name`, but not `salary` or `managerNotes`.

Why it is risky:

- Field-level permissions are easy to miss.
- Nested objects may expose data through indirect paths.
- One query can combine public and sensitive fields.
- Different clients may need different authorization rules.
- Shared resolver code can accidentally bypass business rules.

Common fixes:

- Enforce authorization at resolver/field level.
- Centralize permission checks.
- Use schema directives or middleware for auth rules.
- Avoid exposing sensitive fields unless needed.
- Test nested authorization paths.
- Include user/tenant context in every resolver.
- Log access to sensitive fields.

Interview mental model:

> GraphQL authorization must protect fields and relationships, not just endpoints.

### Pagination

Offset pagination:

```http
GET /posts?offset=100&limit=20
```

Cursor pagination:

```http
GET /posts?cursor=abc123&limit=20
```

Cursor pagination is usually better for large or frequently changing datasets.

Interview mental model:

> API design should match access patterns and failure behavior, not just expose database tables.

---

## Stateless and Stateful Services

A stateless service does not store important state locally between requests.

Example:

```text
Request -> any API server -> cache/database
```

Any server can handle the next request.

Stateless services are easy to scale horizontally.

A stateful service owns or depends on durable/local state.

Examples:

- Database
- Cache cluster
- Queue broker
- Search index
- WebSocket gateway with active connections

Stateful systems are harder because they require:

- Replication
- Backup
- Failover
- Rebalancing
- Consistency handling

Interview mental model:

> Keep application servers stateless where possible. Treat state as the hard part of system design.

---

## Synchronous and Asynchronous Processing

Synchronous processing means the caller waits.

Example:

```text
Client -> API -> Database -> Response
```

Use synchronous processing when the user needs an immediate result.

Asynchronous processing means the system accepts work now and finishes it later.

Example:

```text
Client -> API -> Queue -> Worker
Client receives response before worker finishes
```

Use async processing for:

- Email
- Push notification
- Image processing
- Video transcoding
- Search indexing
- Analytics
- Webhook delivery
- Long-running external calls

Tradeoffs:

| Processing | Pros | Cons |
|---|---|---|
| Synchronous | Simple, immediate answer | Higher latency, tighter coupling |
| Asynchronous | Scalable, resilient | Eventual consistency, duplicates, harder debugging |

Interview mental model:

> Keep user-critical decisions synchronous. Move slow or non-critical side effects asynchronous.

---

## Databases

Databases store durable data.

The database choice depends on access patterns, consistency needs, scale, and data model.

### Relational Databases

Examples:

- PostgreSQL
- MySQL
- SQL Server
- Oracle

Good for:

- Transactions
- Strong consistency
- Joins
- Constraints
- Relational data
- Financial records

### NoSQL Databases

NoSQL is a broad category.

Common types:

| Type | Examples | Good For |
|---|---|---|
| Key-value | Redis, DynamoDB | Fast lookup by key |
| Document | MongoDB, Cosmos DB | Flexible JSON-like documents |
| Wide-column | Cassandra, HBase | High write throughput, large scale |
| Graph | Neo4j | Relationship-heavy queries |
| Time-series | InfluxDB, TimescaleDB | Metrics/events over time |

### Database Selection Examples

| Use Case | Common Choice |
|---|---|
| Payment ledger | Relational database |
| User sessions | Redis/key-value store |
| Product catalog | Document or relational DB |
| Search | Elasticsearch/OpenSearch |
| Analytics | Columnar warehouse |
| Chat messages | Partitioned relational, document, or wide-column DB |
| Metrics | Time-series DB |

Interview mental model:

> Choose storage based on query patterns and correctness requirements, not popularity.

---

## Data Modeling and Access Patterns

Data modeling means deciding what entities exist and how they are stored.

Access patterns mean how the application reads and writes that data.

Example for a feed system:

Entities:

- User
- Post
- Follow
- Like
- TimelineEntry

Access patterns:

- Get posts by user.
- Get feed for user.
- Add new post.
- Fan out post to followers.
- Count likes.

Good data design starts with queries.

Questions to ask:

- What are the most frequent reads?
- What are the most frequent writes?
- What must be strongly consistent?
- What can be eventually consistent?
- What indexes are needed?
- What is the partition key?
- How will data grow?

Interview mental model:

> Design schema from access patterns. Do not design tables in isolation.

---

## Indexes

An index is an additional data structure that makes reads faster.

Without an index, the database may scan many rows.

```sql
SELECT * FROM orders WHERE user_id = 123;
```

With an index:

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

The database can find matching rows faster.

### Common Index Types

| Index | Good For |
|---|---|
| B-tree | Equality, range queries, sorting |
| Hash | Exact key lookup |
| Inverted | Full-text search |
| Composite | Queries filtering by multiple columns |
| Geospatial | Nearby/location queries |

### Index Tradeoffs

Pros:

- Faster reads
- Faster filters
- Faster sorting

Cons:

- Slower writes
- Extra storage
- Index maintenance
- Bad indexes may not be used

Composite index order matters.

Example:

```sql
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);
```

This helps queries by `user_id` and `created_at`, especially retrieving recent orders for a user.

Interview mental model:

> If you propose a query, explain the index that makes it fast.

---

## Transactions

A transaction groups multiple operations into one logical unit.

Classic transaction properties are ACID:

| Property | Meaning |
|---|---|
| Atomicity | All operations succeed or none do. |
| Consistency | Database constraints remain valid. |
| Isolation | Concurrent transactions do not corrupt each other. |
| Durability | Committed data survives failure. |

Example:

Transferring money from account A to account B:

```text
Debit A
Credit B
Commit both together
```

You cannot debit one account and fail to credit the other.

Transactions are easy inside one database. They become harder across services or databases.

Interview mental model:

> Use transactions for correctness-critical state changes inside one service boundary. Be cautious with distributed transactions.

---

## Consistency

Consistency describes what readers are allowed to see after writes.

### Strong Consistency

Reads see the latest committed write.

Use for:

- Payments
- Inventory reservation
- Account balance
- Password changes
- Authorization
- Unique username/email

### Eventual Consistency

Replicas or derived views may temporarily disagree but converge later.

Use for:

- Search indexing
- Feeds
- Like counts
- View counts
- Analytics
- Recommendations
- Notifications

### Read-Your-Writes

A user sees their own updates immediately, even if other users may see them later.

Example:

After changing profile photo, the user should see the new photo on refresh.

### Monotonic Reads

Once a user sees a newer value, they should not later see an older value.

### Causal Consistency

Related events are observed in cause-and-effect order.

Example:

If a reply depends on a comment, users should not see the reply before the original comment.

Interview mental model:

> Use the weakest consistency model that still preserves product correctness.

---

## CAP and PACELC

CAP applies when there is a network partition.

It says a distributed system must choose between:

- Consistency
- Availability

Partition tolerance is not optional because networks fail.

So the practical CAP question is:

> During a partition, should the system reject requests to preserve correctness, or accept requests and reconcile later?

Examples:

| System Path | Better Choice |
|---|---|
| Payment transfer | Consistency |
| Inventory booking | Consistency |
| Feed read | Availability |
| Like count | Availability |
| Search | Availability |

PACELC extends CAP:

- If partition happens, choose availability or consistency.
- Else, choose latency or consistency.

This is more practical because even without failures, stronger consistency can increase latency.

Interview mental model:

> CAP is about behavior during partitions. PACELC also reminds you that latency vs consistency is a normal-day tradeoff.

---

## Replication

Replication means keeping copies of data on multiple nodes.

Why replicate?

- Fault tolerance
- Read scaling
- Lower regional latency
- Disaster recovery

### Leader-Follower Replication

```text
Writes -> Leader -> Followers
Reads  -> Leader or Followers
```

Pros:

- Simple write path
- Followers can serve reads

Cons:

- Leader can be bottleneck
- Failover required
- Followers can lag

### Multi-Leader Replication

Multiple nodes accept writes.

Pros:

- Better write availability
- Useful across regions

Cons:

- Conflicts
- Harder consistency

### Leaderless Replication

Any replica can accept reads/writes. Systems often use quorums.

Example:

```text
N = 3 replicas
W = 2 write acknowledgements
R = 2 read acknowledgements
```

If `R + W > N`, reads and writes overlap, improving consistency.

Interview mental model:

> Replication improves availability and read scale, but introduces lag, failover, and conflict handling.

---

## Partitioning and Sharding

Partitioning splits data into smaller pieces.

Sharding usually means storing those pieces across different machines.

Why shard?

- Dataset is too large for one machine.
- Write traffic is too high for one database.
- Read traffic needs distribution.

### Hash-Based Sharding

```text
shard = hash(user_id) % number_of_shards
```

Pros:

- Even distribution if key is good

Cons:

- Rebalancing can be hard
- Range queries are difficult

### Range-Based Sharding

```text
Shard 1: user_id 1-1M
Shard 2: user_id 1M-2M
```

Pros:

- Range queries are easier

Cons:

- Hot ranges possible

### Geo Sharding

Store data by region.

Pros:

- Lower latency
- Data residency support

Cons:

- Cross-region queries harder
- Users moving regions complicates data placement

### Hot Partitions

A hot partition receives too much traffic.

Examples:

- Celebrity account
- Viral video
- Popular product
- Current timestamp bucket

Solutions:

- Cache hot data
- Split hot keys
- Add random suffixes
- Use adaptive partitioning
- Special-case high-volume users/items

Interview mental model:

> The shard key determines your future bottlenecks. Choose it carefully.

---

## Caching

A cache is a fast temporary copy of data.

Common cache locations:

- Browser
- CDN
- API gateway
- Application memory
- Redis/Memcached
- Database buffer cache

### Cache-Aside

```text
API checks cache
If missing, API reads database
API stores value in cache
API returns value
```

Good for read-heavy data.

### Write-Through

Write goes to cache and database together.

Simplifies reads but increases write latency.

### Write-Behind

Write goes to cache first, then database later.

Fast but risky if cache fails before persistence.

### Cache Invalidation

Invalidation strategies:

- TTL
- Delete on write
- Update on write
- Versioned keys
- Event-driven invalidation

### Common Cache Problems

| Problem | Meaning | Fix |
|---|---|---|
| Cache penetration | Missing keys repeatedly hit DB | Cache nulls, Bloom filter |
| Cache breakdown | Hot key expires and many requests hit DB | Locking, singleflight, early refresh |
| Cache avalanche | Many keys expire together | TTL jitter, staggered expiry |
| Hot key | One key receives huge traffic | Replicate, local cache, split key |

Cache is dangerous for correctness-critical data.

Interview mental model:

> Caching improves latency and reduces load, but creates staleness and invalidation problems.

---

## Queues and Streams

Queues and streams decouple producers from consumers.

### Queue

A queue usually sends each message to one consumer.

Use for:

- Background jobs
- Email sending
- Image processing
- Retryable tasks

Examples:

- SQS
- RabbitMQ
- Azure Service Bus

### Stream

A stream is an append-only event log. Multiple consumers can read the same events.

Use for:

- Analytics
- Event sourcing
- CDC
- Audit logs
- Multiple downstream consumers

Examples:

- Kafka
- Kinesis
- Event Hubs
- Pulsar

### Delivery Semantics

| Semantics | Meaning |
|---|---|
| At-most-once | Message may be lost, but not duplicated. |
| At-least-once | Message is not lost, but duplicates are possible. |
| Exactly-once effect | Achieved with idempotency, dedupe, and transactions. |

Interview mental model:

> Queues smooth spikes and isolate failures, but introduce delay, duplicates, and eventual consistency.

---

## Idempotency and Retries

Retries happen because networks fail.

But retries can duplicate side effects.

Example:

1. Client sends payment request.
2. Server charges card successfully.
3. Response is lost.
4. Client retries.
5. Without idempotency, card may be charged twice.

Idempotency means repeating an operation has the same effect as doing it once.

Example:

```http
POST /v1/payments
Idempotency-Key: payment-123
```

The server stores the result for that key and returns the same result on retry.

Use idempotency for:

- Payment creation
- Order creation
- Booking
- Message send
- Notification send
- Webhook processing

Retry best practices:

- Use timeouts.
- Retry only transient failures.
- Use exponential backoff.
- Add jitter.
- Set retry limits.
- Make writes idempotent.

Interview mental model:

> If a write can be retried, design it to be idempotent.

---

## Rate Limiting

Rate limiting controls how many requests an identity can make.

Identity can be:

- User ID
- IP address
- API key
- Tenant ID
- Device ID

Common algorithms:

| Algorithm | Explanation |
|---|---|
| Fixed window | Count requests in fixed intervals. Simple but bursty. |
| Sliding window log | Store timestamps. Accurate but memory-heavy. |
| Sliding window counter | Approximation with less memory. |
| Token bucket | Tokens refill over time. Allows bursts. |
| Leaky bucket | Requests drain at fixed rate. Smooths traffic. |

### Common Rate Limiting Algorithms Explained

Rate limiting algorithms decide two things:

- How requests are counted.
- When a request should be allowed or rejected.

Assume the rule is:

```text
Allow 100 requests per user per minute
```

Different algorithms enforce this rule differently.

### 1. Fixed Window Counter

Fixed window counts requests in fixed time buckets.

Example:

```text
10:00:00 - 10:00:59 -> allow up to 100 requests
10:01:00 - 10:01:59 -> allow up to 100 requests
```

Simple implementation idea:

```text
key = user_id + current_minute
increment counter
if counter > limit, reject request
```

Example:

```text
User sends 100 requests at 10:00:59
User sends 100 requests at 10:01:00
```

Technically the user stayed within each minute's limit, but they sent 200 requests in 2 seconds. This is the **boundary burst problem**.

Pros:

- Very simple.
- Fast.
- Easy to store in Redis or memory.
- Good for basic API protection.

Cons:

- Bursty at window boundaries.
- Not smooth.
- Can allow more traffic than expected around boundaries.

Use when:

- Simplicity matters more than precision.
- Small bursts are acceptable.
- You need an easy first version.

Interview mental model:

> Fixed window is simple, but users can burst at the boundary between two windows.

### 2. Sliding Window Log

Sliding window log stores timestamps of recent requests.

For every request:

1. Remove timestamps older than the window.
2. Count remaining timestamps.
3. If count is below limit, allow request and store current timestamp.
4. Otherwise, reject.

Example rule:

```text
Allow 100 requests in the last 60 seconds
```

If current time is `10:01:30`, check requests from:

```text
10:00:30 - 10:01:30
```

This avoids the fixed-window boundary burst because the window moves continuously.

Pros:

- Accurate.
- Prevents boundary burst problem.
- Easy to reason about.

Cons:

- Memory-heavy because every request timestamp may be stored.
- Expensive for high-traffic users.
- Cleanup of old timestamps is required.

Use when:

- Accuracy matters.
- Request volume per identity is not extremely high.
- You need exact rolling-window behavior.

Interview mental model:

> Sliding window log is accurate but stores too much data at high scale.

### 3. Sliding Window Counter

Sliding window counter is a memory-efficient approximation of the sliding window log.

The problem with sliding window log is that it stores every request timestamp. Sliding window counter avoids that by storing only two numbers:

- Request count in the current fixed window.
- Request count in the previous fixed window.

Then it estimates how much of the previous window should still count.

Example rule:

```text
Allow 100 requests in the last 60 seconds
```

Suppose the current time is:

```text
10:01:15
```

The real sliding window is the last 60 seconds:

```text
10:00:15 - 10:01:15
```

That real window overlaps with:

```text
Previous fixed window: 10:00:00 - 10:00:59
Current fixed window:  10:01:00 - 10:01:59
```

At `10:01:15`, only 15 seconds of the current minute have passed. That means the last 60 seconds includes:

```text
45 seconds from previous window: 10:00:15 - 10:00:59
15 seconds from current window:  10:01:00 - 10:01:15
```

So we count:

- All requests in the current window so far.
- Only part of the previous window's requests.

Since 45 out of 60 seconds from the previous window still overlap, we count about 75% of the previous window.

Approximate count:

```text
effective_count = current_window_count + previous_window_count * previous_window_weight
```

Example:

```text
current_window_count = 30
previous_window_count = 80
previous_window_weight = 45 / 60 = 0.75

effective_count = 30 + 80 * 0.75 = 90
```

Since 90 is below 100, allow the request.

If the effective count were above 100, reject the request.

#### Why This Is Better Than Fixed Window

Fixed window can allow a big burst around the minute boundary:

```text
100 requests at 10:00:59
100 requests at 10:01:00
```

Sliding window counter smooths this by saying:

> We are just inside the new minute, so most of the previous minute should still count.

That means the second burst is more likely to be rejected.

#### Simple Mental Picture

Imagine a 60-second ruler sliding across time:

```text
Real window: [10:00:15 ---------------------- 10:01:15]

Previous minute: [10:00:00 -------- 10:00:59]
Current minute:                         [10:01:00 -------- 10:01:59]
```

The ruler covers part of the previous minute and part of the current minute. Sliding window counter estimates the request count by weighting the covered part of the previous minute.

#### Another Example

Current time:

```text
10:01:45
```

Real last-60-second window:

```text
10:00:45 - 10:01:45
```

This includes:

```text
15 seconds from previous window
45 seconds from current window
```

So previous window weight is:

```text
15 / 60 = 0.25
```

If:

```text
previous_window_count = 80
current_window_count = 50
```

Then:

```text
effective_count = 50 + 80 * 0.25 = 70
```

So the request is allowed because 70 is below 100.

Pros:

- Much less memory than sliding window log.
- Smoother than fixed window.
- Good balance of accuracy and efficiency.

Cons:

- Approximate, not exact.
- More complex than fixed window.
- Can still allow small inaccuracies.

Use when:

- You want better smoothness than fixed window.
- You do not want to store every request timestamp.
- Approximate limits are acceptable.

Interview mental model:

> Sliding window counter is the practical middle ground between fixed window simplicity and sliding log accuracy.

### 4. Token Bucket

Token bucket uses tokens that refill over time.

Each request consumes one token. If tokens are available, the request is allowed. If the bucket is empty, the request is rejected or delayed.

Example:

```text
Bucket capacity = 100 tokens
Refill rate = 10 tokens/second
Each request costs 1 token
```

If the user is idle, tokens accumulate up to the bucket capacity. This allows a short burst later.

Flow:

```text
Request arrives
Refill tokens based on elapsed time
If tokens >= request cost:
  allow request and subtract token
Else:
  reject or throttle request
```

Example:

```text
User is idle for a while -> bucket fills to 100
User sends 50 quick requests -> allowed
Bucket now has 50 tokens
Tokens continue refilling at 10/second
```

Pros:

- Allows controlled bursts.
- Good for APIs where bursts are normal.
- Efficient memory usage.
- Flexible because different requests can cost different token amounts.

Cons:

- More complex than fixed window.
- Burst size must be chosen carefully.
- If bucket is too large, bursts may overload backend systems.

Use when:

- You want to allow bursts but control long-term rate.
- API clients may send traffic unevenly.
- You need a common production-grade rate limiter.

Interview mental model:

> Token bucket allows bursts while enforcing an average rate over time.

### 5. Leaky Bucket

Leaky bucket smooths traffic into a steady output rate.

Think of requests entering a bucket, and the bucket leaking at a constant rate.

Example:

```text
Requests arrive quickly
Bucket queues them
System processes 10 requests/second
If bucket is full, extra requests are rejected
```

Flow:

```text
Request arrives
If queue/bucket has space:
  enqueue request
Else:
  reject request

Worker drains queue at fixed rate
```

Pros:

- Smooths bursts.
- Protects backend with steady request rate.
- Useful when downstream systems need stable traffic.

Cons:

- Adds queueing delay.
- Not ideal when users expect immediate response.
- Bucket/queue size must be tuned carefully.

Use when:

- Downstream systems need stable load.
- You want traffic shaping, not just request rejection.
- You can tolerate some queueing delay.

Interview mental model:

> Leaky bucket turns bursty input into smooth output, but it may add latency.

### Token Bucket vs Leaky Bucket

These two are easy to confuse.

| Concept | Token Bucket | Leaky Bucket |
|---|---|---|
| Main idea | Tokens refill over time; requests spend tokens. | Requests enter a queue/bucket and drain at fixed rate. |
| Burst behavior | Allows bursts up to bucket capacity. | Smooths bursts into steady output. |
| User experience | Burst requests can be served immediately if tokens exist. | Requests may wait in queue. |
| Best for | Public APIs and client quotas. | Traffic shaping and backend protection. |
| Risk | Large bucket can allow too much burst. | Queueing can increase latency. |

Quick memory trick:

```text
Token bucket controls permission to send.
Leaky bucket controls the rate of processing.
```

### Which Algorithm Should You Choose?

| Requirement | Good Choice |
|---|---|
| Simplest implementation | Fixed window |
| Accurate rolling limit | Sliding window log |
| Balanced accuracy and memory | Sliding window counter |
| Allow controlled bursts | Token bucket |
| Smooth traffic to backend | Leaky bucket |
| Distributed approximate limit | Local counters, per-region quota, or token leasing |
| Strict global limit | Central store such as Redis, with latency/availability tradeoff |

Distributed rate limiting is harder because many servers make decisions at the same time.

Options:

- Central Redis counter
- Local counters with sync
- Per-region quota
- Token leasing
- Approximate limits

Important question:

> If the rate limiter is unavailable, do we fail open or fail closed?

Fail open protects availability but allows abuse. Fail closed protects backend systems but may block legitimate users.

Interview mental model:

> Exact global rate limits cost latency and availability. Approximate local limits often scale better.

---

## Backpressure and Load Shedding

Backpressure means telling upstream systems to slow down because downstream systems cannot keep up.

Examples:

- Queue depth is growing.
- Database connection pool is exhausted.
- Worker CPU is saturated.
- External provider is rate limiting requests.

Without backpressure, the system keeps accepting work until it fails badly.

Load shedding means intentionally rejecting or dropping lower-priority work to protect the core system.

Examples:

- Reject non-critical analytics writes.
- Disable recommendations temporarily.
- Return cached/stale results.
- Drop low-priority background jobs.
- Return 429 or 503 before total overload.

Interview mental model:

> It is better to reject some work cleanly than accept everything and fail everything.

---

## Search Systems

Search systems usually use a separate search index.

Basic flow:

```text
Primary DB -> CDC/Queue -> Indexer -> Search Index -> Search API
```

The primary database is usually the source of truth. The search index is a derived copy.

### Inverted Index

An inverted index maps terms to documents.

```text
system -> doc1, doc5, doc8
design -> doc1, doc2, doc9
```

### Ranking Signals

- Text relevance
- Recency
- Popularity
- Personalization
- Location
- Business rules

### Freshness

Search is often eventually consistent. A new product/post/file may take seconds to appear.

For strict deletion or privacy requirements, use tombstones or query-time permission filtering.

Interview mental model:

> Search is optimized for retrieval and ranking, not as the authoritative source of truth.

---

## File and Media Storage

Large files should usually live in object storage, not a relational database.

Examples:

- Images
- Videos
- PDFs
- Backups
- User uploads

Common upload flow:

```text
Client -> API asks for upload URL
API -> returns pre-signed URL
Client -> uploads file to object storage
Storage event -> Queue -> Processing workers
Workers -> thumbnails/transcoding/virus scan
Metadata DB -> updated
CDN -> serves content
```

Concepts:

- Object storage
- Pre-signed URL
- Multipart upload
- Chunking
- Deduplication
- Metadata database
- CDN
- Transcoding
- Virus scanning

Interview mental model:

> Store file bytes in object storage. Store file metadata in a database.

---

## Real-Time Systems

Real-time systems deliver updates quickly.

Examples:

- Chat
- Live comments
- Collaborative editing
- Stock ticker
- Driver tracking
- Multiplayer games

Transport options:

| Option | Best For |
|---|---|
| Polling | Simple, infrequent updates |
| Long polling | Near real-time without persistent socket complexity |
| Server-Sent Events | Server-to-client updates |
| WebSocket | Bi-directional communication |
| WebRTC | Peer-to-peer audio/video/data |

Challenges:

- Connection management
- Reconnects
- Ordering
- Presence
- Offline delivery
- Fanout
- Backpressure
- Multi-region routing

Interview mental model:

> Real-time design is mostly about connection state, ordering, fanout, and failure recovery.

---

## Feed and Timeline Systems

Feeds show ranked content to users.

Examples:

- Twitter/X timeline
- Instagram feed
- LinkedIn feed
- TikTok recommendations

### Fanout on Write

When a user posts, push the post ID into followers' timelines.

Pros:

- Fast reads

Cons:

- Expensive writes for users with many followers

### Fanout on Read

When a user opens feed, fetch recent posts from followed users.

Pros:

- Cheap writes

Cons:

- Slow reads for users following many accounts

### Hybrid Fanout

Use fanout-on-write for normal users and fanout-on-read for celebrities.

This is common in interviews.

Interview mental model:

> Feed systems trade write amplification against read latency.

---

## Notification Systems

Notifications send messages through push, email, SMS, or in-app channels.

Basic architecture:

```text
Producer -> Notification API -> Queue -> Workers -> Provider
                              -> Preferences Service
                              -> Template Service
```

Important concepts:

- User preferences
- Templates
- Rate limits
- Deduplication
- Retry with backoff
- Dead-letter queue
- Provider failover
- Delivery tracking
- Quiet hours

Notifications are usually asynchronous. The user action should not wait for email/SMS/push delivery unless the notification is core to the flow.

Interview mental model:

> Notification systems are queue-heavy because providers fail, users have preferences, and retries must be controlled.

---

## Payment and Ledger Systems

Payment systems value correctness, auditability, and reconciliation.

Key concepts:

- Idempotency key
- Immutable ledger
- Double-entry accounting
- Payment state machine
- Provider adapter
- Webhook handling
- Reconciliation
- Audit log

Payment state example:

```text
created -> authorized -> captured -> settled
        -> failed
        -> refunded
```

Never design payments as only updating a balance field.

Use ledger entries so every movement of money is recorded.

Example:

```text
Debit buyer account
Credit merchant pending account
Later: move pending to settled
```

External providers can timeout, return delayed webhooks, or send duplicate callbacks. The system must handle all of these safely.

Interview mental model:

> Payment design is about idempotency, immutable records, state transitions, and reconciliation.

---

## Location-Based Systems

Location systems power apps like Uber, DoorDash, and maps.

Core concepts:

- Latitude/longitude
- Geohash
- S2 cells
- H3 hexagons
- Quadtrees
- Nearby search
- Location freshness
- Matching

### Latitude and Longitude

Latitude and longitude represent a point on Earth.

```text
Latitude  -> north/south position
Longitude -> east/west position
```

Example:

```text
New York City: latitude 40.7128, longitude -74.0060
```

In location-based systems, every moving entity usually reports coordinates:

- Driver location
- Rider pickup location
- Restaurant location
- Delivery partner location
- Vehicle location
- Store location

Basic distance between two coordinates can be calculated using the Haversine formula, which accounts for the Earth being spherical.

In interviews, you usually do not need to derive the formula. It is enough to say:

> I would use a geo-distance calculation such as Haversine for accurate distance after narrowing candidates with a spatial index.

Important detail:

Distance calculation alone is not enough at scale.

If there are 10 million drivers, you cannot calculate distance from the rider to every driver for every request. You first need a way to find nearby candidates quickly.

Interview mental model:

> Latitude and longitude tell you where something is. Spatial indexing helps you find nearby things efficiently.

### Geohash

Geohash converts latitude and longitude into a string.

Nearby locations often share the same geohash prefix.

Example:

```text
Location A -> 9q8yyk
Location B -> 9q8yym
```

Both start with `9q8y`, so they are likely geographically close.

Think of geohash as dividing the world into rectangular grid cells. Longer geohashes represent smaller cells.

Example:

| Geohash Length | Meaning |
|---|---|
| Short prefix | Large area |
| Long prefix | Smaller, more precise area |

How it helps nearby search:

1. Convert rider location to geohash.
2. Find drivers in the same geohash cell.
3. Also check neighboring cells.
4. Calculate exact distance only for those candidates.

Why neighboring cells matter:

A rider may be near the edge of a cell. The closest driver may be in the adjacent cell, not the same cell.

Example:

```text
Cell A | Cell B
Rider  | Driver
```

Even though rider and driver are close, they are in different cells. So nearby search must check adjacent cells too.

Pros:

- Simple to store as a string.
- Works well with prefix queries.
- Easy to use in databases and caches.
- Good for approximate nearby lookup.

Cons:

- Grid cells are rectangular and may not match real-world movement.
- Cell boundaries can cause edge cases.
- Precision must be tuned carefully.

Use when:

- You need a simple geospatial indexing strategy.
- You want to group locations by approximate area.
- You want prefix-based lookup in a database or key-value store.

Interview mental model:

> Geohash turns coordinates into searchable grid prefixes. Search the current cell plus nearby cells, then calculate exact distance.

### S2 Cells

S2 is a geometry library that divides the Earth into hierarchical cells.

Instead of treating the Earth as a flat rectangle, S2 models it more naturally on a sphere.

The world is divided into cells at different levels:

```text
Low level number  -> large cells
High level number -> small cells
```

S2 cells are useful because they provide stable cell IDs for geographic areas.

Example use cases:

- Find drivers near a rider.
- Group restaurants by delivery region.
- Route users to regional services.
- Apply surge pricing by area.
- Aggregate demand heatmaps.

How nearby search works with S2:

1. Convert rider coordinates to an S2 cell.
2. Get nearby S2 cells that cover the search radius.
3. Fetch candidate drivers from those cells.
4. Filter candidates by exact distance and availability.

Why S2 is popular:

- Designed for spherical geometry.
- Supports hierarchical cells.
- Good for covering circular or polygon regions.
- Useful for large-scale geospatial systems.

Tradeoff:

S2 is more powerful than geohash, but also more complex to explain and implement.

Interview mental model:

> S2 divides the Earth into hierarchical spherical cells, making it useful for accurate large-scale geospatial indexing.

### H3 Hexagons

H3 is a hexagonal geospatial indexing system.

It divides the world into hexagon-shaped cells at different resolutions.

Hexagons are useful because each cell has roughly uniform neighbors. This makes them good for area-based analysis.

Example use cases:

- Uber-style demand heatmaps.
- Surge pricing zones.
- Delivery coverage zones.
- Supply-demand balancing.
- City-level analytics.

Why hexagons are nice:

- Each hexagon has clear neighboring hexagons.
- Distance between neighboring cells is more uniform.
- Good for visualizing regional demand.
- Good for aggregating metrics by area.

Example:

```text
For each ride request:
  convert pickup location to H3 cell
  increment demand counter for that cell

For each available driver:
  convert driver location to H3 cell
  increment supply counter for that cell
```

Then the system can compare demand and supply per area:

```text
high demand + low supply -> possible surge pricing
low demand + high supply -> reposition drivers
```

H3 is often better for analytics and area aggregation than exact nearest-neighbor lookup.

Interview mental model:

> H3 is great for grouping the world into hexagonal regions for analytics, heatmaps, pricing, and supply-demand balancing.

### Quadtrees

A quadtree is a tree data structure for indexing two-dimensional space.

It repeatedly divides an area into four smaller quadrants.

Example:

```text
Whole city
  -> northwest quadrant
  -> northeast quadrant
  -> southwest quadrant
  -> southeast quadrant
```

If one quadrant has too many points, divide it again.

This is useful because dense areas get smaller partitions, while sparse areas stay larger.

Example:

```text
Downtown: many drivers -> split into smaller cells
Rural area: few drivers -> keep large cell
```

Nearby search with a quadtree:

1. Start at the root area.
2. Traverse only quadrants that overlap the search radius.
3. Collect candidate drivers from matching quadrants.
4. Calculate exact distance for candidates.

Pros:

- Adapts well to uneven density.
- Good for two-dimensional spatial search.
- Can reduce unnecessary distance checks.

Cons:

- More complex to maintain with frequent moving updates.
- Rebalancing may be needed.
- Distributed quadtrees can be harder than static in-memory examples.

Use when:

- The area has uneven density.
- You need efficient spatial range queries.
- You can manage updates and partitioning complexity.

Interview mental model:

> Quadtrees split busy areas more deeply, so dense regions get finer indexing than sparse regions.

### Nearby Search

Nearby search means finding entities close to a given location.

Examples:

- Find drivers near a rider.
- Find restaurants near a customer.
- Find stores within 5 km.
- Find charging stations near a vehicle.

Naive approach:

```text
For every driver:
  calculate distance from rider
  sort by distance
  pick nearest drivers
```

This does not scale because every request scans too many entities.

Scalable approach:

```text
Rider location
  -> convert to spatial cell
  -> fetch candidates from nearby cells
  -> filter by exact distance
  -> rank by ETA, distance, rating, availability, or business rules
```

Typical nearby search flow:

```text
1. Receive rider pickup location.
2. Convert pickup coordinates to geohash/S2/H3 cell.
3. Search current cell and neighboring cells.
4. Fetch available drivers from those cells.
5. Remove stale or unavailable drivers.
6. Calculate actual distance or ETA.
7. Rank candidates.
8. Try to reserve the best driver atomically.
```

Distance is not always enough.

In ride matching, the nearest driver by straight-line distance may not be the fastest driver because roads, traffic, one-way streets, and turns matter.

Better ranking signals:

- Road-network ETA
- Driver availability
- Driver direction of travel
- Vehicle type
- Rider preferences
- Driver acceptance probability
- Fairness and marketplace balance

Interview mental model:

> Use spatial indexing to find candidates, then use exact distance or ETA to rank them.

### Location Freshness

Location freshness means how recent a location update is.

Moving entities become stale quickly.

Example:

```text
Driver was at location X 3 minutes ago.
Driver may now be far away.
```

Every location update should usually include:

- Entity ID
- Latitude
- Longitude
- Timestamp
- Optional speed/direction
- Optional accuracy

Example:

```json
{
  "driverId": "driver-123",
  "lat": 40.7128,
  "lng": -74.0060,
  "timestamp": "2026-04-27T10:15:30Z",
  "speedMetersPerSecond": 8.2,
  "headingDegrees": 90
}
```

Freshness rules:

| Location Age | Meaning |
|---|---|
| 0-10 seconds | Very fresh |
| 10-30 seconds | Usually acceptable |
| 30-120 seconds | Risky for fast-moving entities |
| More than 120 seconds | Often stale |

How systems handle stale locations:

- Ignore old locations during matching.
- Show stale markers differently on maps.
- Ask client to send a fresh update.
- Predict current position using speed and heading.
- Remove entity from active availability after timeout.

Tradeoff:

Frequent updates improve accuracy but increase write load, battery usage, network usage, and backend cost.

Example:

```text
1M active drivers sending location every 5 seconds
= 200K location updates per second
```

This is why location systems often use streaming pipelines, in-memory geo indexes, and TTL-based storage.

Interview mental model:

> In location systems, old coordinates can be worse than no coordinates. Always reason about timestamp and freshness.

### Matching

Matching means choosing the best entity for a request.

In ride-sharing, matching chooses a driver for a rider. In delivery, it may choose a courier for an order.

Matching is not simply nearest-neighbor search.

It is an optimization problem with business constraints.

Example signals:

- Distance to pickup
- ETA to pickup
- Driver availability
- Driver vehicle type
- Driver rating or reliability
- Rider priority
- Current traffic
- Driver direction
- Demand/supply balance
- Cancellation probability
- Fairness across drivers

Basic matching flow:

```text
Rider requests trip
  -> find nearby candidate drivers
  -> rank candidates
  -> reserve best driver
  -> send offer to driver
  -> driver accepts or rejects
  -> if rejected, try next candidate
```

Important race condition:

Two riders may try to match with the same driver at the same time.

Bad behavior:

```text
Rider A sees Driver 1 as available
Rider B sees Driver 1 as available
Both assign Driver 1
```

Fix:

Use an atomic state transition.

```text
available -> reserved
```

Only one request should successfully reserve the driver.

Example database condition:

```sql
UPDATE drivers
SET status = 'reserved', reserved_by = 'rider-123'
WHERE driver_id = 'driver-1'
  AND status = 'available';
```

If the update affects one row, reservation succeeded. If it affects zero rows, another rider got the driver first.

Matching also needs timeouts.

Example:

```text
Driver reserved for Rider A
Driver does not respond in 10 seconds
Reservation expires
Driver becomes available again
System tries next candidate for Rider A
```

Interview mental model:

> Nearby search finds candidates. Matching chooses and reserves one safely under concurrency.

Example ride matching flow:

```text
Driver App -> Location Service -> Geo Index
Rider App -> Matching Service -> Nearby Drivers -> Dispatch
```

Challenges:

- Frequent location updates
- Stale driver locations
- Nearby search latency
- Two riders choosing same driver
- Regional demand imbalance
- Real-time updates

To reserve a driver, use an atomic state transition.

Example:

```text
available -> reserved -> accepted -> on_trip -> available
```

Interview mental model:

> Location design is about indexing moving entities and safely assigning scarce resources.

---

## Microservices

Microservices are independently deployable services organized around business capabilities.

Good service boundaries:

- Order service
- Payment service
- Inventory service
- Catalog service
- Notification service
- User identity service

Bad boundaries:

- Controller service
- Database service
- Business logic service

Those are technical layers, not business capabilities.

Benefits:

- Independent deployment
- Team ownership
- Technology flexibility
- Fault isolation
- Independent scaling

Costs:

- Network complexity
- Distributed tracing needed
- Harder consistency
- More deployments
- More operational overhead
- Service-to-service authentication

Microservices are not always better. A modular monolith is often better early.

Interview mental model:

> Use microservices when team scale and domain boundaries justify the operational cost.

---

## Service Discovery and API Gateway

Service discovery helps services find each other.

In dynamic environments, instances come and go.

```text
Order Service -> Service Registry -> Payment Service instances
```

Service discovery can be:

- Client-side: client picks instance.
- Server-side: load balancer picks instance.

An API gateway is the entry point for client requests.

It can handle:

- Routing
- Authentication
- Rate limiting
- TLS termination
- Request transformation
- Response aggregation

API gateway risk:

- It can become a bottleneck or too much business logic can move into it.

Interview mental model:

> Service discovery is for internal routing. API gateway is for client-facing entry and cross-cutting concerns.

---

## Distributed Transactions and Sagas

A distributed transaction spans multiple services/databases.

Example order flow:

```text
Create order
Reserve inventory
Charge payment
Send confirmation
```

Two-phase commit can coordinate distributed transactions, but it blocks and reduces availability.

Microservices often use sagas instead.

### Saga

A saga breaks a distributed transaction into steps, each with a compensating action.

Example:

```text
Create order
Reserve inventory
Authorize payment
Confirm order
```

If payment fails:

```text
Release inventory
Cancel order
```

Saga styles:

- Choreography: services react to events.
- Orchestration: central coordinator tells services what to do.

Interview mental model:

> Avoid distributed transactions when possible. Use sagas, idempotency, and reconciliation for long-running business workflows.

---

## Outbox Pattern and CDC

The outbox pattern solves a common dual-write problem.

Problem:

```text
Update database
Publish event
```

What if database update succeeds but event publish fails?

Solution:

Write the business data and event record in the same database transaction.

```text
Database transaction:
  update order
  insert outbox event
```

Then a relay publishes outbox events to the message broker.

CDC means Change Data Capture. It reads database changes and publishes them downstream.

Uses:

- Search indexing
- Cache invalidation
- Analytics
- Replication
- Event-driven integration

Interview mental model:

> Outbox makes state changes and event publishing reliable without a distributed transaction.

---

## Consensus and Coordination

Consensus lets distributed nodes agree on a value despite failures.

Examples:

- Raft
- Paxos
- Zab

Used for:

- Leader election
- Metadata consistency
- Configuration management
- Distributed coordination
- Strongly consistent logs

Consensus is powerful but expensive. It adds latency because nodes must communicate before committing decisions.

Interview mental model:

> Use consensus for small, critical coordination metadata, not every high-volume data operation.

---

## Distributed Locks and Fencing Tokens

Distributed locks are hard because systems fail in subtle ways.

Problems:

- Lock holder pauses.
- Network partition occurs.
- Lock lease expires.
- Old owner continues doing work.

Fencing tokens solve stale-owner problems.

Each lock acquisition gets a monotonically increasing token.

```text
Owner A gets token 10
Owner A pauses
Owner B gets token 11
Owner A resumes and tries write with token 10
Storage rejects token 10 because token 11 is newer
```

Interview mental model:

> A lock without fencing can still allow stale writers to corrupt state.

---

## Ordering, Clocks, and Time

Ordering is difficult in distributed systems because machines have different clocks and messages arrive late.

Wall-clock time is not reliable for strict ordering.

Problems:

- Clock skew
- Network delay
- Retries
- Concurrent writes
- Events arriving out of order

Useful tools:

- Sequence numbers
- Stream partitions
- Logical clocks
- Vector clocks
- Version numbers
- Per-entity ordering

Global ordering is expensive. Many systems only need ordering per entity.

Examples:

- Chat messages need ordering per conversation.
- Bank account operations need ordering per account.
- Kafka guarantees order within a partition, not across all partitions.

Interview mental model:

> Avoid global ordering unless truly required. Prefer per-user, per-conversation, or per-account ordering.

---

## Observability

Observability means understanding what the system is doing from the outside.

The three pillars:

| Pillar | Purpose |
|---|---|
| Logs | Detailed events and debugging context |
| Metrics | Numeric trends over time |
| Traces | Request path across services |

Important metrics:

- QPS/RPS
- p50/p95/p99 latency
- Error rate
- CPU/memory
- Queue depth
- Consumer lag
- Cache hit rate
- Database query latency
- Connection pool usage
- Disk usage

Golden signals:

- Latency
- Traffic
- Errors
- Saturation

Good alerts are based on user impact.

Examples:

- p99 latency above SLO
- Error rate spike
- Payment failures above baseline
- Queue lag growing
- Database primary unavailable

Interview mental model:

> If you cannot measure it, you cannot operate it reliably.

---

## Security and Privacy

Security affects architecture from the beginning.

Core concepts:

- Authentication: who are you?
- Authorization: what can you do?
- TLS: encryption in transit
- Encryption at rest
- Secrets management
- Audit logs
- Input validation
- Rate limiting
- Tenant isolation

Authentication examples:

- Username/password
- OAuth2
- OpenID Connect
- Session cookie
- JWT

Authorization examples:

- Role-based access control
- Attribute-based access control
- Resource ownership checks

Privacy concerns:

- PII storage
- Data retention
- Right to delete
- Data residency
- Auditability
- Consent
- Access logging

Interview mental model:

> Security is not one box in the diagram. It is enforced at APIs, data stores, networks, operations, and people/process boundaries.

---

## Multi-Region Design

Multi-region systems run in more than one geographic region.

Reasons:

- Lower user latency
- Higher availability
- Disaster recovery
- Data residency

### Active-Passive

One region serves traffic. Another waits for failover.

Pros:

- Simpler consistency
- Easier operations

Cons:

- Failover may take time
- Passive capacity may be wasted

### Active-Active

Multiple regions serve traffic simultaneously.

Pros:

- Lower latency globally
- Better availability

Cons:

- Harder data consistency
- Conflict resolution
- More expensive

Important questions:

- Can users write in multiple regions?
- How is data replicated?
- What happens during region partition?
- How do we route users?
- What is the failover process?

Interview mental model:

> Multi-region improves latency and availability, but makes data consistency and operations much harder.

---

## Disaster Recovery

Disaster recovery is how the system recovers from major failure.

Key terms:

| Term | Meaning |
|---|---|
| RPO | Recovery Point Objective: how much data loss is acceptable |
| RTO | Recovery Time Objective: how long recovery may take |

Example:

- RPO = 5 minutes means losing up to 5 minutes of data is acceptable.
- RTO = 30 minutes means the system should be restored within 30 minutes.

DR strategies:

- Backups
- Cross-region replication
- Warm standby
- Hot standby
- Regular restore testing
- Runbooks

Backups are only useful if restore has been tested.

Interview mental model:

> Disaster recovery is not just backup. It is proven ability to restore within RPO and RTO.

---

## Capacity Planning

Capacity planning estimates system load before choosing architecture.

Common estimates:

- Daily active users
- Requests per second
- Peak QPS
- Read/write ratio
- Storage per day
- Bandwidth
- Cache size
- Number of partitions

QPS formula:

```text
QPS = requests per day / 86,400
Peak QPS = average QPS * peak factor
```

Storage formula:

```text
storage/day = objects/day * average object size
total = storage/day * retention * replication factor
```

Bandwidth formula:

```text
bandwidth = QPS * response size
```

Example:

```text
100M users
10 app opens per day
5 API calls per open

Requests/day = 100M * 10 * 5 = 5B
Average QPS = 5B / 86,400 = about 58K
Peak QPS = 3x = about 175K
```

Interview mental model:

> Estimates do not need to be perfect. They need to reveal likely bottlenecks.

---

## Cost-Aware Design

Large systems cost money to run.

Main cost drivers:

- Compute
- Database reads/writes
- Storage
- Network bandwidth
- Cross-region replication
- Logs and metrics
- Search indexing
- Queue retention
- CDN traffic

Cost tradeoffs:

- Caching costs money but reduces database load.
- Multi-region costs more but improves latency and availability.
- Strong consistency can increase coordination cost.
- Keeping all logs forever improves debugging but increases storage cost.
- Over-sharding increases operational cost.

Good design is not the most complex design. It is the simplest design that satisfies requirements.

Interview mental model:

> Cost is a real non-functional requirement. Mention it when proposing expensive architecture.

---

## Common Tradeoff Patterns

| Tradeoff | Explanation |
|---|---|
| Latency vs consistency | Stronger consistency often requires more coordination. |
| Availability vs correctness | Some systems reject requests rather than risk incorrect state. |
| Read speed vs write speed | Indexes and materialized views speed reads but slow writes. |
| Simplicity vs scalability | Simple systems are easier to operate but may hit scale limits. |
| Cost vs performance | More replicas/caches/regions improve performance but cost more. |
| Freshness vs speed | Cached or precomputed data is fast but may be stale. |
| Global ordering vs throughput | Total ordering limits parallelism. |
| Microservices vs monolith | Microservices improve autonomy but add distributed complexity. |

When answering system design questions, explicitly name the tradeoff.

Example:

> I would use cache-aside here because reads are much more frequent than writes. The tradeoff is stale data, so I would use a short TTL and invalidate on writes.

---

## How to Think in Interviews

A good system design answer usually follows this path:

1. Clarify requirements.
2. Estimate scale.
3. Define APIs.
4. Define data model.
5. Start with simple architecture.
6. Identify bottlenecks.
7. Add components to solve bottlenecks.
8. Discuss consistency and failure handling.
9. Discuss observability and security.
10. Summarize tradeoffs.

Do not start by drawing a complex architecture.

Start with:

```text
Client -> API -> Database
```

Then evolve the design:

- Add load balancer when one server is not enough.
- Add cache when database reads are hot.
- Add queue when work can be async.
- Add object storage for large files.
- Add search index for full-text search.
- Add sharding when one database cannot handle load.
- Add replication for availability and read scaling.
- Add multi-region when global latency or disaster recovery requires it.

Strong closing language:

> The correctness-critical path uses strong consistency and idempotency. The read-heavy user-facing path uses caching and eventual consistency for low latency. The system scales stateless services horizontally, partitions stateful data by access pattern, and uses queues for non-critical asynchronous work.
