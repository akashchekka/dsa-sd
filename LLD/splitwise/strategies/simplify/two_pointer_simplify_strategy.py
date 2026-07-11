from __future__ import annotations

from interfaces.simplify_strategy import SimplifyStrategy, Settlement


class TwoPointerSimplifyStrategy(SimplifyStrategy):
    def simplify(self, balances: dict[str, float]) -> list[Settlement]:

        debtors:   list[list] = [[u, -b] for u, b in balances.items() if b < 0]
        creditors: list[list] = [[u,  b] for u, b in balances.items() if b > 0]

        i = j = 0
        result: list[Settlement] = []
        EPS = 1e-9

        while i < len(debtors) and j < len(creditors):
            amt = min(debtors[i][1], creditors[j][1])
            result.append((debtors[i][0], creditors[j][0], amt))

            debtors[i][1]   -= amt
            creditors[j][1] -= amt

            if debtors[i][1] <= EPS:
                i += 1
            if creditors[j][1] <= EPS:
                j += 1

        return result
