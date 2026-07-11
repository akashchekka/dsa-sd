"""Owns its spots and guards selection with a per-floor lock so two cars
can't be assigned the same spot concurrently."""
from __future__ import annotations

import threading
from typing import Iterable, Optional

from models.parking_spot import ParkingSpot
from models.vehicle      import VehicleType


class ParkingFloor:
    def __init__(self, number: int, spots: Iterable[ParkingSpot]) -> None:
        self.number = number
        self._spots = list(spots)
        self._lock  = threading.Lock()

    def find_free_spot(self, v: VehicleType) -> Optional[ParkingSpot]:
        with self._lock:
            candidates = [s for s in self._spots if s.is_free and s.can_fit(v)]
            candidates.sort(key=lambda s: s.size)            # smallest fitting first
            return candidates[0] if candidates else None
