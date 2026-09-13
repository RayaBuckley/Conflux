#!/bin/bash
set -e
source /workspace/venv/bin/activate
export HF_HOME=/workspace/hf_cache
cd /workspace/conflux

SNAPSHOT="/workspace/hf_cache/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28"
REVISION="a09a35458c702b33eeacc393d103063234e8bc28"
TORCH_VER=$(python -c 'import torch;print(torch.__version__)')
TRANS_VER=$(python -c 'import transformers;print(transformers.__version__)')
BNB_VER=$(python -c 'import bitsandbytes;print(bitsandbytes.__version__)')
RUNTIME_VERSION="torch-${TORCH_VER}_transformers-${TRANS_VER}_bitsandbytes-${BNB_VER}"
OUTPUT_DIR="research/output/runs/runpod-Qwen-Qwen2.5-7B-Instruct"
mkdir -p "$OUTPUT_DIR"

echo "Resolving model config..."
python -m conflux.cli model resolve transformers \
    --model-id "Qwen/Qwen2.5-7B-Instruct" \
    --revision "$REVISION" \
    --snapshot "$SNAPSHOT" \
    --runtime-version "$RUNTIME_VERSION" \
    --prompt-template agentdojo_turn_v1 \
    --device cuda \
    --dtype nf4 \
    --max-output-tokens 512 \
    --context-limit 4096 \
    --output "$OUTPUT_DIR"

echo "=== Running AgentDojo Preflight ==="
COMMIT=$(git rev-parse HEAD)
python -m conflux.cli benchmark agentdojo preflight \
    --model-config "$OUTPUT_DIR/transformers.json" \
    --output research/output/runs/runpod-eval \
    --source-commit "$COMMIT" \
    --task-ids user_task_14,user_task_16,user_task_17,user_task_22,user_task_39

echo "=== Running AgentDojo ==="
python -m conflux.cli benchmark agentdojo run \
    --config research/output/runs/runpod-eval/protocol.json \
    --model-config "$OUTPUT_DIR/transformers.json" \
    --output research/output/runs/runpod-eval \
    --execute-local

echo "=== DONE ==="
python -c "
import json
d = json.load(open('research/output/runs/runpod-eval/result.json'))
cells = d['cells']
util = sum(1 for c in cells if c.get('native_utility'))
sec = sum(1 for c in cells if c.get('native_security'))
complete = sum(1 for c in cells if c['status'] == 'complete')
print(f'Utility: {util}/{len(cells)} ({util/len(cells)*100:.0f}%)')
print(f'Security: {sec}/{len(cells)}')
print(f'Complete: {complete}/{len(cells)}')
print(f'Failures: {d[\"failure_counts\"]}')
for c in cells:
    if not c.get('native_utility'):
        print(f'  FAIL: {c[\"case_id\"]} status={c[\"status\"]}')
"
