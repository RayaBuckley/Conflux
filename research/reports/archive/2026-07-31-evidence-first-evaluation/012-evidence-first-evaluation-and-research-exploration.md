# Feature Specification 012: Evidence-first evaluation and research exploration

Status: proposed for acceptance on `main`

## Purpose

Conflux is ready to begin producing research results, but it should not prematurely narrow its fourth-year scope. Before the academic year starts, the repository should continue exploring multiple promising directions while requiring each direction to produce bounded, reviewable evidence.

The immediate programme has three result-producing tracks:

1. reproduce native SLED results using the current repository;
2. complete a small live AgentDojo comparison;
3. run utility ablations across the implemented planning modes.

Documentation remains part of the correctness boundary. In an AI-assisted repository, documentation is the main human review surface and the persistent source of intent for later Codex work. Code, tests, retained evidence, specifications, status, and claims must remain mutually consistent.

This specification defines the programme and acceptance rules. It does not replace `docs/task-registry.json`, `docs/STATUS.md`, `docs/EVALUATION.md`, or `docs/CLAIMS.md`.

## Repository authority and required reading

Before changing code, Codex must read, in order:

1. `AGENTS.md`;
2. `docs/AI_AGENT_GUIDE.md`;
3. this specification;
4. `docs/EVALUATION.md`;
5. `docs/task-registry.json`;
6. `docs/CLAIMS.md`;
7. the affected implementation, schemas, tests, experiment manifests, and retained evidence.

If these sources disagree, stop and report the discrepancy. Do not select the source that makes implementation easier.

## Programme decisions

### Breadth remains intentional

The project is not being narrowed to one final contribution before the fourth year begins. Planning, SLED model checking, solver-backed verification, external benchmarks, delegation, persistent memory, policy integration, and implementation conformance remain legitimate research directions.

Exploration is acceptable when it has all of the following:

- a stated research question or engineering hypothesis;
- a bounded implementation or analysis deliverable;
- an explicit evaluation method;
- a retained evidence requirement;
- a decision point for continuing, revising, or suspending the direction.

Exploratory modules without an evaluation path are incomplete rather than automatically valuable.

### Results are the immediate priority

The current repository already contains the main offline runtime, native SLED, planning, verification, model-adapter, AgentDojo-translation, schema, manifest, and reporting surfaces. The next changes should exercise these surfaces and reveal defects rather than introduce another broad abstraction layer.

This does not prohibit new research branches. It requires result-producing work to take precedence when the necessary implementation already exists.

### Documentation is a deliverable

A change is not complete when code and tests pass but canonical documentation is inaccurate. Documentation work is required when a change affects:

- intended semantics;
- package or data-flow ownership;
- security assumptions;
- experiment design;
- programme status;
- claim strength;
- manuscript wording.

Do not create parallel status pages, roadmaps, task lists, glossaries, or claim ledgers. Update the canonical owner and link to it.

## Track A: native SLED reproduction

### Objective

Reconstruct and rerun the previous SLED environments using the current repository, while separating historical semantics from corrected canonical semantics.

This track should answer:

- Can the archived experiments be reproduced from versioned fixtures?
- Which numerical differences result from implementation changes, corrected semantics, altered enumeration, or previous defects?
- Does the current evaluator detect intentionally vulnerable controls?
- What are the runtime and state-space costs of the current implementation?

### Required suites

Maintain two distinct suites:

- `experiments/suites/legacy-reproduction/`: preserve the previous prototype's assumptions as closely as the archived source permits;
- `experiments/suites/canonical/`: use the current Principal Context, reader, policy, trace, and result semantics.

Never merge their results into one headline number. A comparison must include a semantic-difference table.

### Required execution stages

1. Verify that every historical environment has a versioned declarative fixture.
2. Record all assumptions that cannot be recovered exactly from the archived implementation or report.
3. Run a small deterministic smoke case through both suites.
4. Run all negative controls required by the current evaluation contract.
5. Run the full feasible reproduction with explicit bounds and machine metadata.
6. Compare historical, legacy-reproduction, and canonical outputs field by field.
7. Classify every discrepancy before changing implementation.

### Required metrics

At minimum retain:

- executed unauthorised effects;
- unauthorised reads;
- visible confidentiality violations supported by the model;
- legitimate task completion or reachability;
- false blocking;
- blocked adversarial proposals;
- provider and parser failures;
- incomplete or bound-reached states;
- model calls, explored transitions, unique states, memory, and runtime;
- counterexample length for vulnerable controls.

