from __future__ import annotations


class BalanceSheet:
    """Owns the net-balance ledger.

    Positive balance = the user is owed money.
    Negative balance = the user owes money.
    Sum across all users is always 0.
    """

    def __init__(self) -> None:
        self._net: dict[str, float] = {}

    def register(self, user_id: str) -> None:
        if user_id in self._net:
            return
        self._net[user_id] = 0.0

    def record_expense(
        self,
        payer_id: str,
        amount: float,
        shares: dict[str, float],
    ) -> None:
        for user, share in shares.items():
            self._net[user] -= share
        self._net[payer_id] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self._net)
