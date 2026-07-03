"""Immutable message envelope carried by the bus."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    topic: str
    payload: object
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"Message(topic={self.topic!r}, payload={self.payload!r})"
