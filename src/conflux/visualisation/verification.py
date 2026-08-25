"""Verification IR and solver-result visualisation adapter.

Converts a ``VerificationIR`` and ``FormalVerificationResult`` into
``VisualGraph`` objects showing the IR dependency structure, COI
reductions, solver counterexamples, and verdict cards.
"""

from __future__ import annotations

from conflux.verification.ir import VerificationIR
from conflux.verification.reduction import VerificationReduction
from conflux.verification.results import FormalVerdict, FormalVerificationResult
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

_VERDICT_STATUS: dict[FormalVerdict, VisualStatus] = {
    FormalVerdict.SAFE: VisualStatus.SAFE,
    FormalVerdict.BOUNDED_SAFE: VisualStatus.SAFE,
    FormalVerdict.UNSAFE: VisualStatus.UNSAFE,
    FormalVerdict.UNKNOWN: VisualStatus.UNKNOWN,
}


def ir_to_graph(ir: VerificationIR, *, run_id: str = "verification") -> VisualGraph:
    """Convert a VerificationIR into a visual dependency graph.

    Nodes: StateVariable, TransitionRule, SafetyInvariant.
    Edges: DEPENDS_ON (rule->variable), REDUCED_TO (invariant->variable).
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    for var in sorted(ir.variables, key=lambda v: v.name):
        fields: list[VisualField] = [
            VisualField(key="sort", value=var.sort.value),
        ]
        if var.minimum is not None:
            fields.append(VisualField(key="min", value=str(var.minimum)))
        if var.maximum is not None:
            fields.append(VisualField(key="max", value=str(var.maximum)))
        nodes.append(
            VisualNode(
                node_id=f"var:{var.name}",
                kind=NodeKind.VARIABLE,
                label=var.name,
                fields=tuple(fields),
                status=VisualStatus.ACTIVE,
                source_ref=EvidenceReference(
                    source_file=f"{run_id}.json",
                    json_pointer=f"/variables/{var.name}",
                ),
            ),
        )

    for rule in sorted(ir.transitions, key=lambda r: r.id):
        r_fields: list[VisualField] = [
            VisualField(key="assignments", value=str(len(rule.assignments))),
        ]
        nodes.append(
            VisualNode(
                node_id=f"rule:{rule.id}",
                kind=NodeKind.RULE,
                label=f"Rule {rule.id}",
                fields=tuple(r_fields),
                status=VisualStatus.ACTIVE,
                source_ref=EvidenceReference(
                    source_file=f"{run_id}.json",
                    json_pointer=f"/transitions/{rule.id}",
                ),
            ),
        )
        for assignment in rule.assignments:
            edges.append(
                VisualEdge(
                    source=f"rule:{rule.id}",
                    target=f"var:{assignment.variable}",
                    kind=EdgeKind.DEPENDS_ON,
                ),
            )

    for inv in sorted(ir.invariants, key=lambda i: i.id):
        i_fields: list[VisualField] = []
        if inv.description:
            i_fields.append(VisualField(key="description", value=inv.description))
        nodes.append(
            VisualNode(
                node_id=f"inv:{inv.id}",
                kind=NodeKind.INVARIANT,
                label=f"Invariant {inv.id}",
                fields=tuple(i_fields),
                status=VisualStatus.SAFE,
                source_ref=EvidenceReference(
                    source_file=f"{run_id}.json",
                    json_pointer=f"/invariants/{inv.id}",
                ),
            ),
        )

    return VisualGraph(
        graph_id=f"ir:{ir.id}",
        title=f"Verification IR — {ir.id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "ir_id": ir.id,
            "variable_count": str(len(ir.variables)),
            "rule_count": str(len(ir.transitions)),
            "invariant_count": str(len(ir.invariants)),
            "bound": str(ir.bound),
        },
    )


def verdict_to_graph(
    result: FormalVerificationResult,
    *,
    run_id: str = "verification",
) -> VisualGraph:
    """Convert a formal verification result into a verdict card graph.

    Shows the verdict, backend, bound, assumptions, and optional
    counterexample.  ``SAFE on reduced model`` vs ``SAFE on original
    model`` are visually distinct unless preservation is established.
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    verdict_fields: list[VisualField] = [
        VisualField(key="backend", value=result.backend),
        VisualField(key="bound", value=str(result.bound)),
        VisualField(key="ir_hash", value=result.ir_hash[:16] + "..."),
        VisualField(key="query_hash", value=result.query_hash[:16] + "..."),
        VisualField(key="solver_hash", value=result.solver_hash[:16] + "..."),
    ]
    if result.model_hash is not None:
        verdict_fields.append(VisualField(key="model_hash", value=result.model_hash[:16] + "..."))
    for assumption in result.assumptions:
        verdict_fields.append(VisualField(key="assumption", value=assumption))
    if result.error is not None:
        verdict_fields.append(VisualField(key="error", value=result.error))

    verdict_node = VisualNode(
        node_id="verdict",
        kind=NodeKind.VERDICT,
        label=f"Verdict: {result.verdict.value}",
        fields=tuple(verdict_fields),
        status=_VERDICT_STATUS.get(result.verdict),
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer="/verdict",
        ),
    )
    nodes.append(verdict_node)

    if result.counterexample:
        cx_fields: list[VisualField] = []
        for i, state in enumerate(result.counterexample):
            cx_fields.append(VisualField(key=f"state_{i}", value=str(state)))
        cx_node = VisualNode(
            node_id="counterexample",
            kind=NodeKind.ACTION,
            label=f"Counterexample ({len(result.counterexample)} steps)",
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
        graph_id=f"verdict:{run_id}",
        title=f"Verification Verdict — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "verdict": result.verdict.value,
            "backend": result.backend,
            "bound": str(result.bound),
            "has_counterexample": str(bool(result.counterexample)),
        },
    )


