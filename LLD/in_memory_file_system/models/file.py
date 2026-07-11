"""Leaf node. A file holds raw string content; size is content length."""
from __future__ import annotations

from models.file_system_entity import FileSystemEntity


class File(FileSystemEntity):
    def __init__(self, name: str) -> None:
        self.name = name
        self.content: str = ""

    def get_size(self) -> int:
        return len(self.content)

    def is_dir(self) -> bool:
        return False

    def write(self, data: str) -> None:
        self.content += data

    def read(self) -> str:
        return self.content
