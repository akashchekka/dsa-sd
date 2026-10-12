---
title: Video on Demand System Design (Netflix / YouTube)
description: Interview notes on designing a video on demand platform, covering the upload and processing pipeline, adaptive bitrate streaming, CDN delivery, exabyte-scale object storage, hard problems, and failure handling
---

## Clarify the product first

Ask the interviewer which product they mean, because the answer changes where
the hard work is.

| Question                  | YouTube                                | Netflix                             |
|---------------------------|----------------------------------------|-------------------------------------|
| Who uploads?              | Anyone, millions of uploads per day    | The studio, a small curated catalog |
| How is popularity spread? | Long tail: a few videos get most views | Known catalog, predictable demand   |
| Hardest part              | The upload and processing pipeline     | Delivering huge bandwidth cheaply   |

These notes design for YouTube-style uploads and also cover the Netflix
delivery approach, since that's where the two differ.

## Requirements

### Functional requirements

* Upload a video.
* Watch a video smoothly on any device and any network.
* Search, view video details, and resume from where you stopped.

### Non-functional requirements

* **Fast start:** Playback begins in under 2 seconds and rarely stops to
  buffer.
* **Highly available:** Watching keeps working even when parts of the system
  fail.
* **Durable:** An uploaded video is never lost.
* **Eventual consistency is acceptable:** View counts and likes can lag by a
  few seconds.
* **Read heavy:** Roughly 1 upload for every 1,000+ views.

## Rough estimates

Assumptions:

* 1 billion daily users, each watching about 5 videos
* 100 million concurrent viewers at peak, at about 3 Mbps each
* About 500 hours of video uploaded every minute
* About 3 GB stored per hour of video, across all quality versions

| What               | Calculation       | Result                |
|--------------------|-------------------|-----------------------|
| Views per second   | 1B x 5 / 86,400   | ~60k/sec (peak ~150k) |
| Outgoing bandwidth | 100M x 3 Mbps     | **~300 Tbps**         |
| Uploads per day    | 500 hrs x 60 x 24 | ~720k hours/day       |
| New storage        | 720k hrs x 3 GB   | **~2 PB/day**         |

> [!IMPORTANT]
> No single datacenter can send 300 Tbps. **Video bytes must be served from a
> CDN close to users and never pass through our app servers.** That one fact
> shapes the whole design.

## High-level architecture

There are two separate paths: a slow upload path where async work is fine, and
a fast watch path where every millisecond counts.

```text
 UPLOAD PATH (slow, async is fine)
 Client --1. get upload URL--> Upload Service --> Metadata DB (status=UPLOADING)
   |
   +--2. upload chunks directly--> Object Storage (raw video)
                                          |
                                   3. "upload done" event
                                          v
                                    Message Queue
                                          v
                       Processing workers (split, transcode, package)
                                          v
                      Object Storage (segments + manifests) = ORIGIN
                                          v
                              Metadata DB (status=READY)

 WATCH PATH (must be fast)
 Client --1. play request--> Playback Service --> manifest URL + CDN choice
   |
   +--2. fetch segments--> CDN edge --miss--> Regional cache --miss--> Origin
   |
   +--3. progress heartbeats--> Watch History Service
```

The main pieces:

* **API layer:** An API gateway plus the Upload, Metadata, Playback, Search,
  and Watch History services.
* **Object storage:** Holds originals and processed video. Cheap and durable.
* **Processing pipeline:** A queue plus a pool of transcoding workers.
* **CDN:** Delivers the video bytes from servers close to the user.
* **Databases:** Metadata, watch history, and a search index.

## Core APIs

```text
POST /videos                       -> { videoId, uploadUrl }
PUT  <uploadUrl> (chunks)          -> straight to object storage
POST /videos/{id}/complete         -> starts processing
GET  /videos/{id}                  -> title, description, status, thumbnails
GET  /videos/{id}/play             -> { manifestUrl, drmToken }
POST /videos/{id}/progress         -> { positionSec }
GET  /search?q=...                 -> list of videos
```

