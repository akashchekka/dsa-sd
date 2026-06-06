from __future__ import annotations

from typing import Any

from interfaces.split_strategy import SplitStrategy


class ExactSplitStrategy(SplitStrategy):
    def calculate_shares(
        self,
        amount: float,
        participants: list[str],
        **kwargs: Any,
    ) -> dict[str, float]:
        shares: dict[str, float] = kwargs["shares"]
        if abs(sum(shares.values()) - amount) > 0.001:
            raise ValueError("Exact shares must sum to amount")
        return shares
