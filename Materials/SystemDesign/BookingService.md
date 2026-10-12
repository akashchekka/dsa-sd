---
title: Ticket Booking System
description: Interview notes on designing a scalable ticket booking system that prevents double booking
---

## Requirements

### Functional requirements

* Search events by name, location, and date.
* View the seat map and approximate availability.
* Hold selected seats for a short period, such as five minutes.
* Pay for a hold and confirm the booking.
* Cancel a booking according to the event policy.
* View a user's bookings.

### Non-functional requirements

* **No double booking:** For one event, a seat can belong to at most one active
  hold or confirmed booking.
* **High read throughput:** Event search and seat-map views greatly outnumber
  booking writes.
* **Traffic spike tolerance:** Popular sales may receive millions of requests
  in a short period.
* **Strong consistency for booking:** A stale view may show an unavailable seat
  as available, but the booking operation must reject it.
* **Idempotent writes:** Client retries must not create duplicate holds,
  bookings, or payments.

> [!IMPORTANT]
> The booking database is the source of truth. Redis can cache availability,
> but it must not decide who owns a seat.

## Scale assumptions

Assume:

* 10 million daily users
* 100,000 active events
* Up to 50,000 seats per large event
* 10,000 requests per second normally
* Up to 1 million requests per second during a popular sale
* About 100 reads for every booking write

Search and seat-map reads scale independently from the smaller, strongly
consistent booking path.

## High-level architecture

```text
                           +------------------+
Users -> CDN/API Gateway ->| Rate limiter and |
                           | virtual queue    |
                           +--------+---------+
                                    |
             +----------------------+---------------------+
             |                      |                     |
             v                      v                     v
      +--------------+       +--------------+      +--------------+
      | Search       |       | Event and    |      | Booking      |
      | Service      |       | Seat Service |      | Service      |
      +------+-------+       +------+-------+      +------+-------+
             |                      |                     |
             v                      v                     v
      +--------------+       +--------------+      +--------------+
      | Search Index |       | Redis Cache  |      | Booking DB   |
      +--------------+       +--------------+      +------+-------+
                                                           |
                                      +--------------------+-------+
                                      |                            |
                                      v                            v
                               +--------------+              +------------+
                               | Payment      |              | Event Bus  |
                               | Provider     |              +------+-----+
                               +--------------+                     |
                                                                    v
                                                        Ticket and Notification
```

The search and event services serve eventually consistent reads. The booking
service owns seat holds, booking state, and the database transactions that
enforce seat ownership.

## Minimal data model

Only the tables needed to explain booking correctness are shown.

### Event seat

```text
event_seat
----------
event_id
seat_id
price
status             AVAILABLE | HELD | BOOKED
hold_id            nullable
hold_expires_at    nullable
booking_id         nullable
version

PRIMARY KEY (event_id, seat_id)
```

Each event receives its own seat inventory, even when multiple events use the
same physical venue.

### Booking

```text
booking
-------
booking_id
user_id
event_id
hold_id
seat_ids
status             PENDING_PAYMENT | CONFIRMED | FAILED | CANCELLED
total_amount
idempotency_key
created_at

UNIQUE (user_id, idempotency_key)
```

In a relational implementation, `seat_ids` may be normalized into a booking
seat table. The important constraint remains that an event seat has only one
owner.

## Core APIs

```http
GET /v1/events?query=coldplay&city=hyderabad&date=2026-10-10
GET /v1/events/{eventId}/seats

POST /v1/events/{eventId}/holds
Idempotency-Key: 8e4f...

{
  "seatIds": ["A-10", "A-11"]
}

POST /v1/holds/{holdId}/checkout
Idempotency-Key: 47ab...

{
  "paymentMethodToken": "payment-token"
}

GET /v1/bookings/{bookingId}
```

If any requested seat is unavailable, the hold request fails atomically. It
does not reserve a partial set unless the product explicitly supports partial
success.

## Preventing double booking

### Atomic conditional update

The database checks availability and changes ownership in one atomic
operation:

```sql
UPDATE event_seat
SET status = 'HELD',
    hold_id = :hold_id,
    hold_expires_at = :expires_at,
    version = version + 1
WHERE event_id = :event_id
  AND seat_id = :seat_id
  AND (
      status = 'AVAILABLE'
      OR (
          status = 'HELD'
          AND hold_expires_at < CURRENT_TIMESTAMP
      )
  );
```

The affected row count determines the result:

* `1`: The caller acquired the seat.
* `0`: Another user already holds or booked the seat.

If two servers execute this statement at the same time, the database serializes
their updates. Only one request can change the row from available to held.

### Holding multiple seats

All requested seats are acquired in one short database transaction:

```text
BEGIN

Create a hold identifier
Sort requested seat identifiers
Conditionally update every requested seat

If updated row count != requested seat count:
    ROLLBACK
    Return SEAT_UNAVAILABLE

COMMIT
```

Sorting seat identifiers gives concurrent transactions a consistent lock order
and reduces deadlocks for overlapping requests.

An alternative is to select the rows with `SELECT ... FOR UPDATE`, verify their
state, and then update them. Conditional updates fail faster and avoid keeping
waiting transactions open for as long.

### Confirming the booking

After payment authorization, the booking service performs another short
transaction:

1. Verify that the hold is active and belongs to the caller.
2. Verify that every seat still contains the same `hold_id`.
3. Create the booking in `PENDING_PAYMENT`.
4. Change all seats from `HELD` to `BOOKED`.
5. Mark the booking `CONFIRMED`.
6. Commit the transaction.

