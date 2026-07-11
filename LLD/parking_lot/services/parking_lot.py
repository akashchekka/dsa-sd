"""Top-level aggregate. Coordinates allocation strategy, pricing strategy,
and the active-ticket registry. Thread-safe for concurrent Park/Exit."""
from __future__ import annotations

import itertools
import threading
from typing import Iterable, Optional

from interfaces.clock                    import IClock
from interfaces.pricing_strategy         import IPricingStrategy
from interfaces.spot_allocation_strategy import ISpotAllocationStrategy
from models.ticket                       import Ticket
from models.vehicle                      import Vehicle
from services.parking_floor                        import ParkingFloor


class ParkingLot:
    def __init__(self, floors: Iterable[ParkingFloor],
                 allocator: ISpotAllocationStrategy,
                 pricing:   IPricingStrategy,
                 clock:     IClock) -> None:
        self._floors    = list(floors)
        self._allocator = allocator
        self._pricing   = pricing
        self._clock     = clock
        self._active:   dict[str, Ticket] = {}
        self._lock      = threading.Lock()
        self._seq       = itertools.count(1)

    def park(self, v: Vehicle) -> Optional[Ticket]:
        spot = self._allocator.allocate(self._floors, v.type)
        if spot is None:
            return None
        spot.park(v)
        tid = f"TKT-{next(self._seq):06d}"
        ticket = Ticket(id=tid, vehicle=v, spot=spot, entry_at=self._clock.now())
        with self._lock:
            self._active[tid] = ticket
        return ticket

    def exit(self, ticket_id: str) -> Ticket:
        with self._lock:
            t = self._active.pop(ticket_id, None)
        if t is None:
            raise KeyError(f"Unknown ticket {ticket_id}")
        t.exit_at    = self._clock.now()
        t.amount_due = self._pricing.compute(t, t.exit_at)
        t.spot.vacate()
        return t
