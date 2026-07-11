"""Restaurant service (simple management system).

Ties everything together:
- holds the Menu,
- turns a table's requested dish names into an Order (with a unique id),
- places orders onto a thread-safe priority queue,
- runs a pool of cook threads that cook the highest-priority order first, then
  "serve" it and print the bill.

The order lifecycle is PLACED -> COOKING -> READY -> SERVED.
"""
from __future__ import annotations

import itertools
import threading
import time
from typing import Any

from models.menu import Menu
from models.order import Order, OrderStatus, Priority
from queues.priority_queue import CustomPriorityQueue


class Restaurant:
    def __init__(self, menu: Menu, num_cooks: int = 2, order_queue: Any | None = None) -> None:
        self._menu = menu
        self._ids = itertools.count(1)
        self._id_lock = threading.Lock()

        self._queue: Any = order_queue if order_queue is not None else CustomPriorityQueue()
        self._cooks = [
            threading.Thread(target=self._cook, name=f"cook-{i + 1}", args=(i + 1,))
            for i in range(num_cooks)
        ]
        for c in self._cooks:
            c.start()

    def place_order(
        self, table_id: int, item_names: list[str], priority: Priority = Priority.NORMAL
    ) -> Order:
        items = [self._menu.get(name) for name in item_names]   # validates against menu
        with self._id_lock:
            order_id = next(self._ids)
        order = Order(order_id, table_id, items, priority)
        self._queue.put(order, priority) # Waiter/Customer placing order to queue
        print(f"[waiter] placed {priority.name:6} order {order.summary()}")
        return order

    def _cook(self, cid: int) -> None:
        while True:
            order = self._queue.get()               # Cook taking the order
            if order is None:                       # queue closed and drained
                break
            order.status = OrderStatus.COOKING
            print(f"    [cook {cid}] cooking {order.summary()}")
            time.sleep(0.2)                         # simulate cooking time
            order.status = OrderStatus.READY
            self._serve(order)

    def _serve(self, order: Order) -> None:
        order.status = OrderStatus.SERVED
        print(f"        [served] {order.summary()} -> bill ${order.total():.2f}")

    def close(self) -> None:
        """Stop accepting orders, finish what's queued, then wait for cooks."""
        self._queue.close()
        for c in self._cooks:
            c.join()