## Upload flow

1. The client calls `POST /videos`. The service creates a record with
   `status = UPLOADING` and returns a **pre-signed upload URL**.
2. The client uploads **directly to object storage** in chunks of 5 to 10 MB.
   If the network drops, it resumes from the last finished chunk instead of
   starting over. Our servers never touch the video bytes.
3. When the upload finishes, storage emits an event and a message lands on the
   queue.
4. The processing pipeline picks up the job.

## Processing pipeline

Raw uploads can't be streamed as they are. They're too large and come in random
formats. The pipeline:

1. **Validate** the file and check for copyright and policy violations.
2. **Split** the video into small pieces, a few seconds each.
3. **Transcode the pieces in parallel** into a quality ladder (240p, 480p,
   720p, 1080p, 4K) and a few formats (H.264 for compatibility, VP9/AV1 for
   smaller files).
4. **Package** the output into small playable segments of about 4 seconds,
   plus a **manifest file** that lists every segment at every quality.
5. Generate thumbnails and captions.
6. Set `status = READY` and notify the uploader.

**Why split first?** Transcoding a 2-hour movie in one go takes hours. Split
into 1,000 pieces across 1,000 workers, it takes minutes.

The steps form a workflow (a DAG). Every task is **idempotent**, meaning it's
safe to run twice, so if a worker dies the task is retried.

## Adaptive bitrate streaming

This is the most important concept to explain well.

* The video is stored as **many small segments** of about 4 seconds, **at
  several quality levels**.
* The player first downloads the **manifest**, a menu of every segment at
  every quality.
* Before each segment, the player checks its bandwidth and how much video is
  buffered, then **picks the quality for the next segment**.
* On fast Wi-Fi it fetches 1080p. When the user walks into a tunnel, it
  switches to 240p **without stopping playback**.

Why it works so well:

* Playback starts fast, because the first segments can be low quality.
* Rebuffering is rare, because quality drops before the buffer runs out.
* Everything is **plain HTTP file downloads**, so any CDN can cache it.

The standard protocols are **HLS** (from Apple) and **DASH**.

## Watch flow

1. The client calls `GET /videos/{id}/play`.
2. The Playback Service checks login, subscription, and country rights. It
   picks the **best CDN server** for this user based on location, server
   health, and load.
3. It returns a **signed manifest URL** that expires in a few hours and, for
   paid content, a **DRM license** token.
4. The player fetches segments from the CDN edge. An edge hit is served
   directly. A miss goes to the **regional cache**, then the **origin**.
5. Every 10 seconds or so, the player sends a heartbeat with its position (for
   resume) and quality metrics (for monitoring).

## CDN strategy

### YouTube: pull-based for a long tail

* Popularity follows a power law: about 10% of videos get 90% of views.
* Popular segments are pulled into edge caches on first request and evicted
  with LRU.
* Rarely watched videos come from regional caches or the origin. That's
  slower, but rare.

### Netflix: push-based with Open Connect

* The catalog is known, so Netflix puts **its own cache servers inside ISP
  networks**.
* **During off-peak hours at night**, it pushes the content it predicts will
  be popular tomorrow.
* The hit rate is close to 100%, and almost no traffic crosses the internet
  backbone.

### Tiered caching

Edge -> regional -> origin. A miss at one of 1,000 edges hits a regional cache,
not storage, which protects the origin.

## Data storage

| Data                       | Store                                                 | Why                                              |
|----------------------------|-------------------------------------------------------|--------------------------------------------------|
| Video files and segments   | Object storage + CDN                                  | Huge, cheap, durable                             |
| Video metadata             | SQL sharded by `video_id`, read replicas, Redis cache | Read heavy and structured                        |
| Watch history and progress | Wide-column store (Cassandra), keyed by `user_id`     | Write heavy: a heartbeat every 10 sec per viewer |
| View counts and likes      | Events to Kafka, aggregated in batches                | Avoids millions of updates to one row            |
| Search                     | Elasticsearch, fed by changes from the metadata DB    | Full-text search                                 |

