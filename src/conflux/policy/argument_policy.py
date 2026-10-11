"""Deterministic pointwise policy for trusted-role action arguments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from conflux.domain import (
    Action,
    ActionArgument,
    ArgumentRole,
    Decision,
    DecisionCategory,
    EnvironmentSnapshot,
    PrimitiveAction,
    Principal,
)


def _is_sha256(value: str) -> bool:
    """Return True when a value is a lowercase hexadecimal SHA-256 digest."""
    return len(value) == 64 and not any(character not in "0123456789abcdef" for character in value)


@dataclass(frozen=True, slots=True)
class ArgumentRequirement:
    """A condition one grant places on one other argument of the same action.

    A requirement lets a single rule constrain two facts at once, for example that content which
    came only from a reviewed item may travel to a destination. Every condition fails closed: an
    absent argument, unknown provenance, an unlisted source, or a different value denies the grant
    that carries the requirement. A requirement never grants authority; it can only remove an
    allowance the grant it belongs to would otherwise give.
    """

    argument_name: str
    provenance_sources: frozenset[str] | None = None
    value_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.argument_name:
            raise ValueError("argument requirement needs an argument name")
        if self.provenance_sources is None and self.value_fingerprint is None:
            raise ValueError("argument requirement needs a provenance source list or a value fingerprint")
        if self.provenance_sources is not None:
            object.__setattr__(self, "provenance_sources", frozenset(self.provenance_sources))
            if any(not source for source in self.provenance_sources):
                raise ValueError("argument requirement sources must be non-empty")
        if self.value_fingerprint is not None and not _is_sha256(self.value_fingerprint):
            raise ValueError("argument requirement fingerprint must be SHA-256")

    def holds(self, arguments: Mapping[str, ActionArgument]) -> bool:
        """Return True when the named argument of one action satisfies this requirement."""
        argument = arguments.get(self.argument_name)
        if argument is None:
            return False
        if self.provenance_sources is not None:
            provenance = argument.provenance
            if provenance.is_unknown or not provenance.sources:
                return False
            if not provenance.sources <= self.provenance_sources:
                return False
        return self.value_fingerprint is None or argument.value_fingerprint == self.value_fingerprint


@dataclass(frozen=True, slots=True)
class ArgumentPolicyGrant:
    """Immutable grant linking a principal to a specific action-argument role."""

    principal_id: str
    operation: str
    argument_name: str
    role: ArgumentRole
    value_fingerprint: str | None = None
    requires: tuple[ArgumentRequirement, ...] = ()

    def __post_init__(self) -> None:
        if not self.principal_id or not self.operation or not self.argument_name:
            raise ValueError("argument policy grant identity must be non-empty")
        if self.value_fingerprint is not None and not _is_sha256(self.value_fingerprint):
            raise ValueError("argument policy grant fingerprint must be SHA-256")
        object.__setattr__(self, "requires", tuple(self.requires))
        names = [requirement.argument_name for requirement in self.requires]
        if any(name == self.argument_name for name in names):
            raise ValueError("argument policy grant cannot require the argument it grants")
        if len(set(names)) != len(names):
            raise ValueError("argument policy grant has duplicate requirements")


@dataclass(frozen=True, slots=True)
class InMemoryArgumentAuthorisationPolicy:
    """Pointwise authorisation policy backed by a set of argument grants."""

    grants: frozenset[ArgumentPolicyGrant] = field(default_factory=frozenset)
    policy_id: str = "in-memory-argument-policy"
    policy_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", frozenset(self.grants))

    def decide(
        self,
        principal: Principal,
        action: Action,
        argument: ActionArgument,
        environment: EnvironmentSnapshot,
    ) -> Decision:
        """Return an authorisation decision for a single action argument."""
        _ = environment
        if not isinstance(action, PrimitiveAction):
            return Decision(
                DecisionCategory.AUTHORISATION,
                False,
                "argument_action_unsupported",
                self.policy_id,
                self.policy_version,
            )
        matches = tuple(
            grant
            for grant in self.grants
            if grant.principal_id == principal.id
            and grant.operation == action.operation
            and grant.argument_name == argument.name
            and grant.role == argument.role
            and (grant.value_fingerprint is None or grant.value_fingerprint == argument.value_fingerprint)
        )
        arguments = {item.name: item for item in action.arguments}
        failed: set[str] = set()
        allowed = False
        for grant in matches:
            unmet = tuple(requirement for requirement in grant.requires if not requirement.holds(arguments))
            if not unmet:
                allowed = True
                break
            failed.update(requirement.argument_name for requirement in unmet)
        reason = "argument_grant" if allowed else ("argument_requirement_denied" if matches else "argument_deny")
        return Decision(
            DecisionCategory.AUTHORISATION,
            allowed,
            reason,
            self.policy_id,
            self.policy_version,
            evidence=(
                principal.id,
                action.operation,
                argument.name,
                argument.role.value,
                argument.value_fingerprint,
                *(f"requires_failed:{name}" for name in sorted(failed)),
            ),
        )


__all__ = ["ArgumentPolicyGrant", "ArgumentRequirement", "InMemoryArgumentAuthorisationPolicy"]
