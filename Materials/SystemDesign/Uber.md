---
title: Ride Hailing System Design (Uber)
description: Interview notes on designing Uber, covering the geo index, matching without double booking, write-heavy location updates, connection gateways, WebSocket vs MQTT, and Redis GEO vs PostGIS
---

## Requirements

### Functional requirements

* A rider enters pickup and drop-off and sees a price and an arrival time.
* A rider requests a ride, and the system matches them with a nearby driver.
* The driver accepts or declines the request.
* Both sides see each other's location live during the trip.
* Trip lifecycle: requested, driver on the way, trip started, trip completed.
* Payment happens after the trip.

Out of scope (say this out loud): shared rides, food delivery, scheduled rides,
and driver onboarding.

### Non-functional requirements

* **Fast matching:** Matching finishes within a few seconds.
* **Fresh locations:** Drivers send updates every few seconds.
* **No double booking:** A driver never gets two trips at once, and a ride
  never gets two drivers. This part needs strong correctness.
* **Eventually consistent locations:** A position that's 2 seconds old is
  fine.
* **Highly available:** If it goes down, riders get stranded.

> [!IMPORTANT]
> Say this early: "There are two kinds of data here. Driver locations are huge
> in volume but short-lived, so losing one update doesn't matter. Trips are low
> in volume but must be exactly right. I'll design those two parts
> differently."

## Rough estimates

| What                     | Calculation              | Result                         |
|--------------------------|--------------------------|--------------------------------|
| Trips per day            | assume                   | 20M                            |
| Ride requests per second | 20M / 86,400             | ~230/sec average, ~2k/sec peak |
| Drivers online at peak   | assume                   | ~1M                            |
| Location updates         | 1M drivers / every 4 sec | **~250k writes/sec**           |
| Live location memory     | 1M x ~100 bytes          | **~100 MB**                    |

Location updates are the heavy part, and they fit easily in memory. Trips are
low volume. So this is a **write-throughput problem for locations** and a
**correctness problem for trips**, not a storage problem.

## APIs

```text
POST /rides/estimate      {pickup, dropoff}             -> {price, eta, quote_id}
POST /rides               {quote_id, idempotency_key}   -> {ride_id}
POST /drivers/location    {lat, lng, timestamp}         (sent over a persistent connection)
POST /rides/{id}/accept   (driver)
POST /rides/{id}/status   {arrived | started | completed}
Live updates are pushed to apps over a persistent connection (WebSocket, gRPC stream, or MQTT).
```

The **idempotency key** on ride requests means a double tap on a bad network
doesn't create two rides.

## High-level architecture

```text
  Rider app            Driver app
      |                    |   (location every 4-5 sec)
      v                    v
 +--------------------------------+
 | Load balancer + API gateway    |
 | Connection gateway (live push) |
 +--------------------------------+
   |         |          |         |
   v         v          v         v
 Pricing  Matching   Location   Trip service ---> Trip DB (strongly consistent)
 service  service -> service                         |
   ^         |       (in-memory                      v
   |         |        geo index)              Payment service
   |         v           |
   |     ETA / maps      +--> Event stream (Kafka) --> history, analytics,
   +---------------------------------------------- surge calculation
```

Main services:

* **Location service:** Knows where every online driver is right now.
* **Matching service:** Finds the best driver for a request.
* **Trip service:** Owns the trip state machine and is the source of truth.
* **Pricing service:** Price estimates and surge pricing.
* **Connection gateway:** Keeps live connections open to phones.

## Deep dive 1: finding nearby drivers

### The naive approach fails

A query like `SELECT drivers WHERE lat BETWEEN ... AND lng BETWEEN ...` against
a database taking 250k writes per second is too slow, and the indexes thrash on
every write.

### Divide the map into cells

* Split the world into a grid. Each cell gets an ID and covers a few city
  blocks.
