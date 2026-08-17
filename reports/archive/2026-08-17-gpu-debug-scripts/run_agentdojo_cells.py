import sys
import json
import time
from pathlib import Path
from conflux.adapters.models import load_resolved_local_model, TransformersLocalModel
from conflux.adapters.benchmarks.agentdojo_local import PinnedAgentDojoCellExecutor
from conflux.experiments.agentdojo import AgentDojoCell, agentdojo_matrix
from conflux.experiments.protocol import ExperimentProtocol, load_protocol

protocol = load_protocol(Path("runs/agentdojo-qwen-7b-nf4/protocol.json"))
config = Path("runs/agentdojo-qwen-7b-nf4/model-config/transformers.json")
resolved = load_resolved_local_model(config)
model = TransformersLocalModel(resolved.spec, snapshot_path=resolved.snapshot_path, artifact_manifest=resolved.manifest)

preflight = model.preflight()
print(f"Preflight: {preflight}", flush=True)
if not preflight.available or preflight.model_id != protocol.model.model_id:
    print(f"Preflight failed: {preflight.reason}", flush=True)
    sys.exit(1)

cells = agentdojo_matrix(protocol)
print(f"Cells: {len(cells)}", flush=True)

executor = PinnedAgentDojoCellExecutor(Path("runs/agentdojo-qwen-7b-nf4/raw-upstream"))
max_calls = protocol.bounds.get("max_model_calls", 8)

results = []
for i, cell in enumerate(cells):
    t0 = time.time()
    print(f"Cell {i + 1}/{len(cells)}: {cell.id} ...", flush=True)
    result = executor.execute(cell, model, max_calls)
    elapsed = time.time() - t0
    print(
        f"  -> status={result.status} security={result.native_security} utility={result.native_utility} calls={result.model_calls} failures={result.failures} ({elapsed:.0f}s)",
        flush=True,
    )
    results.append(result)

complete = all(r.status == "complete" for r in results)
print(f"\nAll complete: {complete}", flush=True)

from conflux.adapters.benchmarks.agentdojo_local import FAILURE_CATEGORIES
from jsonschema import Draft202012Validator
from conflux.experiments.schemas import load_schema

counts = {category: 0 for category in FAILURE_CATEGORIES}
for result in results:
    for failure in result.failures:
        counts[failure] += 1

payload = {
    "schema_version": "2",
    "protocol_fingerprint": protocol.fingerprint,
    "complete": complete,
    "model_id": protocol.model.model_id,
    "cells": [r.to_dict() for r in results],
    "failure_counts": counts,
}

Draft202012Validator(load_schema("agentdojo-comparison-result-v2.schema.json")).validate(payload)

output_path = Path("runs/agentdojo-qwen-7b-nf4/result.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, default=str)
print(f"Results written to {output_path}", flush=True)
