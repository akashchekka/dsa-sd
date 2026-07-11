"""Sink (appender) — where a log event ends up: console, file, network, ...
Multiple appenders can subscribe to the same logger."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.log_event import LogEvent


class ILogAppender(ABC):
    @abstractmethod
    def append(self, event: LogEvent) -> None: ...
