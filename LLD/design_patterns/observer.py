from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


# ---- Contracts -------------------------------------------------------------

class IObserver(ABC):
    @abstractmethod
    def update(self, subject: "Subject", event: Any) -> None: ...


class Subject:
    """Subject manages its observers. Concrete subjects subclass this."""

    def __init__(self) -> None:
        self._observers: list[IObserver] = []

    def attach(self, observer: IObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: IObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: Any = None) -> None:
        # Iterate over a copy so observers can safely detach during update.
        for obs in list(self._observers):
            obs.update(self, event)


# ---- Concrete Subject ------------------------------------------------------

class StockTicker(Subject):
    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.symbol = symbol
        self._price: float = 0.0

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, new_price: float) -> None:
        if new_price != self._price:
            self._price = new_price
            self.notify(event={"symbol": self.symbol, "price": new_price})


# ---- Concrete Observers ----------------------------------------------------

class ConsoleLogger(IObserver):
    def update(self, subject: Subject, event: Any) -> None:
        print(f"[log] {event['symbol']} → {event['price']:.2f}")


class PriceAlert(IObserver):
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def update(self, subject: Subject, event: Any) -> None:
        if event["price"] >= self.threshold:
            print(f"[alert] {event['symbol']} crossed {self.threshold}")


# ---- Demo ------------------------------------------------------------------

if __name__ == "__main__":
    aapl = StockTicker("AAPL")
    aapl.attach(ConsoleLogger())
    aapl.attach(PriceAlert(threshold=200.0))

    aapl.price = 190.0   # logged only
    aapl.price = 205.0   # logged + alert
    aapl.price = 205.0   # no notify (unchanged)