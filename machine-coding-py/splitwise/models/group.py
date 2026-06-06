from __future__ import annotations

from models.balance_sheet import BalanceSheet
from models.expense       import Expense


class Group:
    """A named collection of users that share expenses.

    Each group owns its own ledger and expense history — settlements are
    computed per-group, never across groups.
    """

    def __init__(self, group_id: str, name: str) -> None:
        self.group_id      = group_id
        self.name          = name
        self.members:       set[str]      = set()
        self.expenses:      list[Expense] = []
        self.balance_sheet: BalanceSheet  = BalanceSheet()

    def add_member(self, user_id: str) -> None:
        if user_id in self.members:
            return
        self.members.add(user_id)
        self.balance_sheet.register(user_id)

    def has_member(self, user_id: str) -> bool:
        return user_id in self.members
    
    def record_expense(self, payer_id: str, amount: float, shares: dict[str, float]) -> None:
        expense = Expense(payer_id, amount, shares)
        self.expenses.append(expense)
        self.balance_sheet.record_expense(payer_id, amount, shares)
