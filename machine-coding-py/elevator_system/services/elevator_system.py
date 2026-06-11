"""Controller: receives hall/cabin calls, dispatches via strategy, and
advances cars one floor per tick (SCAN/LOOK-style)."""
from __future__ import annotations

from interfaces.dispatch_strategy import IDispatchStrategy
from models.direction             import Direction
from models.elevator_car          import ElevatorCar
from models.requests              import CabinRequest, HallCall


class ElevatorSystem:
    def __init__(self, cars: list[ElevatorCar], dispatch: IDispatchStrategy) -> None:
        self._cars     = list(cars)
        self._dispatch = dispatch

    @property
    def cars(self) -> list[ElevatorCar]: return self._cars

    def press_hall(self, call: HallCall) -> None:
        car = self._dispatch.pick(self._cars, call)
        self._add_stop(car, call.floor)

    def press_cabin(self, req: CabinRequest) -> None:
        car = next(c for c in self._cars if c.id == req.car_id)
        self._add_stop(car, req.floor)

    def _add_stop(self, car: ElevatorCar, floor: int) -> None:
        if floor >= car.current_floor:
            car.up_stops.add(floor)
        else:
            car.down_stops.add(floor)
        if car.direction == Direction.IDLE:
            car.direction = Direction.UP if floor >= car.current_floor else Direction.DOWN

    def tick(self) -> None:
        for car in self._cars:
            self._step(car)

    @staticmethod
    def _step(car: ElevatorCar) -> None:
        if not car.has_work:
            car.direction = Direction.IDLE
            return

        if car.direction == Direction.UP:
            if car.current_floor in car.up_stops:
                car.up_stops.remove(car.current_floor)
                return                                                  # doors open this tick
            if car.up_stops and max(car.up_stops) >= car.current_floor:
                car.current_floor += 1
                return
            car.direction = Direction.DOWN

        if car.direction == Direction.DOWN:
            if car.current_floor in car.down_stops:
                car.down_stops.remove(car.current_floor)
                return
            if car.down_stops and min(car.down_stops) <= car.current_floor:
                car.current_floor -= 1
                return
            car.direction = Direction.UP if car.up_stops else Direction.IDLE
