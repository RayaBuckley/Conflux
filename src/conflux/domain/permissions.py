"""Provider-neutral permission names."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Permission:
    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Permission.name must be non-empty")

    def __str__(self) -> str:
        return self.name


READ = Permission("read")
WRITE = Permission("write")
DELETE = Permission("delete")
SHARE = Permission("share")
DELEGATE = Permission("delegate")


def normalise_permission(value: Permission | str) -> Permission:
    return value if isinstance(value, Permission) else Permission(value)


__all__ = [
    "DELEGATE",
    "DELETE",
    "Permission",
    "READ",
    "SHARE",
    "WRITE",
    "normalise_permission",
]
