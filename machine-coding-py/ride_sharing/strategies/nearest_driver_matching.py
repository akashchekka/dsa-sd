"""Naive nearest-driver matcher. O(N) over available drivers per request.
For city scale, partition by geohash / S2 / H3 cells and scan only the
rider's cell + neighbours (sub-linear in practice)."""
from __future__ import annotations

from typing import Iterable, Optional

from interfaces.matching_strategy import IMatchingStrategy
from models.actors                import Driver
from models.trip                  import Trip


class NearestDriverMatching(IMatchingStrategy):
    def match(self, drivers: Iterable[Driver], trip: Trip) -> Optional[Driver]:
        candidates = [d for d in drivers if d.is_available and d.cab == trip.cab]
        if not candidates:
            return None
        return min(candidates, key=lambda d: d.location.distance_km_to(trip.from_loc))
