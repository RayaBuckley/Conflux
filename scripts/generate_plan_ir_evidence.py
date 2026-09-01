"""Generate plan IR verification evidence.

Produces JSON evidence for the extended plan IR invariants, recording
which invariants exist and verifying that plan abstraction produces
serializable IRs.

Usage:
    python scripts/generate_plan_ir_evidence.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from conflux.domain import WRITE, Principal, Provenance
from conflux.planning import (
    ActionTemplate,
    ActionTemplateNode,
    ArgumentSpec,
    ArgumentType,
    DelegationNode,
    LiteralBinding,
    OperationCatalogue,
    OperationSchema,
    Plan,
    TemplateArgument,
)
from conflux.verification import EffectSummary, abstract_plan
from conflux.verification.reduction import reference_safety_check

OUTPUT_DIR = Path("research/output/runs/plan_ir")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    principal = Principal("alice", "Alice")
    source = Provenance.from_principal(principal, source="evidence")
    operation = OperationSchema(
        "filesystem.write",
        "1",
        "filesystem",
        "file",
        "write",
        WRITE,
        (ArgumentSpec("path", ArgumentType.STRING), ArgumentSpec("content", ArgumentType.STRING)),
        "path",
    )
    action = ActionTemplateNode(
        "write",
        ActionTemplate(
            "write",
            operation.id,
            operation.version,
            (TemplateArgument("path", LiteralBinding("safe.txt", source)), TemplateArgument("content", LiteralBinding("safe", source))),
        ),
        source,
    )
    delegation = DelegationNode("delegate", "scope-text", source, ())
    plan = Plan("evidence-plan", "repair", (action, delegation), source)
    catalogue = OperationCatalogue((operation,))

    abstraction = abstract_plan(
        plan,
        catalogue=catalogue,
        effect_summaries=(EffectSummary("write", True, True),),
        bound=4,
    )

    if abstraction.ir is None:
        print("ERROR: plan abstraction returned unsupported", file=sys.stderr)
        return 1

    ir = abstraction.ir
    ref_result = reference_safety_check(ir)

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "module": "conflux.verification.plan_ir",
        "plan_id": plan.id,
        "ir_id": ir.id,
        "ir_fingerprint": ir.fingerprint,
        "bound": ir.bound,
        "variables": [v.name for v in ir.variables],
        "invariants": [{"id": inv.id, "description": inv.description} for inv in ir.invariants],
        "transitions": [rule.id for rule in ir.transitions],
        "assumptions": list(ir.assumptions),
        "reference_verdict": ref_result.verdict.value,
        "reference_states": ref_result.states,
        "reference_transitions": ref_result.transitions,
    }
    output_path = OUTPUT_DIR / "evidence.json"
    output_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    var_count = len(ir.variables)
    inv_count = len(ir.invariants)
    print(f"Generated plan IR evidence: {output_path}")
    print(f"  Variables: {var_count}")
    print(f"  Invariants: {inv_count}")
    print(f"  Verdict: {ref_result.verdict.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