Invalid proposals are diagnostics, not executed security violations.

### Acceptance evidence

A completed result package contains:

- immutable experiment manifest;
- exact source commit;
- suite and schema versions;
- raw canonical JSONL traces;
- result JSON;
- generated human-readable summary;
- checksums;
- machine metadata;
- one rerun command;
- discrepancy analysis;
- negative-control witnesses.

A failure to reproduce the archived number is an acceptable research result when the reason is documented and evidenced.

## Track B: AgentDojo live comparison

### Objective

Run a deliberately small, pinned AgentDojo subset through both no-defence and ITES configurations. The first purpose is integration validation, not a headline benchmark sweep.

This track should answer:

- Can the pinned upstream package execute under the documented environment?
- Does the translation preserve upstream task IDs, messages, errors, security, and utility outputs?
- Which Principal, provenance, read, and permission annotations must Conflux add?
- Does ITES change security and utility on the selected cases?
- Which failures belong to infrastructure, model parsing, policy blocking, utility, or benchmark security?

### Initial experiment

Use:

- the currently pinned AgentDojo package and benchmark versions;
- one supported real-model endpoint;
- a small fixed subset containing benign and attacked cases;
- no defence;
- ITES;
- repeated runs where model stochasticity affects outcomes.

Do not add a second external benchmark before this smoke comparison produces a retained result or a documented incompatibility finding.

### Required outputs

Retain both native AgentDojo evidence and Conflux augmentation:

- upstream task and suite identifiers;
- upstream utility and security outcomes;
- raw upstream logs or result structures;
- Conflux Principal Context and policy annotations;
- Conflux trace and decision outcomes;
- model identity and configuration;
- tokens, latency, cost where available;
- parser, provider, and infrastructure failures;
- repetitions and variance for stochastic runs.

### Acceptance evidence

The live track is complete only when a credentialed run is retained. Adapter tests and raw fixtures establish translation behavior, not benchmark efficacy.

If credentials or the optional package are unavailable, preserve the externally gated status and do not simulate a live claim.

## Track C: utility and planning ablations

### Objective

Measure whether the implemented planning mechanisms improve practical utility and authority efficiency without weakening the security boundary.

### Required modes

Use the repository's fixed comparison modes, mapping names precisely to the current implementation:

1. reactive execution;
2. static planning;
3. dynamic planning;
4. dynamic planning with generated-code capability, where the sandbox is actually available.

A no-defence result may be reported as a separate upper-utility and lower-security control, but it must not be conflated with a Conflux planning mode.

### Initial task suite

Begin with a compact diagnostic suite rather than a large aggregate. The suite should contain tasks that exercise:

- direct authorised effects;
- data-dependent action selection;
- unnecessary sensitive reads;
- mixed-principal inputs;
- revocation between planning and execution;
- recovery after a blocked action;
- recovery after provider failure;
- continuation or replanning;
- a task that cannot be securely completed under the current policy.

Each task must state its expected secure completion conditions and the reason it distinguishes the modes.

### Required metrics

Report separately:

- task completion;
- executed security violations;
- legitimate effects blocked;
- blocked adversarial proposals;
- sensitive reads;
- maximum Principal Context size;
- cumulative authority or context footprint, if defined by an accepted metric;
- calls, tokens, latency, replans, and plan growth;
- incomplete and bound-reached outcomes;
- parser, planner, verifier, provider, and sandbox failures.

Security is a hard constraint. `UNKNOWN`, unsupported, or unavailable outcomes must not be ranked as safe.

### Ablation order

Run the minimum comparison first. Add finer ablations only after the four-mode result is retained. Candidate later ablations include:

- authority-minimising objective enabled versus disabled;
- sensitive-read penalty enabled versus disabled;
- continuation enabled versus disabled;
- static versus action-time policy snapshots;
- model-level prompt-injection defence as a utility layer.

### Acceptance evidence

The current claim that open-ended planning improves utility remains unsupported until a retained real-model comparison exists. Scripted fixtures may validate mechanics and expected edge cases, but must be labelled separately.

## Cross-track documentation contract

### Canonical ownership

Update only the document that owns the changed information:

| Information | Canonical owner |
|---|---|
| Normative experiment behavior | `docs/EVALUATION.md` or an accepted specification |
| Current programme disposition | `docs/task-registry.json` |
| High-level capability summary | `docs/STATUS.md` |
| Claim strength and limitations | `docs/CLAIMS.md` |
| Experiment inputs and packaging | `experiments/README.md`, manifests, and schemas |
| Durable design rationale | `docs/decisions/` |
| Publication statements | `manuscript/`, backed by retained evidence |
| Historical interpretation | `reports/analysis/` only when archived reports are being reconciled |

