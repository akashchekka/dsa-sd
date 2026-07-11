from __future__ import annotations

from typing import Any

from interfaces.split_strategy import SplitStrategy


class PercentageSplitStrategy(SplitStrategy):
    def calculate_shares(
        self,
        amount: float,
        participants: list[str],
        **kwargs: Any,
    ) -> dict[str, float]:
        percentages: dict[str, float] = kwargs["percentages"]
        if sum(percentages.values()) != 100:
            raise ValueError("Percentages must total 100")
        return {u: amount * p / 100 for u, p in percentages.items()}
