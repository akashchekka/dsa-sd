"""Ordered by severity; level filters compare with >=."""
from __future__ import annotations

from enum import IntEnum


class LogLevel(IntEnum):
    DEBUG = 0
    INFO  = 1
    WARN  = 2
    ERROR = 3
    FATAL = 4
