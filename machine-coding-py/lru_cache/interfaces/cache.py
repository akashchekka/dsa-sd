"""Public surface for any cache. Lets callers depend on the abstraction
(single-threaded vs. concurrent vs. distributed wrappers)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class ICache(ABC, Generic[K, V]):
    @abstractmethod
    def get(self, key: K) -> Optional[V]: ...
    @abstractmethod
    def put(self, key: K, value: V) -> None: ...
    @abstractmethod
    def remove(self, key: K) -> bool: ...
    @property
    @abstractmethod
    def count(self) -> int: ...
