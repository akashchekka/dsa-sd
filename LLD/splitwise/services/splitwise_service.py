
from __future__ import annotations

import threading
from typing import Any

from interfaces.simplify_strategy import SimplifyStrategy, Settlement
from interfaces.split_strategy    import SplitStrategy
from models.expense               import Expense
from models.group                 import Group
from models.user                  import User
from services.expense_validator   import ExpenseValidator

GLOBAL_GROUP_ID = "__global__"

class SplitwiseService:
    def __init__(self, simplify_strategy: SimplifyStrategy) -> None:
        self.users:  dict[str, User]  = {}
        self.groups: dict[str, Group] = {}
        self.simplify_strategy: SimplifyStrategy = simplify_strategy
        self._validator: ExpenseValidator = ExpenseValidator(self.users)

        self._users_lock  = threading.Lock()
        self._groups_lock = threading.Lock()
        self.groups[GLOBAL_GROUP_ID] = Group(GLOBAL_GROUP_ID, "Global")

    # --- user / group registry ----------------------------------------------

    def register_user(self, user_id: str, name: str) -> User:
        """Idempotent under contention via double-checked locking."""
        # Fast path — lock-free read; dict.get is atomic under the GIL.
        user = self.users.get(user_id)
        if user is None:
            with self._users_lock:
                # Re-check inside the lock: another thread may have created
                # this user between the first check and acquiring the lock.
                user = self.users.get(user_id)
                if user is None:
                    user = User(user_id, name)
                    self.users[user_id] = user

        self.groups[GLOBAL_GROUP_ID].add_member(user_id)
        return user

    def create_group(self, group_id: str, name: str, member_ids: list[str]) -> Group:
        """Idempotent under contention via double-checked locking.

        Members provided are added on top of any existing members (set
        semantics — concurrent duplicate adds are silently merged).
        """
        if group_id == GLOBAL_GROUP_ID:
            raise ValueError(f"{GLOBAL_GROUP_ID!r} is reserved")

        unknown = set(member_ids) - self.users.keys()
        if unknown:
            raise ValueError(f"Unknown users for group {group_id!r}: {sorted(unknown)}")

        # Fast path.
        group = self.groups.get(group_id)
        if group is None:
            with self._groups_lock:
                group = self.groups.get(group_id)
                if group is None:
                    group = Group(group_id, name)
                    self.groups[group_id] = group

        for uid in member_ids:
            group.add_member(uid)
        return group

    def add_member_to_group(self, group_id: str, user_id: str) -> None:
        if user_id not in self.users:
            raise ValueError(f"Unknown user: {user_id!r}")
        self._group(group_id).add_member(user_id)

    # --- expenses ------------------------------------------------------------

    def add_expense(
        self,
        payer_id: str,
        amount: float,
        participants: list[str],
        split_strategy: SplitStrategy,
        group_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        group = self._group(group_id or GLOBAL_GROUP_ID)
        self._validator.validate(group, payer_id, amount, participants)

        shares = split_strategy.calculate_shares(amount, participants, **kwargs)

        return group.record_expense(payer_id, amount, shares)

    def remove_expense(self, expense_id: str, group_id: str | None = None) -> None:
        self._group(group_id or GLOBAL_GROUP_ID).remove_expense(expense_id)

    # --- settlement ----------------------------------------------------------

    def simplify_debts(self, group_id: str | None = None) -> list[Settlement]:
        return self.simplify_strategy.simplify(
            self._group(group_id or GLOBAL_GROUP_ID).balance_sheet.snapshot()
        )

    # --- helpers -------------------------------------------------------------

    def _group(self, group_id: str) -> Group:
        if group_id not in self.groups:
            raise ValueError(f"Unknown group: {group_id!r}")
        return self.groups[group_id]
