"""Synchronous write to STDOUT. Cheap, blocks the caller."""
from __future__ import annotations

import sys
import threading

from interfaces.log_appender  import ILogAppender
from interfaces.log_formatter import ILogFormatter
from models.log_event         import LogEvent

class ConsoleAppender(ILogAppender):
    def __init__(self, formatter: ILogFormatter) -> None:
        self._formatter = formatter
        self._lock      = threading.Lock()             # serialize writes

    def append(self, event: LogEvent) -> None:
        line = self._formatter.format(event)
        with self._lock:
            print(line, file=sys.stdout, flush=True)
