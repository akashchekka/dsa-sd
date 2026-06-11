"""Composite-pattern Component. Common contract for both leaves (File) and
composites (Directory) so the controller can treat them uniformly."""
from __future__ import annotations

from abc import ABC, abstractmethod


class FileSystemEntity(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def get_size(self) -> int: ...

    @abstractmethod
    def is_dir(self) -> bool: ...
