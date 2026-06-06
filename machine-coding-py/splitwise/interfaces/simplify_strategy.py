from __future__ import annotations

from abc import ABC, abstractmethod

# (debtor, creditor, amount)
Settlement = tuple[str, str, float]


class SimplifyStrategy(ABC):
    @abstractmethod
    def simplify(self, balances: dict[str, float]) -> list[Settlement]:
        ...