* Common options are **Geohash** (squares), **Google S2** (squares on a
  sphere), and **Uber H3** (hexagons).
* Keep an in-memory map from `cell_id` to the set of drivers in that cell.
* **Driver update:** Compute the driver's cell. If it changed, remove the
  driver from the old cell and add them to the new one.
* **Rider search:** Compute the rider's cell plus the neighboring ring of
  cells, collect those drivers, and sort them by distance. If there aren't
  enough, widen the ring.

**Why hexagons?** All 6 neighbors of a hexagon sit at the same distance from
its center. With squares, corner neighbors are farther away than side
neighbors, so the search radius is less even.

### Storage choices

* Keep it **in memory** (Redis GEO or a custom service). The data is only
  100 MB and changes every few seconds.
* **Shard by city or region.** Rides are local, so a rider in Mumbai never
  needs drivers in London. Split a very busy city into more shards by cell.
* Treat it as **soft state.** Each driver entry has a 30-second expiry. If a
  driver goes silent, they drop off the map. If a node dies, drivers resend
  within seconds and the index rebuilds itself.
* **Don't write every location update to a database synchronously.** Send
  updates to Kafka for trip history and analytics instead.

## Deep dive 2: Redis GEO vs PostGIS

Use Redis GEO (or another in-memory index) for **live driver locations**, and
PostGIS for **map data that rarely changes**, like city boundaries, airport
zones, and surge areas. At Uber scale you use both, each for a different job.

### What each one is

**Redis GEO** is a sorted set underneath. Each driver is a member, and the
score is a geohash of their position, a number that encodes latitude and
longitude. Everything lives in memory, and it answers one question well: which
points are within X km of here?

```text
GEOADD    drivers:mumbai:available  72.83 18.94  driver_42      # add or move a driver
GEOSEARCH drivers:mumbai:available  FROMLONLAT 72.83 18.94
          BYRADIUS 2 km  ASC  COUNT 20  WITHDIST                # 20 closest drivers
ZREM      drivers:mumbai:available  driver_42                   # driver took a trip
```

**PostGIS** adds real geography types to PostgreSQL: points, lines, and
polygons. It uses a spatial index (GiST, a tree of bounding boxes) stored on
disk, and it can answer complex questions like "is this point inside this
polygon" and join location data with other tables.

```sql
SELECT id FROM drivers
WHERE  ST_DWithin(location, ST_MakePoint(72.83, 18.94)::geography, 2000)
ORDER  BY location <-> ST_MakePoint(72.83, 18.94)::geography
LIMIT  20;
```

### Side-by-side

| Point                  | Redis GEO                                     | PostGIS                                                                  |
|------------------------|-----------------------------------------------|--------------------------------------------------------------------------|
| Where data lives       | Memory                                        | Disk, with memory caching                                                |
| Write speed            | Very high, 100k+ updates/sec per node         | Much lower. Every update rewrites the index and the write-ahead log.     |
| Read latency           | Under 1 ms                                    | A few ms, more under load                                                |
| Query types            | Points only: radius or box search             | Points, polygons, routes, intersections, joins                           |
| Durability             | Optional, may lose recent writes              | Fully durable, with transactions                                         |
| Frequent updates       | Built for it: an update replaces one number   | Painful: each update leaves an old row version, and vacuum falls behind  |
| Expiring stale drivers | No per-member expiry, needs a cleanup job     | Needs a query and a cleanup job                                          |
| Scaling out            | Shard by key, for example one key per city    | Harder: read replicas, or manual sharding                                |

### Why Redis wins for live locations

With ~250k updates per second and ~100 MB of data:

* The data fits in memory, so disk durability buys nothing.
* Each location is overwritten seconds later, so saving every version to disk
  wastes work.
* Postgres writes a new row version per update and marks the old one dead. At
  this rate, dead rows pile up faster than vacuum can clean them, and the
  spatial index keeps getting rewritten.
* A lost update doesn't matter, because the driver sends a new one shortly.

