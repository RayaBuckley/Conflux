# Evaluation

Security and utility are separate outcomes. ITES records what was proposed,
authorised, blocked, incomplete, executed, or provider-failed. A rejected
adversarial proposal is defence evidence, not an executed invariant failure.

## Versioned evidence

Schemas under `schemas/` define proposal batches, scenarios, trace events, run
results, experiment manifests, plans, and verification results. Unknown
versions and fields fail closed.

Trace event version 2 records deterministic event and causal-parent IDs for
runs, branches, proposals, independent policy decisions, actions, providers,
and bounds. An injected clock provides presentation timestamps, which are
excluded from semantic fingerprints. Canonically ordered JSONL traces and
result JSON are linked by SHA-256.

Native and planning SLED retain their finite bounds and abstractions. Planning
comparison uses the fixed reactive, static, dynamic, and dynamic-with-code
modes. Aggregation requires matching task IDs and keeps blocked, failed, and
bound-reached cases alongside completed cases. It reports security separately
from utility, calls, tokens, latency, replans, plan growth, sensitive reads,
and maximum context size.

AgentDojo translation is pinned to package `0.1.35` and benchmark `v1.2.2`.
Upstream IDs, messages, errors, utility, and security remain native evidence;
Conflux Principal Context and policy annotations are an explicit augmentation.
The raw fixture validates translation only. A live comparative efficacy claim
requires a separately retained result.

## Rationale

| Evidence decision | Why |
|---|---|
| Separate security and utility | A safe block can reduce completion, while a useful action can be unsafe |
| Retain blocked, failed, and incomplete runs | Exclusion would bias aggregates toward successful cases |
| Hash semantic records | Reproducibility should not depend on wall-clock presentation |
| Preserve native benchmark metrics | Conflux annotations must not overwrite upstream meaning |
| Execute negative controls | A harness that misses a known defect is not defence evidence |
| Gate live claims on retained results | Adapter code and fixtures do not establish empirical efficacy |

See the [claim ledger](CLAIMS.md), [negative controls](NEGATIVE_CONTROLS.md),
and [smoke evidence](MVP_RESULTS.md) for the strength of current claims.
