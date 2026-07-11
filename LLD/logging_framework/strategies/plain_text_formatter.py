"""e.g. '2026-05-25T03:14:00Z  INFO  Auth - User signed in'"""
from __future__ import annotations

from interfaces.log_formatter import ILogFormatter
from models.log_event         import LogEvent


class PlainTextFormatter(ILogFormatter):
    def format(self, e: LogEvent) -> str:
        ts   = e.timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        lvl  = e.level.name.ljust(5)
        line = f"{ts}  {lvl}  {e.category} - {e.message}"
        if e.exception is not None:
            line = f"{line} | ex={type(e.exception).__name__}: {e.exception}"
        return line
