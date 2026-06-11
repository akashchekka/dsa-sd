"""Controller: resolves POSIX-style paths, auto-creates intermediate
directories on traversal (LeetCode 588 semantics), and exposes mkdir,
add_content_to_file, and ls."""
from __future__ import annotations

from typing import List

from models.directory import Directory
from models.file      import File


class InMemoryFileSystem:
    def __init__(self) -> None:
        self.root = Directory("/")

    def _traverse(self, path: str) -> Directory:
        """Resolve a directory path; auto-create missing intermediate dirs."""
        if path == "/":
            return self.root

        parts = path.strip("/").split("/")
        curr: Directory = self.root

        for part in parts:
            if part not in curr.children:
                curr.children[part] = Directory(part)
            node = curr.children[part]
            if not node.is_dir():
                raise ValueError(f"{part} is a file, not a directory.")
            curr = node  # type: ignore[assignment]
        return curr

    def mkdir(self, path: str) -> None:
        self._traverse(path)

    def add_content_to_file(self, file_path: str, content: str) -> None:
        parts     = file_path.strip("/").split("/")
        file_name = parts.pop()
        dir_path  = "/" + "/".join(parts)

        directory = self._traverse(dir_path)

        if file_name not in directory.children:
            directory.children[file_name] = File(file_name)

        file_node = directory.children[file_name]
        if file_node.is_dir():
            raise ValueError(f"{file_name} is a directory.")

        file_node.write(content)  # type: ignore[attr-defined]

    def ls(self, path: str) -> List[str]:
        if path == "/":
            curr = self.root
        else:
            curr = self.root
            for part in path.strip("/").split("/"):
                curr = curr.children[part]  # type: ignore[assignment]

        if not curr.is_dir():
            return [curr.name]

        return sorted(curr.children.keys())
