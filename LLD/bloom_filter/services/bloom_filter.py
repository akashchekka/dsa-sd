"""Standard Bloom filter.
  * Sizes m (bits) and k (hash functions) from expected item count n and
    target false-positive rate p.
  * Delegates bit storage to BitArray and index generation to an IHashStrategy.
Guarantees: no false negatives; false positives bounded by p. No deletions
(clearing a bit could corrupt other items — use a counting filter for that)."""
from __future__ import annotations

import math
from typing import Any, Optional

from interfaces.bloom_filter import IBloomFilter
from interfaces.hash_strategy import IHashStrategy
from models.bit_array import BitArray
from strategies.double_hashing import DoubleHashingStrategy


class BloomFilter(IBloomFilter):
    def __init__(
        self,
        expected_items: int,
        false_positive_rate: float,
        hash_strategy: Optional[IHashStrategy] = None,
    ) -> None:
        if expected_items <= 0:
            raise ValueError("expected_items > 0")
        if not 0.0 < false_positive_rate < 1.0:
            raise ValueError("0 < false_positive_rate < 1")

        self._m = self._optimal_m(expected_items, false_positive_rate)
        self._k = self._optimal_k(self._m, expected_items)
        self._bits = BitArray(self._m)
        self._hasher = hash_strategy or DoubleHashingStrategy()

    @staticmethod
    def _optimal_m(n: int, p: float) -> int:
        # m = -(n * ln p) / (ln 2)^2
        return max(1, math.ceil(-(n * math.log(p)) / (math.log(2) ** 2)))

    @staticmethod
    def _optimal_k(m: int, n: int) -> int:
        # k = (m / n) * ln 2
        return max(1, round((m / n) * math.log(2)))

    def add(self, item: Any) -> None:
        for idx in self._hasher.indexes(item, self._k, self._m):
            self._bits.set(idx)

    def might_contain(self, item: Any) -> bool:
        # Any zero bit => definitely absent.
        return all(self._bits.get(idx) for idx in self._hasher.indexes(item, self._k, self._m))

    def __contains__(self, item: Any) -> bool:
        return self.might_contain(item)

    @property
    def bit_size(self) -> int:
        return self._m

    @property
    def hash_count(self) -> int:
        return self._k
