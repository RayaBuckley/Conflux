"""Generate aggregated paper tables and evidence index from all evidence bundles.

Reads committed evidence bundles from research/output/runs/ and
produces a deterministic JSON summary with per-experiment tables and
a claim-to-evidence index.

Usage::

    python scripts/generate_paper_tables.py
    python scripts/generate_paper_tables.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "paper-tables-v1"

EVIDENCE_DIRS = {
    "sledv_scaling": ROOT / "research" / "output" / "runs" / "sledv-scaling-v1",
    "mutation_benchmark": ROOT / "research" / "output" / "runs" / "mutation-benchmark-v1",
    "provenance_precision": ROOT / "research" / "output" / "runs" / "provenance-precision-v1",
}


def _load_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _table_sledv_scaling(bundle: dict[str, Any]) -> dict[str, Any]:
    """T1: SLED-V scaling summary by family."""
    by_fam = bundle.get("by_family", {})
    rows = []
    for fam_name, metrics in sorted(by_fam.items()):
        rows.append(
            {
                "family": fam_name,
                "fixtures": metrics["total_fixtures"],
                "max_original_states": metrics["max_original_states"],
                "max_reduced_states": metrics["max_reduced_states"],
                "max_original_variables": metrics["max_original_variables"],
                "max_reduced_variables": metrics["max_reduced_variables"],
                "state_reduction_ratio": round(metrics["state_reduction_ratio"], 2),
            },
        )
    return {
        "table_id": "T1",
        "title": "SLED-V scaling: state reduction by family",
        "columns": [
            "family",
            "fixtures",
            "max_original_states",
            "max_reduced_states",
            "max_original_variables",
            "max_reduced_variables",
            "state_reduction_ratio",
        ],
        "rows": rows,
        "summary": bundle.get("summary", {}),
    }


def _table_mutation_benchmark(bundle: dict[str, Any]) -> dict[str, Any]:
    """T2: Mutation benchmark summary by family."""
    families = bundle.get("summary", {}).get("families", {})
    rows = []
    for fam_name, metrics in sorted(families.items()):
        rows.append(
            {
                "family": fam_name,
                "mutants": metrics["count"],
                "killed": metrics["killed"],
                "kill_rate": round(metrics["killed"] / metrics["count"], 4) if metrics["count"] else 0.0,
                "backend": metrics["backend"],
            },
        )
    return {
        "table_id": "T2",
        "title": "Security mutation benchmark: kill rate by family",
        "columns": ["family", "mutants", "killed", "kill_rate", "backend"],
        "rows": rows,
        "summary": bundle.get("summary", {}),
    }


def _table_provenance_precision(bundle: dict[str, Any]) -> dict[str, Any]:
    """T3: Provenance precision vs utility summary."""
    summary = bundle.get("summary", {})
    by_n = bundle.get("by_n_possible_authors", {})
    rows = []
    for n, metrics in sorted(by_n.items()):
        rows.append(
            {
                "n_possible_authors": n,
                "c0_completion": round(metrics["c0_completion"], 4),
                "c1_completion": round(metrics["c1_completion"], 4),
                "c2_completion": round(metrics["c2_completion"], 4),
                "c1_mean_pc": round(metrics["c1_mean_pc"], 2),
                "c2_mean_pc": round(metrics["c2_mean_pc"], 2),
            },
        )
    return {
        "table_id": "T3",
        "title": "Provenance precision vs utility: completion by possible authors",
        "columns": ["n_possible_authors", "c0_completion", "c1_completion", "c2_completion", "c1_mean_pc", "c2_mean_pc"],
        "rows": rows,
        "summary": summary,
    }


def _evidence_index() -> list[dict[str, str]]:
    """Map every numerical claim to its evidence run path."""
    return [
        {
            "claim": "SLED-V reduces 1,462,607 traces to 31 canonical states",
            "evidence_path": "research/output/runs/sledv-scaling-v1/result.json",
            "field": "historical_anchor.total_traces / total_canonical_states",
        },
        {
            "claim": "COI reduction never causes safe-to-unsafe verdict downgrade",
            "evidence_path": "research/output/runs/sledv-scaling-v1/result.json",
            "field": "summary.no_coi_downgrade",
        },
        {
            "claim": "Z3 BMC agrees with reference on all tested fixtures",
            "evidence_path": "research/output/runs/sledv-scaling-v1/result.json",
            "field": "summary.ref_z3_agree",
        },
        {
            "claim": "26 mutants across 4 families, 100% kill rate",
            "evidence_path": "research/output/runs/mutation-benchmark-v1/result.json",
            "field": "summary.total_mutants / total_killed / kill_rate",
        },
        {
            "claim": "Authenticated provenance recovers utility without soundness violations",
            "evidence_path": "research/output/runs/provenance-precision-v1/result.json",
            "field": "summary.c2_sound_violations / utility_recovery",
        },
        {
            "claim": "Conservative provenance overapproximates PC size vs authenticated",
            "evidence_path": "research/output/runs/provenance-precision-v1/result.json",
            "field": "summary.c1_mean_pc / c2_mean_pc / pc_reduction",
        },
        {
            "claim": "22 planning diagnostic scenarios across 16 categories",
            "evidence_path": "research/experiments/suites/planning-diagnostic-v1.yaml",
            "field": "scenarios",
        },
    ]


def generate() -> dict[str, Any]:
    """Generate aggregated paper tables and evidence index."""
    tables: list[dict[str, Any]] = []
    evidence_sources: dict[str, str] = {}

    if EVIDENCE_DIRS["sledv_scaling"].exists():
        bundle = _load_json(EVIDENCE_DIRS["sledv_scaling"] / "result.json")
        tables.append(_table_sledv_scaling(bundle))
        evidence_sources["sledv_scaling"] = str(EVIDENCE_DIRS["sledv_scaling"].relative_to(ROOT))

    if EVIDENCE_DIRS["mutation_benchmark"].exists():
        bundle = _load_json(EVIDENCE_DIRS["mutation_benchmark"] / "result.json")
        tables.append(_table_mutation_benchmark(bundle))
        evidence_sources["mutation_benchmark"] = str(EVIDENCE_DIRS["mutation_benchmark"].relative_to(ROOT))

    if EVIDENCE_DIRS["provenance_precision"].exists():
        bundle = _load_json(EVIDENCE_DIRS["provenance_precision"] / "result.json")
        tables.append(_table_provenance_precision(bundle))
        evidence_sources["provenance_precision"] = str(EVIDENCE_DIRS["provenance_precision"].relative_to(ROOT))

    return {
        "schema_version": "1",
        "id": "paper-tables-v1",
        "tables": tables,
        "evidence_index": _evidence_index(),
        "evidence_sources": evidence_sources,
        "summary": {
            "table_count": len(tables),
            "experiments_covered": list(evidence_sources.keys()),
            "experiments_pending": ["agentdojo_live", "planning_live", "cedar_differential", "confidentiality"],
        },
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(output: Path, bundle: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    data = payload.encode("utf-8")
    (output / "result.json").write_bytes(data)
    (output / "CHECKSUMS.sha256").write_text(f"{_sha256(data)}  result.json\n", encoding="utf-8", newline="\n")


def _check(output: Path) -> bool:
    result_path = output / "result.json"
    if not result_path.is_file():
        return False
    retained = result_path.read_bytes()
    regenerated = json.dumps(generate(), indent=2, sort_keys=True).encode("utf-8") + b"\n"
    return retained == regenerated


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate aggregated paper tables and evidence index.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Paper tables evidence regeneration check passed")
            return 0
        print("Paper tables evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated paper tables evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
