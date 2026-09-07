#!/bin/bash
# Run Conflux evaluations on a RunPod GPU instance.
# Run this script ON the pod after setup_pod.sh has completed.
#
# Usage: bash run_evaluations.sh [OUTPUT_DIR] [MODEL_CONFIG]
set -euo pipefail

OUTPUT_DIR="${1:-research/output/runs/runpod-eval}"
MODEL_CONFIG="${2:-research/output/runs/runpod-Qwen-Qwen2.5-7B-Instruct/transformers.json}"

# Activate venv if available
if [ -f /workspace/venv/bin/activate ]; then
    source /workspace/venv/bin/activate
fi

cd /workspace/conflux
COMMIT="$(git rev-parse HEAD)"

echo "=== Running AgentDojo Preflight ==="
python -m conflux.cli benchmark agentdojo preflight \
    --model-config "$MODEL_CONFIG" \
    --output "$OUTPUT_DIR" \
    --source-commit "$COMMIT"

echo "=== Running AgentDojo Comparison ==="
python -m conflux.cli benchmark agentdojo run \
    --config "$OUTPUT_DIR/protocol.json" \
    --model-config "$MODEL_CONFIG" \
    --output "$OUTPUT_DIR" \
    --execute-local

echo "=== Running Planning Pilot ==="
python -m conflux.cli plan pilot \
    --model-config "$MODEL_CONFIG" \
    --output "${OUTPUT_DIR}/planning" \
    --source-commit "$COMMIT" \
    --execute-local

echo "=== Evaluations complete ==="
echo "Results: $OUTPUT_DIR/"
echo ""
echo "AgentDojo result:"
python -c "import json; d=json.load(open('$OUTPUT_DIR/result.json')); print(f'  Complete: {d[\"complete\"]}'); [print(f'  {c[\"case_id\"]}: utility={c[\"native_utility\"]} security={c[\"native_security\"]}') for c in d['cells']]" 2>/dev/null || echo "  (see result.json)"
echo ""
echo "Planning result:"
python -c "import json; d=json.load(open('${OUTPUT_DIR}/planning/result.json')); print(f'  Complete: {d[\"complete\"]}'); [print(f'  {o[\"case_id\"]}: {o[\"status\"]} util={o[\"utility_completed\"]}') for o in d['observations']]" 2>/dev/null || echo "  (see result.json)"
