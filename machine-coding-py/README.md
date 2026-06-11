# Machine Coding (Python — Folder Layout)

Python ports of the C# machine-coding solutions in [`../machine-coding/`](../machine-coding/), with the **exact same folder layout**.

Each problem is a Python package:

```
<problem>/
├── __init__.py          # marks the package
├── __main__.py          # entry point (was Program.csx) — runs the demo
├── models/              # POCOs, enums, value objects (one type per file)
├── interfaces/          # ABCs / protocols
├── strategies/          # Concrete pluggable behaviours (Strategy pattern)
└── services/            # Aggregates / orchestrators
```

## Run any solution

From inside this folder:

```pwsh
cd machine-coding-py
python -m parking_lot
python -m splitwise
python -m lru_cache
python -m rate_limiter
python -m tic_tac_toe
python -m elevator_system
python -m ride_sharing
python -m snake_and_ladder
python -m notification_service
python -m logging_framework
python -m pub_sub
```

`python -m <pkg>` runs the package's `__main__.py`. Imports inside the package are relative (`from ..models.vehicle import Vehicle`) — same idea as `#load` in the C# `.csx` files, but using Python's package system.

## Run all demos

```pwsh
cd machine-coding-py
@(
  'parking_lot','splitwise','lru_cache','rate_limiter','tic_tac_toe',
  'elevator_system','ride_sharing','snake_and_ladder',
  'notification_service','logging_framework','pub_sub'
) | ForEach-Object { Write-Host "`n===== $_ =====" -ForegroundColor Cyan; python -m $_ }
```

No `pip install` needed — Python 3.10+ standard library only.

## Catalogue

| # | Problem | Package | Core concepts |
|---|---------|---------|---------------|
| 1 | Parking Lot          | [parking_lot/](parking_lot/)                   | Strategy, Factory, polymorphism, pricing |
| 2 | Splitwise            | [splitwise/](splitwise/)                       | Balance graph, expense splits, greedy settlement |
| 3 | LRU Cache            | [lru_cache/](lru_cache/)                       | Doubly linked list + dict, generics, thread-safety |
| 4 | Rate Limiter         | [rate_limiter/](rate_limiter/)                 | Token bucket, sliding window, fixed window |
| 5 | Tic Tac Toe          | [tic_tac_toe/](tic_tac_toe/)                   | Board state, O(1) win detection per move |
| 6 | Elevator System      | [elevator_system/](elevator_system/)           | State machine, SCAN/LOOK dispatch, multi-car |
| 7 | Ride Sharing (Uber)  | [ride_sharing/](ride_sharing/)                 | Matching, geospatial, pricing, lifecycle |
| 8 | Snake & Ladder       | [snake_and_ladder/](snake_and_ladder/)         | Board modelling, dice abstraction, multiplayer |
| 9 | Notification Service | [notification_service/](notification_service/) | Pub/Sub, channel strategies, retry/backoff |
| 10| Logging Framework    | [logging_framework/](logging_framework/)       | Levels, appenders, async sink (decorator) |
| 11| Pub/Sub Broker       | [pub_sub/](pub_sub/)                           | In-memory broker, per-subscriber worker, wildcard topics, backpressure |

## Why this layout (vs single-file)

- **Parity with C# folders** — same `models/ interfaces/ strategies/ services/` partitioning.
- **One type per file** — easy to extend (drop in a new `ev_spot.py` next to `parking_spot.py`).
- **Each interface stands alone** — clear contracts under `interfaces/`.

For machine-coding **rounds** themselves (where you have one editor pane), a single-file version is more practical. This layout is what you'd produce in a real codebase / PR.

## Python design conventions used

- **`abc.ABC` + `@abstractmethod`** for interfaces (enforced at instantiation).
- **`@dataclass(frozen=True)`** for immutable value objects / records.
- **`enum.Enum` / `IntEnum`** for closed type sets.
- **`threading.Lock` with `with` blocks** for thread-safety.
- **`queue.Queue`** + worker thread for the async log appender.
- **`asyncio` + `gather`** for the notification fan-out.
- **Relative imports** (`from ..models.vehicle import Vehicle`) inside each package.
- **Type hints throughout** for tooling support.

## Interview rubric this targets

Same as the C# version — see [`../machine-coding/SOLID_and_DesignPatterns.md`](../machine-coding/SOLID_and_DesignPatterns.md):

1. **Clarify** — assumptions listed at top of each `__main__.py`.
2. **Model** — domain entities first, services second.
3. **Extensible** — open for extension via Strategy/Factory.
4. **Thread-safe** where the problem demands it; documented otherwise.
5. **Testable** — depend on abstractions (`IClock`, `IDice`, `IPricingStrategy`...).
6. **Demoable** — every package runs end-to-end and prints meaningful output.
