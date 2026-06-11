"""Top-level service: registers drivers, accepts trip requests, drives the
trip state machine, and reports fares on completion."""
from __future__ import annotations

import itertools
import threading
from datetime import datetime, timezone
from typing import Callable, Optional

from interfaces.matching_strategy import IMatchingStrategy
from interfaces.pricing_strategy  import IPricingStrategy
from models.actors                import CabType, Driver, Rider
from models.location              import Location
from models.trip                  import Trip, TripStatus


class RideService:
    def __init__(self, matcher: IMatchingStrategy, pricing: IPricingStrategy,
                 surge_provider: Optional[Callable[[], float]] = None) -> None:
        self._drivers: dict[str, Driver] = {}
        self._trips:   dict[str, Trip]   = {}
        self._matcher  = matcher
        self._pricing  = pricing
        self._surge    = surge_provider or (lambda: 1.0)
        self._seq      = itertools.count(1)
        self._lock     = threading.Lock()

    def register_driver(self, d: Driver) -> None:
        with self._lock:
            self._drivers[d.id] = d

    def update_location(self, driver_id: str, loc: Location) -> None:
        d = self._drivers.get(driver_id)
        if d is not None:
            d.location = loc

    def request(self, rider: Rider, from_loc: Location, to_loc: Location, cab: CabType) -> Trip:
        tid  = f"TRIP-{next(self._seq):06d}"
        trip = Trip(id=tid, rider=rider, from_loc=from_loc, to_loc=to_loc,
                    cab=cab, created_at=datetime.now(timezone.utc))
        with self._lock:
            driver = self._matcher.match(self._drivers.values(), trip)
            if driver is not None:
                driver.is_available = False
                trip.driver = driver
                trip.status = TripStatus.MATCHED
            self._trips[tid] = trip
        return trip

    def start_trip(self, trip_id: str) -> None:
        t = self._require(trip_id)
        if t.status != TripStatus.MATCHED:
            raise RuntimeError(f"cannot start trip in status {t.status}")
        t.status = TripStatus.IN_PROGRESS

    def complete_trip(self, trip_id: str) -> Trip:
        t = self._require(trip_id)
        if t.status != TripStatus.IN_PROGRESS:
            raise RuntimeError(f"cannot complete trip in status {t.status}")
        km = t.from_loc.distance_km_to(t.to_loc)
        t.fare   = self._pricing.quote(t, km, self._surge())
        t.status = TripStatus.COMPLETED
        if t.driver is not None:
            t.driver.location     = t.to_loc                # driver now at drop-off
            t.driver.is_available = True
        return t

    def cancel(self, trip_id: str) -> None:
        t = self._require(trip_id)
        if t.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            return
        if t.driver is not None:
            t.driver.is_available = True
        t.status = TripStatus.CANCELLED

    def _require(self, trip_id: str) -> Trip:
        t = self._trips.get(trip_id)
        if t is None:
            raise KeyError(f"unknown trip {trip_id}")
        return t
