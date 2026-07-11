from dataclasses import dataclass
from .enums import RequestType

@dataclass(frozen=True)
class Request:
    floor: int
    type: RequestType
