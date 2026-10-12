---
title: Instagram System Design
description: Interview notes on designing Instagram, covering media upload, CDN delivery, social graphs, hybrid feed fan-out, ranking, pagination, and consistency
---

## Requirements

### Functional requirements

* A user uploads a photo or short video with a caption.
* A user follows or unfollows another user.
* A user opens a personalized home feed containing recent posts from followed
  accounts.
* A user likes or comments on a post.
* A user views a profile and its posts.

Out of scope (say this out loud): stories, reels recommendation, direct
messages, ads, live streaming, search, and content discovery.

### Non-functional requirements

* Feed requests return in under 200 milliseconds at the server.
* Uploaded media is durable and is delivered with low latency worldwide.
* Feed and engagement counts can be eventually consistent.
* Privacy changes and authorization checks must be correct.
* The system remains available when a region or downstream service fails.
* The read path is much heavier than the write path.

> [!IMPORTANT]
> State the main split early: "Media bytes are large and belong in object
> storage behind a CDN. Metadata and social relationships are small but drive
> the product. The hardest problem is producing a personalized feed without
> doing expensive work on every read or creating millions of writes for every
> celebrity post."

## Rough estimates

Assume:

* 1 billion daily active users
* 100 million new posts per day
* 20 home-feed opens per user per day
* 100 media items viewed per user per day
* 2 MB average original upload, including the photo and video mix
* Three processed bytes stored for each original byte

| What                    | Calculation                  | Result                         |
|-------------------------|------------------------------|--------------------------------|
| New posts               | 100M / 86,400                | ~1,200/sec average, ~10k peak  |
| Feed requests           | 1B x 20 / 86,400             | ~230k/sec average, ~1M peak    |
| New original media      | 100M x 2 MB                  | ~200 TB/day                    |
| Processed media storage | 200 TB x 3                   | ~600 TB/day                    |
| Media delivery          | 1B x 100 x 1 MB              | ~100 PB/day                    |
| Feed-entry fan-out      | 100M posts x 500 followers   | ~50B references/day, if pushed |

The exact numbers are less important than the conclusions:

* Media delivery dominates bandwidth and must use a CDN.
* Feed reads dominate request volume.
* Precomputing every feed is attractive, but pure fan-out on write breaks for
  accounts with millions of followers.
* Feed entries should contain post IDs and ranking metadata, not media bytes.

## APIs

```text
POST   /v1/posts/uploads
       {media_type, size, checksum}
       -> {upload_id, post_id, part_urls}

POST   /v1/posts/{post_id}/publish
       {upload_id, caption, idempotency_key}
       -> {post_id, status}

GET    /v1/feed/home?cursor={cursor}&limit=20
       -> {items, next_cursor}

GET    /v1/users/{user_id}/posts?cursor={cursor}&limit=20
       -> {items, next_cursor}

PUT    /v1/users/{user_id}/following/{target_id}
DELETE /v1/users/{user_id}/following/{target_id}

PUT    /v1/posts/{post_id}/likes/me
DELETE /v1/posts/{post_id}/likes/me

POST   /v1/posts/{post_id}/comments
       {text, idempotency_key}
```

The client uploads media directly to object storage by using short-lived,
pre-signed URLs. App servers create and authorize the upload but never proxy
the large media bytes.

`PUT` makes following and liking naturally idempotent. Repeating the same
request produces the same final state.

## High-level architecture

```text
                        WRITE PATH

 Mobile client --create upload--> API gateway --> Post service --> Metadata DB
      |
      +--multipart upload------------------------------> Object storage
                                                              |
                                                      "upload complete"
                                                              v
                                                     Processing queue
                                                              |
                                           +------------------+----------------+
                                           |                                   |
                                      Media workers                    Safety checks
                                  resize/transcode/package             moderation
                                           |                                   |
                                           +------------------+----------------+
                                                              |
                                              Processed object storage (origin)
                                                              |
                                                        Post becomes READY
                                                              |
                                                        Post event stream
                                                              |
                                                  Feed fan-out workers
                                                              |
                                                     Home feed store

                         READ PATH

 Mobile client --> CDN ---------------------> Object storage origin
      |
      +--> API gateway --> Feed service --> Feed cache/store
                               |                  |
                               |                  +--> Post hydration service
                               |                           |
                               v                           +--> Metadata cache/DB
                         Ranking service
                               |
                         Social graph service
```

