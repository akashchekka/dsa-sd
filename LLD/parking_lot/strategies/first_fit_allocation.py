"""Walks floors in order and asks each for a free, fitting spot.
O(F*S) worst case; simple and predictable. Replace with priority-queue
or geo-aware policy in a real system."""
from __future__ import annotations

from typing import Iterable, Optional

from interfaces.spot_allocation_strategy import ISpotAllocationStrategy
from models.parking_spot                 import ParkingSpot
from models.vehicle                      import VehicleType
from services.parking_floor              import ParkingFloor


class FirstFitAllocation(ISpotAllocationStrategy):
    def allocate(self, floors: Iterable[ParkingFloor], v: VehicleType) -> Optional[ParkingSpot]:
        for f in floors:
            spot = f.find_free_spot(v)
            if spot is not None:
                return spot
        return None
