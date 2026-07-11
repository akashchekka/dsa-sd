"""Classic O(1) LRU cache.
  * dict[K, _Node] => O(1) lookup
  * doubly linked list (sentinel head/tail) => O(1) move-to-front + evict
Not thread-safe. Wrap with ConcurrentLruCache for concurrency."""
from __future__ import annotations

from typing import Generic, Hashable, Optional, TypeVar

from interfaces.cache import ICache
from models.lru_node  import LruNode

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LruCache(ICache[K, V]):
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity > 0")
        self._capacity = capacity
        self._map: dict[K, LruNode[K, V]] = {}
        self._head: LruNode[K, V] = LruNode()             # MRU sentinel
        self._tail: LruNode[K, V] = LruNode()             # LRU sentinel
        self._head.next = self._tail
        self._tail.prev = self._head

    @property
    def count(self) -> int: return len(self._map)

    def get(self, key: K) -> Optional[V]:
        if key in self._map:
            self._remove_node(self._map[key])
            self._add_to_head(self._map[key])
            return self._map[key].value
        return None

    def put(self, key: K, value: V) -> None:
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._remove_node(node)
            self._add_to_head(node)
            return

        node = LruNode(key, value)
        self._map[key] = node
        self._add_to_head(node)

        if len(self._map) > self._capacity:
            lru = self._tail.prev
            self._remove_node(lru)
            del self._map[lru.key]

    def remove(self, key: K) -> bool:
        n = self._map.pop(key, None)
        if n is None:
            return False
        self._remove_node(n)
        return True

    # --- list helpers ---
    def _remove_node(self, node: LruNode[K, V]) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_head(self, node: LruNode[K, V]) -> None:
        node.next = self._head.next
        node.prev = self._head
        self._head.next.prev = node
        self._head.next = node
