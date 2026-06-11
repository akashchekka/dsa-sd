"""
=============================================================================
 ElevatorSystem — entry point
=============================================================================
 Run:  python -m elevator_system   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

from models.direction              import Direction
from models.elevator_car           import ElevatorCar
from models.requests               import CabinRequest, HallCall
from services.elevator_system      import ElevatorSystem
from strategies.nearest_car_dispatch import NearestCarDispatch


def main() -> None:
    cars = [
        ElevatorCar(id=1, min_floor=0, max_floor=10, start=0),
        ElevatorCar(id=2, min_floor=0, max_floor=10, start=5),
    ]
    system = ElevatorSystem(cars, NearestCarDispatch())

    system.press_hall(HallCall(floor=3, direction=Direction.UP))
    system.press_hall(HallCall(floor=7, direction=Direction.DOWN))

    def snapshot() -> str:
        return " | ".join(f"car{c.id}@{c.current_floor}({c.direction.value})" for c in system.cars)

    for _ in range(8):
        system.tick()
        print(snapshot())

    # A passenger inside car 1 selects floor 6.
    system.press_cabin(CabinRequest(car_id=1, floor=6))
    for _ in range(6):
        system.tick()
        print(snapshot())


if __name__ == "__main__":
    main()
