import json
import os
import sys

p = "c:/repos/Conflux/runs/agentdojo-qwen-7b-nf4/model-config/transformers.json"
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Current device: {data['spec']['device']}")
print(f"Current dtype: {data['spec']['dtype']}")

data["spec"]["device"] = "cuda"
data["spec"]["dtype"] = "nf4"
data["spec"]["max_output_tokens"] = 512
data["spec"]["context_limit"] = 8192

with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.flush()
    os.fsync(f.fileno())

with open(p, "r", encoding="utf-8") as f:
    check = json.load(f)
print(f"Updated device: {check['spec']['device']}")
print(f"Updated dtype: {check['spec']['dtype']}")
