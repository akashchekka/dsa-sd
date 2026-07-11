# In-Memory File System

POSIX-style in-memory file system built with the **Composite** pattern. Supports `mkdir`, `add_content_to_file` (create-or-append), and `ls` (LeetCode 588).

## Run

```pwsh
cd machine-coding-py
python -m in_memory_file_system
```

## Design patterns

| Pattern | Where | Why it works |
|---|---|---|
| **Composite** | `FileSystemEntity` (Component) → `File` (Leaf), `Directory` (Composite) | A directory holds children that are themselves entities, so `get_size()` recurses uniformly and the controller treats a single file and a whole folder through one interface — the essence of part–whole tree data. |

## File layout

```
in_memory_file_system/
├── __main__.py                       # demo: mkdir, write, ls
├── models/
│   ├── file_system_entity.py         # Component (ABC): name, get_size, is_dir
│   ├── file.py                       # Leaf: content + read/write
│   └── directory.py                  # Composite: name → child entities
└── services/
    └── in_memory_file_system.py      # controller: _traverse / mkdir / add_content_to_file / ls
```

## Key design choices

| Concern | Decision | Why |
|---|---|---|
| **Tree shape** | Composite pattern | `File` and `Directory` share one interface so traversal code is uniform |
| **Path resolution** | `_traverse` auto-creates missing dirs | Matches LeetCode 588 semantics: `mkdir /a/b/c` works even if `/a` doesn't exist |
| **`ls` on a file** | Returns `[file_name]` | Spec quirk: `ls` of a file lists just that file |
| **`ls` on a directory** | Returns sorted child names | Deterministic output |
| **Append vs overwrite** | `add_content_to_file` appends | Matches the LeetCode contract |
| **Size** | Recursive sum on `Directory` | Composite delegates to children — no special-casing in the controller |