The main components are:

* The Post service owns post metadata and lifecycle.
* The Media pipeline validates, scans, resizes, and transcodes uploads.
* The Social Graph service owns follow relationships.
* The Feed service builds candidate lists and serves home feeds.
* The Ranking service orders candidates for a specific viewer.
* The Engagement service owns likes, comments, and counters.
* Object storage holds originals and processed media.
* The CDN serves media close to users.
* An event stream separates publishing from feed generation, notifications,
  analytics, and moderation.

## Data model

### Core entities

```text
User
  user_id, username, profile, privacy_mode, status, created_at

Post
  post_id, author_id, caption, media_manifest_key,
  status, visibility, created_at, deleted_at

MediaAsset
  asset_id, post_id, type, variant, object_key,
  width, height, duration, checksum, status

Follow
  follower_id, followee_id, status, created_at

Like
  post_id, user_id, created_at

Comment
  comment_id, post_id, author_id, text, status, created_at

FeedEntry
  owner_id, post_id, author_id, event_time, ranking_features
```

### Identifier choice

Use roughly time-ordered 64-bit IDs, such as Snowflake IDs:

```text
timestamp | region or worker | per-millisecond sequence
```

They are unique without a central database round trip, and their time ordering
helps pagination and storage locality. Do not expose raw database auto-
increment IDs across shards.

### Partition keys

| Data              | Partition key              | Reason                                      |
|-------------------|----------------------------|---------------------------------------------|
| User profile      | `user_id`                  | Direct lookup                               |
| Author's posts    | `author_id`                | Profile page reads one author's timeline    |
| Followers         | `followee_id` plus buckets | Fan-out needs all followers of an author    |
| Following         | `follower_id`              | Authorization and feed reads need followees |
| Home feed entries | `owner_id` plus time bucket | One user's feed is read together           |
| Likes             | `post_id` plus buckets     | A popular post may receive massive traffic  |
| Comments          | `post_id` plus buckets     | Comments are read with the post             |

Very large adjacency lists need buckets. A celebrity's followers cannot fit
in one partition, so split them by a stable hash of `follower_id`.

## Deep dive 1: media upload and delivery

### Upload flow

1. The client asks the Post service to create an upload.
2. The service creates a `PENDING_UPLOAD` post and returns pre-signed
   multipart URLs.
3. The client uploads chunks directly to object storage. It can retry only
   failed chunks after a network interruption.
4. Object storage emits an upload-complete event.
5. Workers verify the checksum, inspect the file, and run safety checks.
6. Image workers create sizes and formats such as JPEG, WebP, and AVIF. Video
   workers create several resolutions, bitrates, thumbnails, and a streaming
   manifest.
7. Workers write immutable variants to processed object storage.
8. A finalizer transaction changes the post to `READY` and writes a
   `PostPublished` event through an outbox.
9. Feed generation starts only after the post is ready.

### Why a post has a lifecycle

```text
PENDING_UPLOAD -> PROCESSING -> READY
                       |
                       +-> REJECTED

READY -> DELETING -> DELETED
```

A feed must never point at a half-processed upload. The state machine makes
that rule explicit. Conditional updates prevent two completion callbacks from
publishing the post twice.

### Transactional outbox

Updating the post and publishing an event as two unrelated operations creates
two failure cases:

* The post becomes ready, but the process crashes before emitting the event.
* The event is emitted, but the database transaction later fails.

Write the post update and an outbox row in one database transaction. A relay
publishes outbox rows to the event stream and marks them delivered. Consumers
deduplicate by event ID, so relay retries are safe.

