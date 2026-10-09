"""Generate defence model verification evidence JSON.

Runs all defence model IRs through Z3 BMC and retains a deterministic
JSON evidence bundle at ``research/output/runs/defence-models-v1/``.

Z3 is an optional dependency: each property result records the verdict *and* the
solver error, and every summary counter covers only the models the solver
answered.  UNKNOWN results get their own counters and are never counted as safe,
so a missing solver reports ``pe_safe: 0`` with ``formal_backends`` unavailable
instead of converting UNKNOWN into a safety claim.  ``pe_unknown`` counts the
*measured* rows whose verdict is inconclusive, not the rows no backend answered;
those are the difference between ``total_models`` and ``pe_measured``.

nuXmv is an optional binary as well.  A host without it records the
``optional_binary_unavailable:nuXmv`` marker on every row and keeps the last
measured verdicts under ``nuxmv_evidence.recorded`` together with the revision
they came from, because that measurement cannot be reproduced without the
binary.  A host with the binary records the fresh measurement instead.  Retained
solver bundles are therefore regenerated in an environment that has the optional
backend, and the gate checks them in-process instead of running ``--check``; see
"Offline and optional evidence" in ``docs/DEVELOPMENT.md``.

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
from conflux.verification.nuxmv_backend import NuXmvBackend
from conflux.verification.reduction import reference_safety_check
from conflux.verification.z3_backend import verify_with_z3

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "output" / "runs" / "defence-models-v1"

_nuxmv = NuXmvBackend()

# The last nuXmv measurement in the corpus: taken on a nuXmv-capable host and
# retained in the bundle committed at bbd59a2 (verified against
# ``git show bbd59a2:research/output/runs/defence-models-v1/result.json``).  nuXmv is
# not installed in either standard environment, so the historical values are kept
# under an explicit provenance field instead of being dropped on regeneration.
NUXMV_HISTORICAL_ORIGIN = "nuXmv-capable host"
NUXMV_HISTORICAL_REVISION = "bbd59a2"
NUXMV_HISTORICAL_NOTE = "not reproducible without a nuXmv binary on this host"
NUXMV_HISTORICAL_VERDICTS: dict[str, dict[str, str | None]] = {
    "Dual-LLM": {"pe": "unsafe", "native": "safe"},
    "CaMeL": {"pe": "unsafe", "native": "safe"},
    "Progent": {"pe": "unsafe", "native": "safe"},
    "PACT": {"pe": "unsafe", "native": "safe"},
    "Requester-only": {"pe": "unsafe", "native": None},
    "ITES": {"pe": "safe", "native": None},
}


def _verify(ir_fn: Any) -> dict[str, Any]:
    ir = ir_fn()
    result = verify_with_z3(ir)
    ref = reference_safety_check(ir)
    nuxmv_result = _nuxmv.verify(ir)
    return {
        "verdict": result.verdict.value,
        "error": result.error,
        "counterexample": bool(result.counterexample),
        "counterexample_length": len(result.counterexample) if result.counterexample else 0,
        "reference_verdict": ref.verdict.value,
        "reference_states": ref.states,
        "nuxmv_verdict": nuxmv_result.verdict.value,
        "nuxmv_error": nuxmv_result.error,
    }


SAFE_VERDICTS = ("safe", "bounded_safe")
UNSAFE_VERDICTS = ("unsafe",)


def _measured(property_result: dict[str, Any] | None) -> bool:
    """True when the optional solver answered this property query."""
    return property_result is not None and property_result["error"] is None


def _count(rows: list[dict[str, Any]], verdicts: tuple[str, ...]) -> int:
    return sum(1 for row in rows if row["verdict"] in verdicts)


def _backend(available: bool) -> dict[str, Any]:
    return {"available": available, "reason": None if available else "unavailable"}


def _row_nuxmv_verdicts(model: dict[str, Any]) -> dict[str, str | None]:
    """Return the nuXmv verdicts recorded for one model, per property."""
    results = {"pe": model["pe_property"], "native": model["native_property"]}
    return {name: (result or {}).get("nuxmv_verdict") for name, result in results.items()}


def _retained_bundle(output: Path | None = None) -> dict[str, Any] | None:
    """Read the currently retained bundle, if any, for provenance carry-forward."""
    result_path = (output or OUTPUT) / "result.json"
    if not result_path.is_file():
        return None
    try:
        retained = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return retained if isinstance(retained, dict) else None


def _historical_nuxmv() -> dict[str, Any]:
    """Return the last nuXmv measurement of the corpus with its provenance."""
    return {
        "origin": NUXMV_HISTORICAL_ORIGIN,
        "source_revision": NUXMV_HISTORICAL_REVISION,
        "reproducible_here": False,
        "note": NUXMV_HISTORICAL_NOTE,
        "verdicts": {name: dict(verdicts) for name, verdicts in NUXMV_HISTORICAL_VERDICTS.items()},
    }


def _preserved_nuxmv(output: Path | None = None) -> dict[str, Any]:
    """Return the last measured nuXmv verdicts and their provenance.

    A later regeneration on a host without the binary carries the record forward
    instead of dropping the corpus's only nuXmv measurement.  A retained record
    wins, verdicts on the retained rows come next, and the historical measurement
    above is the last resort.
    """
    retained = _retained_bundle(output)
    if retained is not None:
        evidence = retained.get("nuxmv_evidence")
        recorded = evidence.get("recorded") if isinstance(evidence, dict) else None
        if isinstance(recorded, dict) and isinstance(recorded.get("verdicts"), dict):
            return recorded
        verdicts = {
            model["name"]: _row_nuxmv_verdicts(model)
            for model in retained.get("models", [])
            if isinstance(model, dict) and (model.get("pe_property") or {}).get("nuxmv_error") is None
        }
        if verdicts:
            preserved = _historical_nuxmv()
            preserved["verdicts"] = verdicts
            return preserved
    return _historical_nuxmv()


def _nuxmv_evidence(models: list[dict[str, Any]], available: bool, output: Path | None = None) -> dict[str, Any]:
    """Record the current nuXmv state and preserve the last measurement without it.

    Preserve when the binary is missing, overwrite with a fresh measurement when it
    is present.
    """
    reason = next((model["pe_property"]["nuxmv_error"] for model in models if model["pe_property"]["nuxmv_error"]), None)
    if not available:
        return {"available_here": False, "unavailable_reason": reason, "recorded": _preserved_nuxmv(output)}
    verdicts = {
        model["name"]: _row_nuxmv_verdicts(model) for model in models if model["pe_property"]["nuxmv_error"] is None
    }
    recorded = {
        "origin": "this host",
        "source_revision": None,
        "reproducible_here": True,
        "note": None,
        "verdicts": verdicts,
    }
    return {"available_here": True, "unavailable_reason": None, "recorded": recorded}


def generate() -> dict[str, Any]:
    """Generate the defence model verification evidence bundle.

    Counters cover only the models the optional solver measured; UNKNOWN results
    are counted in their own fields and never as safe.  The nuXmv measurement is
    preserved with its provenance when the binary is absent, so regenerating on a
    host without nuXmv does not drop the only measurement of it (see
    ``_nuxmv_evidence``).
    """
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
    pe_measured = [m["pe_property"] for m in models if _measured(m["pe_property"])]
    native_measured = [m["native_property"] for m in models if _measured(m["native_property"])]
    nuxmv_available = any(m["pe_property"]["nuxmv_error"] is None for m in models)
    pe_safe = _count(pe_measured, SAFE_VERDICTS)
    pe_unsafe = _count(pe_measured, UNSAFE_VERDICTS)
    native_satisfied = _count(native_measured, SAFE_VERDICTS)
    return {
        "schema_version": "1",
        "id": "defence-models-v1",
        "models": models,
        "formal_backends": {"z3": _backend(bool(pe_measured)), "nuxmv": _backend(nuxmv_available)},
        "available_formal_backends": [
            name for name, available in (("z3", bool(pe_measured)), ("nuxmv", nuxmv_available)) if available
        ],
        "nuxmv_evidence": _nuxmv_evidence(models, nuxmv_available),
        "summary": {
            "total_models": len(models),
            "pe_measured": len(pe_measured),
            "pe_safe": pe_safe,
            "pe_unsafe": pe_unsafe,
            "pe_unknown": len(pe_measured) - pe_safe - pe_unsafe,
            "native_measured": len(native_measured),
            "native_satisfied": native_satisfied,
            "native_unknown": len(native_measured) - native_satisfied - _count(native_measured, UNSAFE_VERDICTS),
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
