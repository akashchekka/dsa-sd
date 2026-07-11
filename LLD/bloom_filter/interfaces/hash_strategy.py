"""Strategy for producing k bit-indexes for an item. Swapping this lets the
filter change its hashing scheme (double hashing, murmur, cryptographic, ...)
without touching the filter logic."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator


class IHashStrategy(ABC):
    @abstractmethod
    def indexes(self, item: Any, k: int, m: int) -> Iterator[int]:
        """Yield k indexes in the range [0, m) for the given item."""