### Media object keys

Use immutable, versioned object keys:

```text
media/{post_id}/{asset_id}/{processing_version}/{variant}.{extension}
```

Immutable URLs cache well because the bytes never change. If processing logic
changes, write a new version and atomically update the media manifest instead
of overwriting cached objects.

### CDN delivery

The feed API returns metadata and CDN URLs. The client then fetches media
directly from a nearby CDN edge:

```text
Client -> edge cache -> regional cache -> object storage origin
```

Use long cache lifetimes for immutable media. Public posts can use signed or
unsigned CDN URLs depending on abuse requirements. Private posts should use
short-lived signed URLs created only after authorization.

### Deletion and privacy

Deleting the database row is not enough because the CDN may still hold bytes.

1. Write a deletion tombstone and immediately deny new metadata and signed URL
   requests.
2. Publish a high-priority deletion event.
3. Purge CDN keys and delete all object variants.
4. Remove the post from feed stores and search indexes.
5. Retain the tombstone long enough to reject delayed retries and replayed
   events.

CDN purge is not instantaneous. Sensitive media URLs should expire quickly,
and the CDN should recheck authorization when required. Privacy correctness is
more important than maximizing cache hit rate.

## Deep dive 2: social graph

### Store both directions

A follow relationship supports two different queries:

```text
following(user_id) -> accounts this user follows
followers(user_id) -> users who follow this account
```

Store both adjacency lists because deriving one from the other at read time
would require scanning the whole graph. A follow command writes the source of
truth and emits an event that updates both query views.

For a public account:

```text
NONE -> FOLLOWING -> NONE
```

For a private account:

```text
NONE -> REQUESTED -> FOLLOWING
            |
            +-> REJECTED
```

The authorization service treats only `FOLLOWING` as permission to see
private posts.

### Consistency choice

The follower count can lag. Access control cannot.

* The authoritative relationship is read with strong consistency when
  checking a private post.
* Cached adjacency lists and displayed follower counts are eventually
  consistent.
* Blocking or removing a follower writes a deny record first. Asynchronous
  jobs then clean feed entries and caches.

This favors false denial for a short period over leaking private media.

### High-degree accounts

A normal user's follower list can live in one or a few partitions. A celebrity
may have hundreds of millions of followers, so:

* Bucket followers by `hash(follower_id) % N`.
* Read buckets in parallel for background jobs.
* Increase `N` without moving everything at once by using virtual buckets.
* Never load the entire list into one process.

## Deep dive 3: home feed generation

The home feed needs two stages:

1. Candidate generation finds eligible posts.
2. Ranking orders those posts for the viewer.

Trying to join posts, follows, privacy rules, and engagement for every feed
request is too slow at hundreds of thousands of reads per second.

### Option 1: fan-out on read

When a user opens the feed:

1. Read the accounts they follow.
2. Fetch recent posts from each account.
3. Merge the sorted lists.
4. Filter and rank the result.

Advantages:

* Publishing is cheap.
* Deleted and newly published posts are naturally fresh.
* Celebrity posts do not cause millions of writes.

Disadvantages:

* Feed reads perform work proportional to the number of followed accounts.
* A user following thousands of accounts causes a wide scatter-gather query.
* Ranking cannot start until candidate collection finishes.

### Option 2: fan-out on write

When an author publishes, workers append the post ID to each follower's home
feed inbox.

Advantages:

* Feed reads become a fast lookup by viewer ID.
* Candidate generation is already done.
* The system can absorb fan-out asynchronously through a queue.

Disadvantages:

* A celebrity post creates millions of writes.
* Many generated entries are never read.
* Unfollow, deletion, and privacy changes require cleanup or read-time
  filtering.

### Hybrid fan-out

Use fan-out on write for normal accounts and fan-out on read for high-degree
accounts.

