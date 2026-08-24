# Visualisation Design Note

## Status

Design note for [ADR-021](../decisions/021-human-reviewable-evidence-and-visualisation.md).
This is a reference document, not a normative specification.

## Rationale

Conflux has strong machine-oriented validation but limited human-reviewable
evidence. The visualisation layer projects existing structured evidence into
deterministic SVG and HTML diagrams without reconstructing security semantics.

## Architecture

```
domain / ITES / evaluation / verification / planning
                     |
                     v
               evidence schemas
                     |
                     v
               visualisation
```

The `src/conflux/visualisation/` package is not part of the security kernel.
Security-critical packages must never import it. The architecture audit
enforces this constraint.

## Intermediate graph model

A subsystem-independent `VisualGraph` sits between evidence adapters and
renderers. Adapters convert structured evidence (result JSON, trace events,
verification results) into `VisualNode` and `VisualEdge` objects. Each node
and edge carries an `EvidenceReference` pointing back to the authoritative
source.

## Stable identifiers

Existing stable identifiers available for visualisation:

| Source | Identifier | Type |
|--------|-----------|------|
| `RunResult` | `run_id` | SHA-256 hex |
| `RunResult` | `trace.path` + `trace.sha256` | File reference |
| `TraceEvent` | `event_id` | SHA-256 content hash |
| `TraceEvent` | `branch_id`, `sequence` | Composite key |
| `TraceEvent` | `causal_parent_ids` | DAG edges |
| `DecisionCertificate` | `id` | SHA-256 hex |
| `BranchState` | `state_key`, `branch_id`, `parent_branch_id`, `depth` | Tree structure |
| `FormalVerificationResult` | `ir_hash`, `query_hash`, `solver_hash` | Provenance |
| `PlanExecutionState` | `run_id`, `plan_id`, `plan_fingerprint` | Plan identity |
| `NodeState` | `node_id` | DAG node |
| `PlanTraceEvent` | `id`, `causal_parent_ids` | Event DAG |

## Known schema gaps

The following gaps exist between Python dataclasses and JSON schemas. The
visualiser reads result JSON (not Python objects), so these gaps affect what
diagrams can display:

1. `result.schema.json` fields (`security`, `source`, `bounds`, `diagnostics`)
   are `type: object` without nested structure. The visualiser must
   hardcode expected keys per result type.
2. `trace-event-v3.schema.json` `payload` is untyped. The visualiser must
   know expected keys per `event_type`.
3. `verification-result.schema.json` lacks `backend`, `ir_hash`,
   `query_hash`, `solver_hash`, and `assumptions` — these exist in the Python
   `FormalVerificationResult` but are lost in the JSON schema. The visualiser
   uses the Python `to_dict()` output (which includes these fields) rather
   than the schema-validated JSON.
4. `dynamic-plan-result.schema.json` `nodes`, `outputs`, `events` are
   untyped arrays. The visualiser must know the `NodeState.to_dict()` shape.
5. No `run_id` on `DecisionCertificate`, `PlannerRecord`, or
   `FormalVerificationResult`. These are linked to a run only through trace
   context.
6. Plan node dependency edges live in `Plan`, not in the serialised result.
   The visualiser cannot reconstruct the full plan DAG from result JSON alone.

These gaps do not block the first milestone (M1: ITES Review Pack) because
the ITES execution graph derives from trace events and `RunResult`, which have
sufficient structure.

## Determinism

- Nodes and edges are sorted by stable IDs.
- Principal ordering is canonical (alphabetical by Principal ID).
- Artifact ordering is canonical (alphabetical by artifact key).
- No timestamps inside SVG unless explicitly requested.
- No random IDs.
- Graphviz output is canonicalised before comparison if needed.

## Graphviz dependency

Graphviz is an optional dependency declared as `visualisation` in
`pyproject.toml`. The `dot` binary is detected at runtime via
`shutil.which("dot")`. If unavailable, the visualiser returns
`UNAVAILABLE` status. Core Conflux execution is unaffected.

## Security

- Default diagrams do not embed raw document contents, secrets, credentials,
  full prompts, or confidential payloads.
- All untrusted labels are HTML/SVG-escaped.
- The `--include-values` opt-in mode may create sensitive evidence and is
  documented as such.
