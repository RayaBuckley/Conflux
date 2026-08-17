import sys
import traceback
from pathlib import Path
from conflux.adapters.models import load_resolved_local_model, TransformersLocalModel
from conflux.adapters.benchmarks.agentdojo_local import PinnedAgentDojoCellExecutor, _failure_category
from conflux.experiments.agentdojo import AgentDojoCell

config = Path("runs/agentdojo-qwen-7b-nf4/model-config/transformers.json")
resolved = load_resolved_local_model(config)
model = TransformersLocalModel(resolved.spec, snapshot_path=resolved.snapshot_path, artifact_manifest=resolved.manifest)

cell = AgentDojoCell(attacked=False, defence="no_defence", repetition=0, seed=0)
print(f"Cell: {cell.id}", flush=True)

# Call _execute directly to see the real error
executor = PinnedAgentDojoCellExecutor(Path("runs/agentdojo-qwen-7b-nf4/raw-upstream"))
try:
    result = executor._execute(cell, model, 8)
    print(
        f"Result: status={result.status}, security={result.native_security}, utility={result.native_utility}, model_calls={result.model_calls}",
        flush=True,
    )
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