```text
Normal author publishes
    -> event stream
    -> workers read follower buckets
    -> append post reference to follower inboxes

Celebrity author publishes
    -> append once to celebrity outbox

Viewer opens feed
    -> read precomputed inbox
    -> fetch recent posts from followed celebrity outboxes
    -> merge, filter, rank, and paginate
```

The threshold should be operational, not hard-coded forever. It depends on
follower count, posting frequency, active-follower ratio, fan-out queue depth,
and available write capacity.

> [!TIP]
> Say this clearly: "A user with 100 million followers is not only a large
> normal user. They need a different write strategy. I avoid the celebrity
> fan-out explosion by pulling those authors' recent posts during feed reads."

### Feed entry contents

A feed entry is a small reference:

```text
viewer_id, post_id, author_id, published_at,
reason, lightweight ranking features
```

Do not copy captions, counters, profiles, or media URLs into every feed entry.
Those fields change and would multiply update cost. Hydrate selected post IDs
in batches from metadata caches after ranking.

### Fan-out worker design

1. Consume a `PostPublished` event.
2. Read one follower bucket at a time.
3. Write feed entries in batches.
4. Checkpoint the last completed bucket and page.
5. Retry failed batches.
6. Deduplicate with `(viewer_id, post_id)`.

Partition the event stream by `author_id` to preserve an author's post order.
Use enough follower buckets to parallelize a popular author's fan-out without
letting one post monopolize all workers.

### Backpressure

If the fan-out queue grows:

* Prioritize recent posts over old retries.
* Reserve worker capacity per author class to prevent a popular account from
  starving normal users.
* Reduce nonessential precomputed features.
* Temporarily move large authors to pull-on-read.
* Keep serving the previous feed instead of failing requests.

The queue turns a sudden burst into delayed freshness rather than an outage.

## Deep dive 4: ranking and pagination

### Candidate generation before ranking

Ranking every post from every followed account is too expensive. First collect
perhaps 500 to 2,000 eligible recent candidates from:

* The viewer's precomputed inbox
* Recent celebrity posts pulled on read
* A small retry window for fan-out lag

Then apply:

1. Hard filters for blocks, privacy, deletion, region policy, and content
   safety.
2. Lightweight ranking to reduce the set.
3. A more expensive model for the final candidates.
4. Diversity rules that limit repeated posts from one author or media type.

Example ranking features:

* Recency
* Relationship strength from profile visits, messages, and prior engagement
* Predicted probability of viewing, liking, commenting, or hiding
* Post engagement rate, normalized for author size and post age
* Content type preference
* Negative feedback and safety signals

Ranking features must be available from low-latency stores. The request path
cannot run large analytical queries.

### Stable pagination

Offset pagination such as `?page=10` is a poor fit:

* New posts shift every later page.
* The same post can appear twice or be skipped.
* Large offsets become expensive.

Use an opaque cursor:

```text
base64(feed_session_id, last_rank, last_post_id, model_version, expiry)
```

On the first request, create a short-lived feed session containing an ordered
candidate snapshot or enough state to reconstruct it. Later requests continue
after the last returned item.

The cursor is signed so the client cannot change viewer or ranking state. It
expires after a short period, such as 10 to 30 minutes. A refresh starts a new
session and can include new posts.

### Why not sort only by timestamp

Reverse chronological order is simple and deterministic, and it is a good
fallback. At Instagram scale, users cannot read every eligible post. Ranking
improves relevance but adds model latency, feature dependencies, and
explainability concerns.

If the Ranking service is unavailable, serve a reverse-chronological merge of
the stored candidates. A less personalized feed is better than no feed.

### Read-time correctness filters

Precomputed feeds are stale by design. Before returning an item, batch-check:

* The post is still `READY` and not deleted.
* The viewer is not blocked by the author and has not blocked the author.
* A private author's follow relationship is still valid.
* The post is allowed in the viewer's region and age group.

Background cleanup reduces stale entries, but read-time filtering is the final
privacy boundary.

