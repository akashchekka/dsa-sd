from __future__ import annotations

from typing import Any

from interfaces.split_strategy import SplitStrategy


class EqualSplitStrategy(SplitStrategy):
    def calculate_shares(
        self,
        amount: float,
        participants: list[str],
        **kwargs: Any,
    ) -> dict[str, float]:
        share = amount / len(participants)
        return {p: share for p in participants}
