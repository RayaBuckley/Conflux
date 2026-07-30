"""Typed continuation requests and immutable-history plan patches."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from conflux.domain import Provenance, fingerprint, provenance_union

from .model import Plan, PlanNode, TerminalNode, TerminalOutcome

PATCH_SCHEMA_VERSION = "1"


class PatchKind(StrEnum):
    APPEND = "append"
    REPLACE = "replace"
    SPAWN_SUBPLAN = "spawn_subplan"
    TERMINATE = "terminate"


class HistoricalNodeStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

    @property
    def immutable_history(self) -> bool:
        return self != HistoricalNodeStatus.PENDING


@dataclass(frozen=True, slots=True)
class PatchOperation:
    id: str
    kind: PatchKind
    nodes: tuple[PlanNode, ...] = ()
    target_node_ids: tuple[str, ...] = ()
    subplans: tuple[Plan, ...] = ()
    terminal_outcome: TerminalOutcome | None = None
    terminal_reason: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("patch operation id must be non-empty")
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "target_node_ids", tuple(self.target_node_ids))
        object.__setattr__(self, "subplans", tuple(self.subplans))
        if self.kind == PatchKind.APPEND and not self.nodes:
            raise ValueError("append operation requires nodes")
        if self.kind == PatchKind.REPLACE and (not self.nodes or not self.target_node_ids):
            raise ValueError("replace operation requires targets and replacement nodes")
        if self.kind == PatchKind.SPAWN_SUBPLAN and not self.subplans:
            raise ValueError("spawn operation requires subplans")
        if self.kind == PatchKind.TERMINATE and (
            self.terminal_outcome is None or not self.terminal_reason
        ):
            raise ValueError("terminate operation requires outcome and reason")

    def to_dict(self) -> dict[str, object]:
        from .model import node_to_dict

        return {
            "id": self.id,
            "kind": self.kind.value,
            "nodes": [node_to_dict(node) for node in self.nodes],
            "target_node_ids": list(self.target_node_ids),
            "subplans": [plan.to_dict() for plan in self.subplans],
            "terminal_outcome": (
                self.terminal_outcome.value if self.terminal_outcome is not None else None
            ),
            "terminal_reason": self.terminal_reason,
        }


@dataclass(frozen=True, slots=True)
class PlanPatch:
    id: str
    plan_id: str
    operations: tuple[PatchOperation, ...]
    schema_version: str = PATCH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.id or not self.plan_id:
            raise ValueError("patch and plan ids must be non-empty")
        if self.schema_version != PATCH_SCHEMA_VERSION:
            raise ValueError(f"unsupported patch schema version: {self.schema_version}")
        object.__setattr__(self, "operations", tuple(self.operations))
        operation_ids = [operation.id for operation in self.operations]
        if not self.operations or len(operation_ids) != len(set(operation_ids)):
            raise ValueError("patch operations must be non-empty and uniquely identified")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "plan_id": self.plan_id,
            "operations": [
                operation.to_dict()
                for operation in sorted(self.operations, key=lambda item: (item.id, item.kind.value))
            ],
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class PatchApplication:
    plan: Plan
    added_node_ids: tuple[str, ...]
    removed_node_ids: tuple[str, ...]
    added_subplan_ids: tuple[str, ...]
    terminal_node_id: str | None = None


def apply_patch(
    plan: Plan,
    patch: PlanPatch,
    *,
    history: dict[str, HistoricalNodeStatus],
    request_provenance: Provenance,
) -> PatchApplication:
    if patch.plan_id != plan.id:
        raise ValueError("patch targets a different plan")
    nodes = list(plan.nodes)
    subplans = list(plan.subplans)
    added: list[str] = []
    removed: list[str] = []
    added_subplans: list[str] = []
    terminal_node_id: str | None = None

    for operation in sorted(patch.operations, key=lambda item: (item.id, item.kind.value)):
        if operation.kind == PatchKind.REPLACE:
            removal = _replacement_closure(tuple(nodes), operation.target_node_ids)
            immutable = {
                node_id
                for node_id in removal
                if history.get(node_id, HistoricalNodeStatus.PENDING).immutable_history
            }
            if immutable:
                raise ValueError(f"patch cannot mutate completed history: {sorted(immutable)}")
            nodes = [node for node in nodes if node.id not in removal]
            removed.extend(sorted(removal))
            inherited = tuple(
                _inherit_control(node, request_provenance) for node in operation.nodes
            )
            nodes.extend(inherited)
            added.extend(node.id for node in inherited)
        elif operation.kind == PatchKind.APPEND:
            inherited = tuple(
                _inherit_control(node, request_provenance) for node in operation.nodes
            )
            nodes.extend(inherited)
            added.extend(node.id for node in inherited)
        elif operation.kind == PatchKind.SPAWN_SUBPLAN:
            for child in operation.subplans:
                inherited_plan = replace(
                    child,
                    invocation_provenance=provenance_union(
                        child.invocation_provenance,
                        request_provenance,
                    ).with_activity(f"patch:{patch.id}"),
                )
                subplans.append(inherited_plan)
                added_subplans.append(inherited_plan.id)
        else:
            assert operation.terminal_outcome is not None
            terminal_node_id = f"patch:{patch.id}:{operation.id}:terminal"
            terminal = TerminalNode(
                terminal_node_id,
                operation.terminal_outcome,
                operation.terminal_reason,
                request_provenance.with_activity(f"patch:{patch.id}"),
            )
            nodes.append(terminal)
            added.append(terminal.id)

    updated = Plan(
        plan.id,
        plan.goal,
        tuple(nodes),
        plan.invocation_provenance,
        tuple(subplans),
        plan.schema_version,
    )
    return PatchApplication(
        updated,
        tuple(added),
        tuple(removed),
        tuple(added_subplans),
        terminal_node_id,
    )


def _replacement_closure(
    nodes: tuple[PlanNode, ...],
    targets: tuple[str, ...],
) -> frozenset[str]:
    by_id = {node.id: node for node in nodes}
    unknown = set(targets) - by_id.keys()
    if unknown:
        raise ValueError(f"patch replacement targets are unknown: {sorted(unknown)}")
    removal = set(targets)
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if node.id not in removal and removal.intersection(node.dependencies):
                removal.add(node.id)
                changed = True
    return frozenset(removal)


def _inherit_control(node: PlanNode, provenance: Provenance) -> PlanNode:
    inherited = provenance_union(node.control_provenance, provenance).with_activity(
        f"continuation:{node.id}"
    )
    return replace(node, control_provenance=inherited)


__all__ = [
    "HistoricalNodeStatus",
    "PATCH_SCHEMA_VERSION",
    "PatchApplication",
    "PatchKind",
    "PatchOperation",
    "PlanPatch",
    "apply_patch",
]
