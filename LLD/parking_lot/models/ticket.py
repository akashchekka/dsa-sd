"""Ticket entity. Mutable on exit: exit_at + amount_due populated by the
lot when the ticket is closed. Keep anemic — pricing lives in a strategy."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.parking_spot import ParkingSpot
from models.vehicle      import Vehicle


@dataclass
class Ticket:
    id: str
    vehicle: Vehicle
    spot: ParkingSpot
    entry_at: datetime
    exit_at: Optional[datetime] = None
    amount_due: Optional[float] = None
