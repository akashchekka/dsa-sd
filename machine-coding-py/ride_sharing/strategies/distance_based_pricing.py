"""Per-km rate by cab tier, multiplied by surge. Minimum 1 km charged."""
from __future__ import annotations

from interfaces.pricing_strategy import IPricingStrategy
from models.actors               import CabType
from models.trip                 import Trip


class DistanceBasedPricing(IPricingStrategy):
    _PER_KM = {CabType.MINI: 10.0, CabType.SEDAN: 15.0, CabType.SUV: 20.0}

    def quote(self, trip: Trip, distance_km: float, surge: float) -> float:
        km = max(1.0, distance_km)
        return round(self._PER_KM[trip.cab] * km * surge, 2)
