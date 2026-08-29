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
     --gpuType "NVIDIA A100 80GB PCIe" \
     --gpuCount 1 \
     --volumeSize 10 \
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
