from threading import RLock
from .enums import Direction, RequestType
from .request import Request

MIN_FLOOR = 0
MAX_FLOOR = 9

class Elevator:
    """One elevator car. Owns its movement logic (SCAN) and is independently
    thread-safe: every public method runs under its own lock."""

    def __init__(self, elevator_id: int):
        self.id = elevator_id
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.requests: set[Request] = set()
        self._lock = RLock()

    def add_request(self, request: Request) -> bool:
        """Unified entry for both hall calls and in-cabin destinations."""
        with self._lock:
            if request.floor < MIN_FLOOR or request.floor > MAX_FLOOR:
                return False
            if request.floor == self.current_floor:
                return True  # already here, treat as no-op
            self.requests.add(request)  # set dedupes by (floor, type)
            return True

    def step(self) -> None:
        with self._lock:
            # Case 1: nothing to do -> go idle.
            if not self.requests:
                self.direction = Direction.IDLE
                return

            # Case 2: idle but have work -> pick a direction from nearest request.
            if self.direction == Direction.IDLE:
                nearest: Request = min(
                    self.requests,
                    key=lambda r: (abs(r.floor - self.current_floor), r.floor),
                )
                self.direction = (
                    Direction.UP if nearest.floor > self.current_floor else Direction.DOWN
                )

            # Case 3: stop here if a request matches our travel direction.
            pickup_type = (
                RequestType.PICKUP_UP if self.direction == Direction.UP
                else RequestType.PICKUP_DOWN
            )
            pickup = Request(self.current_floor, pickup_type)
            destination = Request(self.current_floor, RequestType.DESTINATION)

            if pickup in self.requests or destination in self.requests:
                self.requests.discard(pickup)
                self.requests.discard(destination)
                if not self.requests:
                    self.direction = Direction.IDLE
                return  # stopped this tick, don't move

            # Case 4: nothing ahead in this direction -> reverse (no move this tick).
            if not self._has_requests_ahead(self.direction):
                self.direction = (
                    Direction.DOWN if self.direction == Direction.UP else Direction.UP
                )
                return

            # Case 5: move one floor in the current direction.
            self.current_floor += 1 if self.direction == Direction.UP else -1

    def _has_requests_ahead(self, direction: Direction) -> bool:
        """Any request beyond us in `direction`, regardless of type — we travel
        toward every request but only *stop* for direction-matching ones.
        Called only while the lock is already held."""
        for r in self.requests:
            if direction == Direction.UP and r.floor > self.current_floor:
                return True
            if direction == Direction.DOWN and r.floor < self.current_floor:
                return True
        return False

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "id": self.id,
                "current_floor": self.current_floor,
                "direction": self.direction,
            }
