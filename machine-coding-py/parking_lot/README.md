# Parking Lot

A multi-floor parking lot with pluggable allocation and pricing strategies. Classic LLD problem (Google / Uber / Amazon).

## Run

```pwsh
cd machine-coding-py
python -m parking_lot
```

## The subject

**Problem.** Model a real-world parking garage: multiple floors, spots of different sizes, vehicles of different sizes, time-based billing. A car drives up → gets a spot → eventually exits → pays.

**Why it's a classic interview problem.** It looks trivial but stresses every LLD skill:

- **Entity modeling** — what is a `Vehicle`? A `Spot`? A `Ticket`? Who owns whom?
- **Polymorphism** — vehicle types and spot types vary; can a motorcycle park in a car spot? (yes) Can a truck park in a motorcycle spot? (no)
- **Strategy selection** — *which* spot do you give the next car? Nearest entrance? First-fit? Least-occupied floor? Each is a policy that should be swappable.
- **Pricing variation** — flat fee, hourly, surge, monthly pass — same domain, many billing rules.
- **Concurrency** — two cars at two gates may grab the same spot.
- **Extensibility** — the question always evolves mid-interview: "now add EV charging spots," "now add reservations," "now make it a chain of lots."

The core insight is that **structure and policy are different concerns**. Spots, floors, tickets are *structure*. Allocation and pricing are *policy*. Confusing them produces code where adding EV support requires editing 12 files.

**Core concepts exercised.** Strategy pattern, Factory pattern, Open/Closed Principle, value vs. entity objects, time as an injected dependency (`IClock`), and the Façade pattern (`ParkingLot` hides the floor/spot/strategy machinery from callers).

## What's implemented

A `ParkingLot` made of `ParkingFloor`s. A vehicle drives in → the lot asks an **allocation strategy** for a fitting free spot → a `Ticket` is issued. On exit, a **pricing strategy** computes the amount due based on entry/exit times from an injected `IClock`.

## File layout

```
parking_lot/
├── __main__.py                       # demo: park 2 vehicles, exit one
├── models/
│   ├── vehicle.py                    # Vehicle (frozen), VehicleType, factories
│   ├── parking_spot.py               # ParkingSpot + SpotType (IntEnum: ordered)
│   └── ticket.py                     # Ticket (entry time, spot, vehicle, amount_due)
├── interfaces/
│   ├── clock.py                      # IClock + SystemClock (testability seam)
│   ├── pricing_strategy.py           # IPricingStrategy
│   └── spot_allocation_strategy.py   # ISpotAllocationStrategy
├── strategies/
│   ├── first_fit_allocation.py       # FirstFitAllocation — first spot that fits
│   └── hourly_tiered_pricing.py      # HourlyTieredPricing — rate per vehicle type
└── services/
    ├── parking_floor.py              # ParkingFloor — owns spots, find-and-claim
    └── parking_lot.py                # ParkingLot — façade: park() / exit()
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **New vehicle types** (EV, bus) | `Enum` + `can_fit` predicate on spot | Adding a type doesn't touch allocation/pricing |
| **Allocation policy** | `ISpotAllocationStrategy` (Strategy pattern) | Swap `FirstFit` → `NearestEntrance` / `LeastOccupiedFloor` without changing the lot |
| **Pricing policy** | `IPricingStrategy` | Hourly, flat, surge — all interchangeable |
| **Time source** | `IClock` injected | Tests can fast-forward; production uses `SystemClock` |
| **Spot ordering** | `SpotType` is `IntEnum` (SMALL < MEDIUM < LARGE) | Small vehicles can fit in larger spots (`vehicle.size <= spot.size`) |
| **Vehicle as value object** | `@dataclass(frozen=True)` | Two `Car("ABC")` are equal; safe as dict keys |

## SOLID applied

- **S** — `ParkingFloor` owns spots, `ParkingLot` orchestrates, strategies decide policy.
- **O** — Add `EvAllocationStrategy` without touching `ParkingLot`.
- **L** — Any `IPricingStrategy` works wherever the interface is expected.
- **D** — `ParkingLot` depends on `IClock` / `IPricingStrategy`, not concrete classes.

## How to extend

| Add… | Change |
|---|---|
| **Electric vehicle** | New `SpotType.EV`, new `VehicleType.EV`, update `can_fit` |
| **Reservation** | New `IAllocationStrategy` that consults a reservation map |
| **Surge pricing** | New `SurgePricing(IPricingStrategy)` that multiplies the hourly rate |
| **Multi-lot chain** | Wrap `ParkingLot` instances in a `ParkingLotChain` façade |

## Edge cases handled

- Lot full → `park()` returns `None` (caller decides retry/turn-away).
- Exit with invalid ticket → raised by `ParkingLot.exit`.
- Mixed-size availability → allocation walks floors in order, first fitting spot wins.

## Out of scope (clarified upfront)

- Payments / refunds (only `amount_due` returned).
- Reservations.
- Persistence — in-memory only.
- Concurrency — single-lot demo; wrap floors in locks for real deployments.