def reduction_to_graph(
    reduction: VerificationReduction,
    *,
    run_id: str = "verification",
) -> VisualGraph:
    """Convert a COI reduction into a visual graph.

    Shows original vs retained variables and rules, reduction
    applicability, and witness-lifting evidence.
    """
    nodes: list[VisualNode] = []
    edges: list[VisualEdge] = []

    summary_fields: list[VisualField] = [
        VisualField(key="applicable", value=str(reduction.applicable)),
        VisualField(key="retained_variables", value=str(len(reduction.retained_variables))),
        VisualField(key="removed_variables", value=str(len(reduction.removed_variables))),
        VisualField(key="retained_rules", value=str(len(reduction.retained_rules))),
        VisualField(key="removed_rules", value=str(len(reduction.removed_rules))),
        VisualField(key="witness_strategy", value=reduction.witness_lifting.strategy),
        VisualField(key="witness_validated", value=str(reduction.witness_lifting.validated)),
        VisualField(key="rule_ids_preserved", value=str(reduction.witness_lifting.rule_ids_preserved)),
    ]
    if reduction.reason:
        summary_fields.append(VisualField(key="reason", value=reduction.reason))

    summary_node = VisualNode(
        node_id="reduction",
        kind=NodeKind.SUMMARY,
        label="COI Reduction",
        fields=tuple(summary_fields),
        status=VisualStatus.SAFE if reduction.applicable else VisualStatus.UNKNOWN,
        source_ref=EvidenceReference(
            source_file=f"{run_id}.json",
            json_pointer="/reduction",
        ),
    )
    nodes.append(summary_node)

    for var_name in sorted(reduction.retained_variables):
        nodes.append(
            VisualNode(
                node_id=f"retained:{var_name}",
                kind=NodeKind.VARIABLE,
                label=var_name,
                fields=(VisualField(key="status", value="retained"),),
                status=VisualStatus.ACTIVE,
            ),
        )
        edges.append(
            VisualEdge(
                source="reduction",
                target=f"retained:{var_name}",
                kind=EdgeKind.REDUCED_TO,
            ),
        )

    for var_name in sorted(reduction.removed_variables):
        nodes.append(
            VisualNode(
                node_id=f"removed:{var_name}",
                kind=NodeKind.VARIABLE,
                label=var_name,
                fields=(VisualField(key="status", value="removed"),),
                status=VisualStatus.PRUNED,
            ),
        )
        edges.append(
            VisualEdge(
                source="reduction",
                target=f"removed:{var_name}",
                kind=EdgeKind.REDUCED_TO,
            ),
        )

    return VisualGraph(
        graph_id=f"reduction:{run_id}",
        title=f"COI Reduction — {run_id}",
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={
            "run_id": run_id,
            "applicable": str(reduction.applicable),
            "retained_variables": str(len(reduction.retained_variables)),
            "removed_variables": str(len(reduction.removed_variables)),
            "witness_validated": str(reduction.witness_lifting.validated),
        },
    )
