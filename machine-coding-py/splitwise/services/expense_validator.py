from __future__ import annotations

from models.group import Group
from models.user  import User


class ExpenseValidator:
    """Pre-flight checks for add_expense. Fails fast before any state mutation."""

    def __init__(self, users: dict[str, User]) -> None:
        self._users = users

    def validate(
        self,
        group: Group,
        payer_id: str,
        amount: float,
        participants: list[str],
    ) -> None:
        if amount <= 0:
            raise ValueError(f"Amount must be positive (got {amount})")

        if payer_id not in self._users:
            raise ValueError(f"Unknown payer: {payer_id!r}")

        if not participants:
            raise ValueError("Participants list is required")

        unknown = set(participants) - self._users.keys()
        if unknown:
            raise ValueError(f"Unknown participants: {sorted(unknown)}")

        if len(set(participants)) != len(participants):
            raise ValueError(f"Duplicate participants: {participants}")

        if not group.has_member(payer_id):
            raise ValueError(
                f"Payer {payer_id!r} is not a member of group {group.group_id!r}"
            )

        non_members = set(participants) - group.members
        if non_members:
            raise ValueError(
                f"Participants not in group {group.group_id!r}: {sorted(non_members)}"
            )
