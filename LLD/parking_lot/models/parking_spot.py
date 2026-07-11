"""A parking spot belongs to a floor. A spot can host a vehicle whose type
fits the spot size: Small (motorcycle), Medium (motorcycle+car),
Large (everything). Adding EV/Handicapped is one extra enum value + a
can_fit branch — open/closed friendly."""
from __future__ import annotations

from enum import IntEnum
from typing import Optional

from models.vehicle import Vehicle, VehicleType


class SpotType(IntEnum):                # ordered: smaller value = smaller spot
    SMALL  = 1
    MEDIUM = 2
    LARGE  = 3


class ParkingSpot:
    def __init__(self, spot_id: str, size: SpotType) -> None:
        self.id   = spot_id
        self.size = size
        self.occupant: Optional[Vehicle] = None

    @property
    def is_free(self) -> bool: return self.occupant is None

    def can_fit(self, v: VehicleType) -> bool:
        if self.size == SpotType.SMALL:  return v == VehicleType.MOTORCYCLE
        if self.size == SpotType.MEDIUM: return v in (VehicleType.MOTORCYCLE, VehicleType.CAR)
        return True                                     # LARGE fits everything

    def park(self, v: Vehicle) -> None: self.occupant = v
    def vacate(self) -> None:           self.occupant = None
