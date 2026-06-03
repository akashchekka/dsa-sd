"""Per-hour rate by spot size; minimum 1 hour charged."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from interfaces.pricing_strategy import IPricingStrategy
from models.parking_spot         import SpotType
from models.ticket               import Ticket


class HourlyTieredPricing(IPricingStrategy):
    _RATES = {SpotType.SMALL: 1.0, SpotType.MEDIUM: 2.0, SpotType.LARGE: 4.0}

    def compute(self, t: Ticket, exit_time: datetime) -> float:
        hours = math.ceil((exit_time - t.entry_at) / timedelta(hours=1))
        hours = max(1, hours)
        return round(hours * self._RATES[t.spot.size], 2)