### Why PostGIS still has a place

Some location data is slow-changing and needs rich queries:

* Geofences: is the pickup inside the airport zone, which has special rules?
* City and service-area boundaries: is this address inside an area we serve?
* Surge zones and pricing regions, which are polygons.
* Analytics on trip history: which neighborhoods had the most cancellations
  last week?

Redis GEO can't do "point inside polygon" at all.

### Practical gotchas with Redis GEO

1. **No expiry per driver.** Expiry applies to the whole key. Keep a sorted
   set of `driver -> last_seen_time` and run a job every few seconds that
   removes drivers silent for more than 30 seconds.
2. **Store only available drivers in the search key.** Remove a driver
   (`ZREM`) when they take a trip, so matching doesn't filter out busy
   drivers.
3. **Avoid one giant key.** A key lives on one Redis node. Use one key per
   city, or per cell in very busy cities.
4. **Single-threaded per node.** A large radius search in a dense area can
   block other commands. Keep searches small and limit results with `COUNT`.

> [!TIP]
> "I'd keep live driver positions in an in-memory geo index like Redis GEO,
> sharded by city, because the workload is constant overwrites of disposable
> data. I'd use PostGIS for geofences, service areas, and historical analytics,
> where I need polygons and durability but the data rarely changes."

At very large scale, Uber built a custom in-memory service on H3 hexagon cells
instead of Redis. It's the same idea (cell ID mapped to the set of drivers)
with more control over sharding and ranking.

## Deep dive 3: matching (dispatch)

### The basic flow

1. A rider requests a ride, and the trip service creates it with state
   `REQUESTED`.
2. The matching service asks the location service for available drivers
   nearby.
3. It ranks them by **ETA on actual roads**, not straight-line distance. A
   driver across a river can be 200 m away and 15 minutes out.
4. It offers the ride to the best driver with a **15-second timeout**.
5. If the driver declines or times out, it offers the ride to the next driver.

### No double booking

Two ride requests could pick the same driver at the same moment. Fix it with
an **atomic claim** on the driver:

* Each driver has a status: `AVAILABLE`, `OFFERED`, or `ON_TRIP`.
* To offer a ride, matching does a **compare-and-set**: "change driver X from
  `AVAILABLE` to `OFFERED(ride 123)`, only if they're still `AVAILABLE`." Only
  one request can win.
* The offer is a **lease with a 15-second expiry**. If the matching server
  crashes mid-offer, the lease expires and the driver becomes free again.

### The trip as a state machine

```text
REQUESTED -> MATCHING -> DRIVER_ASSIGNED -> DRIVER_ARRIVED -> IN_PROGRESS -> COMPLETED
                \______________________________________________/
                                    -> CANCELLED
```

