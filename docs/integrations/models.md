# Model Integrations

## OpenAI-compatible HTTP

Install `conflux[openai-compatible]`. `OpenAICompatibleModel` accepts an exact
endpoint, model name, allowed resource identities, timeout, and bounded retry
policy. The API key value is read only from the configured environment
variable at request time; constructors and manifests store the variable name,
never the secret.

The request asks for strict proposal-batch JSON Schema output. Responses with
unknown fields, action kinds, input IDs, or resource identities raise
`ModelOutputError` and become `model.parse_failed`/`run.failed` evidence in the
mediated trace. HTTP 429 and 5xx responses retry within the configured bound;
other HTTP failures and exhausted transports fail closed. Retained response
records redact authorization, key, token, and secret fields and replace the
current key value before hashing.

No live endpoint result is committed. Offline fake-transport tests establish
request shape, retry, parsing, resource allowlisting, redaction, and failure
classification; they do not validate a vendor service.

## Optional local causal model

Install `conflux[local-model]`. The one documented path is
[`HuggingFaceTB/SmolLM2-360M-Instruct`](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct)
at revision `c38281e01d0c0b0c36eac2f5bcb5b51fa2e803fc`. The adapter records model
ID, revision, device, dtype, and output bound. Transformers is imported only
when the adapter loads a real generator, keeping the core install light.

The model is treated as untrusted: generated text still passes the same strict
proposal parser and resource allowlist. A real local-model smoke is externally
gated by model-weight access and suitable compute and is not claimed here.

## Dual-backend laptop smoke

The checked-in plan is
`research/experiments/manifests/planning-laptop-smoke-v1.json`. It fixes two scenarios,
four modes, seed zero, one repetition, the SmolLM2 source revision, and
llama.cpp release `b9637` with Q8_0 conversion. Transformers and llama.cpp are
distinct model identities; their outputs must not be pooled as though the
runtimes and converted weights were identical.

Conflux never downloads or converts the model. After acquiring the pinned
weights, reviewing their licence, converting with the official
[`convert_hf_to_gguf.py`](https://github.com/ggml-org/llama.cpp/blob/master/convert_hf_to_gguf.py),
and obtaining the pinned
[`llama.cpp` release](https://github.com/ggml-org/llama.cpp/releases), resolve
local protocols with hashes of the actual artifacts:

```text
python scripts/prepare_laptop_smoke.py --plan research/experiments/manifests/planning-laptop-smoke-v1.json --transformers-weight-manifest LOCAL_MANIFEST --transformers-runtime-version VERSION --llama-binary LLAMA_SERVER --gguf MODEL.gguf --conversion-command "RECORDED COMMAND" --output research/experiments/local-runs/laptop-smoke --licence-reviewed
```

Preflight both adapters and inspect all 16 cells before invocation:

```text
conflux plan laptop-smoke --plan research/experiments/manifests/planning-laptop-smoke-v1.json --transformers-config research/experiments/local-runs/laptop-smoke/transformers.json --llama-config research/experiments/local-runs/laptop-smoke/llama_cpp_q8_0.json
```

Add `--execute-local --output research/output/runs/laptop-planning-smoke-v1` only as a
deliberate operator action. The endpoint must remain loopback. The resulting
bundle records raw failures rather than repairing malformed tiny-model output,
then requires human review before any larger suite or GPU run.

## Rationale

The HTTP adapter is vendor-neutral because the security boundary is structured
output, not a provider brand. Exact schemas and resource allowlists keep free-
form model text from selecting undeclared authority. Environment-only secrets,
redacted evidence, and bounded retries make confidentiality and availability
policy explicit.

The local adapter is optional and revision-pinned so core validation remains
small, offline, and deterministic. Both paths share the same untrusted-output
parser and ITES mediation.

The laptop smoke uses two runtimes because it tests integration sensitivity,
not because converted and original weights are assumed equivalent. Requiring
artifact hashes, the recorded conversion command, and an explicit licence flag
makes operator assumptions visible without turning CI into a model-acquisition
system.