## Deep dive 5: likes, comments, and counters

### Likes

The source-of-truth row uses `(post_id, user_id)` as its unique key:

```sql
INSERT INTO likes(post_id, user_id, created_at)
VALUES (?, ?, ?)
ON CONFLICT DO NOTHING;
```

This prevents duplicate likes when a mobile client retries. An unlike deletes
that row idempotently. At very high scale, this write moves off the request
path and into the async Kafka and Flink pipeline described below.

A popular post can overload one partition. Hash likes into buckets:

```text
partition = (post_id, hash(user_id) % 128)
```

The exact relationship is authoritative. The displayed count is a derived,
eventually consistent value maintained by stream processors.

### Counters

Updating `posts.like_count = like_count + 1` for every event creates a hot
row. Instead:

1. Like and unlike events enter a partitioned stream.
2. Consumers aggregate deltas in memory over a short window.
3. Consumers flush bucketed counters.
4. The read path sums cached bucket values or reads a compacted total.
5. Periodic reconciliation compares totals with source-of-truth like rows.

A user may see a count that is a few seconds behind, which is acceptable.

### Async like pipeline with Kafka and Flink

At peak, likes can reach millions per second. Writing each one to the
database inside the API request puts storage latency on the user's path and
sends traffic spikes straight to the database. Instead, make the write path
asynchronous:

```text
Client
  |
  v
Like API  (auth, rate limit, validate)
  |
  | LikeSet { operation_id, user_id, post_id, liked: true/false, sequence }
  v
Kafka: like-commands  (partition key = hash(post_id, user_id))
  |
  v
+--------------------------------------------------------------+
| Flink job                                                    |
|                                                              |
|  Stage 1: keyBy(post_id, user_id)                            |
|  "Did this user's like state actually change?"               |
|        |                                                     |
|        +----------------------> Kafka: like-state-changes    |
|        |                              |                      |
|        | (+1 / -1 only)               v                      |
|        v                       Like State Writer (batched)   |
|  Stage 2: keyBy(post_id)              |                      |
|  "What is the total now?"             v                      |
|        |                       Sharded Like Store            |
+--------|-----------------------------------------------------+
         v
   Kafka: like-count-updates  (or a direct Redis sink)
         |
         v
   Redis + durable counter store
```

#### API behavior

* The client sends the desired state (`liked=true`), not an increment.
  Sending the same desired state twice has no extra effect.
* The API returns `202 Accepted` after Kafka confirms the write is replicated.
  At that point the like is durably accepted but not yet stored in the
  database.
* If Kafka is unavailable, return a retryable error. Never acknowledge a like
  that isn't durably stored.
* Partition by `(post_id, user_id)` so like, unlike, and like again for one
  pair stay in order. Partitioning only by `post_id` would make a viral post
  a hot partition.

#### Stage 1: find real changes for each pair

Keyed by `(post_id, user_id)`. Flink stores the last known `liked` value and
sequence number for each pair.

| Stored state       | Incoming          | Output                      |
|--------------------|-------------------|-----------------------------|
| false, seq 16      | liked=true, 17    | `+1`, update state          |
| true, seq 17       | liked=false, 18   | `-1`, update state          |
| true, seq 17       | liked=true, 17    | Nothing (duplicate)         |
| true, seq 19       | liked=false, 18   | Nothing (old, out of order) |

The output contains only real changes:

```text
LikeStateChanged { operation_id, post_id, user_id,
                   previous: false, current: true, delta: +1 }
```

This output goes to two places:

1. The Kafka topic `like-state-changes`. The Like State Writer reads it,
   groups events by shard, and upserts
   `(post_id, user_id) -> liked, sequence` in batches. The upsert is
   idempotent, so replaying a batch after a crash is safe.
2. Stage 2 of the same Flink job. Flink passes data between stages
   internally, so this hop doesn't need Kafka.

#### Stage 2: add up the count for each post

