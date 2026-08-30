"""Generate defence model verification evidence JSON.

Runs all defence model IRs through Z3 BMC and retains a deterministic
JSON evidence bundle at ``research/output/runs/defence-models-v1/``.

Usage::

    python scripts/generate_defence_evidence.py
    python scripts/generate_defence_evidence.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from conflux.verification.defence_models import (
    camel_ir,
    camel_native_property_ir,
    dual_llm_baseline_ir,
    dual_llm_native_property_ir,
    ites_defective_requester_only_ir,
    ites_reference_ir,
    pact_ir,
    pact_native_property_ir,
    progent_ir,
    progent_native_property_ir,
)
from conflux.verification.reduction import reference_safety_check
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "defence-models-v1"


def _verify(ir_fn: Any) -> dict[str, Any]:
    ir = ir_fn()
    result = verify_with_z3(ir)
    ref = reference_safety_check(ir)
    return {
        "verdict": result.verdict.value,
        "counterexample": result.counterexample is not None,
        "counterexample_length": len(result.counterexample) if result.counterexample else 0,
        "reference_verdict": ref.verdict.value,
        "reference_states": ref.states,
    }


def generate() -> dict[str, Any]:
    """Generate the defence model verification evidence bundle."""
    models: list[dict[str, Any]] = [
        {
            "name": "Dual-LLM",
            "pe_property": _verify(dual_llm_baseline_ir),
            "native_property": _verify(dual_llm_native_property_ir),
        },
        {
            "name": "CaMeL",
            "pe_property": _verify(camel_ir),
            "native_property": _verify(camel_native_property_ir),
        },
        {
            "name": "Progent",
            "pe_property": _verify(progent_ir),
            "native_property": _verify(progent_native_property_ir),
        },
        {
            "name": "PACT",
            "pe_property": _verify(pact_ir),
            "native_property": _verify(pact_native_property_ir),
        },
        {
            "name": "Requester-only",
            "pe_property": _verify(ites_defective_requester_only_ir),
            "native_property": None,
        },
        {
            "name": "ITES",
            "pe_property": _verify(ites_reference_ir),
            "native_property": None,
        },
    ]
    return {
        "schema_version": "1",
        "id": "defence-models-v1",
        "models": models,
        "summary": {
            "total_models": len(models),
            "pe_unsafe": sum(1 for m in models if m["pe_property"]["verdict"] == "unsafe"),
            "pe_safe": sum(1 for m in models if m["pe_property"]["verdict"] != "unsafe"),
            "native_satisfied": sum(1 for m in models if m["native_property"] and m["native_property"]["verdict"] != "unsafe"),
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
    parser = argparse.ArgumentParser(description="Generate defence model verification evidence from Z3.")
    parser.add_argument("--check", action="store_true", help="Verify retained bundle matches regeneration.")
    arguments = parser.parse_args()

    if arguments.check:
        if _check(OUTPUT):
            print("Defence model evidence regeneration check passed")
            return 0
        print("Defence model evidence is stale or missing", file=sys.stderr)
        return 1

    bundle = generate()
    _write_bundle(OUTPUT, bundle)
    print(f"Generated defence model evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