Every change is a conditional update ("move to `IN_PROGRESS` only if the
current state is `DRIVER_ARRIVED`"), so retries and duplicate messages are
harmless.

### Batch matching

Greedy matching (each rider takes the closest driver) isn't globally best.
Instead, collect requests in an area for 1 to 2 seconds and assign drivers to
riders together to minimize **total** wait time. It costs a small delay and
produces better matches across the whole city.

## Deep dive 4: handling write-heavy location updates

### Size the problem

| What                                        | Calculation                               | Result         |
|---------------------------------------------|-------------------------------------------|----------------|
| Online drivers at peak                      | assume                                    | 1M             |
| Updates per second                          | 1M / 5 sec                                | **200k/sec**   |
| Peak with headroom (events, New Year's Eve) | x 2.5                                     | **~500k/sec**  |
| Size per update                             | driver ID, lat, lng, time, heading, speed | ~100 bytes     |
| Bandwidth                                   | 500k x 100 bytes                          | **~50 MB/sec** |

Bandwidth is small. The challenge is the **number of tiny requests per
second**, so the design focuses on making each write as cheap as possible.

### The pipeline

```text
 Driver apps (1M)
     |  persistent connection, one small message every 5 sec
     v
 +-------------------------+
 | Connection gateways     |  ~30-40 servers, ~30k connections each
 | (validate, drop stale,  |
 |  attach city)           |
 +-------------------------+
     |
     v
 +-------------------------+
 | Kafka                   |  topic "driver-locations", partitioned by city
 | (buffer, durable log)   |
 +-------------------------+
     |            |              |                 |
     v            v              v                 v
 Geo index     Live trip     History store     Surge / analytics
 updater       tracking      (Bigtable or      (stream processing)
 -> Redis GEO  -> push to    Cassandra,
 (per city)    the rider     batched writes)
```

### 1. Persistent connections instead of one HTTP request per update

With plain HTTP, every update might open a connection, do a TLS handshake, and
send headers, all for 100 bytes of data.

* Keep **one long-lived connection** per driver over WebSocket, gRPC
  streaming, or MQTT.
* The handshake happens once, and each update is a small frame.
* Use a binary format like Protocol Buffers instead of JSON, which makes each
  message about 3 to 5 times smaller.
* The same connection carries ride offers **to** the driver, so it's needed
  anyway.

Gateway count: 1M connections / ~30k per server is about 35 servers, plus
headroom for losing a zone.

### 2. Keep the request path tiny

The gateway does only cheap work:

1. Checks the driver is authenticated (once, when the connection opens).
2. Drops the update if its timestamp is older than the last one seen from this
   driver, because networks can deliver messages out of order.
3. Tags the update with the driver's city.
4. Publishes it to Kafka and returns.

No database writes and no business logic in the request path. Updating the geo
index, pushing to the rider, saving history, and computing surge all happen
asynchronously in Kafka consumers.

### 3. Kafka as a shock absorber

* **Absorbs spikes:** If Redis slows down, updates wait in Kafka instead of
  failing.
* **Many readers share one write:** Geo index, live tracking, history, surge,
  and fraud detection each read the same stream.
* **Allows replay:** A rebuilt geo index node can reread recent updates.
* **Handles the volume:** 500k small messages per second (~50 MB/sec) is
  routine with around 100 partitions.

Partition by city, or by driver ID within very large cities, so all updates
for one driver stay in order.

Kafka adds roughly 10 to 50 ms of delay, which doesn't matter for locations
that refresh every 5 seconds.

> [!NOTE]
> The gateway could write straight to Redis and publish to Kafka on the side.
> That's slightly fresher, but the gateway then depends on Redis being healthy.
> Kafka first gives better isolation.

### 4. Make the writes cheap

In the geo index (Redis):

* Consumers **batch** updates, sending hundreds of `GEOADD` commands in one
  round trip (pipelining).
* Shard by city key, so no single node handles the whole world.
* Last write wins. An update overwrites the position, so the data never grows.

In the history store:

* Use a write-optimized database like **Bigtable or Cassandra**, which append
  writes to memory and a log and merge them to disk later.
* Write in batches, for example one row per driver per minute holding 12
  points.
* Use a row key like `driver_id + time` so a trip's route is one quick range
  read for billing.
* Old data expires or moves to cheap file storage for analytics.

### 5. Send fewer updates in the first place

| Driver state                | Update frequency                                       |
|-----------------------------|--------------------------------------------------------|
| On a trip                   | Every 3 to 5 sec (the rider is watching)               |
| Available and moving        | Every 5 sec                                            |
| Available but parked        | Only when moved more than ~50 m, or every 30 sec       |
| Offline                     | No updates                                             |

* **Distance filter:** Skip the update if the driver moved only a few meters.
* **Batch on bad networks:** In a tunnel, buffer points and send them together
  on reconnect, so billing routes stay complete.

This can cut total writes by 30 to 50%, because many available drivers are
parked.

### 6. Protect the system under overload

* **Per-driver rate limit:** At most one update every 2 seconds per driver,
  which guards against buggy or modified apps.
* **Load shedding with priority:** Drop updates from parked, available drivers
  first. Never drop updates for drivers on a trip.
* **No retries for stale data:** A failed update isn't retried. The app sends
  a fresh one instead.
* **Light acknowledgments:** No acknowledgment per update, or batched
  acknowledgments.

### Failure handling for location updates

| Failure                     | What happens                                    | Why it's fine                                                       |
|-----------------------------|-------------------------------------------------|---------------------------------------------------------------------|
| A gateway dies              | Its ~30k drivers reconnect to other gateways    | Apps reconnect with random delays (jitter), not all at once         |
| A Redis node dies           | Drivers in that city are briefly invisible      | The replacement fills from Kafka replay, or from fresh updates      |
| Kafka consumers fall behind | Positions get stale                             | Skip to the latest message per driver. Old positions are worthless. |
| History store is slow       | Writes queue up in Kafka                        | Matching and live tracking don't depend on it                       |

## Deep dive 5: live updates and connection gateways

### Push flow

* Each phone keeps a persistent connection open to a gateway server.
* A **connection registry** (in Redis) records which gateway each user is
  connected to.
* When an on-trip driver's location updates, the system looks up the rider's
  gateway and pushes the new position there.
* Ride offers go over the persistent connection, with a mobile push
  notification (APNs or FCM) as a fallback when the app is in the background.
* Every update carries a timestamp, and older updates are dropped. The driver
  app buffers locations while offline and uploads them later.

### Connection gateway vs API gateway

An API gateway handles short requests and forgets them. A connection gateway
holds a connection open for minutes or hours and must remember who is on it.

| Point               | API gateway / load balancer                     | Connection gateway                                        |
|---------------------|-------------------------------------------------|-----------------------------------------------------------|
| Lifetime            | Milliseconds per request                        | Minutes to hours per connection                           |
| State               | Stateless: any server can take the next request | Stateful: this server holds this user's connection        |
| Direction           | Client asks, server answers                     | Both directions. The server can push at any time.         |
| Routing             | Each request routed independently               | Routed once at connect time, then pinned to one server    |
| Bottleneck          | CPU per request                                 | Memory per connection, open files, heartbeats             |
| Server-to-user push | Not possible                                    | Needs a lookup: "which gateway holds user X?"             |
| Deploys             | Easy: drain in seconds                          | Hard: drain connections, and clients reconnect            |

```text
 Phones
   |
   v
 L4 load balancer      <- only spreads NEW connections, then steps aside
   |  (least-connections, not round robin)
   v
 +-----------+  +-----------+  +-----------+
 | Gateway 1 |  | Gateway 2 |  | Gateway N |   <- hold connections, heartbeats
 +-----------+  +-----------+  +-----------+
       ^              ^
       |  push        |  "user 42 is on Gateway 2"
       |              |
 Connection registry (Redis): user_id -> gateway
       ^
       |
 Backend services (matching, trips) push "new ride offer to driver 42"
```

The matching service looks up driver 42 in the registry, finds Gateway 2, and
sends the message there. Alternatively, each gateway subscribes to a pub/sub
channel for its own users.

### Problems only connection gateways have

* **Uneven load:** Connections last a long time, so round robin overloads old
  servers. Use least-connections balancing.
* **Load balancer idle timeouts:** Many cloud load balancers close silent
  connections after about 60 seconds. Send a heartbeat ping every 20 to 30
  seconds, which also detects dead phones.
* **Reconnect storms:** If a gateway with 30k users dies, they all reconnect.
  Clients wait a random delay with exponential backoff.
* **Deploys:** Ask clients to reconnect gradually over several minutes.
* **Missed messages:** Messages sent during a reconnect are lost unless they
  carry sequence numbers and the client asks for what it missed.

### What's used in practice

* **Load balancers for long-lived connections:** Envoy, NGINX, HAProxy, Google
  Cloud Load Balancing, AWS Network or Application Load Balancer.
* **Custom gateways at large scale:** Go, Java with Netty, or Erlang/Elixir
  (WhatsApp, Discord). Examples include Uber's push platform (moved to gRPC
  streaming), Netflix Zuul Push, Slack's edge gateways, and Facebook Messenger
  (MQTT).
* **Open-source starting points:** Socket.IO, Centrifugo, and MQTT brokers like
  EMQX, HiveMQ, and Mosquitto.
* **Managed services:** AWS API Gateway WebSocket APIs, AWS IoT Core, Azure Web
  PubSub, Azure SignalR Service, Firebase, Pusher, Ably, PubNub.
* **Fallback when the app is closed:** Apple Push Notification service and
  Firebase Cloud Messaging wake the app, for example to show a ride offer.

### Sizing for the Uber design

Connections:      ~1M drivers + ~1M riders with the app open = ~2M

Target per server: ~50k     (a crash disconnects only ~2.5% of users)

Servers needed:    2M / 50k = 40

Survive a zone:    spread across 3 zones, add ~50% -> ~60 servers

Message load:      200k location updates/sec / 60 = ~3.3k msgs/sec per server (easy)

Each server would hold only a few GB of connection state, with plenty of CPU left over. The 50k target comes from blast radius, not hardware.

### WebSocket vs WebRTC

One gateway can't handle both completely. It can carry WebRTC **setup**, but
audio and video need separate infrastructure.

| Point                   | WebSocket                                          | WebRTC                                                         |
|-------------------------|----------------------------------------------------|----------------------------------------------------------------|
| Purpose                 | Messages between a client and a server             | Audio, video, and data, ideally directly between two devices  |
| Transport               | TCP: reliable and in order                         | Mostly UDP: fast, late packets are dropped                     |
| How it starts           | An HTTP request that upgrades to a WebSocket       | Devices exchange connection details through a server, then connect |
| Traffic                 | Small messages (KBs)                               | Heavy media streams (Mbps)                                     |
| Other end               | Always your server                                 | Usually the other device, sometimes a relay or media server    |

```text
  Phone A                                              Phone B
     |  1. "Here's how to reach me" (signaling)            |
     +-------> WebSocket gateway  <------------------------+   <- can reuse your gateway
     |                                                     |
     |  2. "What's my public address?"  -> STUN server     |   <- tiny, cheap
     |                                                     |
     |  3a. Direct connection (UDP)  <-------------------->|   <- most calls
     |  3b. If firewalls block it: relay via TURN server   |   <- bandwidth heavy
     |                                                     |
     |  Group calls: everyone sends to a media server      |
     |  (SFU) that forwards streams to the others          |
```

* **Signaling** is small messages, so the WebSocket gateway can do it.
* **STUN servers** tell a phone its public internet address.
* **TURN servers** relay media when a direct connection is blocked, roughly 10
  to 20% of calls.
* **SFU servers** forward each person's stream to the others in group calls.

TURN and SFU servers need UDP, large port ranges, high bandwidth, and placement
close to users, so keep them as a separate fleet. Tools include coturn,
mediasoup, Janus, Jitsi Videobridge, LiveKit, Pion, and managed options like
Twilio, Cloudflare, Agora, Daily, and Amazon Chime SDK.

> [!NOTE]
> For Uber, rider-to-driver calls usually go through a phone provider like
> Twilio with number masking, so neither side sees the other's real number.
> In-app voice calls would use WebRTC, with signaling over the existing driver
> connection.

### WebSocket vs MQTT

They work at different layers. **WebSocket is a pipe:** a two-way connection
where you design the messages. **MQTT is a messaging system:** publish and
subscribe with topics, delivery guarantees, offline handling, and presence
detection, built around a central broker. MQTT can also run over a WebSocket,
which is how browsers use it.

```text
 WebSocket:   App  <---- raw messages (you design everything) ---->  Your gateway

 MQTT:        App  -- publish "location/mumbai/driver42" -->  Broker  --> subscribers
              App  <-- subscribed to "drivers/42/offers" ---  Broker  <-- matching service
```

| Point                     | WebSocket                                     | MQTT                                                                         |
|---------------------------|-----------------------------------------------|------------------------------------------------------------------------------|
| What it is                | A two-way connection                          | Publish/subscribe messaging protocol                                         |
| Server side               | Your own gateway code                         | An off-the-shelf broker (EMQX, HiveMQ, Mosquitto, AWS IoT Core)              |
| Message routing           | You build it, including the registry          | Built in: publish to a topic, the broker delivers to subscribers             |
| Delivery guarantees       | None. You build acknowledgments and retries.  | QoS 0 at most once, QoS 1 at least once, QoS 2 exactly once                  |
| Phone offline briefly     | Messages lost unless you build replay         | Persistent session: the broker queues messages for reconnect                 |
| Detecting a dead client   | You build heartbeats and timeouts             | Keep-alive, plus a "last will" message the broker publishes on disconnect    |
| Latest-value storage      | You build it                                  | Retained message: new subscribers get the last value immediately             |
| Message overhead          | Small (2 to 14 byte frame header)             | Very small (2 byte minimum), designed for weak networks and battery          |
| Browser support           | Native                                        | Needs MQTT over WebSocket                                                    |
| Flexibility               | Total                                         | Within the topic and QoS model                                               |

#### How MQTT maps to Uber

| Need                               | MQTT feature                          | Setting                                                                  |
|------------------------------------|---------------------------------------|--------------------------------------------------------------------------|
| Driver sends location every 5 sec  | Publish to `location/mumbai/driver42` | QoS 0. Losing one update is fine.                                        |
| Driver must receive a ride offer   | Subscribe to `drivers/42/offers`      | QoS 1. Duplicates are filtered by ride ID.                               |
| Driver's phone dies or loses signal | Last will: "driver42 offline"        | The broker announces it, so no more offers go to that driver             |
| Driver goes through a tunnel       | Persistent session                    | The offer waits in the broker and arrives on reconnect, if not expired   |
| Rider watches the driver's car     | Subscribe to `trips/123/driver-location` | The broker handles fan-out                                            |

Avoid QoS 2: its 4-step handshake per message is slow. Use QoS 1 and have the
receiver ignore duplicates by ID, the standard way to get exactly-once
behavior.

#### Downsides of each

MQTT:

* The broker is a big stateful system holding millions of connections,
  subscriptions, and queued messages.
* Custom per-message logic fits awkwardly into the topic model.
* Bad topic design, like everyone subscribing to `location/#`, overwhelms
  subscribers.
* Ordering is only per topic and per QoS level.

WebSocket:

* You build acknowledgments, retries, offline queues, presence, replay, and
  pub/sub routing yourself, in exchange for full control.

#### When to choose which

| Choose WebSocket when                                    | Choose MQTT when                                         |
|----------------------------------------------------------|----------------------------------------------------------|
| Clients are mostly browsers                              | Clients are mobile apps or IoT devices                   |
| You need custom logic per message (chat, editing, games) | Traffic fits publish/subscribe naturally                 |
| You want full control of the real-time stack             | You want delivery guarantees and offline handling built in |
| Patterns are request and response plus push              | Networks are unreliable and battery matters              |

Facebook Messenger adopted MQTT for mobile, AWS IoT Core and Azure IoT Hub are
MQTT at heart, Slack and Discord use WebSocket with custom gateways, and gRPC
bidirectional streaming is a third option (Uber's newer push platform).

> [!TIP]
> "For a driver app on unreliable mobile networks, MQTT fits well: locations at
> QoS 0, ride offers at QoS 1 with duplicate filtering by ride ID, and last
> will to mark drivers offline. The cost is running a large broker cluster. For
> browsers or custom per-message logic, I'd pick WebSocket with my own
> gateways."

## Pricing and surge

* Stream processing reads ride requests (demand) and available drivers
  (supply) per cell, every minute.
* If demand is much higher than supply, the cell gets a surge multiplier,
  stored in a cache.
* An estimate returns a **quote ID that locks the price for about 5 minutes**,
  so the rider pays the price they saw.

## Data storage

| Data                  | Store                                                         | Why                                           |
|-----------------------|---------------------------------------------------------------|-----------------------------------------------|
| Live driver locations | In memory, sharded by city                                    | Huge write rate, short-lived, fine to lose    |
| Trips                 | Strongly consistent database (Spanner, or sharded MySQL/Postgres) | Needs transactions and exact state        |
| Riders and drivers    | Relational database                                           | Low volume, structured                        |
| Location history      | Kafka, then Bigtable or Cassandra                             | Large, append-only, for billing and analytics |
| Geofences and zones   | PostGIS                                                       | Polygons, rarely changes                      |
| Payments              | Separate ledger service                                       | Must be exact and auditable                   |

Payments happen after the trip, asynchronously. Charge the card with an
idempotency key so a retry never double charges. If the charge fails, the trip
still completes and the rider gets an outstanding balance.

## Scale and multiple regions

* **Partition by geography.** Each region serves its own cities end to end:
  location, matching, and trips. A failure in one region affects only that
  region.
* **Region failure:** Active trip state is replicated to a standby region. Uber
  also keeps a copy of the current trip on the driver's phone, so a fresh
  datacenter can rebuild the trip from the app.

## Failure scenarios

| Failure                       | What happens                       | Mitigation                                                           |
|-------------------------------|------------------------------------|----------------------------------------------------------------------|
| Driver loses network mid-trip | Rider sees a frozen car            | App buffers locations and the trip continues. Upload on reconnect.  |
| Driver ignores the offer      | Rider waits                        | 15-second timeout, then offer to the next driver                     |
| Matching server crashes       | An offer is in flight              | Lease expires and the ride is re-queued. Matching holds no state.    |
| Location node dies            | Some drivers are briefly invisible | Drivers resend within seconds and the index rebuilds                 |
| Double tap on "Request"       | Possible duplicate ride            | Idempotency key                                                      |
| Payment provider down         | Charge fails                       | Retry later with the same idempotency key                            |

## Trade-offs to state clearly

* **Locations are eventually consistent and in memory.** Fast and cheap, and
  stale data lasts only seconds.
* **Trips and driver claims are strongly consistent.** Double booking is
  unacceptable, and the volume is low enough to afford it.
* **Sharding by geography** matches how the product works, but very busy
  cities need finer splitting.
* **Batch matching** gives better results in exchange for 1 to 2 seconds of
  delay.
* **Kafka in the location path** adds tens of milliseconds but isolates the
  gateways from downstream slowness.

## The answer in one paragraph

> "I'd split the design by data type. Driver locations arrive at about 200k to
> 500k tiny updates per second, so drivers keep one persistent connection to
> stateless gateways that validate updates and publish them to Kafka,
> partitioned by city. Consumers update an in-memory geo index built on
> hexagon cells or Redis GEO, sharded by city, push positions to riders on
> active trips, and write batched history to Bigtable. Matching searches
> nearby cells, ranks drivers by road ETA, and claims a driver with an atomic
> compare-and-set and a 15-second lease, so no driver gets two trips. Trips
> live in a strongly consistent database as a state machine with conditional
> updates and idempotency keys. Each region serves its own cities end to end,
> so a failure stays local."

**Suggested 45-minute split:** 5 minutes requirements, 3 estimates, 7
high-level design, 25 on deep dives (location index, matching correctness,
write-heavy updates, live connections), and 5 on failures and scaling.
