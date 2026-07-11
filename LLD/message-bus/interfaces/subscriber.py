"""Subscriber contract. Implement `on_message` to receive delivered messages."""
from __future__ import annotations

from abc import ABC, abstractmethod
from models.message import Message

class Subscriber(ABC):
    @abstractmethod
    def on_message(self, message: Message) -> None:
        """Handle one delivered message.

        Called on the topic's worker thread. Exceptions raised here are
        isolated by the bus and never affect other subscribers.
        """
        ...