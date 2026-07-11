from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.log_level import LogLevel


@dataclass(frozen=True)
class LogEvent:
    timestamp_utc: datetime
    level: LogLevel
    category: str
    message: str
    exception: Optional[BaseException] = None
