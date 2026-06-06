from __future__ import annotations

import heapq

from interfaces.simplify_strategy import SimplifyStrategy, Settlement


class HeapSimplifyStrategy(SimplifyStrategy):
    def simplify(self, balances: dict[str, float]) -> list[Settlement]:
        debtors:   list[tuple[float, str]] = []
        creditors: list[tuple[float, str]] = []

        for user, balance in balances.items():
            if balance < 0:
                heapq.heappush(debtors, (balance, user))
            elif balance > 0:
                heapq.heappush(creditors, (-balance, user))

        result: list[Settlement] = []

        while debtors and creditors:
            debt,   debtor   = heapq.heappop(debtors)
            credit, creditor = heapq.heappop(creditors)

            debt   = -debt
            credit = -credit

            amt = min(debt, credit)
            result.append((debtor, creditor, amt))

            debt   -= amt
            credit -= amt

            if debt:
                heapq.heappush(debtors, (-debt, debtor))
            if credit:
                heapq.heappush(creditors, (-credit, creditor))

        return result
