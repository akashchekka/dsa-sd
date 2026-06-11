"""Pluggable matcher. Today: nearest available driver of the requested tier.
Production: ETA-aware, batched assignment, surge-aware re-balancing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from models.actors import Driver
from models.trip   import Trip


class IMatchingStrategy(ABC):
    @abstractmethod
    def match(self, drivers: Iterable[Driver], trip: Trip) -> Optional[Driver]: ...
