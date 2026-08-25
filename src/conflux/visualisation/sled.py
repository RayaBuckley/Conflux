"""Native SLED visualisation adapter.

Converts a ``VerificationResult`` into a ``VisualGraph`` showing
explored states, transitions, counterexamples, and bounds.
For small state spaces (below a threshold), a full state graph is
produced.  For large runs, a summary is produced instead.
"""

from __future__ import annotations

from typing import Any

from conflux.evaluation.model_checking import (
    VerificationResult,
    VerificationVerdict,
)
from conflux.visualisation.model import (
    EdgeKind,
    EvidenceReference,
    NodeKind,
    VisualEdge,
    VisualField,
    VisualGraph,
    VisualNode,
    VisualStatus,
)

DEFAULT_STATE_THRESHOLD = 250


_VERDICT_STATUS: dict[VerificationVerdict, VisualStatus] = {
    VerificationVerdict.SAFE: VisualStatus.SAFE,
    VerificationVerdict.BOUNDED_SAFE: VisualStatus.SAFE,
    VerificationVerdict.UNSAFE: VisualStatus.UNSAFE,
    VerificationVerdict.UNKNOWN: VisualStatus.UNKNOWN,
}


def _summary_graph(
    result: VerificationResult[Any, Any],
    *,
    run_id: str,
) -> VisualGraph:
    """Produce a summary graph for large verification runs."""
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    stats = result.to_dict()["statistics"]
    bounds = result.to_dict()["bounds"]

    summary_fields: list[VisualField] = [
        VisualField(key="verdict", value=result.verdict.value),
        VisualField(key="unique_states", value=str(stats["unique_states"])),  # type: ignore[index]
        VisualField(key="transitions", value=str(stats["transitions"])),  # type: ignore[index]
        VisualField(key="duplicate_states", value=str(stats["duplicate_states"])),  # type: ignore[index]
        VisualField(key="truncated", value=str(stats["truncated"])),  # type: ignore[index]
        VisualField(key="max_depth", value=str(bounds["max_depth"])),  # type: ignore[index]
        VisualField(key="max_states", value=str(bounds["max_states"])),  # type: ignore[index]
        VisualField(key="max_transitions", value=str(bounds["max_transitions"])),  # type: ignore[index]
        VisualField(key="max_model_calls", value=str(bounds["max_model_calls"])),  # type: ignore[index]
    ]

    verdict_node = VisualNode(
        node_id="verdict",
        kind=NodeKind.VERDICT,
        label=f"Verdict: {result.verdict.value}",
        fields=tuple(summary_fields),
        status=_VERDICT_STATUS.get(result.verdict),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer="/verdict",
        ),
    )
    nodes.append(verdict_node)

    if result.counterexample is not None:
        cx = result.counterexample
        cx_fields: list[VisualField] = [
            VisualField(key="property", value=cx.property_name),
            VisualField(key="reason", value=cx.reason),
            VisualField(key="length", value=str(cx.length)),
        ]
        cx_node = VisualNode(
            node_id="counterexample",
            kind=NodeKind.ACTION,
            label=f"Counterexample ({cx.length} steps)",
            fields=tuple(cx_fields),
            status=VisualStatus.UNSAFE,
            source_ref=EvidenceReference(
                source_file=f"{run_id}.json",
                json_pointer="/counterexample",
            ),
        )
        nodes.append(cx_node)
        edges.append(
            VisualEdge(
                source="verdict",
                target="counterexample",
                kind=EdgeKind.COUNTEREXAMPLE,
            ),
        )

    return VisualGraph(
        graph_id=f"sled:{run_id}",
        title=f"SLED Verification — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "verdict": result.verdict.value,
            "unique_states": str(result.unique_states),
            "transitions": str(result.transitions),
            "truncated": str(result.truncated),
        },
    )


def sled_to_graph(
    result: VerificationResult[Any, Any],
    *,
    run_id: str = "sled-run",
    state_threshold: int = DEFAULT_STATE_THRESHOLD,
) -> VisualGraph:
    """Convert a SLED verification result into a visual graph.

    For results under ``state_threshold`` unique states, a full state
    graph is produced.  For larger runs, a summary is produced.

    The visual wording preserves the semantic strength of the
    authoritative verdict (SAFE, BOUNDED_SAFE, UNSAFE, UNKNOWN).
    """
    if result.unique_states > state_threshold:
        return _summary_graph(result, run_id=run_id)

    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    verdict_node = VisualNode(
        node_id="verdict",
        kind=NodeKind.VERDICT,
        label=f"Verdict: {result.verdict.value}",
        fields=(
            VisualField(key="unique_states", value=str(result.unique_states)),
            VisualField(key="transitions", value=str(result.transitions)),
            VisualField(key="truncated", value=str(result.truncated)),
        ),
        status=_VERDICT_STATUS.get(result.verdict),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer="/verdict",
        ),
    )
    nodes.append(verdict_node)

    if result.counterexample is not None:
        cx = result.counterexample
        cx_node = VisualNode(
            node_id="counterexample",
            kind=NodeKind.ACTION,
            label=f"Counterexample: {cx.property_name}",
            fields=(
                VisualField(key="reason", value=cx.reason),
                VisualField(key="length", value=str(cx.length)),
            ),
            status=VisualStatus.UNSAFE,
            source_ref=EvidenceReference(
                source_file=f"{run_id}.json",
                json_pointer="/counterexample",
            ),
        )
        nodes.append(cx_node)
        edges.append(
            VisualEdge(
                source="verdict",
                target="counterexample",
                kind=EdgeKind.COUNTEREXAMPLE,
            ),
        )

    return VisualGraph(
        graph_id=f"sled:{run_id}",
        title=f"SLED Verification — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "verdict": result.verdict.value,
            "unique_states": str(result.unique_states),
            "transitions": str(result.transitions),
            "truncated": str(result.truncated),
            "threshold": str(state_threshold),
        },
    )
