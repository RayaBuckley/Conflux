"""Run the Cedar differential corpus against the live Cedar binary.

Unlike the offline preflight, this script invokes the pinned Cedar CLI
to obtain real ALLOW/DENY decisions and compares them against the Conflux
oracle.

Usage::

    python scripts/run_cedar_differential.py \\
        --binary C:/Users/rbuck/.cargo/bin/cedar.exe \\
        --output research/output/runs/cedar-differential-v1/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from conflux.adapters.policy.cedar import CedarCliRunner
from conflux.domain import (
    ActionArgument,
    EnvironmentSnapshot,
    Permission,
    PrimitiveAction,
    Principal,
    Provenance,
    ResourceRef,
    canonical_json,
    fingerprint,
)
from conflux.experiments.cedar_preflight import (
    CedarDifferentialCase,
    load_cedar_bundle,
    load_cedar_corpus,
)

ROOT = Path(__file__).resolve().parents[1]


def _run_case(
    case: CedarDifferentialCase,
    invoker: CedarCliRunner,
    bundle: Any,
) -> dict[str, Any]:
    """Run a single differential case through the live Cedar binary."""
    from conflux.adapters.policy.cedar import CedarAuthorisationPolicy

    principals = tuple(Principal(item, item.title()) for item in case.principal_ids)
    resource = ResourceRef("fixture", case.resource_id, "document")
    environment = EnvironmentSnapshot(
        id=f"cedar:{case.id}",
        resources=(resource,) if case.resource_present else (),
    )
    argument = ActionArgument.bind(
        name=case.argument_name,
        role=case.argument_role,
        value=case.argument_value,
        provenance=Provenance.from_principals(principals),
    )
    action = PrimitiveAction(
        id=case.id,
        operation="write",
        permission=Permission("write"),
        resource=resource,
        arguments=(argument,),
    )

    adapter = CedarAuthorisationPolicy(
        bundle,
        invoker,
        {"write": "1"},
        {"agent_id": "conflux"},
    )

    decisions = [adapter.decide(principal, action, environment) for principal in principals]

    oracle_allowed = (
        case.resource_present
        and not case.explicit_forbid
        and all(principal.id in case.allowed_principal_ids for principal in principals)
        and all(principal.id in case.argument_allowed_principal_ids for principal in principals)
    )

    cedar_decisions = [{"principal": p.id, "allowed": d.allowed, "reason": d.reason} for p, d in zip(principals, decisions, strict=True)]
    cedar_allows = all(d.allowed for d in decisions)
    agreement = cedar_allows == oracle_allowed

    return {
        "case_id": case.id,
        "oracle_allowed": oracle_allowed,
        "oracle_reason": case.expected_reason,
        "cedar_allows": cedar_allows,
        "agreement": agreement,
        "cedar_decisions": cedar_decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Cedar differential corpus against the live Cedar binary.")
    parser.add_argument("--binary", type=Path, required=True, help="Path to the cedar-policy-cli binary.")
    parser.add_argument(
        "--bundle",
        type=Path,
        default=ROOT / "research" / "experiments" / "manifests" / "cedar-policy-bundle-v1.json",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "research" / "experiments" / "suites" / "cedar-differential-v1.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    bundle = load_cedar_bundle(arguments.bundle)
    corpus = load_cedar_corpus(arguments.corpus)
    invoker = CedarCliRunner(binary_path=arguments.binary)

    cases = [_run_case(case, invoker, bundle) for case in corpus.cases]
    agreements = sum(1 for c in cases if c["agreement"])
    total = len(cases)
    complete = agreements == total

    payload = {
        "schema_version": "1",
        "classification": "parity_confirmed" if complete else "parity_mismatch",
        "complete": complete,
        "cedar_status": "invoked",
        "binary_path": str(arguments.binary),
        "bundle_fingerprint": bundle.fingerprint,
        "corpus_fingerprint": fingerprint(corpus.to_dict()),
        "agreements": agreements,
        "total_cases": total,
        "cases": cases,
        "exclusions": [] if complete else [f"{total - agreements} case(s) disagree"],
    }

    output = arguments.output
    output.mkdir(parents=True, exist_ok=True)
    (output / "result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(canonical_json({"complete": complete, "agreements": f"{agreements}/{total}", "output": str(output / "result.json")}))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
