"""Factory + cache. Real frameworks (Serilog, log4j) read config here
and build a logger per category. Keep it simple for the round."""
from __future__ import annotations

import threading

from interfaces.log_appender import ILogAppender
from models.log_level        import LogLevel
from services.logger                   import Logger


class LoggerFactory:
    def __init__(self, default_level: LogLevel = LogLevel.INFO) -> None:
        self._default_level = default_level
        self._appenders: list[ILogAppender] = []
        self._cache: dict[str, Logger] = {}
        self._lock  = threading.Lock()

    def add_appender(self, appender: ILogAppender) -> "LoggerFactory":
        self._appenders.append(appender)
        return self

    def get_logger(self, category: str) -> Logger:
        with self._lock:
            log = self._cache.get(category)
            if log is None:
                log = Logger(category, self._default_level, self._appenders)
                self._cache[category] = log
            return log
