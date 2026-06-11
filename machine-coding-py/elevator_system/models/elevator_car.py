"""State of a single elevator car. Up/Down stop sets are kept separately
so a SCAN-style controller can sweep them efficiently."""
from __future__ import annotations

from models.direction import Direction


class ElevatorCar:
    def __init__(self, id: int, min_floor: int, max_floor: int, start: int) -> None:
        self.id        = id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_floor = start
        self.direction: Direction = Direction.IDLE
        self.up_stops:   set[int] = set()
        self.down_stops: set[int] = set()

    @property
    def has_work(self) -> bool:
        return bool(self.up_stops) or bool(self.down_stops)
