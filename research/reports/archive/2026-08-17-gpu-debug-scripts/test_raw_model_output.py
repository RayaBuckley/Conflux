import sys
import json
from pathlib import Path
from conflux.adapters.models import load_resolved_local_model, TransformersLocalModel
from conflux.ports import LocalModelRequest
from conflux.adapters.benchmarks.agentdojo_local import _turn_schema
from conflux.domain import canonical_json

config = Path("runs/agentdojo-qwen-7b-nf4/model-config/transformers.json")
resolved = load_resolved_local_model(config)
model = TransformersLocalModel(resolved.spec, snapshot_path=resolved.snapshot_path, artifact_manifest=resolved.manifest)

schema = _turn_schema()
schema_hint = json.dumps(dict(schema), indent=None, separators=(",", ":"))

system_prompt = 'You MUST respond with exactly ONE JSON object. To call a tool: {"final":null,"tool_call":{"name":"<tool>","arguments":{<args>}}}. To give a final answer: {"final":"<your answer>","tool_call":null}. Never leave both fields null. Never emit more than one JSON object.'
user_prompt = canonical_json(
    {
        "query": "Please list the files in the workspace.",
        "messages": [],
        "tools": [{"name": "list_files", "description": "List files in workspace", "parameters": {"type": "object", "properties": {}}}],
    }
)
prompt = f"{system_prompt}\n{user_prompt}\nReturn JSON matching this schema: {schema_hint}"

print(f"Prompt length: {len(prompt)} chars", flush=True)
print(f"Generating...", flush=True)

# Call generator directly
from conflux.adapters.models.local_transformers import _strip_markdown_fences, _extract_first_json

if model.generator is None:
    model.generator = model._load_generator()
generated = model.generator(
    prompt,
    max_new_tokens=model.spec.max_output_tokens,
    temperature=model.spec.temperature,
    top_p=model.spec.top_p,
    seed=model.spec.seed,
)
content = generated.content if hasattr(generated, "content") else generated
print(f"Raw content type: {type(content)}", flush=True)
print(f"Raw content repr: {repr(content[:500])}", flush=True)
print(f"Stripped: {repr(_strip_markdown_fences(content)[:500])}", flush=True)
try:
    decoded = _extract_first_json(content)
    print(f"Decoded: {decoded}", flush=True)
except Exception as e:
    print(f"Parse error: {type(e).__name__}: {e}", flush=True)
