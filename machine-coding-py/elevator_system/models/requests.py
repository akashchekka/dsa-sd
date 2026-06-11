"""Hall call: someone on `floor` wants to go `direction`.
Cabin request: passenger inside a car picks a destination."""
from __future__ import annotations

from dataclasses import dataclass

from models.direction import Direction


@dataclass(frozen=True)
class HallCall:
    floor: int
    direction: Direction


@dataclass(frozen=True)
class CabinRequest:
    car_id: int
    floor: int
