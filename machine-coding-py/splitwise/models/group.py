from __future__ import annotations

import threading

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
        self._lock: threading.Lock        = threading.Lock()

    def add_member(self, user_id: str) -> None:
        if user_id in self.members:
            return
        self.members.add(user_id)
        self.balance_sheet.register(user_id)

    def has_member(self, user_id: str) -> bool:
        return user_id in self.members
    
    def record_expense(self, payer_id: str, amount: float, shares: dict[str, float]) -> str:
        expense = Expense(payer_id, amount, shares)

        with self._lock:
            self.expenses.append(expense)
            self.balance_sheet.record_expense(payer_id, amount, shares)

        return expense.expense_id

    def remove_expense(self, expense_id: str) -> Expense:
        """Hard-delete an expense and reverse its effect on the balance sheet."""
        with self._lock:
            idx = next(
                (i for i, e in enumerate(self.expenses) if e.expense_id == expense_id),
                None,
            )
            if idx is None:
                raise ValueError(f"Unknown expense: {expense_id!r}")
            expense = self.expenses.pop(idx)
            self.balance_sheet.reverse_expense(
                expense.payer_id, expense.amount, expense.shares
            )
            return expense
