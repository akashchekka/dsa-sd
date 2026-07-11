"""Formats a LogEvent into a string. Plain, JSON, structured — pluggable."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.log_event import LogEvent


class ILogFormatter(ABC):
    @abstractmethod
    def format(self, event: LogEvent) -> str: ...
