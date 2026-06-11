# Ride Sharing (Uber-style)

Rider requests a ride → matched to a nearby driver → trip lifecycle (REQUESTED → ONGOING → COMPLETED) → fare computed.

## Run

```pwsh
cd machine-coding-py
python -m ride_sharing
```

## The subject

**Problem.** A rider opens an app, picks a destination, and asks for a ride. The system finds a nearby available driver of the right cab type, assigns them, tracks the trip state (driver en route → trip started → trip completed), and finally bills the rider based on distance, time, and dynamic demand ("surge").

**Why it's a classic interview problem.** It's an entire domain compressed into 45 minutes:

- **Multiple actors and a lifecycle.** Rider, Driver, Trip — each with its own state and rules. The Trip is the *aggregate root* that ties them together and enforces lifecycle invariants (you can't complete a trip that never started).
- **Geospatial matching.** "Nearest driver" sounds simple — but how do you compute distance on a sphere (Haversine vs. flat Euclidean)? How do you avoid scanning all 10,000 drivers in a city per request? (Answer in follow-up: geohash, quadtree, S2, R-tree.)
- **Strategy proliferation.** Matching can be by distance, by ETA (which depends on traffic), by driver rating, by ML-predicted acceptance probability. Pricing can be flat, per-km, time-based, surge-multiplied, promo-discounted. Each must be swappable.
- **State machine enforcement.** `REQUESTED → ASSIGNED → ONGOING → COMPLETED`, with branches for `CANCELLED_BY_RIDER`, `NO_DRIVER_FOUND`, `CANCELLED_BY_DRIVER`. Illegal transitions ("complete a not-yet-started trip") must be impossible, not just discouraged.
- **Concurrency and race conditions.** Two riders requesting at the same time may both be matched to the same closest driver. Driver acceptance must be atomic.
- **Real-world constraints.** Cab-type filtering (SEDAN, SUV, BIKE), surge pricing per geo-zone, multi-stop trips, ride-pooling — each is a possible extension you should be ready to discuss.

**Why it's hard to design well.** You're modeling a marketplace with two sides (supply: drivers; demand: riders) and a matching engine in the middle. The naive design puts matching, pricing, and lifecycle in one giant `Uber` class. The right design has small services with clear contracts: matcher, pricer, trip state machine, location index — each independently testable and swappable.

**Core mental model.**
```
request(rider, src, dst, cab_type)
   → matcher.match(rider, available_drivers, cab_type, src) → driver
   → Trip(REQUESTED → ASSIGNED)
start_trip(id)    → Trip.ONGOING (driver picked up rider)
complete_trip(id) → fare = pricing.compute(trip, surge) → Trip.COMPLETED
```

**Core concepts exercised.** Strategy pattern (matching, pricing), state machine (Trip lifecycle), geospatial computation, marketplace design (two-sided), aggregate roots (Trip), injected providers (surge), service composition.

## What's implemented

`RideService` is the façade. It registers drivers, takes ride requests, runs them through a **matching strategy** (nearest by Haversine distance), holds the trip state machine, then bills via a **pricing strategy** with optional surge multiplier.

## File layout

```
ride_sharing/
├── __main__.py                       # demo: 3 drivers, 1 rider, full trip with 1.5x surge
├── models/
│   ├── location.py                   # Location (lat, lon) + distance helper
│   ├── actors.py                     # Rider, Driver, CabType enum
│   └── trip.py                       # Trip + TripStatus enum
├── interfaces/
│   ├── matching_strategy.py          # IMatchingStrategy.match(rider, drivers, ...)
│   └── pricing_strategy.py           # IPricingStrategy.compute(trip, surge)
├── strategies/
│   ├── nearest_driver_matching.py    # NearestDriverMatching — min Haversine distance
│   └── distance_based_pricing.py     # base fare + per-km × surge
└── services/
    └── ride_service.py               # register_driver / request / start_trip / complete_trip
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Matching policy** | `IMatchingStrategy` | Swap nearest-driver → ETA-based → ML-ranked without touching service |
| **Pricing policy** | `IPricingStrategy` | Distance, time, dynamic — all interchangeable |
| **Surge** | Injected via callable `surge_provider: () → float` | Decouples surge calc (could be ML / city-zone lookup) from billing |
| **Trip state machine** | `TripStatus` enum + transition methods | Illegal transitions raise; no boolean flags scattered around |
| **CabType filtering** | Driver has a `cab_type`; request specifies required type | Matching filters before scoring |
| **Distance calc** | Haversine (great-circle) on lat/lon | Real geospatial; not Euclidean |
| **Drivers/riders as dataclasses** | Lightweight value objects with id | Easy to swap with ORM entities later |

## Trip lifecycle

```
REQUESTED  → assigned a driver (via matching)
   ↓ start_trip()
ONGOING    → driver is en route / driving
   ↓ complete_trip()
COMPLETED  → fare computed, driver freed
```

Cancellation states (`CANCELLED_BY_RIDER`, `NO_DRIVER`) are natural extensions of the enum.

## Pricing

```
fare = base_fare + (distance_km × per_km_rate) × surge_multiplier
```

`DistanceBasedPricing` reads cab-type-specific rates from a table. Surge is multiplicative and pluggable per trip.

## How to extend

| Add… | Change |
|---|---|
| **ETA-based matching** | New `EtaMatchingStrategy` calling a traffic provider |
| **Pool / shared rides** | `Trip.passengers: list[Rider]`; matching considers detour cost |
| **Driver availability** | `driver.is_available: bool`; matching filters |
| **Geo-index** | Replace linear scan in matcher with quadtree / S2 cells |
| **Cancellation fees** | `TripStatus.CANCELLED_*` + pricing branch on cancel reason |
| **Multiple cities** | Service keyed by `city_id`; surge provider per city |

## Edge cases handled

- No drivers match the cab type → request returns trip with no driver (caller decides retry/escalate).
- Distance calc on identical points → 0 km, base fare only.
- Trying to `complete_trip()` on a non-ongoing trip → invalid state error.

## Out of scope

- Auth / payments (only fare amount is returned).
- Real-time location updates (driver location is set at registration only).
- Push notifications, ratings, multi-stop trips.
- Concurrency — matching scans drivers without locks; wrap for production.
