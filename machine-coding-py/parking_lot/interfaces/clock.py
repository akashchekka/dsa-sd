"""Inject a clock so unit tests can advance time deterministically
without depending on datetime.now()."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class IClock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...


class SystemClock(IClock):
    def now(self) -> datetime: return datetime.now(timezone.utc)
