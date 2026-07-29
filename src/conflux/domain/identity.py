"""Principal identities and conservative Principal Context values."""

from __future__ import annotations

from dataclasses import dataclass, field

from .serialization import fingerprint


@dataclass(frozen=True, slots=True, order=True)
class Principal:
    """An authenticated identity; policy, not identity, owns authority."""

    id: str
    name: str
    kind: str = "human"

    def __post_init__(self) -> None:
        if not self.id or not self.name or not self.kind:
            raise ValueError("Principal fields must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "kind": self.kind}


@dataclass(frozen=True, slots=True)
class PrincipalContext:
    """The immutable conservative set of Principals influencing a decision."""

    principals: frozenset[Principal] = field(default_factory=frozenset)
    unknown: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "principals", frozenset(self.principals))

    @classmethod
    def from_principals(cls, principals: frozenset[Principal]) -> "PrincipalContext":
        return cls(principals=principals, unknown=not principals)

    @property
    def is_authority_bearing(self) -> bool:
        return bool(self.principals) and not self.unknown

    def extend(self, *principals: Principal, unknown: bool = False) -> "PrincipalContext":
        return PrincipalContext(
            principals=self.principals | frozenset(principals),
            unknown=self.unknown or unknown,
        )

    def merge(self, other: "PrincipalContext") -> "PrincipalContext":
        return PrincipalContext(
            principals=self.principals | other.principals,
            unknown=self.unknown or other.unknown,
        )

    def contains(self, principal: Principal) -> bool:
        return principal in self.principals

    def to_dict(self) -> dict[str, object]:
        return {
            "principal_ids": sorted(principal.id for principal in self.principals),
            "unknown": self.unknown,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


__all__ = ["Principal", "PrincipalContext"]
