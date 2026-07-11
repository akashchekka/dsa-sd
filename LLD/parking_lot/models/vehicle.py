"""Vehicle hierarchy. Polymorphism lets us add new vehicle types
(Electric, Bus, ...) without modifying spot/allocation code."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VehicleType(Enum):
    MOTORCYCLE = "motorcycle"
    CAR        = "car"
    TRUCK      = "truck"


@dataclass(frozen=True)
class Vehicle:
    license_plate: str
    type: VehicleType


def Motorcycle(plate: str) -> Vehicle: return Vehicle(plate, VehicleType.MOTORCYCLE)
def Car(plate: str)        -> Vehicle: return Vehicle(plate, VehicleType.CAR)
def Truck(plate: str)      -> Vehicle: return Vehicle(plate, VehicleType.TRUCK)
