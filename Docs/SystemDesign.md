# System Design Interview Guide - Basic to Advanced

## Table of Contents

- [How to Study System Design](#how-to-study-system-design)
- [What Is System Design?](#what-is-system-design)
- [Interview Mindset](#interview-mindset)
- [System Design Interview Framework](#system-design-interview-framework)
- [Requirement Gathering](#requirement-gathering)
- [Back-of-the-Envelope Estimation](#back-of-the-envelope-estimation)
- [Core Building Blocks](#core-building-blocks)
- [Client-Server Architecture](#client-server-architecture)
- [DNS, CDN, and Edge](#dns-cdn-and-edge)
- [Load Balancers](#load-balancers)
- [API Design](#api-design)
- [Databases](#databases)
- [Indexes](#indexes)
- [Caching](#caching)
- [Queues and Streams](#queues-and-streams)
- [Scalability](#scalability)
- [Availability and Reliability](#availability-and-reliability)
- [Consistency and CAP](#consistency-and-cap)
- [Partitioning, Sharding, and Replication](#partitioning-sharding-and-replication)
- [Microservices and Service Boundaries](#microservices-and-service-boundaries)
- [Rate Limiting](#rate-limiting)
- [Search Systems](#search-systems)
- [Feed and Timeline Systems](#feed-and-timeline-systems)
- [Notification Systems](#notification-systems)
- [Payment and Ledger Systems](#payment-and-ledger-systems)
- [Location-Based Systems](#location-based-systems)
- [File and Media Systems](#file-and-media-systems)
- [Real-Time Systems](#real-time-systems)
- [Observability and Operations](#observability-and-operations)
- [Security and Privacy](#security-and-privacy)
- [Advanced Concepts](#advanced-concepts)
- [Common System Design Templates](#common-system-design-templates)
- [Regular Interview Questions](#regular-interview-questions)
- [Tricky Interview Questions](#tricky-interview-questions)
- [Scenario-Based Questions](#scenario-based-questions)
- [Common Design Problems and Key Ideas](#common-design-problems-and-key-ideas)
- [Mistakes to Avoid](#mistakes-to-avoid)
- [Quick Revision Notes](#quick-revision-notes)

---

## How to Study System Design

System design interviews test how you think through large-scale software systems. They are not about memorizing one perfect architecture. They are about making reasonable tradeoffs under unclear requirements.

Study in this order:

1. Learn the common building blocks: load balancer, cache, database, queue, CDN, API gateway.
2. Learn scale estimation: QPS, storage, bandwidth, cache size.
3. Learn data modeling and access patterns.
4. Learn consistency, replication, sharding, and failure handling.
5. Practice common designs: URL shortener, news feed, chat, rate limiter, file storage, notification system, payment system.
6. Practice explaining tradeoffs clearly.

Strong candidates do not just draw boxes. They explain why each box exists.

---

## What Is System Design?

System design is the process of defining the architecture, components, APIs, data model, storage, scaling strategy, and operational behavior of a software system.

In interviews, you usually design a large-scale application such as:

- YouTube
- WhatsApp
- Uber
- Twitter/X
- Instagram
- Google Docs
- Dropbox
- Netflix
- Amazon product search
- Ticket booking
- Payment processing

The goal is not to build the entire system perfectly. The goal is to show that you can reason about:

- Functional requirements
- Non-functional requirements
- Scale
- Latency
- Availability
- Consistency
- Data storage
- APIs
- Failure modes
- Security
- Monitoring

---

## Interview Mindset

### What Interviewers Look For

| Skill | What It Means |
|---|---|
| Requirement clarity | You ask useful questions before designing. |
| Tradeoff thinking | You compare options instead of forcing one answer. |
| Scale awareness | You estimate traffic, storage, and bottlenecks. |
| Data modeling | You choose schemas/storage based on access patterns. |
| Reliability thinking | You handle failures, retries, backups, and monitoring. |
| Communication | You explain clearly and adapt to interviewer feedback. |

### Good System Design Language

Use phrases like:

- "For the first version, I would keep this simple with..."
- "At this scale, the likely bottleneck is..."
- "This path needs strong consistency, but this other path can be eventually consistent."
- "I would make this async because the user does not need to wait for it."
- "This cache improves latency but introduces invalidation concerns."
- "The system should be idempotent because retries can duplicate requests."

---

## System Design Interview Framework

Use this every time.

### 1. Clarify Requirements

Ask about:

- Users
- Core features
- Out of scope features
- Read/write ratio
- Latency requirements
- Consistency requirements
- Availability requirements
- Scale
- Data retention
- Security/privacy constraints

### 2. Estimate Scale

Estimate:

- Daily active users
- Requests per second
- Peak traffic
- Storage per day
- Bandwidth
- Cache size
- Number of database partitions

### 3. Define APIs

Sketch simple APIs.

Example:

```http
POST /v1/posts
GET /v1/users/{userId}/feed
POST /v1/messages
GET /v1/files/{fileId}
```

### 4. Define Data Model

Identify entities and relationships.

Example:

- User
- Post
- Comment
- Like
- Follow
- TimelineEntry

### 5. High-Level Design

Start simple:

```
Client -> Load Balancer -> API Service -> Database
```

Then add components as needed:

- Cache
- Queue
- Workers
- Search index
- Object storage
- CDN
- Analytics pipeline

### 6. Deep Dive

Choose the hard part. Interviewers care most about bottlenecks and tradeoffs.

Deep dive examples:

- Feed generation
- Payment idempotency
- Message ordering
- Inventory consistency
- Search indexing
- File upload flow
- Rate limiter algorithm

### 7. Failure Handling and Operations

Discuss:

- Retries
- Timeouts
- Circuit breakers
- Replication
- Backups
- Monitoring
- Alerts
- Rollbacks
- Security

---

## Requirement Gathering

Requirements are split into two types.

### Functional Requirements

What the system should do.

Example for chat app:

- Send one-to-one messages.
- Support group chats.
- Show online status.
- Deliver push notifications.
- Store message history.

### Non-Functional Requirements

How the system should behave.

Examples:

- Low latency
- High availability
- Strong consistency for some data
- Eventual consistency for some data
- Scalability
- Security
- Fault tolerance
- Observability

### Common Clarifying Questions

- How many users?
- Is this global or single region?
- What is read/write ratio?
- Is data loss acceptable?
- Is ordering required?
- Is exact count required or approximate count okay?
- Do we need real-time updates?
- What should happen when dependencies fail?
- Are there compliance requirements?

---

## Back-of-the-Envelope Estimation

Estimation helps you choose architecture.

### Useful Numbers

Approximate numbers to remember:

| Operation | Rough Latency |
|---|---|
| Memory access | Nanoseconds |
| SSD read | 100 microseconds to 1 ms |
| Network call within same region | 1 to 5 ms |
| Cross-region network call | 50 to 200 ms |
| Database query | 1 to 50 ms depending on query/index/load |
| Cache lookup | Sub-ms to few ms |

### QPS Estimate

```
QPS = total requests per day / 86,400
Peak QPS = average QPS * peak factor
```

Example:

```
100 million users
Each user opens app 10 times/day
Each open makes 5 API calls

Requests/day = 100M * 10 * 5 = 5B
Average QPS = 5B / 86,400 = ~58K
Peak QPS = 3x = ~175K
```

### Storage Estimate

```
storage/day = number of objects * average object size
total storage = storage/day * retention * replication factor
```

Example:

```
500M messages/day
Average message = 500 bytes
Raw daily storage = 250 GB/day
With indexes/metadata ~2x = 500 GB/day
Replication factor 3 = 1.5 TB/day
1 year = ~547 TB
```

### Bandwidth Estimate

```
bandwidth = QPS * response size
```

Example:

```
100K QPS * 10 KB response = 1 GB/sec
```

---

## Core Building Blocks

| Component | Purpose |
|---|---|
| Client | Browser, mobile app, desktop app, external service. |
| DNS | Resolves domain name to IP address. |
| CDN | Caches static/media content close to users. |
| Load balancer | Distributes traffic to servers. |
| API gateway | Handles routing, auth, rate limits, request shaping. |
| Application service | Business logic. |
| Cache | Fast temporary storage. |
| Database | Durable source of truth. |
| Queue | Async task buffering. |
| Stream | Append-only event log for replayable events. |
| Worker | Background processor. |
| Object storage | Stores large blobs like images/videos/files. |
| Search index | Full-text or vector search. |
| Monitoring | Metrics, logs, traces, alerts. |

---

## Client-Server Architecture

The simplest web architecture:

```
Client -> Server -> Database
```

This works for small systems but has limits:

- Single server can fail.
- Database can become bottleneck.
- Static content is slow for distant users.
- Long-running work blocks requests.

Scaled version:

```
Client
  -> DNS
  -> CDN
  -> Load Balancer
  -> API Servers
  -> Cache
  -> Database
  -> Queue
  -> Workers
```

---

## DNS, CDN, and Edge

### DNS

DNS maps domain names to IP addresses.

Example:

```
api.example.com -> 20.40.60.80
```

DNS can support:

- Geo routing
- Failover
- Weighted routing
- Latency-based routing

### CDN

CDN caches content near users.

Good for:

- Images
- Videos
- CSS/JS
- Public files
- Static pages

Benefits:

- Lower latency
- Lower origin load
- Better global performance
- DDoS absorption

### Edge Computing

Edge computing runs some logic near users.

Examples:

- Authentication checks
- Request routing
- Image resizing
- A/B testing
- Personalization hints

Tradeoff:

- Lower latency but harder debugging and deployment.

---

## Load Balancers

Load balancers distribute requests across backend servers.

### L4 vs L7

| Type | Works At | Routes Based On |
|---|---|---|
| L4 | TCP/UDP | IP and port |
| L7 | HTTP/application | Path, host, headers, cookies |

### Algorithms

- Round robin
- Weighted round robin
- Least connections
- Least response time
- Random
- Consistent hashing

### Health Checks

Load balancers should avoid unhealthy instances.

Use:

- Liveness check: is process alive?
- Readiness check: can it serve traffic?

Tricky point:

> A service may be live but not ready. For example, process is running but database connection pool is exhausted.

---

## API Design

Good APIs are simple, versioned, secure, and stable.

### REST

Example:

```http
POST /v1/orders
GET /v1/orders/{orderId}
PATCH /v1/orders/{orderId}
DELETE /v1/orders/{orderId}
```

Best for:

- Public APIs
- CRUD-style resources
- Browser/mobile clients

### gRPC

Best for:

- Internal service communication
- Low latency
- Strong schema contracts
- Streaming

### GraphQL

Best for:

- Frontend aggregation
- Mobile/web clients needing flexible fields

Risks:

- N+1 backend calls
- Query complexity attacks
- Harder caching
- Authorization complexity

### API Design Rules

- Use versioning.
- Validate input.
- Return clear errors.
- Support pagination.
- Make write APIs idempotent when retries are possible.
- Avoid exposing internal database schema.
- Use authentication and authorization.

### Pagination

Offset pagination:

```http
GET /posts?offset=100&limit=20
```

Problem: slow for large offsets and inconsistent when data changes.

Cursor pagination:

```http
GET /posts?cursor=abc123&limit=20
```

Better for large feeds and changing data.

---

## Databases

### SQL Databases

Examples:

- PostgreSQL
- MySQL
- SQL Server

Good for:

- Transactions
- Relational data
- Joins
- Strong consistency
- Constraints

### NoSQL Databases

Examples:

- DynamoDB
- Cassandra
- MongoDB
- Cosmos DB
- Redis

Good for:

- Large scale
- Flexible schema
- Simple access patterns
- High write throughput
- Low latency key-value access

### Database Choice by Use Case

| Use Case | Common Choice |
|---|---|
| Payments | Relational DB + ledger |
| User profile | Relational or document DB |
| Session store | Redis |
| Product catalog | Document DB or relational DB |
| Search | Elasticsearch/OpenSearch |
| Chat messages | Wide-column, relational partitioned, or document DB |
| Metrics | Time-series DB |
| Analytics | Columnar warehouse |
| File metadata | Relational DB or scalable key-value DB |

### Rule

Choose the database based on access patterns, not hype.

Ask:

- Do we need joins?
- Do we need transactions?
- What is the primary key access pattern?
- What queries must be fast?
- How large is the data?
- How frequently is it updated?
- What consistency is needed?

---

## Indexes

An index speeds up reads by maintaining an additional data structure.

### B-Tree Index

Good for:

- Equality lookup
- Range queries
- Sorting

Example:

```sql
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);
```

### Hash Index

Good for:

- Exact key lookup

Bad for:

- Range queries

### Inverted Index

Used for full-text search.

Example:

```
word -> list of documents containing word
```

### Index Tradeoffs

Pros:

- Faster reads
- Faster filters/sorts

Cons:

- Slower writes
- Extra storage
- Maintenance cost
- Bad indexes may not help

### Interview Tip

If you propose a query, mention the index that supports it.

---

## Caching

Caching stores hot data in faster storage.

### Cache-Aside Pattern

```
value = cache.get(key)
if value is missing:
    value = db.get(key)
    cache.set(key, value, ttl)
return value
```

### Where to Cache

- Browser
- CDN
- API gateway
- Application memory
- Redis/Memcached
- Database buffer cache

### Cache Invalidation

Common strategies:

- TTL
- Delete on write
- Update on write
- Versioned keys
- Event-driven invalidation

### Common Cache Problems

| Problem | Meaning | Fix |
|---|---|---|
| Cache penetration | Requests for missing keys hit DB repeatedly | Cache nulls, Bloom filter |
| Cache breakdown | Hot key expires and many requests hit DB | Lock, singleflight, early refresh |
| Cache avalanche | Many keys expire together | TTL jitter, staggered refresh |
| Hot key | One key gets huge traffic | Replicate key, local cache, split key |

### Stale Cache Risk

Cache is dangerous for:

- Permissions
- Inventory reservation
- Payment state
- Fraud decisions
- Pricing if legally sensitive

Cache is safer for:

- Product descriptions
- Public profiles
- Feed items
- Static metadata
- Counts where approximate values are okay

---

## Queues and Streams

Queues and streams decouple producers from consumers.

### Queue

One message is usually processed by one consumer.

Examples:

- SQS
- RabbitMQ
- Azure Service Bus

Use for:

- Email sending
- Image processing
- Background jobs
- Retryable tasks

### Stream

Events are stored in an append-only log and can be replayed.

Examples:

- Kafka
- Kinesis
- Event Hubs
- Pulsar

Use for:

- Event sourcing
- Analytics pipeline
- CDC
- Multiple consumers reading same events

### Delivery Semantics

| Type | Meaning |
|---|---|
| At-most-once | May lose message, no duplicate. |
| At-least-once | No loss if system works, duplicates possible. |
| Exactly-once effect | Achieved through transactions, idempotency, and dedupe. |

### Why Async Helps

- Smooth traffic spikes.
- Reduce user-facing latency.
- Isolate failures.
- Retry safely.
- Enable fanout to many consumers.

---

## Scalability

### Vertical Scaling

Use bigger machine.

Pros:

- Simple
- No sharding complexity

Cons:

- Hardware limit
- Expensive
- Single failure domain

### Horizontal Scaling

Use more machines.

Pros:

- Scales further
- Better availability

Cons:

- Requires distributed design
- More operational complexity

### Stateless Services

Easy to scale horizontally.

```
Load Balancer -> API Server 1
              -> API Server 2
              -> API Server 3
```

### Stateful Services

Harder to scale.

Examples:

- Database
- Queue
- Cache cluster
- Search index

Need:

- Replication
- Partitioning
- Backup
- Failover
- Rebalancing

---

## Availability and Reliability

### Availability

Availability is the percentage of time a system is usable.

| Availability | Downtime/Year Approx |
|---|---|
| 99% | 3.65 days |
| 99.9% | 8.76 hours |
| 99.99% | 52.6 minutes |
| 99.999% | 5.26 minutes |

### Reliability Patterns

- Replication
- Failover
- Redundancy
- Retry with backoff
- Circuit breaker
- Bulkhead
- Timeout
- Graceful degradation
- Load shedding
- Backup and restore

### Graceful Degradation

When some dependency fails, keep core experience working.

Examples:

- Show cached feed without personalization.
- Disable recommendations.
- Queue emails for later.
- Return approximate counts.

### Disaster Recovery

| Term | Meaning |
|---|---|
| RPO | How much data loss is acceptable. |
| RTO | How long recovery may take. |

---

## Consistency and CAP

### Strong Consistency

Every read sees latest committed write.

Needed for:

- Payments
- Inventory booking
- Account balances
- Permissions
- Unique username/email

### Eventual Consistency

Replicas eventually converge.

Acceptable for:

- Feeds
- Likes
- Comments count
- Search index
- Analytics
- Recommendations

### CAP

During network partition, choose consistency or availability.

### PACELC

If partition happens, choose availability or consistency. Else, choose latency or consistency.

### Practical Interview Answer

Most systems mix consistency levels:

- Strong consistency for money, inventory, permissions.
- Eventual consistency for feeds, notifications, search, analytics.

---

## Partitioning, Sharding, and Replication

### Replication

Multiple copies of data.

Benefits:

- Read scaling
- Fault tolerance
- Disaster recovery

Tradeoff:

- Replication lag
- Conflict handling
- Failover complexity

### Sharding

Split data across nodes.

Strategies:

- Hash by ID
- Range by time/id
- Geo by region
- Tenant by customer
- Directory-based mapping

### Hot Partition

One partition receives too much traffic.

Examples:

- Celebrity account
- Viral video
- Popular product
- Current timestamp partition

Solutions:

- Cache hot objects
- Split hot key
- Add random suffix
- Use adaptive partitioning
- Special-case celebrity/high-volume entities

---

## Microservices and Service Boundaries

Microservices are independently deployable services organized around business capabilities.

### Good Service Boundaries

- Billing service
- Order service
- Inventory service
- Catalog service
- User identity service
- Notification service

### Bad Service Boundaries

- Controller service
- Business logic service
- Database service

These are technical layers, not business capabilities.

### Database per Service

Each service owns its data.

Pros:

- Independent schema changes
- Clear ownership
- Service autonomy

Cons:

- Cross-service queries are harder
- Distributed transactions are harder
- Eventual consistency required

---

## Rate Limiting

Rate limiting protects systems from abuse and overload.

### Algorithms

| Algorithm | Description | Notes |
|---|---|---|
| Fixed window | Count requests per fixed interval | Simple but bursty at boundary |
| Sliding window log | Store timestamps of requests | Accurate but memory-heavy |
| Sliding window counter | Approximate weighted previous/current window | Balanced |
| Token bucket | Tokens refill over time; request consumes token | Allows bursts |
| Leaky bucket | Requests drain at constant rate | Smooth output rate |

### Distributed Rate Limiter

Options:

- Central Redis counter
- Local counters with periodic sync
- Per-region quota
- Token leasing
- Approximate rate limiting

Tradeoff:

- Strong global limits cost latency and availability.
- Approximate local limits scale better.

---

## Search Systems

Search systems need indexing.

### Basic Flow

```
Database -> CDC/Queue -> Indexer -> Search Index -> Query Service
```

### Inverted Index

```
term -> document IDs
```

### Search Ranking Signals

- Text relevance
- Recency
- Popularity
- Personalization
- Location
- Business rules

### Search Consistency

Search is usually eventually consistent. A newly created item may take seconds to appear.

---

## Feed and Timeline Systems

### Fanout on Write

When a user posts, push post ID to followers' timelines.

Pros:

- Fast reads

Cons:

- Expensive for users with many followers

### Fanout on Read

When user opens feed, fetch posts from followed users.

Pros:

- Cheap writes

Cons:

- Slow reads for users following many accounts

### Hybrid Fanout

Use fanout on write for normal users. Use fanout on read for celebrities.

This is a common FAANG-style answer.

---

## Notification Systems

Notification systems send email, SMS, push, or in-app notifications.

### Architecture

```
Producer Service -> Notification API -> Queue -> Workers -> Provider
                                      -> Preferences Service
                                      -> Template Service
```

### Important Concerns

- User preferences
- Rate limiting
- Deduplication
- Retry with backoff
- Dead-letter queue
- Provider failover
- Delivery tracking
- Template versioning

---

## Payment and Ledger Systems

Payments require correctness over cleverness.

### Key Concepts

- Idempotency key
- Immutable ledger
- Double-entry accounting
- Payment state machine
- External provider callbacks
- Reconciliation
- Audit logs

### Payment State Example

```
created -> authorized -> captured -> settled
        -> failed
        -> refunded
```

### Rule

Never design payment as just updating a balance field. Use immutable ledger entries.

---

## Location-Based Systems

Used in Uber-like designs.

### Concepts

- Geohash
- S2 cells
- H3 hexagons
- Quadtrees
- Nearby search
- Driver location freshness
- Matching service

### Common Flow

```
Driver App -> Location Service -> Geo Index
Rider App -> Matching Service -> Nearby Drivers -> Dispatch
```

### Tricky Part

Two riders may try to reserve the same driver. Use atomic compare-and-set on driver state.

---

## File and Media Systems

Used in Dropbox, Google Drive, YouTube, Instagram.

### Upload Flow

```
Client -> API asks for upload URL
Client -> uploads file to object storage
Storage -> event -> processing workers
Workers -> thumbnails/transcoding/metadata
Metadata DB updated
CDN serves final content
```

### Concepts

- Object storage
- Multipart upload
- Pre-signed URL
- Metadata database
- CDN
- Chunking
- Deduplication
- Virus scanning
- Transcoding

---

## Real-Time Systems

Examples:

- Chat
- Live comments
- Collaborative editing
- Multiplayer game
- Stock ticker
- Driver tracking

### Transport Options

| Option | Best For |
|---|---|
| Polling | Simple, low-frequency updates |
| Long polling | Better near-real-time without WebSockets |
| Server-Sent Events | Server-to-client updates |
| WebSocket | Bi-directional real-time communication |
| WebRTC | Peer-to-peer audio/video/data |

### Real-Time Challenges

- Connection management
- Ordering
- Reconnects
- Offline delivery
- Presence
- Backpressure
- Fanout
- Multi-region routing

---

## Observability and Operations

### Logs, Metrics, Traces

| Tool | Purpose |
|---|---|
| Logs | Detailed events and debugging. |
| Metrics | Numerical health over time. |
| Traces | Request path across services. |

### Important Metrics

- RPS/QPS
- p50/p95/p99 latency
- Error rate
- CPU/memory
- Queue depth
- Consumer lag
- Cache hit rate
- Database connection pool usage
- Disk usage

### Golden Signals

- Latency
- Traffic
- Errors
- Saturation

### Alerting

Alert on user impact, not just CPU.

Good alerts:

- p99 latency above SLO
- Error rate spike
- Queue lag growing
- Payment failures above baseline
- Database primary unavailable

Bad alerts:

- CPU briefly at 80% with no user impact

---

## Security and Privacy

### Security Basics

- Authentication
- Authorization
- TLS
- Encryption at rest
- Secrets management
- Rate limiting
- Input validation
- Audit logs

### Auth Concepts

| Term | Meaning |
|---|---|
| Authentication | Who are you? |
| Authorization | What are you allowed to do? |
| OAuth2 | Delegated authorization framework. |
| OIDC | Identity layer on OAuth2. |
| JWT | Signed token containing claims. |
| mTLS | Mutual TLS for service identity. |

### Privacy

Consider:

- PII storage
- Data retention
- Right to delete
- Auditability
- Tenant isolation
- Data residency

---

## Advanced Concepts

### Consensus

Consensus algorithms like Raft and Paxos let nodes agree on values despite failures.

Used for:

- Leader election
- Distributed locks
- Metadata consistency
- Configuration management

### Distributed Transactions

2PC coordinates transactions across systems but is often avoided in microservices because it blocks and reduces availability.

Alternatives:

- Saga
- Outbox pattern
- Idempotency
- Reconciliation

### Outbox Pattern

Problem:

> You update database and publish event. What if database succeeds but event publish fails?

Solution:

Write business data and event record to same database transaction. A relay later publishes the event.

### Change Data Capture

CDC reads database changes and publishes them to downstream systems.

Used for:

- Search indexing
- Cache invalidation
- Analytics
- Replication

### Bloom Filter

A probabilistic data structure that tells whether an item is definitely not present or maybe present.

Used for:

- Avoiding cache penetration
- Checking if username might exist
- Reducing expensive lookups

### Consistent Hashing

Maps keys to nodes so adding/removing nodes remaps only a fraction of keys.

Used for:

- Distributed caches
- Sharded storage
- Load distribution

### CRDTs

Conflict-free replicated data types allow distributed replicas to merge changes without central coordination.

Used for:

- Collaborative editing
- Counters
- Sets
- Offline-first systems

### Vector Clocks

Track causal relationships between events in distributed systems.

Used for:

- Conflict detection
- Versioning
- Causal ordering

---

## Common System Design Templates

### Read-Heavy System

```
Client -> CDN -> Load Balancer -> API -> Cache -> DB Read Replicas
                                      -> Async Workers
```

Use for:

- Product catalog
- Public profiles
- News pages

### Write-Heavy System

```
Client -> API -> Queue/Stream -> Workers -> Sharded DB
                             -> Analytics/Search Index
```

Use for:

- Logging
- Metrics
- Location updates
- Event ingestion

### Media Upload System

```
Client -> API -> Pre-signed URL
Client -> Object Storage
Object Storage Event -> Processing Workers -> Metadata DB -> CDN
```

### Search System

```
Primary DB -> CDC -> Stream -> Indexer -> Search Index -> Search API
```

### Payment System

```
Client -> Payment API -> Idempotency Store -> Ledger DB
                    -> Provider Adapter -> External Payment Provider
                    -> Webhook Handler -> Reconciliation
```

---

## Regular Interview Questions

### Q1: How do you approach a system design interview?

Clarify requirements, estimate scale, define APIs, model data, create high-level design, deep dive into bottlenecks, then discuss reliability, security, and monitoring.

### Q2: What is the difference between functional and non-functional requirements?

Functional requirements describe features. Non-functional requirements describe system qualities like latency, availability, consistency, security, and scalability.

### Q3: What is horizontal scaling?

Adding more machines or instances to handle more load.

### Q4: What is vertical scaling?

Using a larger machine with more CPU, RAM, or disk.

### Q5: What is a load balancer?

A component that distributes traffic across multiple backend instances to improve scalability and availability.

### Q6: What is caching?

Caching stores frequently used data in faster storage to reduce latency and backend load.

### Q7: What is database replication?

Maintaining copies of data across multiple nodes for availability, read scaling, and disaster recovery.

### Q8: What is database sharding?

Splitting data horizontally across multiple machines based on a shard key.

### Q9: What is eventual consistency?

Replicas may temporarily disagree but eventually converge if no new writes happen.

### Q10: What is strong consistency?

Reads return the latest committed write according to the consistency model.

### Q11: What is CDN?

A content delivery network caches static or media content near users to reduce latency and origin load.

### Q12: What is API gateway?

An API gateway handles client-facing concerns like routing, authentication, rate limiting, TLS, and request transformation.

### Q13: What is idempotency?

An operation is idempotent if repeating it has the same effect as doing it once.

### Q14: Why use a queue?

Queues decouple producers and consumers, smooth traffic spikes, and allow async processing with retries.

### Q15: What is a dead-letter queue?

A queue for messages that failed processing repeatedly.

### Q16: What is the difference between monolith and microservices?

A monolith is deployed as one unit. Microservices are independently deployable services organized around business capabilities.

### Q17: What is rate limiting?

Rate limiting controls how many requests a user, IP, API key, or service can make in a time window.

### Q18: What is observability?

The ability to understand system behavior through logs, metrics, traces, and alerts.

### Q19: What is graceful degradation?

Keeping core functionality working while optional features fail or are disabled.

### Q20: What is the outbox pattern?

A pattern where business data and an event record are written in one database transaction, then a relay publishes the event later.

---

## Tricky Interview Questions

### Q1: Is a cache always safe to add?

No. Caches can return stale data and break correctness for permissions, payments, inventory, and pricing. Use caches where staleness is acceptable or carefully invalidate/update them.

### Q2: Can a high cache hit rate still overload the database?

Yes. At very high traffic, even 1% misses can be huge. Also, synchronized cache expiry can create sudden database spikes.

### Q3: Why can retries be dangerous?

Retries can duplicate side effects and amplify load during outages. Use idempotency keys, backoff, jitter, retry limits, and circuit breakers.

### Q4: Is exactly-once delivery possible?

In practice, systems usually provide exactly-once effects using idempotency, deduplication, and transactions. Network-level exactly-once delivery is not something to casually assume.

### Q5: If the database write succeeds but the response is lost, what should the client do?

Retry with an idempotency key or query operation status. Without idempotency, the client may create duplicate side effects.

### Q6: Why is global ordering hard?

Distributed systems have clock skew, network delays, and independent writers. Use per-entity ordering, sequence numbers, logical clocks, or stream partitions instead of relying on wall-clock time.

### Q7: Is eventual consistency always bad?

No. It is often the right choice for feeds, likes, search, analytics, notifications, and recommendations because it improves availability and latency.

### Q8: Should every system use microservices?

No. Microservices add network, deployment, observability, and consistency complexity. A modular monolith is often better for small teams or early products.

### Q9: Can a system be strongly consistent and highly available?

During normal operation, yes. During a network partition, CAP forces a tradeoff for affected operations.

### Q10: Why is using timestamp as ID risky?

Multiple machines can generate the same timestamp, clocks can move backward, and timestamp-only IDs can create hot partitions.

### Q11: Why can adding a queue hide problems?

Queues buffer load, but if consumers cannot keep up, lag grows. Users may see delayed effects, storage may grow, and failures become less visible without monitoring.

### Q12: What is wrong with offset pagination at large scale?

Large offsets are slow because the database may scan many rows. Results can also shift when new data is inserted. Cursor pagination is usually better.

### Q13: Why is a shared database bad in microservices?

It couples services through schema, makes independent deployment harder, and allows services to bypass each other's business logic.

### Q14: What if a user deletes data but it still appears in search?

Search indexes are usually eventually consistent. Use CDC/delete events, tombstones, and possibly query-time filtering for strict privacy requirements.

### Q15: Why can health checks cause outages?

If health checks are too strict, many instances can be removed during a transient dependency issue. If too weak, bad instances receive traffic. Separate liveness and readiness.

### Q16: Why are distributed locks hard?

Lock holders can pause, lock leases can expire, networks can partition, and old owners can continue acting. Use fencing tokens and prefer idempotent designs.

### Q17: Is reading from replicas always safe?

No. Replicas can lag. For read-your-writes or critical decisions, read from leader or use version-aware routing.

### Q18: Why can fanout be expensive?

Pushing one event to millions of followers creates huge write amplification. Celebrity users need special handling such as fanout-on-read.

### Q19: Why should payment systems use ledgers?

Ledgers provide immutable audit records, reconciliation, and correctness. Updating only a balance loses history and is risky.

### Q20: What is the hardest part of system design?

Usually not drawing components. The hard part is choosing tradeoffs for consistency, latency, availability, cost, operational complexity, and correctness.

---

## Scenario-Based Questions

### Scenario 1: Design a URL Shortener

Key requirements:

- Create short URL.
- Redirect short URL to long URL.
- Track analytics.

Design:

- API service creates unique short code.
- Store mapping in database.
- Cache hot mappings in Redis/CDN.
- Redirect service is read-heavy.
- Analytics events go to queue/stream.

Tricky questions:

- How do you avoid collisions?
- How do you support custom aliases?
- What if a short code is abused?

### Scenario 2: Design Instagram Feed

Key requirements:

- Users create posts.
- Users follow others.
- Show ranked feed.

Design:

- Post service stores posts.
- Follow graph stores relationships.
- Feed service uses hybrid fanout.
- Timeline cache stores feed IDs.
- Ranking service scores candidates.
- Media served from object storage/CDN.

Tricky questions:

- What about celebrity users?
- How do you handle deleted posts?
- How fresh should the feed be?

### Scenario 3: Design Chat App

Key requirements:

- Real-time messaging.
- Offline delivery.
- Message history.
- Read receipts.

Design:

- WebSocket gateway manages connections.
- Message service persists messages.
- Queue delivers messages.
- Push notification service handles offline users.
- Use conversation ID as partition key for ordering.

Tricky questions:

- How do you avoid duplicate messages?
- Is ordering global or per conversation?
- What happens on reconnect?

### Scenario 4: Design Distributed Rate Limiter

Key requirements:

- Limit requests per user/API key/IP.
- Work across many API servers.

Design:

- Token bucket or sliding window.
- Redis centralized counters for simpler design.
- Local counters plus periodic sync for higher scale.
- Per-region quotas for multi-region.

Tricky questions:

- Fail open or fail closed?
- Exact global limit or approximate limit?
- How to handle hot users?

### Scenario 5: Design File Storage Like Dropbox

Key requirements:

- Upload files.
- Download files.
- Sync across devices.
- Share files.

Design:

- Metadata service stores file metadata.
- Object storage stores file chunks.
- Chunking enables resumable uploads and dedupe.
- Sync service tracks versions.
- CDN serves downloads.

Tricky questions:

- How do you handle concurrent edits?
- How do you deduplicate files?
- How do you support huge files?

### Scenario 6: Design Payment System

Key requirements:

- Create payment.
- Call external provider.
- Track status.
- Handle webhooks.

Design:

- Payment API with idempotency key.
- Ledger DB for immutable records.
- Provider adapter.
- Webhook processor.
- Reconciliation job.

Tricky questions:

- Provider times out but later succeeds.
- Client retries payment request.
- Refund happens after settlement.

### Scenario 7: Design Search Autocomplete

Key requirements:

- Return suggestions as user types.
- Low latency.
- Rank by popularity and personalization.

Design:

- Prefix index/trie or search index.
- Precompute top suggestions for hot prefixes.
- Cache common prefixes.
- Update ranking asynchronously.

Tricky questions:

- What about very common prefixes like `a`?
- How do you update trending terms fast?
- How do you filter unsafe suggestions?

### Scenario 8: Design Uber Ride Matching

Key requirements:

- Track driver locations.
- Find nearby drivers.
- Match rider to driver.
- Handle driver acceptance.

Design:

- Location ingestion service.
- Geo index using geohash/S2/H3.
- Matching service queries nearby drivers.
- Atomic driver assignment.
- Dispatch and notification services.

Tricky questions:

- Two riders select same driver.
- Driver location is stale.
- Region has no drivers.

---

## Common Design Problems and Key Ideas

| Problem | Key Ideas |
|---|---|
| URL shortener | ID generation, cache, redirect latency, analytics async. |
| Pastebin | Object storage, TTL, access control, read-heavy cache. |
| Twitter feed | Fanout, ranking, timeline cache, celebrity handling. |
| Instagram | Media upload, CDN, feed, comments/likes eventually consistent. |
| YouTube | Upload, transcoding, CDN, recommendations, metadata. |
| Netflix | CDN, video encoding, playback analytics, recommendations. |
| WhatsApp | WebSockets, message ordering, offline delivery, idempotency. |
| Uber | Geospatial index, matching, real-time updates, state transitions. |
| Dropbox | Chunking, metadata, object storage, sync conflicts. |
| Google Docs | CRDT/OT, real-time collaboration, conflict resolution. |
| Rate limiter | Token bucket, Redis, local/global tradeoff. |
| Payment system | Idempotency, ledger, provider webhooks, reconciliation. |
| Notification system | Queue, preferences, templates, retries, DLQ. |
| Search engine | Crawling/indexing, inverted index, ranking, freshness. |
| Ticket booking | Inventory hold, payment, expiry, strong consistency. |

---

## Mistakes to Avoid

- Starting with architecture before clarifying requirements.
- Ignoring non-functional requirements.
- Not estimating scale.
- Saying "use microservices" without explaining boundaries.
- Adding Kafka/Redis/Elasticsearch everywhere without justification.
- Ignoring data model and access patterns.
- Ignoring failure modes.
- Ignoring idempotency for write APIs.
- Claiming exactly-once without explaining how.
- Using cache for strongly consistent data without invalidation plan.
- Forgetting pagination.
- Forgetting monitoring and alerting.
- Treating search as strongly consistent by default.
- Treating payment as a simple database update.
- Not discussing hot partitions or celebrity users.

---

## Quick Revision Notes

- Start every system design with requirements and scale.
- Separate functional and non-functional requirements.
- Use simple design first, then scale bottlenecks.
- Stateless services scale horizontally more easily.
- Stateful systems need replication, sharding, backups, and failover.
- Cache improves latency but creates invalidation and staleness problems.
- Queues decouple services and smooth traffic spikes.
- Streams support replay and multiple consumers.
- Strong consistency is needed for money, inventory, permissions, and uniqueness.
- Eventual consistency is usually fine for feeds, likes, search, analytics, and notifications.
- API writes should be idempotent when clients may retry.
- Use cursor pagination for large or changing datasets.
- Use CDN for static/media content.
- Use object storage for large files.
- Search indexes are usually eventually consistent.
- Feed systems often use hybrid fanout.
- Payment systems need ledger, idempotency, webhooks, and reconciliation.
- Rate limiters trade exactness for latency and availability.
- Monitor p95/p99 latency, not only averages.
- Design for failure: timeouts, retries, circuit breakers, bulkheads, graceful degradation.
- Explain tradeoffs clearly. That is the real interview skill.

---

## Final Study Checklist

Before an interview, make sure you can design these without notes:

- URL shortener
- Rate limiter
- News feed
- Chat/messaging app
- Notification system
- File storage system
- Video upload/streaming system
- Search autocomplete
- Payment system
- Ticket booking system
- Uber ride matching
- Distributed cache

For each one, practice explaining:

- Requirements
- Scale estimates
- APIs
- Data model
- High-level architecture
- Bottlenecks
- Consistency choices
- Failure handling
- Monitoring
- Security
