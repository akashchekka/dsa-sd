from interfaces.scheduling_strategy import SchedulingStrategy

class NearestElevatorStrategy(SchedulingStrategy):
    def select_elevator(self, elevators, request):
        return min(
            elevators,
            key=lambda e: abs(e.snapshot()["current_floor"] - request.floor),
        )
