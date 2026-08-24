"""Subsystem-independent graph model for deterministic visualisation.

This module defines the intermediate representation that sits between
evidence adapters (ITES, SLED, verification, planning) and renderers
(Graphviz SVG, HTML).  Every node and edge carries an ``EvidenceReference``
pointing back to the authoritative structured evidence.

The visual graph is never the canonical security record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VisualStatus(Enum):
    """Stable status vocabulary for visual elements.

    Status is never encoded exclusively through colour.  Every status has
    text and icon/shape distinction where practical.
    """

    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    INCOMPLETE = "INCOMPLETE"
    PRUNED = "PRUNED"
    REVISITED = "REVISITED"
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NodeKind(Enum):
    """Category of a visual node."""

    EXECUTION = "execution"
    ACTION = "action"
    PRINCIPAL = "principal"
    ARTIFACT = "artifact"
    STATE = "state"
    INVARIANT = "invariant"
    VARIABLE = "variable"
    RULE = "rule"
    ASSUMPTION = "assumption"
    OPERATION = "operation"
    OBSERVATION = "observation"
    DECISION = "decision"
    APPROVAL = "approval"
    DELEGATION = "delegation"
    TERMINAL = "terminal"
    GOAL = "goal"
    FAILURE = "failure"
    SUMMARY = "summary"
    VERDICT = "verdict"


class EdgeKind(Enum):
    """Category of a visual edge."""

    AUTHORED = "AUTHORED"
    DERIVED_FROM = "DERIVED_FROM"
    INPUT_TO = "INPUT_TO"
    OUTPUT_OF = "OUTPUT_OF"
    INFLUENCES = "INFLUENCES"
    PROPOSED = "PROPOSED"
    EXECUTED = "EXECUTED"
    OBSERVABLE_TO = "OBSERVABLE_TO"
    PARENT_OF = "PARENT_OF"
    TRANSITION = "TRANSITION"
    DEPENDS_ON = "DEPENDS_ON"
    REDUCED_TO = "REDUCED_TO"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    APPROVAL = "APPROVAL"
    DELEGATION = "DELEGATION"
    RETRY = "RETRY"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"


@dataclass(frozen=True)
class EvidenceReference:
    """Pointer back to the authoritative structured evidence.

    ``json_pointer`` uses RFC 6901 syntax relative to the evidence file
    identified by ``source_file``.
    """

    source_file: str
    json_pointer: str

    def to_dict(self) -> dict[str, str]:
        """Serialise to a JSON-compatible dictionary."""
        return {"source_file": self.source_file, "json_pointer": self.json_pointer}


@dataclass(frozen=True)
class VisualField:
    """A key-value pair displayed on a visual node."""

    key: str
    value: str
    status: VisualStatus | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dictionary."""
        result: dict[str, Any] = {"key": self.key, "value": self.value}
        if self.status is not None:
            result["status"] = self.status.value
        return result


@dataclass(frozen=True)
class VisualNode:
    """A node in a visual graph.

    ``node_id`` must be stable across repeated renderings of the same
    evidence.  ``source_ref`` links back to the authoritative evidence.
    """

    node_id: str
    kind: NodeKind
    label: str
    fields: tuple[VisualField, ...] = ()
    status: VisualStatus | None = None
    source_ref: EvidenceReference | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
        }
        if self.fields:
            result["fields"] = [field.to_dict() for field in self.fields]
        if self.status is not None:
            result["status"] = self.status.value
        if self.source_ref is not None:
            result["source_ref"] = self.source_ref.to_dict()
        return result


@dataclass(frozen=True)
class VisualEdge:
    """An edge in a visual graph.

    ``source`` and ``target`` must reference existing ``VisualNode.node_id``
    values.  ``source_ref`` is optional because some edges are structural
    rather than directly evidenced.
    """

    source: str
    target: str
    kind: EdgeKind
    label: str | None = None
    source_ref: EvidenceReference | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dictionary."""
        result: dict[str, Any] = {
            "source": self.source,
            "target": self.target,
            "kind": self.kind.value,
        }
        if self.label is not None:
            result["label"] = self.label
        if self.source_ref is not None:
            result["source_ref"] = self.source_ref.to_dict()
        return result


@dataclass(frozen=True)
class VisualGraph:
    """A layout-agnostic graph projecting structured evidence.

    Nodes and edges are sorted by stable IDs for deterministic output.
    The ``graph_id`` must be stable across repeated renderings of the
    same evidence.
    """

    graph_id: str
    title: str
    nodes: tuple[VisualNode, ...]
    edges: tuple[VisualEdge, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dictionary with deterministic ordering."""
        sorted_nodes = sorted(self.nodes, key=lambda n: n.node_id)
        sorted_edges = sorted(self.edges, key=lambda e: (e.source, e.target, e.kind.value))
        result: dict[str, Any] = {
            "graph_id": self.graph_id,
            "title": self.title,
            "nodes": [node.to_dict() for node in sorted_nodes],
            "edges": [edge.to_dict() for edge in sorted_edges],
        }
        if self.metadata:
            result["metadata"] = dict(sorted(self.metadata.items()))
        return result

    @property
    def node_ids(self) -> set[str]:
        """Return the set of all node IDs in this graph."""
        return {node.node_id for node in self.nodes}


def validate_graph(graph: VisualGraph) -> list[str]:
    """Check structural invariants of a visual graph.

    Returns a list of error messages.  An empty list means the graph
    is structurally valid.
    """
    errors: list[str] = []

    node_ids = graph.node_ids

    for edge in graph.edges:
        if edge.source not in node_ids:
            errors.append(f"edge source {edge.source} not in nodes")
        if edge.target not in node_ids:
            errors.append(f"edge target {edge.target} not in nodes")

    seen_ids: set[str] = set()
    for node in graph.nodes:
        if node.node_id in seen_ids:
            errors.append(f"duplicate node id: {node.node_id}")
        seen_ids.add(node.node_id)

    return errors
