from __future__ import annotations

from abc import ABC, abstractmethod

from models.message import Message


class Subscriber(ABC):
    @abstractmethod
    def consume(self, message: Message) -> None: ...
