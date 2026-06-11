"""Decides which car services a new hall call. Plug in different policies
(nearest car, least busy, predictive ML, energy-optimised) without
changing the controller."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.elevator_car import ElevatorCar
from models.requests     import HallCall


class IDispatchStrategy(ABC):
    @abstractmethod
    def pick(self, cars: list[ElevatorCar], call: HallCall) -> ElevatorCar: ...
