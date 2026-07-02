from models.elevator import Elevator
from models.enums import RequestType
from strategies.nearest_elevator_strategy import NearestElevatorStrategy
from controllers.elevator_system import ElevatorSystem

def main():
    elevators = [Elevator(0), Elevator(1), Elevator(2)]
    system = ElevatorSystem(elevators, NearestElevatorStrategy())

    # Hall call: someone on floor 7 wants to go UP.
    system.request_elevator(7, RequestType.PICKUP_UP)

    for tick in range(10):
        system.step()
        snapshot = " | ".join(
            f"E{e.id}@{e.current_floor}({e.direction.value})" for e in elevators
        )
        print(f"tick {tick:2d}: {snapshot}")

        # Once an elevator reaches floor 7, the passenger picks floor 2.
        if tick == 6:
            system.select_floor(elevator_id=0, floor=2)

    print("Simulation completed")

if __name__ == "__main__":
    main()