Keyed by `post_id`. Flink adds up the `+1` and `-1` values and sends the
**absolute count** every second or so:

```text
SET post:123:like_count 8501     # safe to repeat
INCR post:123:like_count         # NOT safe: a replay double counts
```

For viral posts, avoid one hot Flink task by using two-level aggregation:

```text
keyBy(post_id, hash(user_id) % 128)  -> partial counts
keyBy(post_id)                        -> combine partials into the total
```

The result goes to a Kafka topic when several consumers need it (Redis,
counter DB, trending, notifications), or straight to Redis through a sink
when it's the only consumer. The durable counter store uses a versioned
upsert so an older count never overwrites a newer one.

#### Why two stages

They need different keys. Removing duplicates must happen per user and post,
because only that pair knows whether a like is new. Counting must happen per
post. Flink re-routes the data between the two keys, but it's one job with one
checkpoint, so both stages recover together.

#### Stage 1 state size

Stage 1 keeps one entry for every like ever made, which could be trillions.

* Use the RocksDB state backend, which keeps state on local disk instead of
  in memory.
* A TTL saves space, but an expired entry looks like `liked=false`. A
  repeated `liked=true` would then count `+1` again by mistake.
* Fix: on a state miss, look up the Like Store with Flink Async I/O before
  deciding. Hot pairs stay in Flink state, and cold pairs fall back to the
  database.

#### Showing the user's own like right away

The Like Store can trail the API by a few seconds. Handle it with:

* An optimistic UI: the app fills in the heart right away and keeps it unless
  the server reports an error.
* Optionally, a short-lived `pending-like:{user_id}:{post_id}` cache entry
  that the read path checks before the Like Store.

Waiting for the database write to finish before replying would bring back the
latency this design removes, so don't do that for ordinary likes.

#### Failure behavior

| Failure                     | Effect                         | Why it's safe                                |
|-----------------------------|--------------------------------|----------------------------------------------|
| Flink falls behind          | Counts are stale               | Kafka keeps commands, so nothing is lost     |
| Flink restarts from checkpoint | Events are processed again  | Stage 1 removes duplicates, and counts are absolute `SET`s |
| Like State Writer crashes   | Batch is replayed              | Upsert with sequence is idempotent           |
| Redis is down               | Count is missing or older      | Read the durable counter store               |

Millions of writes per second are not the real problem. A single hot row is.
Relationship rows spread across `(post_id, bucket, user_id)` and written in
batches to an LSM-based store (Cassandra, ScyllaDB, DynamoDB) handle that
volume. The `like_count = like_count + 1` row does not.

> [!TIP]
> Interview line: "The API checks the request and returns once Kafka has
> durably stored the desired-state command. One Flink job has two stages.
> Stage 1 is keyed by post and user. It removes duplicate and old events and
> outputs only real +1 or -1 changes to a topic that a batch writer saves to
> the like store. Stage 2 is keyed by post. It adds up those changes and
> writes absolute counts to Redis and durable storage. The stages are
> separate because removing duplicates needs the user-post key and counting
> needs the post key."

### Comments

Comments need durable ordering and moderation. Partition by post and a bucket
for extremely popular posts. Store a time-ordered comment ID and paginate with
a cursor.

For a normal post, newest-first or oldest-first reads are straightforward.
For a viral post, rank a small "top comments" view separately while keeping
the complete chronological log as the source of truth.

### Exactly once is not required

Message systems normally provide at-least-once delivery. End-to-end
correctness comes from:

* Idempotent commands
* Unique database constraints
* Event IDs and consumer deduplication
* Reconciliation jobs

Claiming that Kafka alone makes likes exactly once would be incomplete.

## Caching

Use caches for data that is frequently read and safe to reconstruct:

