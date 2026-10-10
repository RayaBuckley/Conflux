#!/bin/bash
# Expanded AgentDojo evidence at 14B on a RunPod H100 (Qwen2.5-14B-Instruct, NF4).
#
# Mirrors scripts/runpod/run_agentdojo_h100.sh (7B) with the differences the 2026-10-10
# run established:
#   1. the pinned snapshot is hard-linked under a plain model root first, because the
#      local-artifact guard refuses the shared hub/blobs cache layout;
#   2. the five-task pilot writes to its own bundle directory;
#   3. only the workspace suite is mediated beyond the two pilot tools, so the sweep is run per suite.
set -e
source /workspace/venv/bin/activate
cd /workspace/conflux

MODEL_ID="Qwen/Qwen2.5-14B-Instruct"
REVISION="cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
CACHE_SNAPSHOT="/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/${REVISION}"
MODEL_ROOT="/root/modelroot/Qwen--Qwen2.5-14B-Instruct"
SNAPSHOT="${MODEL_ROOT}/${REVISION}"
CONFIG_DIR="research/output/runs/runpod-Qwen-Qwen2.5-14B-Instruct"
PILOT_DIR="research/output/runs/runpod-h100-14b-v1"
SWEEP_ROOT="research/output/runs/runpod-h100-14b-stratified"
TASK_IDS="user_task_14,user_task_16,user_task_17,user_task_22,user_task_39"

echo "=== Hard-linking the cached snapshot into a plain model root ==="
python - "${CACHE_SNAPSHOT}" "${SNAPSHOT}" <<'PY'
import os
import pathlib
import sys

source, target = (pathlib.Path(argument) for argument in sys.argv[1:3])
for path in sorted(source.rglob("*")):
    if path.is_dir():
        continue
    destination = target / path.relative_to(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        os.link(path.resolve(), destination)
print("linked", sum(1 for item in target.rglob("*") if item.is_file()), "files")
PY

echo "=== Resolving model config ==="
mkdir -p "${CONFIG_DIR}" "${PILOT_DIR}"
python -m conflux.cli model resolve transformers \
    --model-id "${MODEL_ID}" \
    --revision "${REVISION}" \
    --snapshot "${SNAPSHOT}" \
    --runtime-version "torch-$(python -c 'import torch;print(torch.__version__)')_transformers-$(python -c 'import transformers;print(transformers.__version__)')_bitsandbytes-$(python -c 'import bitsandbytes;print(bitsandbytes.__version__)')" \
    --prompt-template agentdojo_turn_v1 \
    --device cuda \
    --dtype nf4 \
    --max-output-tokens 256 \
    --context-limit 4096 \
    --output "${CONFIG_DIR}"

echo "=== Five-task pilot ==="
COMMIT=$(git rev-parse HEAD)
python -m conflux.cli benchmark agentdojo preflight \
    --model-config "${CONFIG_DIR}/transformers.json" \
    --output "${PILOT_DIR}" \
    --source-commit "${COMMIT}" \
    --task-ids "${TASK_IDS}"
python -m conflux.cli benchmark agentdojo run \
    --config "${PILOT_DIR}/protocol.json" \
    --model-config "${CONFIG_DIR}/transformers.json" \
    --output "${PILOT_DIR}" \
    --execute-local

echo "=== Stratified banking sweep ==="
# The 2026-10-10 run started this sweep with --suite all; banking completed first and the sweep was
# then stopped, so banking is re-requested on its own here to reproduce that bundle.
python scripts/run_agentdojo_sweep.py \
    --suite banking \
    --model-config "${CONFIG_DIR}/transformers.json" \
    --output-root "${SWEEP_ROOT}" \
    --source-commit "${COMMIT}"

echo "=== Stratified workspace sweep ==="
# Only the workspace suite is mediated beyond the two pilot tools, so every other suite blocks on
# unsupported_tool; the workspace sweep therefore runs on its own.
python scripts/run_agentdojo_sweep.py \
    --suite workspace \
    --model-config "${CONFIG_DIR}/transformers.json" \
    --output-root "${SWEEP_ROOT}" \
    --source-commit "${COMMIT}"

echo "=== DONE ==="
