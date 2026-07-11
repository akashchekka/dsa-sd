"""Coarse-grained-lock wrapper. Adequate for most rounds.
For high QPS, shard keys across N inner caches."""
from __future__ import annotations

import threading
from typing import Generic, Hashable, Optional, TypeVar

from interfaces.cache import ICache
from services.lru_cache         import LruCache

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class ConcurrentLruCache(ICache[K, V]):
    def __init__(self, capacity: int) -> None:
        self._inner = LruCache[K, V](capacity)
        self._lock  = threading.Lock()

    def get(self, key: K) -> Optional[V]:
        with self._lock: return self._inner.get(key)
    def put(self, key: K, value: V) -> None:
        with self._lock: self._inner.put(key, value)
    def remove(self, key: K) -> bool:
        with self._lock: return self._inner.remove(key)
    @property
    def count(self) -> int:
        with self._lock: return self._inner.count
