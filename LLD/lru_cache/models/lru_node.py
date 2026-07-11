"""Internal node of the recency-ordered doubly linked list owned by the cache."""
from __future__ import annotations

from typing import Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LruNode(Generic[K, V]):
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: K = None, value: V = None) -> None:   # type: ignore[assignment]
        self.key   = key
        self.value = value
        self.prev: Optional[LruNode[K, V]] = None
        self.next: Optional[LruNode[K, V]] = None
