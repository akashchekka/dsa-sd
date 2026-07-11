"""Composite node. Holds named children (files or sub-directories); size is
the recursive sum of child sizes."""
from __future__ import annotations

from typing import Dict

from models.file_system_entity import FileSystemEntity


class Directory(FileSystemEntity):
    def __init__(self, name: str) -> None:
        self.name = name
        self.children: Dict[str, FileSystemEntity] = {}

    def get_size(self) -> int:
        return sum(child.get_size() for child in self.children.values())

    def is_dir(self) -> bool:
        return True

    def add_entity(self, entity: FileSystemEntity) -> None:
        self.children[entity.name] = entity
