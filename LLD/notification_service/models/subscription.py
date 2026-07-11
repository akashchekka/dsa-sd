"""A subscriber registers (user_id, preferred channel) per topic."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Channel(Enum):
    EMAIL = "email"
    SMS   = "sms"
    PUSH  = "push"


@dataclass(frozen=True)
class Subscription:
    user_id: str
    topic: str
    channel: Channel
    address: str
