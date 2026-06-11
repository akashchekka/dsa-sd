"""Exponential backoff with jitter — standard pattern for downstream calls.
max_attempts includes the first try."""
from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable

from interfaces.retry_policy import IRetryPolicy


class ExponentialBackoffRetry(IRetryPolicy):
    def __init__(self, max_attempts: int = 3, base_delay_seconds: float = 0.05) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts >= 1")
        self._max_attempts = max_attempts
        self._base = base_delay_seconds
        self._rng  = random.Random()

    async def execute(self, action: Callable[[], Awaitable[bool]]) -> bool:
        for attempt in range(1, self._max_attempts + 1):
            try:
                if await action():
                    return True
            except Exception as ex:
                print(f"  retry: attempt {attempt} threw {type(ex).__name__}")
            if attempt < self._max_attempts:
                jitter = self._rng.random()
                delay  = self._base * (2 ** (attempt - 1)) * (0.5 + jitter)
                await asyncio.sleep(delay)
        return False
