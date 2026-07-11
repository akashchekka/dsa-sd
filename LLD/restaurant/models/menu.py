from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MenuItem:
    name: str
    price: float

class Menu:
    def __init__(self) -> None:
        self._items: dict[str, MenuItem] = {}

    def add(self, name: str, price: float) -> None:
        self._items[name] = MenuItem(name, price)

    def get(self, name: str) -> MenuItem:
        if name not in self._items:
            raise KeyError(f"{name!r} is not on the menu")
        return self._items[name]
