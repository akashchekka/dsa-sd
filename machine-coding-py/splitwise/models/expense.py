
from dataclasses import dataclass
from typing import Dict

@dataclass
class Expense:
    payer_id: str
    amount: float
    shares: Dict[str, float]
