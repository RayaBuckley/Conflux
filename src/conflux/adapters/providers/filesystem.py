"""Read-only filesystem materialisation with explicit provenance metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from conflux.domain import DataItem, EnvironmentSnapshot, Principal


@dataclass(frozen=True, slots=True)
class FilesystemSnapshotProvider:
    """Materialise a read-only environment snapshot from a filesystem root."""

    root: Path
    author: Principal
    readers: frozenset[Principal]

    def snapshot(self) -> EnvironmentSnapshot:
        """Build an :class:`EnvironmentSnapshot` from all files beneath the root."""
        root = self.root.resolve()
        if not root.is_dir():
            raise ValueError("filesystem root must be a directory")
        paths = tuple(sorted(root.rglob("*")))
        if any(path.is_symlink() for path in paths):
            raise ValueError("filesystem snapshot rejects symlinks")
        items = tuple(
            DataItem(
                id=path.relative_to(root).as_posix(),
                value=path.read_text(encoding="utf-8"),
                authors=frozenset({self.author}),
                readers=self.readers,
                label=path.name,
            )
            for path in paths
            if path.is_file()
        )
        return EnvironmentSnapshot(id=f"filesystem:{root.name}", data=items)


__all__ = ["FilesystemSnapshotProvider"]