| Cache                         | Key                 | Typical policy                         |
|-------------------------------|---------------------|----------------------------------------|
| User profile                  | `user_id`           | Minutes, invalidate on profile update  |
| Post metadata                 | `post_id`           | Minutes, tombstone on deletion         |
| Follow authorization          | viewer and author   | Short TTL, deny-first invalidation     |
| Home feed first page          | `viewer_id`         | Seconds to a few minutes               |
| Engagement counts             | `post_id`           | Seconds                                |
| Media                         | Immutable object URL | Long TTL at CDN                        |

Protect against cache stampedes with request coalescing, randomized expiry,
and stale-while-revalidate for non-sensitive data. Never serve stale privacy
authorization merely to improve availability.

## Storage choices

| Data                   | Store                                                | Reason                                         |
|------------------------|------------------------------------------------------|------------------------------------------------|
| User and post metadata | Sharded MySQL/PostgreSQL or distributed SQL          | Transactions, indexes, lifecycle correctness   |
| Media                  | Object storage plus CDN                              | Durable, cheap, large binary objects            |
| Follow graph           | Sharded key-value or wide-column store               | Large adjacency lists and direct key reads      |
| Home feed entries      | Cassandra, ScyllaDB, or another wide-column store    | High write rate, owner and time range reads     |
| Feed first page        | Redis or equivalent                                  | Very low read latency                           |
| Likes and comments     | Sharded relational or wide-column store              | Idempotent writes and post-scoped reads         |
| Event stream           | Kafka or equivalent                                  | Fan-out, counters, moderation, notifications    |
| Ranking features       | Online feature store plus offline analytical storage | Low-latency inference and model training        |

Product requirements should drive the database choice. A named technology is
not the design.

### Feed store shape

For a wide-column store:

```text
Partition key: (viewer_id, time_bucket)
Clustering key: published_at DESC, post_id DESC
Value: author_id, source, lightweight features
```

Time buckets stop a very active user's partition from growing forever. Retain
only a bounded candidate window, such as the latest few thousand entries.
Older feed entries can be rebuilt from author timelines if needed.

## Multi-region design

### User home region

Assign each user a home region:

* User and relationship writes go to the home region.
* Post metadata is synchronously durable within that region and replicated to
  other regions.
* Media uploads go to the nearest object-storage endpoint and replicate in the
  background.
* Feed entries are generated in the follower's home region when practical.
* Clients read from a nearby region that has the required authorization data.

This avoids active-active conflicts for most user-owned records.

### Global publishing

A post event crosses regions through replicated event streams. Followers may
see a new post at slightly different times. That is acceptable.

Privacy, blocks, and deletion events use a high-priority path and deny-first
semantics. If authorization state is uncertain, hide the content until the
system confirms access.

### Regional failure

During home-region failure:

* Serve replicated profiles, posts, cached feeds, and media.
* Accept engagement writes into a durable regional log with globally unique
  operation IDs, then reconcile later.
* Route privacy-changing writes only to a region that can provide required
  consistency, or fail them explicitly.
* Fall back to chronological feeds if ranking features are unavailable.

Do not make every feature equally consistent. Feed freshness can degrade.
Privacy must not.

## Failure scenarios

| Failure                         | User impact                              | Mitigation                                             |
|---------------------------------|------------------------------------------|--------------------------------------------------------|
| Upload interrupted              | Post remains pending                     | Multipart resume and upload expiry                     |
| Media worker crashes            | Processing is delayed                    | Idempotent tasks, visibility timeout, retry queue      |
| Publish relay crashes           | Feed event is delayed                    | Transactional outbox and relay retry                   |
| Fan-out workers fall behind     | New posts appear late                    | Queue buffering, autoscaling, pull-on-read fallback    |
| Duplicate post event            | Duplicate candidate is possible          | Unique `(viewer_id, post_id)` feed entry               |
| Feed cache is down              | Higher latency                           | Read durable feed store and rebuild cache              |
| Ranking service is down         | Less personalized feed                   | Reverse-chronological fallback                         |
| Metadata database is unavailable | Some posts cannot be hydrated           | Serve cached valid items and omit uncertain items      |
| CDN edge misses                 | Media starts more slowly                 | Regional shield cache and origin capacity              |
| Like event is delivered twice   | Count could drift                        | Event deduplication and periodic reconciliation        |
| User unfollows a private account | Stale feed entries may remain internally | Read-time authorization denies access immediately      |
| Post is deleted                 | Cached references may remain             | Tombstone, CDN purge, read-time status filter          |

