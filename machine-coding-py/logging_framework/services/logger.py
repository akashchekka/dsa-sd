"""Logger: filters by minimum level, fans out to all registered appenders.
Multiple loggers can coexist (one per Category). Cheap to construct."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from interfaces.log_appender import ILogAppender
from models.log_event        import LogEvent
from models.log_level        import LogLevel


class Logger:
    def __init__(self, category: str, min_level: LogLevel,
                 appenders: list[ILogAppender]) -> None:
        self._category  = category
        self._min_level = min_level
        self._appenders = appenders

    def log(self, level: LogLevel, message: str,
            ex: Optional[BaseException] = None) -> None:
        if level < self._min_level:
            return
        event = LogEvent(datetime.now(timezone.utc), level, self._category, message, ex)
        for a in self._appenders:
            a.append(event)

    def debug(self, m: str) -> None: self.log(LogLevel.DEBUG, m)
    def info (self, m: str) -> None: self.log(LogLevel.INFO,  m)
    def warn (self, m: str) -> None: self.log(LogLevel.WARN,  m)
    def error(self, m: str, ex: Optional[BaseException] = None) -> None: self.log(LogLevel.ERROR, m, ex)
    def fatal(self, m: str, ex: Optional[BaseException] = None) -> None: self.log(LogLevel.FATAL, m, ex)
