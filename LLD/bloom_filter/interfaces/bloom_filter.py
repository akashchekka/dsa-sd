"""Public surface for a Bloom filter. Callers depend on the abstraction so the
underlying bit array / hashing strategy can vary (standard, counting, scalable)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IBloomFilter(ABC):
    @abstractmethod
    def add(self, item: Any) -> None:
        """Insert an item into the set."""

    @abstractmethod
    def might_contain(self, item: Any) -> bool:
        """False => item is DEFINITELY absent (no false negatives).
        True  => item is POSSIBLY present (may be a false positive)."""

    @property
    @abstractmethod
    def bit_size(self) -> int:
        """Size of the underlying bit array (m)."""

    @property
    @abstractmethod
    def hash_count(self) -> int:
        """Number of hash functions (k)."""
