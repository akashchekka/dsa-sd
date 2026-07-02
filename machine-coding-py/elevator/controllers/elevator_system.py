from threading import RLock
from models.enums import RequestType
from models.request import Request
from interfaces.scheduling_strategy import SchedulingStrategy

MIN_FLOOR = 0
MAX_FLOOR = 9

class ElevatorSystem:
    def __init__(self, elevators, strategy):
        self.elevators = elevators
        self.strategy: SchedulingStrategy = strategy
        self._lock = RLock()

    def request_elevator(self, floor: int, request_type: RequestType) -> bool:
        with self._lock:
            if floor < MIN_FLOOR or floor > MAX_FLOOR:
                return False
            if request_type == RequestType.DESTINATION:
                return False  # hall calls only; destinations come from inside

            request = Request(floor, request_type)
            elevator = self.strategy.select_elevator(self.elevators, request)
            return elevator.add_request(request)

    def select_floor(self, elevator_id: int, floor: int) -> bool:
        with self._lock:
            for elevator in self.elevators:
                if elevator.id == elevator_id:
                    request = Request(floor, RequestType.DESTINATION)
                    return elevator.add_request(request)
            return False

    def step(self) -> None:
        with self._lock:
            for elevator in self.elevators:
                elevator.step()
