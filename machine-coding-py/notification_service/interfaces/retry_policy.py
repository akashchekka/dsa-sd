"""Strategy for 'should we try again after a failure?'.
Pluggable: NoRetry, FixedDelay, ExponentialBackoff, ..."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

class IRetryPolicy(ABC):
    @abstractmethod
    def execute(self, action: Callable[[], bool]) -> bool: ...
