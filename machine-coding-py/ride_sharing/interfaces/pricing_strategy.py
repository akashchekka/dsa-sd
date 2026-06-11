"""Pluggable pricing. Today: linear in distance with tier multiplier and a
surge factor. Real system: base + per-min + per-km + dynamic surge + tolls."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.trip import Trip


class IPricingStrategy(ABC):
    @abstractmethod
    def quote(self, trip: Trip, distance_km: float, surge: float) -> float: ...