**Why not increment a counter on every view?** A viral video would send 100k
writes per second to one row, making it a hot spot. Instead, view events are
streamed, counted in memory over short windows, and written every few seconds.
A count that's a few seconds stale is fine.

## Storage at scale: 2 PB per day

### Check the numbers

| What                            | Calculation       | Result                     |
|---------------------------------|-------------------|----------------------------|
| Write speed needed              | 2 PB / 86,400 sec | **~23 GB/sec**             |
| Data written per year           | 2 PB x 365        | **~730 PB (~0.7 EB)**      |
| Raw disk with 3 copies          | 730 PB x 3        | ~2.2 EB                    |
| Raw disk with erasure coding    | 730 PB x 1.4      | **~1 EB**                  |
| Hard disks (20 TB each)         | 1 EB / 20 TB      | **~50,000 disks per year** |
| Storage servers (60 disks each) | 50,000 / 60       | **~850 servers per year**  |

What the numbers say:

* **Speed is not the problem.** One hard disk writes about 150 MB/sec, so
  23 GB/sec needs only a few hundred disks writing at once, and we'll have
  tens of thousands.
* **Capacity, cost, and failures are the problem.** We add about 850 servers
  every year. The design must scale out by adding machines, survive several
  disk failures every day, and use as few bytes as possible per byte stored.

> [!TIP]
> In the interview, first say: "I'd use a managed object store such as S3,
> GCS, or Azure Blob, which already run at exabyte scale." Then explain how
> one works inside if the interviewer asks.

### Why object storage fits video

Video is **written once, read many times, and never edited**.

* **Flat namespace:** A key such as `videos/abc123/1080p.mp4` maps to bytes.
  There are no real folders and no locking.
* **Immutable objects:** Nobody edits the middle of a file, which removes the
  hardest storage problems, like concurrent edits and partial updates.
* **Simple API:** `PUT`, `GET` (including **byte-range GET**), and `DELETE`.

### How a distributed object store works inside

The key idea: **separate "where is it" from the actual bytes.**

```text
                 Client (upload/transcode worker or CDN)
                         |
                         v
                 +---------------+
                 |  Front-end    |   stateless, auth, routing
                 |  API servers  |
                 +-------+-------+
            "where?"     |        "the bytes"
         +---------------+------------------+
         v                                  v
 +------------------+            +-----------------------------+
 | Metadata service |            | Storage nodes (thousands)   |
 | key -> chunk IDs |            | each: 60 HDDs, stores chunks|
 | chunk -> nodes   |            | across racks and zones      |
 | (sharded KV DB)  |            +-----------------------------+
 +------------------+                       ^
                                            |
                              Background: repair, scrub, rebalance
```

1. **Split big files into chunks.** A 3 GB file becomes 64 MB chunks spread
   across many storage nodes. Reads and writes run in parallel across many
   disks, and no single disk fills up with one giant file.
2. **Track locations in a metadata service.** It stores
   `object key -> [chunk IDs]` and `chunk -> [nodes]`. It's a sharded,
   replicated key-value database that holds only small records, never video
   bytes, so it stays fast.
3. **Write path.** The front end asks metadata for healthy nodes **in
   different racks and zones**, writes the chunks there, and returns
   **success only after enough copies are on disk**. That's what makes
   uploads durable.
4. **Read path.** Look up chunk locations (heavily cached), then read the
   chunks directly from storage nodes in parallel. **Byte-range reads** let
   the CDN fetch just one segment out of a large file.

### Durability: replication vs erasure coding

This is the biggest cost lever.

* **3 copies (replication):** Store each chunk on 3 nodes in 3 zones. Simple
  and fast, but costs 3x the raw size.
