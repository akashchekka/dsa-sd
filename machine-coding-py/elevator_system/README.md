# Elevator System

Multi-car elevator bank with pluggable dispatch. Models hall calls, in-cabin requests, and per-tick simulation.

## Run

```pwsh
cd machine-coding-py
python -m elevator_system
```

## The subject

**Problem.** A building has multiple elevator cars sharing a set of floors. Two kinds of input arrive: **hall calls** ("someone on floor 3 wants to go UP") and **cabin requests** ("the person inside car 1 pressed floor 6"). The system decides which car should service each hall call, and each car decides how to schedule its accumulated stops. The goal: minimize wait times, minimize travel distance, never strand a passenger.

**Why it's a classic interview problem.** Concurrent, stateful, with a real optimization objective:

- **Two different request types** with different semantics. Mixing them up is the first mistake — a hall call has a *direction intent*; a cabin request does not.
- **Dispatching is a real algorithm.** Naive: nearest car. Better: SCAN/LOOK (cars already heading toward the call have priority). Even better: weight by current load, direction-of-travel, and predicted future demand. The interview tests how you *structure* this so the dispatcher is swappable, not which one you pick first.
- **State machine per car** — `IDLE / MOVING_UP / MOVING_DOWN`, plus a sorted set of pending stops. Updates must respect direction (you don't reverse mid-trip if more stops exist in your current direction).
- **Time discretization.** Real elevators run on continuous time; simulating that on a whiteboard is painful. Tick-based time ("every tick a car moves one floor") is the standard simplification — and lets tests be deterministic.
- **Concurrency.** Many calls arrive simultaneously from different floors; many cars are moving at once. Even though this implementation is single-threaded, the design must accommodate locks/queues.
- **Constraints multiply the problem.** "Express elevator that only serves even floors." "Service elevator for freight, hidden from regular dispatch." "Lobby car that always returns to floor 0 when idle." Each is a constraint that should be a small change, not a rewrite.

**Why it's hard to design well.** The temptation is to put the dispatch logic *inside* the `ElevatorSystem` class. Then every new policy is a god-class rewrite. The right move is `IDispatchStrategy` as a tiny, pure interface: `(cars, hall_call) → car`. Everything else is mechanics.

**Core mental model.**
```
hall_call → dispatcher picks a car → car appends stop to its schedule
cabin_req → routed directly to the named car's schedule
tick     → every car advances one floor toward its next stop;
            stops served on arrival
```

**Core concepts exercised.** Strategy pattern (dispatch), state machines (per car), discrete-event simulation (ticks), request classification (hall vs. cabin), concurrency-friendly design, multi-constraint optimization.

## What's implemented

A `ElevatorSystem` of N `ElevatorCar`s sharing a queue of `HallCall`s. Each tick:

1. Dispatch pending hall calls to cars via an `IDispatchStrategy`.
2. Each car advances one floor toward its current target.
3. Stops, opens doors, removes served requests.

In-cabin requests (someone inside car 1 presses floor 6) are routed directly to that car's request queue.

## File layout

```
elevator_system/
├── __main__.py                       # demo: 2 cars, hall calls + cabin request
├── models/
│   ├── direction.py                  # Direction enum (UP, DOWN, IDLE)
│   ├── elevator_car.py               # ElevatorCar: current_floor, direction, request set
│   └── requests.py                   # HallCall, CabinRequest
├── interfaces/
│   └── dispatch_strategy.py          # IDispatchStrategy.pick(cars, hall_call)
├── strategies/
│   └── nearest_car_dispatch.py       # NearestCarDispatch — min-distance tie-break by id
└── services/
    └── elevator_system.py            # press_hall / press_cabin / tick / cars
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Dispatch policy** | `IDispatchStrategy` (Strategy pattern) | Swap nearest-car → SCAN/LOOK → ML-based without touching `ElevatorSystem` |
| **Time as ticks** | `tick()` advances all cars one floor | Deterministic, testable; no real clocks involved |
| **Hall vs cabin distinction** | Two request types | Hall = "I want to be picked up here going UP"; cabin = "I'm in car 1, take me to 6" |
| **Direction modelling** | Enum `{UP, DOWN, IDLE}` | Direction matters for hall call matching (UP call should go to a car heading up) |
| **Car state machine** | `current_floor` + `direction` + `pending_stops: set[int]` | Simple, debuggable |
| **Dispatch returns a car** | Not a flag/event | Pure function: `(cars, call) → car`; no side effects in strategy |

## Algorithm — NearestCarDispatch

For an incoming hall call:
1. Compute `|car.current_floor − call.floor|` for each car.
2. Pick min. Tie-break by car id (deterministic).

**Trade-off:** doesn't account for direction-of-travel. A more realistic SCAN/LOOK would prefer cars already heading toward the call. The interface supports either — just drop in a new strategy.

## How to extend

| Add… | Change |
|---|---|
| **SCAN / LOOK** | New `LookDispatchStrategy` that scores cars by direction compatibility |
| **Express elevators** | `ElevatorCar.allowed_floors: set[int]`; dispatch filters incompatible cars |
| **Capacity** | `car.load`; dispatch skips full cars |
| **Maintenance mode** | `car.is_in_service: bool`; dispatch filters |
| **Energy optimization** | New strategy that prefers idle cars over moving ones |

## Edge cases handled

- Hall call for a floor outside car's `[min_floor, max_floor]` range → dispatch should filter (extension point).
- Multiple cars equidistant → tie-broken by id for determinism.
- Car becomes IDLE when no pending stops — direction resets cleanly.

## Out of scope

- Real-time scheduling under load.
- Door open/close timing as separate ticks.
- Inter-bank optimization (multiple shafts coordinating).
- Persistence — in-memory state only.
