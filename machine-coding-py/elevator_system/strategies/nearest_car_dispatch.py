"""Nearest-Car strategy: pick the car whose direction is compatible with
the call and whose current floor is closest. Heavy penalty for wrong
direction."""
from __future__ import annotations

from interfaces.dispatch_strategy import IDispatchStrategy
from models.direction             import Direction
from models.elevator_car          import ElevatorCar
from models.requests              import HallCall


class NearestCarDispatch(IDispatchStrategy):
    def pick(self, cars: list[ElevatorCar], call: HallCall) -> ElevatorCar:
        best: ElevatorCar | None = None
        best_score = float("inf")
        for car in cars:
            distance = abs(car.current_floor - call.floor)
            penalty  = 0
            if car.direction == Direction.UP and (
                call.direction == Direction.DOWN or call.floor < car.current_floor):
                penalty = 1000
            if car.direction == Direction.DOWN and (
                call.direction == Direction.UP or call.floor > car.current_floor):
                penalty = 1000
            score = distance + penalty
            if score < best_score:
                best_score = score
                best = car
        assert best is not None, "need at least one car"
        return best