* **Erasure coding (10+4):** Split a chunk into 10 data pieces and compute 4
  extra parity pieces with Reed-Solomon math. Store all 14 on different nodes.
  **Any 10 of the 14 rebuild the original**, so up to 4 can be lost, at only
  1.4x the raw size.

| Approach            | Storage overhead | Failures survived | Read and repair speed                      |
|---------------------|------------------|-------------------|--------------------------------------------|
| 3 copies            | 3.0x             | 2                 | Fast                                       |
| Erasure code (10+4) | **1.4x**         | **4**             | Slower: rebuilding needs math and 10 reads |

**Use both, based on age.** New uploads and hot videos keep 3 copies for fast
access and transcoding. After a few weeks, when most videos stop getting
views, convert them to erasure coding. At our scale, that saves about 1 EB of
disk per year. Facebook described this pattern publicly: Haystack for hot
data, f4 for warm data.

### Surviving constant disk failures

With 50,000+ disks, failures are a daily routine, not an emergency.

* **Heartbeats:** Every storage node reports its health every few seconds.
* **Automatic repair:** When a disk dies, the system finds every chunk that
  lost a copy and rebuilds it on other nodes. Chunks are spread widely, so
  hundreds of disks share the repair work and it finishes quickly.
* **Scrubbing:** A background job re-reads data and checks **checksums** to
  catch silent corruption (bit rot), then fixes it from the good copies.
* **Placement rules:** No two copies or pieces share a rack or power domain,
  so one rack failure never loses data.

### The hidden trap: too many small files

Count the **files**, not just the bytes:

* 720k hours/day x 900 segments per hour x ~12 versions (qualities x formats)
* = **~7.8 billion tiny files per day**

Every file costs one metadata record and one disk seek, so this would
overwhelm the metadata service.

**The fix:** Store **one file per quality level**, not one file per segment.
Each 4-second segment becomes a **byte range** inside that file, and the
manifest lists the ranges. Both HLS and DASH support this. That drops it to
about 10 million files per day, roughly 800x fewer, with the same bytes.

### Store fewer bytes in the first place

| Technique                        | How                                                                                      | Saving                                      |
|----------------------------------|------------------------------------------------------------------------------------------|---------------------------------------------|
| Lazy versions                    | Create only basic qualities at upload. Create 4K and AV1 only when a video gets popular. | Large, since most videos get few views      |
| Deduplication                    | Hash each upload. If the same file exists, point to it.                                  | Re-uploads and reposts                      |
| Storage tiers by age             | Hot (fast disks) -> warm (erasure coded) -> cold archive (cheapest, slow to read)        | Cold storage costs a fraction of hot        |
| Original in cold storage         | Keep the raw upload, but archive it. It's only needed to re-encode with future codecs.   | The largest file moves to the cheapest tier |
| Better codecs for popular videos | AV1/VP9 files are about 30 to 50% smaller than H.264.                                    | Saves storage and CDN bandwidth             |
| Delete unwatched versions        | If a 4K version isn't watched for a year, delete it and re-create it on demand.          | Long tail cleanup                           |

```text
 Upload --> HOT tier (3 copies)  -- weeks -->  WARM tier (erasure coded)
              ^     |                                  |
   popular again    v                         months, no views
              |   CDN pulls segments                   v
              +------------------------------ COLD / ARCHIVE tier
                                              (originals, dead videos)
```

> [!NOTE]
> The pattern to state out loud: video popularity follows a power law. **A
> small fraction of videos gets nearly all the views**, so spend storage and
> compute on popular videos and keep the long tail cheap.

## The hard problems

### 1. Viral video (hot content)

A new video goes viral and every edge misses at once, flooding the origin.

* **Request coalescing:** If 10,000 users ask an edge for the same missing
  segment, the edge fetches it **once** and serves everyone.
* **Tiered caching:** Regional caches absorb the edge misses.
* **Pre-push trending videos** to edges before demand peaks.

