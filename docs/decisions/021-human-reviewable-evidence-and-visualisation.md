# Specification 021: Human-Reviewable Evidence and Visualisation

Type: specification
Status: accepted for implementation
Evidence date: 2026-08-24

## Goal and success criteria

Make correctness claims inspectable by humans rather than dependent on
AI-generated prose. Add a deterministic visualisation layer that projects
existing machine-checkable evidence into SVG and HTML diagrams. Success
requires every visual element to map to a structured evidence object,
visualisation failure to never affect security decisions, and repeated
rendering of identical evidence to produce semantically identical output.

## Core design principle

Machine-checkable structured evidence is authoritative. Human-readable
diagrams and reports are deterministic projections of that evidence.
AI-generated explanations may explain evidence but must never replace it.

Consequences:

1. Visualisation code must not independently reconstruct security semantics.
2. A diagram must be reproducible from a stored structured result.
3. Every visual element should map to a structured evidence object.
4. Visualisation failure must never affect security decisions.
5. Visualisation must not silently omit security-relevant information.
6. `SAFE`, `UNSAFE`, `UNKNOWN`, `BLOCKED`, `ALLOWED`, and `UNAVAILABLE` must
   remain visibly distinct.
7. Bounded evidence must visibly state its bounds.
8. Generated evidence must identify the code/configuration that generated it.

## Package architecture

Add `src/conflux/visualisation/` with adapters for ITES, provenance, native
SLED, verification, and planning. A common graph model (`VisualGraph`,
`VisualNode`, `VisualEdge`, `EvidenceReference`) sits between evidence
adapters and renderers. A Graphviz SVG renderer and a static HTML report
generator produce the final output.

Dependency direction:

```
domain / ITES / evaluation / verification / planning
                     |
                     v
               evidence schemas
                     |
                     v
               visualisation
```

Security-critical code (domain, ITES, policy, execution) must never import
visualisation. The architecture audit must enforce this.

Graphviz is an optional dependency. Core execution must succeed without it.
Visualisation failure produces `UNAVAILABLE`, not a security failure. The
`dot` binary is detected at runtime via `shutil.which("dot")`.

## Scope

### ITES

Execution hierarchy, Principal Context, provenance, proposed actions, action
authorisation, argument authorisation, read decisions, visibility decisions,
consent decisions, delegation decisions, final allow/block decision, decision
certificates, and nested executions.

### Native SLED

Explored states, transitions, revisited/canonical states, terminal states,
violations, shortest counterexamples, bounds, and exploration statistics.

### SLED-V / verification

VerificationIR, state variables, transition dependencies, safety invariants,
cone-of-influence reductions, solver verdicts, counterexamples, assumptions,
bounds, and witness lifting.

### Planning

Plan graph, operation nodes, success/error transitions, observations,
Principal Context evolution, required permissions, required reads,
sensitive information exposure, delegation/approval transitions, irreversible
effects, and execution state.

## Stable visual statuses

`ALLOWED`, `BLOCKED`, `SAFE`, `UNSAFE`, `UNKNOWN`, `UNAVAILABLE`,
`INCOMPLETE`, `PRUNED`, `REVISITED`, `ACTIVE`, `SUCCESS`, `FAILED`,
`NOT_APPLICABLE`.

Status is never encoded exclusively through colour. Every status has text
and icon/shape distinction.

## CLI design

```
conflux visualise <result.json>
```

Options: `--format svg|html`, `--view execution|provenance|sled|verification|planning`,
`--all`, `--output PATH`, `--max-nodes N`.

Also integrated into `conflux report --visual`.

## Security requirements

Default diagrams must not embed raw document contents, secrets, credentials,
full prompts, or confidential payloads. Use artifact IDs, safe labels,
content hashes, classification, size, and provenance. Full values appear only
under explicit `--include-values` opt-in.

All untrusted labels are HTML/SVG-escaped. No untrusted HTML execution.

## Implementation phases

1. Phase 0: inspect existing schemas and identify stable identifiers.
2. Phase 1: common graph model (`visualisation/model.py`,
   `visualisation/graph/model.py`).
3. Phase 2: ITES and provenance adapters.
4. Phase 3: Graphviz SVG renderer.
5. Phase 4: native SLED visualisation.
6. Phase 5: verification (IR, COI, solver witness, verdict card).
7. Phase 6: planning (topology, authority overlay, observation timeline).
8. Phase 7: static HTML report combining all views.
9. Phase 8: semantic diff (baseline vs candidate).
10. Phase 9: AI workflow and CI integration.

## Milestones

### M1: ITES Review Pack

`conflux demo --scenario ... && conflux visualise result.json` produces
`evidence/index.html`, `evidence/execution.svg`, `evidence/provenance.svg`,
`evidence/manifest.json`.

### M2: Verification Review Pack

Adds SLED summary, counterexample, verification IR, COI, and solver witness
diagrams.

## Expected file set and change budget

- `src/conflux/visualisation/` (new package)
- `schemas/visual-graph.schema.json`, `schemas/visualisation-manifest.schema.json`
- `tests/test_visualisation*.py`
- `tests/fixtures/visualisation/`
- `pyproject.toml` (optional `visualisation` extra)
- `src/conflux/cli.py` (new `visualise` subcommand)
- `docs/reference/VISUALISATION.md` (design note)

No new top-level directory. No competing status, claim, or roadmap document.

## Tests and acceptance criteria

- Evidence to VisualGraph conversion is deterministic.
- Every edge endpoint exists in the node set.
- Every source reference resolves to authoritative evidence.
- Every action has a final status.
- No fabricated Principal or transition exists.
- Same evidence rendered twice produces semantically identical SVG.
- Hostile labels cannot inject HTML/SVG content.
- Graphviz absence produces `UNAVAILABLE`, not a crash.
- No security-critical package imports visualisation.
- Branch coverage threshold is maintained.

## Security impact

Visualisation is an information-release surface. It does not change
authorisation, visibility, consent, or delegation semantics. It does not
execute generated programs. It does not contact networks or external
services. The `--include-values` opt-in mode may create sensitive evidence
and must be documented.

## Assumptions

- Graphviz 16.0.0 is installed at `C:\Program Files\Graphviz\bin\dot.exe`.
- The Python `graphviz` 0.21 package is installed.
- CI runners may not have Graphviz; visualisation tests must degrade
  gracefully.
- Existing result schemas may need extension to expose stable identifiers
  required by diagrams; Phase 0 determines this.
