"""Lightweight (lat, lng) value type with Haversine distance.
For a real system, swap with S2 / H3 cell IDs for indexing."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float

    _EARTH_KM = 6371.0

    def distance_km_to(self, other: "Location") -> float:
        to_rad = math.radians
        d_lat = to_rad(other.lat - self.lat)
        d_lng = to_rad(other.lng - self.lng)
        a = (math.sin(d_lat / 2) ** 2
             + math.cos(to_rad(self.lat)) * math.cos(to_rad(other.lat))
             * math.sin(d_lng / 2) ** 2)
        return 2 * self._EARTH_KM * math.asin(min(1.0, math.sqrt(a)))
