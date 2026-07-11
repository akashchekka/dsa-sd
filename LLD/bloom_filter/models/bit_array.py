"""Fixed-size bit array. O(1) set/get."""
from __future__ import annotations


class BitArray:
    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValueError("size > 0")
        self._bits = [False] * size

    @property
    def size(self) -> int:
        return len(self._bits)

    def set(self, index: int) -> None:
        self._bits[index] = True

    def get(self, index: int) -> bool:
        return self._bits[index]