## Abuse and safety

Safety is part of the architecture, not a later batch job:

* Validate file type and size before issuing upload credentials.
* Scan uploads before publication where policy requires it.
* Rate-limit posts, follows, likes, and comments by account, device, and
  network signals.
* Run spam and abuse detection on commands and event streams.
* Keep moderation state separate from public post state.
* Support legal holds and audit trails without exposing deleted content to
  normal read paths.
* Use random or signed media URLs so object keys cannot be enumerated.

## Trade-offs to state clearly

* Hybrid fan-out gives normal users fast reads without creating a celebrity
  write explosion. It makes the read path more complex because two candidate
  sources must be merged.
* Precomputed feeds trade storage and write amplification for predictable
  read latency.
* Ranking improves relevance but adds feature dependencies and model failure
  modes. Chronological order remains the fallback.
* Engagement counts are eventually consistent, while like membership is
  idempotent and authoritative.
* Long CDN caching reduces cost and latency, but private content needs
  short-lived authorization and fast revocation.
* Denormalized query views make reads fast, but events, deduplication, and
  reconciliation are required to keep them correct.
* Multi-region replication improves availability, but user ownership and
  deny-first privacy rules limit conflict complexity.

## Common interviewer follow-ups

### How does a new user get a feed

A new user has no graph history, so the Following feed may be empty. Product
onboarding can suggest accounts and a separate recommendation system can
provide discovery candidates. That recommendation system is outside this
core-following-feed design.

### What happens after an unfollow

The authoritative graph changes immediately. Old feed entries may remain in
the denormalized feed store, but read-time filtering removes them. A
background job later deletes them to save storage.

### How do we avoid one celebrity blocking the queue

Do not perform push fan-out for high-degree accounts. Also isolate worker
pools, limit per-author concurrency, partition follower buckets, and use fair
queue scheduling.

### How do we show a user's own new post immediately

Return the published post to the client and optimistically insert it into the
local profile view. The server also writes the author's profile timeline in
the publish transaction. Feed fan-out can remain asynchronous.

### How do we handle edits

Captions can update metadata and invalidate the post cache. Media edits create
new immutable variants and a new manifest version. Existing feed entries keep
the same post ID and hydrate the latest authorized metadata.

### Why not use a graph database

The main graph operations are direct adjacency-list reads: who I follow and
who follows an author. A sharded key-value or wide-column store handles those
queries predictably. A graph database is useful for multi-hop exploration,
but the critical feed path should not depend on expensive graph traversal.

## The answer in one paragraph

> "I would keep media bytes out of application servers. The client uploads
> multipart data directly to object storage, an asynchronous pipeline scans
> and creates immutable image or video variants, and a CDN serves those
> variants globally. Post metadata becomes visible only after processing
> completes, and a transactional outbox publishes the post event. For the home
> feed, I would use hybrid fan-out: push normal authors' post IDs into each
> follower's bounded feed inbox, but pull celebrity posts at read time to avoid
> millions of writes per post. The Feed service merges those candidates,
> applies privacy and deletion filters, ranks a few hundred items, hydrates
> metadata in batches, and returns a signed cursor. Likes are idempotent source-
> of-truth relationships, while counts are asynchronously aggregated. Feed
> freshness and counts are eventually consistent, but private-content access,
> blocks, and deletion use authoritative checks and deny-first behavior."

**Suggested 45-minute split:** 5 minutes requirements, 3 minutes estimates, 7
minutes high-level architecture, 20 minutes on media and hybrid feed fan-out,
5 minutes on ranking and pagination, and 5 minutes on failures and trade-offs.
