from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Notification:
    id: str
    topic: str
    body: str
    created_at: datetime
