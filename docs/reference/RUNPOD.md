# RunPod Remote Access Guide

## Usage guidelines

Per supervisor guidance:

- Keep usage reasonable and ensure instances are stopped when not in use.
- Day-to-day development: a single H100 or H200.
- Occasional short multi-GPU runs for larger experiments are acceptable.
- Let the supervisor know if you anticipate needing more than this; the main
  consideration is keeping accounts topped up, not a hard resource constraint.

## Bypassing the RunPod proxy via SSH key injection

You can bypass the RunPod proxy by embedding your public key directly into the
pod at creation time.

1. Display your public key string:

   ```
   type .ssh\your_key.pub
   ```

2. Copy the entire output (starting with `ssh-ed25519` and ending with the
   comment), e.g. `ssh-ed25519 AAAA... your_key`.

3. Re-create the pod with the `PUBLIC_KEY` environment variable. Replace
   `[PASTE_YOUR_PUBLIC_KEY_HERE]` with the string you just copied:

   ```bash
   runpodctl create pod \
     --name jimmy-working-pod \
     --templateId runpod-torch-v240 \
     --imageName runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04 \
     --gpuType "NVIDIA H100 80GB HBM3" \
     --gpuCount 1 \
     --volumeSize 20 \
     --containerDiskSize 50 \
     --communityCloud \
     --ports "22/tcp" \
     --env PUBLIC_KEY="[PASTE_YOUR_PUBLIC_KEY_HERE]"
   ```

4. Once the pod is running, grab the IP and port from the RunPod dashboard.
   Connect directly without passing through the proxy:

   ```bash
   ssh root@<tcp_ip> -p <tcp_public_port> -i .ssh/your_key
   ```

## Full experiment setup (transformers backend, Qwen2.5-7B-Instruct)

Once SSH'd into the pod, run the following to set up the Conflux environment,
download the model, resolve it, and run the AgentDojo six-cell comparison.

### 1. Clone and install

```bash
git clone <repo-url> conflux && cd conflux
pip install -e ".[dev,agentdojo,local-model,verification]"
pip install bitsandbytes
```

### 2. Download model weights

```bash
huggingface-cli download Qwen/Qwen2.5-7B-Instruct
```

### 3. Resolve model into a Conflux manifest

```bash
# Find the snapshot path and revision
SNAPSHOT_DIR=$(find /root/.cache/huggingface -type d -path "*Qwen2.5-7B-Instruct*/snapshots" | head -1)
REVISION=$(ls "$SNAPSHOT_DIR")

conflux model resolve transformers \
  --model-id Qwen/Qwen2.5-7B-Instruct \
  --revision "$REVISION" \
  --snapshot "$SNAPSHOT_DIR/$REVISION" \
  --runtime-version "torch-$(python -c 'import torch;print(torch.__version__)')_transformers-$(python -c 'import transformers;print(transformers.__version__)')_bitsandbytes-$(python -c 'import bitsandbytes;print(bitsandbytes.__version__)')" \
  --prompt-template agentdojo_turn_v1 \
  --output research/output/runs/agentdojo-7b-v1/
```

### 4. Edit transformers.json for GPU inference

The resolve command creates `device: "cpu"` and `dtype: "float32"` by default.
For H100 inference with NF4 quantisation:

```bash
python -c "
import json
p = 'research/output/runs/agentdojo-7b-v1/transformers.json'
d = json.load(open(p))
d['spec']['device'] = 'cuda'
d['spec']['dtype'] = 'nf4'
json.dump(d, open(p, 'w'), indent=2)
print('Updated device=cuda, dtype=nf4')
"
```

### 5. Create AgentDojo protocol and preflight

```bash
conflux benchmark agentdojo preflight \
  --model-config research/output/runs/agentdojo-7b-v1/transformers.json \
  --output research/output/runs/agentdojo-7b-v1/ \
  --source-commit "$(git rev-parse HEAD)"
```

### 6. Run the six-cell AgentDojo comparison

```bash
conflux benchmark agentdojo run \
  --config research/output/runs/agentdojo-7b-v1/protocol.json \
  --output research/output/runs/agentdojo-7b-v1/ \
  --execute-local
```

### 7. Run the planning pilot (optional, while pod is running)

```bash
conflux plan pilot \
  --model-config research/output/runs/agentdojo-7b-v1/transformers.json \
  --output research/output/runs/planning-pilot-7b-v1/ \
  --source-commit "$(git rev-parse HEAD)" \
  --execute-local
```

### 8. Retrieve evidence and stop the pod

```bash
# From your local machine, copy evidence off the pod
scp -P <tcp_public_port> -i .ssh/your_key \
  root@<tcp_ip>:/workspace/conflux/research/output/runs/agentdojo-7b-v1/result.json \
  research/output/runs/agentdojo-7b-v1/result.json
# Repeat for other files: protocol.json, transformers.json, preflight.json, RERUN.txt, etc.

# Or push from the pod if you have git credentials configured
cd /workspace/conflux
git add research/output/runs/agentdojo-7b-v1/ research/output/runs/planning-pilot-7b-v1/
git commit -m "feat(evidence): add AgentDojo 7B comparison evidence"
git push
```

Stop the pod from the RunPod dashboard when done.

## vLLM alternative (for larger models or faster inference)

For Qwen2.5-14B/32B or faster 7B inference, use vLLM with the
`openai_compatible` backend instead of the `transformers` backend.

### 1. Start vLLM server

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-14B-Instruct \
  --port 8000 \
  --gpu-memory-utilization 0.9
```

### 2. Create an openai_compatible protocol manually

The `conflux model resolve transformers` command only works with the
`transformers` backend. For `openai_compatible`, create a protocol.json by
hand or adapt the existing 1.5B protocol.json with these fields changed:

```json
{
  "model": {
    "backend": "openai_compatible",
    "model_id": "Qwen/Qwen2.5-14B-Instruct",
    "endpoint": "http://localhost:8000/v1",
    "allow_private_remote": false,
    "revision": "<model-revision>",
    "weight_manifest_sha256": "<64-char-sha256-of-weight-manifest>",
    "tokenizer_id": "Qwen/Qwen2.5-14B-Instruct",
    "tokenizer_revision": "<model-revision>",
    "prompt_template_version": "agentdojo_turn_v1",
    "seed": 0,
    "temperature": 0.0,
    "top_p": 1.0,
    "max_output_tokens": 256,
    "context_limit": 32768,
    "device": "cuda",
    "dtype": "float16",
    "runtime_version": "vllm-<version>"
  }
}
```

The `SelfHostedOpenAIModel` adapter treats `localhost` as "loopback" scope,
so `allow_private_remote` is not needed.

### 3. Run the comparison

```bash
conflux benchmark agentdojo run \
  --config research/output/runs/agentdojo-14b-v1/protocol.json \
  --output research/output/runs/agentdojo-14b-v1/ \
  --execute-local
```
