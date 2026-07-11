from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, IntEnum
from models.menu import MenuItem

class Priority(IntEnum):
    VIP = 0        # cooked first
    NORMAL = 1     # cooked after all VIP orders

class OrderStatus(Enum):
    PLACED = "PLACED"
    COOKING = "COOKING"
    READY = "READY"
    SERVED = "SERVED"

@dataclass
class Order:
    order_id: int
    table_id: int
    items: list[MenuItem]
    priority: Priority = Priority.NORMAL
    status: OrderStatus = OrderStatus.PLACED

    def total(self) -> float:
        return sum(item.price for item in self.items)

    def summary(self) -> str:
        names = ", ".join(item.name for item in self.items)
        return f"#{self.order_id} (table {self.table_id}): {names}"
