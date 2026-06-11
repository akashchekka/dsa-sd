"""
=============================================================================
 InMemoryFileSystem — entry point
=============================================================================
 Run:  python -m in_memory_file_system   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

from services.in_memory_file_system import InMemoryFileSystem


def main() -> None:
    fs = InMemoryFileSystem()

    fs.mkdir("/a/b/c")
    fs.add_content_to_file("/a/b/c/hello.txt", "hello ")
    fs.add_content_to_file("/a/b/c/hello.txt", "world")
    fs.add_content_to_file("/a/readme.md",     "top-level note")

    print("ls /         :", fs.ls("/"))
    print("ls /a        :", fs.ls("/a"))
    print("ls /a/b/c    :", fs.ls("/a/b/c"))
    print("ls file path :", fs.ls("/a/b/c/hello.txt"))
    print("root size    :", fs.root.get_size())


if __name__ == "__main__":
    main()
