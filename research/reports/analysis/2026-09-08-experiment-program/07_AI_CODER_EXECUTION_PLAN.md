# AI coder execution plan

## Operating instruction

Treat this as a staged programme, not one large refactor. Before changing code, inspect the current tree because this plan was written against `main` as of 2026-09-08 and the repository may have advanced.

Do not implement a task if the current repository already contains equivalent functionality and evidence. Instead, document the existing implementation and move to the next unmet acceptance criterion.

## Phase 0 — Baseline and gap audit

### Tasks

1. Run `python scripts/validate.py`.
2. Run the deterministic evidence/smoke regeneration currently documented by the repo.
3. Inspect:
   - `src/conflux/evaluation`;
   - `src/conflux/verification`;
   - `src/conflux/planning`;
   - AgentDojo adapters/runners;
   - `research/experiments/manifests`;
   - `research/experiments/suites`;
   - `docs/evidence/task-registry.json`;
   - `docs/evidence/STATUS.md`.
4. Produce a short `gap-audit.md` in the experiment work branch mapping each proposed experiment to existing code/evidence.
5. Do not commit duplicate infrastructure.

### Stop conditions

Stop and report before semantic changes if:

- canonical ITES semantics disagree with `SECURITY_MODEL.md`;
- current tests fail before your work;
- a claimed backend is silently unavailable;
- the external benchmark lock/version differs from the documented boundary.

## Phase 1 — Verification experiments

### Commit plan

Suggested atomic commits:

1. `feat(verification): add <reduction/backend>`
2. `test(verification): add preservation and mutation controls`
3. `feat(experiments): add sled-v scaling manifests and generators`
4. `evidence(verification): retain sled-v scaling results`
5. `docs(evidence): record verified claim strength`

Every commit message should include the repository-required `Security impact:` line.

### Implementation rules

- Reuse the existing serialisable IR.
- Do not encode a second ITES semantics in the experiment runner.
- All reduction transforms must preserve stable rule/state IDs or maintain a reversible mapping.
- Unsafe reduced-model witnesses must lift to the original model and replay.
- Unsupported solver features must return `UNKNOWN` or explicit unavailable state.
- The unbounded backend must expose which algorithm/mode established the result.

## Phase 2 — Implementation conformance

### Commit plan

1. `feat(verification): add runtime-to-ir projection`
2. `test(verification): add kernel conformance corpus`
3. `test(verification): add generated conformance cases`
4. `evidence(verification): retain conformance summary and minimal mismatch fixtures`

### Rules

- Instrument the canonical ITES kernel; do not copy its logic.
- Projection functions must be pure and separately tested.
- If runtime carries richer state than the IR, document what is intentionally abstracted and prove/test that it is irrelevant to the checked property.
- A mismatch is a research result until explained; do not immediately change one side to make tests pass.

## Phase 3 — Comparative defence models

### Before coding

For CaMeL, Progent, PACT, and Dual-LLM, inspect primary papers and pinned source code where available. Create validation notes before modifying model rules.

### Rules

- Keep native property definitions separate from PE.
- Version every abstraction.
- Preserve counterexamples.
- Label results `finite abstraction`, never `implementation verified`, unless C2-style conformance exists.

## Phase 4 — AgentDojo real-model experiment

### Preflight

1. Verify pinned AgentDojo version and lock.
2. Run no-defence benign qualification.
3. Confirm model can complete multi-turn tool use and answer formatting.
4. Confirm model identity is correctly recognised by AgentDojo attack registry.
5. Confirm supported-tool filtering matches mediator annotations.

### Model selection

Prefer an existing supported local/self-hosted model that passes qualification. If using a larger remote GPU, retain model revision, quantisation, server/runtime version, and hardware details.

### Never do

- Do not modify the official benchmark success evaluator to improve utility.
- Do not count crashes as secure.
- Do not discard failed rows.
- Do not compare a qualified large model against an unqualified tiny-model baseline as if model capability were controlled.

## Phase 5 — Planning efficacy

### Preflight

- Inspect existing four-mode planning implementation.
- Run structured-output qualification.
- Confirm plans cannot assert provenance, Principal Context, or authority.
- Confirm runtime execution still passes through ITES action-time reauthorisation.

### Required negative controls

Add adversarial plans attempting:

- provenance removal;
- argument-role relabelling;
- stale certificate reuse;
- unsupported tool insertion;
- contamination laundering across subplans.

All must fail closed.

## Phase 6 — Semantic extensions

Persistent memory and richer argument effects are allowed only after the formal model and verification tests exist.

Delegation runtime activation is last. Keep it disabled until the entire activation checklist in `05_SEMANTIC_EXTENSION_EXPERIMENTS.md` passes.

## Validation before each evidence commit

Run at minimum:

- targeted unit tests;
- full pytest suite;
- strict mypy;
- Ruff;
- schema validation;
- repository audit;
- deterministic regeneration check for the experiment bundle;
- human-readable evidence generation.

Then run `python scripts/validate.py` before finalising the phase unless the environment explicitly prevents a component. Record unavailable checks.

## Final deliverables expected from the coder

For each completed experiment:

1. source/implementation changes;
2. tests;
3. tracked experiment definition/manifests;
4. reproducible runner command;
5. retained raw evidence;
6. aggregate JSON;
7. human-readable summary;
8. plots/tables generated from raw evidence;
9. claim-ledger/status/task-registry updates at the correct strength;
10. concise commit history with no mixed unrelated cleanup.

## Completion criterion for the whole programme

The programme is successful when the repository can support a concise supervisor/reviewer statement of the form:

- the canonical ITES finite model has an unbounded authority-confinement proof, or the precise unsupported boundary is established;
- reductions preserve verdicts and materially improve scaling;
- the runtime kernel conforms to the formal IR over a declared subset;
- comparative models show which properties do and do not imply one another without misrepresenting other systems;
- a capable real model has been evaluated on AgentDojo with failures cleanly separated;
- planning has a measured utility/authority-footprint effect while ITES security remains unchanged.
