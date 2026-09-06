#!/bin/bash
# Setup Conflux environment on a RunPod GPU instance.
# Run this script ON the pod after SSH-ing in.
#
# Usage: bash setup_pod.sh [MODEL_ID] [GIT_REPO]
#
# Environment variables:
#   HF_TOKEN  - HuggingFace token for gated models (optional for public models)
set -euo pipefail

MODEL_ID="${1:-Qwen/Qwen2.5-7B-Instruct}"
GIT_REPO="${2:-https://github.com/RayaBuckley/Conflux.git}"
WORKDIR="/workspace/conflux"

echo "=== Conflux RunPod Setup ==="
echo "Model: $MODEL_ID"
echo "Repo:  $GIT_REPO"

# 1. Clone and install
echo "--- Cloning repository ---"
if [ ! -d "$WORKDIR" ]; then
    git clone "$GIT_REPO" "$WORKDIR"
fi
cd "$WORKDIR"

echo "--- Creating virtual environment ---"
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate
python --version
pip install --upgrade pip

echo "--- Installing Conflux with all extras ---"
pip install -e ".[dev,agentdojo,local-model,verification,openai-compatible]"
pip install bitsandbytes

echo "--- Configuring HuggingFace token ---"
if [ -n "${HF_TOKEN:-}" ]; then
    huggingface-cli login --token "$HF_TOKEN"
    echo "HF token configured."
else
    echo "Warning: HF_TOKEN not set. Gated models will fail to download."
fi

# 2. Download model weights
echo "--- Downloading model weights: $MODEL_ID ---"
huggingface-cli download "$MODEL_ID"

# 3. Resolve model config
echo "--- Resolving model configuration ---"
SNAPSHOT_PATH=$(python -c "
from huggingface_hub import scan_cache_dir
info = scan_cache_dir()
for repo in info.repos:
    if repo.repo_id == '$MODEL_ID' and repo.repo_type == 'model':
        rev = list(repo.revisions)[0]
        print(rev.snapshot_path)
        break
" 2>/dev/null)

if [ -z "$SNAPSHOT_PATH" ]; then
    echo "Error: Could not find snapshot path for $MODEL_ID"
    exit 1
fi

REVISION=$(python -c "
from huggingface_hub import scan_cache_dir
info = scan_cache_dir()
for repo in info.repos:
    if repo.repo_id == '$MODEL_ID' and repo.repo_type == 'model':
        print(list(repo.revisions)[0].commit_hash)
        break
")

RUNTIME_VERSION="torch-$(python -c 'import torch;print(torch.__version__)')_transformers-$(python -c 'import transformers;print(transformers.__version__)')_bitsandbytes-$(python -c 'import bitsandbytes;print(bitsandbytes.__version__)')"

OUTPUT_DIR="research/output/runs/runpod-$(echo $MODEL_ID | tr '/' '-')"
mkdir -p "$OUTPUT_DIR"

python -m conflux.cli model resolve transformers \
    --model-id "$MODEL_ID" \
    --revision "$REVISION" \
    --snapshot "$SNAPSHOT_PATH" \
    --runtime-version "$RUNTIME_VERSION" \
    --prompt-template agentdojo_turn_v1 \
    --device cuda \
    --dtype nf4 \
    --max-output-tokens 512 \
    --output "$OUTPUT_DIR"

echo "=== Setup complete ==="
echo "Model config: $OUTPUT_DIR/transformers.json"
echo ""
echo "Next steps:"
echo "  conflux benchmark agentdojo preflight --model-config $OUTPUT_DIR/transformers.json --output $OUTPUT_DIR --source-commit \$(git rev-parse HEAD)"
echo "  conflux benchmark agentdojo run --config $OUTPUT_DIR/protocol.json --output $OUTPUT_DIR --execute-local"
echo "  conflux plan pilot --model-config $OUTPUT_DIR/transformers.json --output $OUTPUT_DIR/planning --source-commit \$(git rev-parse HEAD) --execute-local"
