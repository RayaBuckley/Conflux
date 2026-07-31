# Evaluation

Security verification and empirical utility are separate results. ITES reports
what was proposed, authorised, blocked, incomplete, executed, or failed.
Rejected adversarial proposals do not make an executed-safety property fail.

## Versioned evidence records

Schemas in `schemas/` define proposal batches, scenarios, trace events, run
results, experiment manifests, and native-verification results. Schema versions
are strings and are rejected when unknown.

Trace event version 2 records deterministic event and causal-parent IDs for run,
branch, proposal, each independent policy decision, action, provider, and bound
outcomes. An injected clock supplies presentation timestamps. Timestamps are
excluded from event fingerprints, so the same semantic run has the same IDs.
JSONL traces and result JSON are written with canonical ordering and SHA-256
linkage. Security assessments and utility outcomes remain distinct fields.
Action counters count lifecycle events, so an executed action remains visible
in both the authorised and executed totals.

SLED uses adversarial typed choices and reports finite bounds. Planning SLED
models any schema-valid continuation and any code effect permitted by its
capability envelope. It abstracts program semantics and records that assumption
instead of claiming arbitrary-code verification.

Planning comparison observations use four fixed modes—reactive, static,
dynamic, and dynamic with code—and retain blocked, failed, and bound-reached
runs. Aggregation requires identical task IDs and reports security separately
from utility, calls, tokens, latency, replans, plan growth, sensitive reads, and
maximum context size.

AgentDojo translation is pinned to package `0.1.35` and benchmark `v1.2.2`.
Exact upstream IDs, injections, messages, errors, utility, and security are
preserved. Conflux Principal Context and policy annotations are an explicit
benchmark augmentation. The raw fixture validates translation only; a real
comparative efficacy claim still requires a retained live result.
