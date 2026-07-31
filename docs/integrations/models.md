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

## Rationale

The HTTP adapter is vendor-neutral because the security boundary is structured
output, not a provider brand. Exact schemas and resource allowlists keep free-
form model text from selecting undeclared authority. Environment-only secrets,
redacted evidence, and bounded retries make confidentiality and availability
policy explicit.

The local adapter is optional and revision-pinned so core validation remains
small, offline, and deterministic. Both paths share the same untrusted-output
parser and ITES mediation.
