from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

V = TypeVar("V")

@dataclass
class Entry(Generic[V]):
    value: V
    expiry: Optional[float] = None
