from interfaces.scheduling_strategy import SchedulingStrategy
from models.enums import Direction, RequestType


class ScanElevatorStrategy(SchedulingStrategy):
    """SCAN/LOOK dispatch: prefer an idle car, or one already moving toward the
    request in the matching direction; otherwise fall back to distance."""

    def select_elevator(self, elevators, request):
        if not elevators:
            return None
        return min(elevators, key=lambda e: self._cost(e, request))

    def _cost(self, elevator, request):
        snap = elevator.snapshot()
        floor = snap["current_floor"]
        direction = snap["direction"]
        distance = abs(floor - request.floor)

        if direction == Direction.IDLE:
            return (0, distance)

        # Direction implied by the hall call.
        req_dir = (
            Direction.UP if request.type == RequestType.PICKUP_UP
            else Direction.DOWN
        )

        same_direction = direction == req_dir
        approaching = (
            (direction == Direction.UP and floor <= request.floor)
            or (direction == Direction.DOWN and floor >= request.floor)
        )
        if same_direction and approaching:
            return (1, distance)

        # Tier 2: car is moving away or opposite -> must finish its sweep first.
        return (2, distance)
