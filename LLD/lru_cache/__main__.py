"""
=============================================================================
 LRUCache — entry point
=============================================================================
 Run:  python -m lru_cache   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

from interfaces.cache       import ICache
from services.lru_cache     import LruCache


def main() -> None:
    cache: ICache[int, str] = LruCache(3)
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")
    cache.get(1)                        # 1 -> MRU; LRU order: 2, 3, 1
    cache.put(4, "four")                # evicts 2

    print(f"has 2? {cache.get(2) is not None}")
    print(f"has 3? {cache.get(3)!r}")
    print(f"has 4? {cache.get(4)!r}")


if __name__ == "__main__":
    main()
