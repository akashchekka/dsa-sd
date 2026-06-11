"""One implementation per delivery channel. Returns True on success so the
retry policy can decide whether to back off and re-try."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models.notification import Notification
from models.subscription import Channel


class INotificationChannel(ABC):
    @property
    @abstractmethod
    def kind(self) -> Channel: ...

    @abstractmethod
    async def send(self, address: str, notification: Notification) -> bool: ...
