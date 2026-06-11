"""Trip lifecycle:
REQUESTED -> MATCHED -> IN_PROGRESS -> COMPLETED (or CANCELLED)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from models.actors   import CabType, Driver, Rider
from models.location import Location


class TripStatus(Enum):
    REQUESTED   = "requested"
    MATCHED     = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    CANCELLED   = "cancelled"


@dataclass
class Trip:
    id: str
    rider: Rider
    from_loc: Location
    to_loc: Location
    cab: CabType
    created_at: datetime
    driver: Optional[Driver] = None
    status: TripStatus = TripStatus.REQUESTED
    fare: Optional[float] = None
