"""Direction of motion. IDLE means the car is parked waiting for work."""
from __future__ import annotations

from enum import Enum


class Direction(Enum):
    UP   = "up"
    DOWN = "down"
    IDLE = "idle"
