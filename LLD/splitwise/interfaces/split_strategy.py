from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SplitStrategy(ABC):
    @abstractmethod
    def calculate_shares(
        self,
        amount: float,
        participants: list[str],
        **kwargs: Any,
    ) -> dict[str, float]:
        ...
