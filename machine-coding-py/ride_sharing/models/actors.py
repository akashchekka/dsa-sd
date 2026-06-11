"""Cab tier + Rider + Driver. Pricing and matching differ per tier."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from models.location import Location


class CabType(Enum):
    MINI  = "mini"
    SEDAN = "sedan"
    SUV   = "suv"


@dataclass(frozen=True)
class Rider:
    id: str
    name: str


class Driver:
    """Lifecycle: Offline -> Available -> OnTrip -> Available..."""
    def __init__(self, id: str, name: str, cab: CabType, location: Location) -> None:
        self.id = id
        self.name = name
        self.cab = cab
        self.location = location
        self.is_available = True
