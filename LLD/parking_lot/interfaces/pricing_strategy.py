"""Strategy pattern: lets pricing evolve (flat, hourly, peak-hour, weekend)
without touching the ParkingLot service."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from models.ticket import Ticket


class IPricingStrategy(ABC):
    @abstractmethod
    def compute(self, ticket: Ticket, exit_time: datetime) -> float: ...