The ownership check belongs in the update:

```sql
UPDATE event_seat
SET status = 'BOOKED',
    booking_id = :booking_id,
    hold_id = NULL,
    hold_expires_at = NULL
WHERE event_id = :event_id
  AND hold_id = :hold_id
  AND status = 'HELD'
  AND hold_expires_at >= CURRENT_TIMESTAMP;
```

The transaction commits only when the affected row count equals the expected
seat count.

## Hold expiration

Correctness must not depend on a cleanup worker running exactly on time. A seat
with an expired hold is treated as available by the conditional update.

A background worker still clears expired rows in small batches:

```sql
UPDATE event_seat
SET status = 'AVAILABLE',
    hold_id = NULL,
    hold_expires_at = NULL
WHERE status = 'HELD'
  AND hold_expires_at < CURRENT_TIMESTAMP;
```

Database time avoids differences between application-server clocks. Multiple
cleanup workers can use row locking with `SKIP LOCKED` to process separate
batches safely.

## Idempotency

Clients retry requests after timeouts. Every hold, checkout, and payment request
therefore includes an idempotency key.

The service stores the key with the operation result. A retry with the same
user, key, and request body returns the original response instead of creating a
new resource. Reusing a key with a different request body is rejected.

Idempotency prevents duplicate requests from one user. The atomic seat update
prevents competing users from acquiring the same seat. Both protections are
required.

## Payment consistency

The service must not keep a database transaction open while calling an external
payment provider.

```text
Hold seats
    |
Authorize payment with booking_id as the provider idempotency key
    |
Confirm seat ownership in a database transaction
    |
Capture payment
    |
Mark booking CONFIRMED
```

If confirmation fails, the service voids the authorization. If capture succeeds
but the response is lost, a reconciliation worker queries the provider and
repairs the booking state. A stable `booking_id` ensures retries do not charge
the user twice.

## Cache behavior

The cache may contain:

* Event details
* Seat-map layout
* Prices, when versioned
* Approximate seat availability

After a seat transaction commits, the service publishes an event to invalidate
the cache and update connected clients. A user may briefly select a seat that
was recently taken. The authoritative database operation then returns
`SEAT_UNAVAILABLE`.

Distributed locks in Redis are not the final correctness mechanism. A lease may
expire while a paused process still believes it owns the lock, or failover may
temporarily produce conflicting observations. Database transactions and
ownership conditions remain authoritative.

## Handling extreme demand

### Virtual waiting room

A popular event can overwhelm the database even when every transaction is
correct. A virtual waiting room admits only a controlled number of users into
the booking flow.

Admission tokens are signed, short-lived, and tied to the user and event.
Requests without a valid token cannot attempt a hold.

### Partitioning

Partition inventory by `event_id`:

```text
shard = hash(event_id) % number_of_shards
```

Keeping all seats for one event on the same shard allows multi-seat holds to use
one local transaction. A popular event remains a hot partition, so the waiting
room controls its write rate.

### Abuse controls

* Limit seats per user and event.
* Limit active holds per user.
* Rate-limit repeated hold attempts.
* Require authentication before checkout.
* Add bot protection for high-demand sales.

## Multi-region design

Browsing can run active-active across regions. Booking writes for each event go
to one home region:

```text
London event    -> Europe booking region
Hyderabad event -> India booking region
```

This gives each event one strongly consistent write authority and avoids a
cross-region transaction for every seat.

If the home region becomes unavailable, pause new bookings for its events until
a synchronized replica is promoted. Temporary unavailability is safer than
selling one seat twice.

## Reliable downstream processing

Booking confirmation and event publication use a transactional outbox:

```text
BEGIN

Mark booking CONFIRMED
Mark seats BOOKED
Insert BookingConfirmed event into outbox

COMMIT
```

A background publisher sends outbox records to the event bus. Notification and
ticket-generation consumers process messages idempotently, so retries do not
produce duplicate tickets.

## Failure scenarios

| Scenario                                  | Handling                                                       |
|-------------------------------------------|----------------------------------------------------------------|
| Two users hold the same seat              | Only one conditional update succeeds                           |
| Two requests contain overlapping seats    | One transaction succeeds; the other rolls back                 |
| Client retries after a timeout             | Idempotency returns the original result                        |
| Hold expires during checkout               | Confirmation rechecks ownership and expiry                     |
| Cache shows stale availability             | The database rejects the hold                                  |
| Payment succeeds but response is lost      | Provider idempotency and reconciliation recover the result     |
| Service crashes after database commit      | Retry reads the existing result; outbox publishes the event    |
| Hold cleanup is delayed                    | Acquisition treats expired holds as available                  |
| Booking region fails                       | Writes pause until a synchronized replica is promoted          |
| Event message is delivered more than once  | Consumers deduplicate by event or booking identifier           |

## Interview summary

Separate highly scalable, eventually consistent browsing from strongly
consistent seat allocation. The booking database is the source of truth. A
conditional update inside a transaction atomically acquires a seat, and a
multi-seat request commits only when every requested seat is acquired.

Expiring holds improve the user experience without weakening correctness.
Idempotency handles retries, payment reconciliation handles external failures,
and a transactional outbox reliably triggers ticket generation. Cache and
distributed locks may improve performance, but database ownership conditions
prevent double booking.
