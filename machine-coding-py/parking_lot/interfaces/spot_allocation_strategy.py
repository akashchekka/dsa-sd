"""Strategy for choosing which spot to assign. Allows swapping policies
(first-fit, nearest-to-entrance, balanced-by-floor, ML-based)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from models.parking_spot          import ParkingSpot
from models.vehicle               import VehicleType
from services.parking_floor       import ParkingFloor


class ISpotAllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, floors: Iterable[ParkingFloor], v: VehicleType) -> Optional[ParkingSpot]: ...