### 2. Slow start and rebuffering

* Start at low quality, then step up.
* Keep the first segments short, about 2 seconds.
* **Prefetch the first few seconds** of the video the user will likely click
  next. Netflix does this on its home screen.

### 3. Transcoding cost

Transcoding is very expensive compute.

* Do cheap encoding (H.264, a few qualities) for every video.
* Do expensive encoding (AV1, 4K) **only for videos that become popular**. The
  bandwidth savings pay for the compute.
* **Per-title encoding (Netflix):** A cartoon needs a lower bitrate than an
  action movie for the same visual quality.

### 4. Upload reliability

* Resumable chunked uploads.
* Hash the content to detect duplicate uploads.

### 5. Content protection

* Signed CDN URLs that expire.
* **DRM** encrypts segments, so only licensed players can decode them.
* Fingerprinting (like Content ID) catches copyrighted re-uploads.

### 6. Global availability

* Metadata is replicated across regions, and the CDN is everywhere.
* If a region dies, the Playback Service steers users to other regions.
  Videos already cached at edges keep playing.

## Failure scenarios

| Failure                    | What happens                  | Mitigation                                                     |
|----------------------------|-------------------------------|----------------------------------------------------------------|
| CDN edge down              | Nearby users lose that server | Playback Service steers them to the next-nearest edge          |
| Origin storage slow        | Cache misses get slow         | Tiered caching, coalescing, serving slightly stale content     |
| Transcoding worker crashes | That task stalls              | The queue redelivers it, and idempotent tasks make retry safe  |
| Disk or storage node dies  | Some chunks lose a copy       | Automatic repair rebuilds them from the remaining copies       |
| Metadata DB down           | Video pages can't load        | Read replicas plus cache, and playback of known videos goes on |
| Whole region down          | API calls fail there          | Route users to another region, since the CDN is independent    |

## What to monitor

* **Video start time:** How long until the first frame appears.
* **Rebuffer ratio:** The share of watch time spent buffering. This is the
  top user-experience metric.
* **CDN hit rate** at the edge and regional tiers.
* **Transcoding queue lag:** How long uploads take to become watchable.
* **Storage growth and repair backlog:** Tell you when to add capacity.
* **Playback error rate**, split by device, ISP, and region.

## Interview summary

> "The defining fact is bandwidth: hundreds of terabits per second. So video
> bytes never touch our servers. They go **straight to object storage on
> upload** and are served **from a CDN on playback**.
>
> On upload, the client sends chunks directly to storage with a pre-signed URL.
> An event triggers a pipeline that **splits the video, transcodes the pieces
> in parallel** into several qualities and formats, and packages them into
> **small segments with a manifest**.
>
> On playback, the Playback Service checks rights, picks the best CDN server,
> and returns a signed manifest URL. The player uses **adaptive bitrate
> streaming**, choosing a quality per segment based on network speed, so
> playback starts fast and rarely stalls.
>
> Caching is tiered (edge, regional, origin) with request coalescing to
> survive viral videos. YouTube pulls popular content into caches. Netflix
> **pushes predicted content to servers inside ISPs at night**.
>
> Storage grows by about 2 PB a day. An object store splits files into chunks
> tracked by a metadata service. Hot data keeps **3 copies**, and older data
> moves to **erasure coding** at 1.4x cost. Segments are byte ranges inside
> one file per quality to avoid billions of tiny files. And we **store less**
> by creating high qualities only for popular videos, deduplicating, and
> tiering cold content to archive.
>
> Metadata lives in sharded SQL with a cache, watch progress in Cassandra, and
> view counts are aggregated from an event stream instead of updated per view."

### How to spend a 45-minute interview

* 5 minutes on requirements and estimates.
* 10 minutes on the architecture diagram and the two paths.
* 20 minutes on deep dives: processing, adaptive streaming, CDN, and storage.
* 10 minutes on hard problems and failures.
