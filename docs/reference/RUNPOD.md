# RunPod Remote Access Guide

## Usage guidelines

Per supervisor guidance:

- Keep usage reasonable and ensure instances are stopped when not in use.
- Day-to-day development: a single H100 or H200.
- Occasional short multi-GPU runs for larger experiments are acceptable.
- Let the supervisor know if you anticipate needing more than this; the main
  consideration is keeping accounts topped up, not a hard resource constraint.

## Cost guard and shared-account safety

`scripts/runpod/guard.py` is the supported way to create or stop a pod from this
repository, and the only path that enforces the identity rule and the cost caps in
code. A single H100 and one pod at a time are enforced there.

```bash
python scripts/runpod/guard.py status          # Conflux pods, burn rate, budget
python scripts/runpod/guard.py preflight --hours 2
python scripts/runpod/guard.py create --run-id pilot-1 --hours 2 --yes
python scripts/runpod/guard.py stop --run-id pilot-1 --yes
python scripts/runpod/guard.py stop-all --yes  # panic switch
python scripts/runpod/guard.py watch           # stop pods whose TTL has passed
python scripts/runpod/guard.py report --days 7
```

The account is shared with other students, so the guard's first job is identity.
A pod is Conflux's only if its name matches `^conflux-...` **and** either it carries
the `CONFLUX_MANAGED=1` environment marker or its id appears in a **live, recent**
ledger entry (state `created` or `running`, recorded within `TRUST_WINDOW_DAYS`).
A finished or older entry does not authorise anything, because pod ids can be
recycled on a shared account. Anything else is treated as someone else's pod.

Foreign pods are never named, listed, stopped, started or terminated. The guard does
not repeat a foreign pod's id, name or environment value anywhere - not on stdout,
not on stderr and not in the audit log, including in a refusal, which reports only a
count. Foreign pods appear solely as an aggregate count and hourly cost. Destructive
subcommands resolve their targets through the identity check and refuse the whole
command if any target is foreign.

Caps live in `.local/runpod/budget.json` (created on first use, gitignored).
Configuration may lower them but never raise them past the absolute limits in the
module: one GPU, H100 family only, one Conflux pod at a time, 12 hours per pod,
USD 50 per pod, USD 100 per day. A non-finite value (`NaN`, infinity) is rejected
rather than clamped, because a NaN would otherwise pass every comparison.

`create`, `stop`, `terminate` and `stop-all` require `--yes` and are appended to
`.local/runpod/audit.jsonl` **before** the API call, so a failed call still leaves
the record. Three stops run without `--yes` on purpose, because each can only stop
our own pods and only reduces spend: `watch` (the expiry watchdog), the compensating
stop of a pod that fails the identity recheck right after creation, and the
compensating stop of a pod whose real rate exceeds the per-pod cap. None of the three
ever creates, terminates or deletes anything.

After creation the guard re-reads the pod, checks its identity again, and records the
hourly rate **the vendor reports**. If the vendor does not report a price, the
observed rate is stored as 0.0 - an assumed rate is never written as an observed one,
so it cannot seed later estimates - and the projected cost uses the rate you passed.
When a real rate is reported above the per-pod cap, the pod is stopped immediately.

`stop_pod.py` and `run_all.py` no longer act on a pod themselves. Both route every
stop through `guard.py`, so they refuse a pod that is not Conflux's, and `run_all.py`
re-reads the account and re-checks identity before it opens the first ssh connection:
a wrong id, a stale id or a recycled id must never become a shell or a kill on
somebody else's pod. `tests/test_runpod_guard.py` fails if any other file under
`scripts/` gains a way to stop or delete a pod.

`create_pod.py` and the SSH-key recipe below still create pods outside the guard, so
they enforce neither the caps nor a ledger record. `create_pod.py` does set the marker
and a conforming name, so the pods it creates stay manageable, but the recipe does not:
without the marker and a `conflux-` name the guard treats the pod it creates as another
user's pod.

### Hard rules on a shared account

- Never run an account-wide command: no stop-all or remove-all through `runpodctl`, no
  listing piped into a stop, and no loop over pods this machine did not create.
- Never stop, terminate, restart or reconfigure a pod that is not Conflux's, even if it
  looks abandoned and even if it appears to waste money. Report it to the account owner
  instead.
- Never pass an id you typed by hand. Pass a run id or pod id that the guard can verify
  against the ledger or against the `CONFLUX_MANAGED` marker.
- Treat a refusal as final. The guard fails closed by design, and a refusal says nothing
  about the pod it protected - that is the point, not a missing message.
- Read before you touch: `guard.py status` for Conflux pods, `guard.py report --days 7`
  for spend, and `guard.py watch` to let expired pods stop themselves.

## Bypassing the RunPod proxy via SSH key injection

You can bypass the RunPod proxy by embedding your public key directly into the
pod at creation time.

1. Display your public key string:

   ```powershell
   type .ssh\your_key.pub
   ```

2. Copy the entire output (starting with `ssh-ed25519` and ending with the
   comment), e.g. `ssh-ed25519 AAAA... your_key`.

3. Re-create the pod with the `PUBLIC_KEY` environment variable. Replace
   `[PASTE_YOUR_PUBLIC_KEY_HERE]` with the string you just copied:

   This recipe bypasses the guard: it enforces no cap, and without the
   `CONFLUX_MANAGED=1` marker and a `^conflux-...` name the guard will treat the pod
   it creates as another user's and refuse to manage it.

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
