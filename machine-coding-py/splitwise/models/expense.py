
from dataclasses import dataclass, field
from typing import Dict
from uuid import uuid4


@dataclass
class Expense:
    payer_id: str
    amount: float
    shares: Dict[str, float]
    expense_id: str = field(default_factory=lambda: str(uuid4()))
