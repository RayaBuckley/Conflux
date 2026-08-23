import sys
import traceback
from pathlib import Path
from conflux.adapters.models import load_resolved_local_model, TransformersLocalModel
from conflux.ports import LocalModelRequest

config = Path("runs/agentdojo-qwen-7b-nf4/model-config/transformers.json")
resolved = load_resolved_local_model(config)
print(f"Model: {resolved.spec.model_id}, device={resolved.spec.device}, dtype={resolved.spec.dtype}", flush=True)

model = TransformersLocalModel(
    resolved.spec,
    snapshot_path=resolved.snapshot_path,
    artifact_manifest=resolved.manifest,
)
print(f"Preflight: {model.preflight()}", flush=True)

request = LocalModelRequest(
    "test-1",
    "Return either one tool call or a final answer.",
    '{"query": "What day is it?", "tools": []}',
    "test",
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["final", "tool_call"],
        "properties": {
            "final": {"type": ["string", "null"]},
            "tool_call": {
                "oneOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "arguments"],
                        "properties": {
                            "name": {"type": "string"},
                            "arguments": {"type": "object"},
                        },
                    },
                ]
            },
        },
    },
)

print("Calling model.generate()...", flush=True)
try:
    result = model.generate(request)
    print(f"Generate OK: {result.payload}", flush=True)
except Exception as e:
    print(f"Generate FAILED: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
