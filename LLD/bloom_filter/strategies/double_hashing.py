"""Double hashing: derive k indexes from two base hashes as
g_i(x) = (h1 + i * h2) mod m. One md5 digest split into two halves gives h1, h2."""
from __future__ import annotations

import hashlib
from typing import Any, Iterator

from interfaces.hash_strategy import IHashStrategy


class DoubleHashingStrategy(IHashStrategy):
    def indexes(self, item: Any, k: int, m: int) -> Iterator[int]:
        # k = number of indexes to generate
        # m = size of the bit array
        digest = hashlib.md5(str(item).encode()).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:], "big")
        for i in range(k):
            yield (h1 + i * h2) % m
