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

SLED uses adversarial typed choices and reports finite bounds. Experimental
external benchmark records retain separate `secure` and `useful` fields and
reject unknown schemas. Real AgentDojo, CaMeL, and model experiments require
pinned upstream revisions, raw fixtures, manifests, and repeatable aggregation
before supporting claims.