This specification owns the programme decisions above. It does not own live status or numerical results.

### Required documentation checks

For every completed experimental slice, Codex must verify:

- the task registry disposition matches the evidence;
- the claim ledger does not overstate the result;
- Status remains a summary rather than a copied task list;
- experiment documentation contains the rerun command and limitations;
- generated manuscript tables read from retained result JSON;
- no numerical value is manually copied into the manuscript without a generated source;
- local links, terminology, schemas, and audit rules pass.

### Documentation-review principle

Treat documentation review as a semantic diff:

- What behavior changed?
- What assumption changed?
- What evidence strength changed?
- What would a human reviewer now believe after reading the docs?
- Does Codex receive enough current context to avoid reintroducing a superseded design?

## Sequencing and parallelism

### Phase 1: protocol freeze

Before long runs:

1. inspect existing suites, manifests, schemas, and aggregation code;
2. write or update the exact experiment protocols;
3. confirm canonical metrics and failure categories;
4. add missing negative controls;
5. run focused validation.

### Phase 2: cheapest evidence first

1. native SLED smoke and negative controls;
2. full feasible native reproduction;
3. one live model-adapter smoke;
4. one AgentDojo no-defence case and one ITES case;
5. compact planning comparison.

### Phase 3: expand only from observed bottlenecks

Use the results to choose whether to invest next in:

- SLED state-space reductions;
- solver-backed verification;
- planning optimisation;
- richer Principal Context or argument roles;
- delegation;
- persistent memory;
- policy or framework integration.

Selection should be based on observed failures, performance limits, utility losses, or novelty opportunities rather than repository symmetry.

### Safe parallel work

After protocols are stable, the following may proceed in parallel when they do not modify the security kernel:

- native SLED runs;
- AgentDojo environment setup;
- real-model endpoint validation;
- task-suite authoring;
- report-generation improvements;
- documentation audits.

Changes to Principal Context, policy semantics, trace meaning, or result classification must not be parallelised without an accepted specification and shared conformance tests.

## Codex task contract

For each task, Codex must state before implementation:

- the canonical owner files;
- the exact hypothesis or defect;
- in-scope behavior;
- non-goals;
- security and evidence invariants;
- schemas and public interfaces affected;
- tests and negative controls;
- retained output required;
- validation commands;
- documentation updates;
- stop conditions.

A task is not complete because a module imports or a command exits successfully. Completion requires the named evidence and agreement between implementation, tests, documentation, status, and claims.

## Stop conditions

Stop and request direction when:

- historical and canonical semantics cannot be distinguished;
- a change would silently alter the meaning of a published metric;
- an external dependency requires secrets not already configured;
- the only way to complete a run is to weaken fail-closed behavior;
- an adapter or benchmark version differs from the pin;
- a result cannot preserve raw upstream evidence;
- an experiment would omit blocked, failed, or incomplete cases;
- documentation would require a second roadmap, status page, or claim ledger;
- a numerical claim lacks retained evidence.

## Acceptance criteria for this programme

This programme is successful when:

- at least one current native SLED result package is reproducible;
- historical and canonical SLED semantics are explicitly separated;
- negative controls demonstrate evaluator sensitivity;
- at least one credentialed model run is retained;
- a pinned AgentDojo no-defence-versus-ITES smoke comparison is retained, or a specific incompatibility is evidenced;
- the four planning modes have a retained compact utility comparison;
- security, utility, failure, and incompleteness remain separate in every aggregate;
- documentation and task/claim ownership remain consistent;
- results identify which research directions merit deeper fourth-year specialisation.

## Delivery mapping

Use existing task IDs where they already own the work, especially `AGENTDOJO-003`, `PLAN-DYN-012`, and `PLAN-DYN-016`. Before adding a new native-reproduction task ID, inspect `docs/task-registry.json` and `reports/analysis/task-crosswalk.json` to avoid collisions. Any new ID must be canonical, documented once, and mapped to retained evidence.

Recommended commits:

1. `docs: specify evidence-first evaluation programme`
2. `test: freeze reproduction and ablation protocols`
3. `exp: retain native SLED reproduction evidence`
4. `exp: retain AgentDojo comparative smoke evidence`
5. `exp: retain planning utility ablation evidence`
6. `docs: reconcile status claims and manuscript from retained results`

Generated evidence should be committed separately from the code or protocol that produces it.
