# Conflux implementation technical specification

**Status:** Codex-ready implementation plan  
**Repository inspected:** `RayaBuckley/Conflux`, public `main` branch  
**Inspection date:** 29 July 2026  
**Target:** a coherent, executable research system that can (1) be interacted with locally, (2) produce reproducible ITES + SLED results, (3) support a genuine AgentDojo integration, and (4) begin SLED-V formal-verification experiments.

## 1. Executive decision

Conflux should now enter a consolidation-and-evidence phase. The repository already has a substantial domain model, provenance objects, action types, ITES mediation, evaluation and reporting abstractions, policy/provider prototypes, benchmark wrappers, tests, documentation and a clean-architecture migration slice. What it does not yet have is one authoritative end-to-end runtime that is semantically consistent, directly runnable, connected to a real model, and capable of producing a versioned experiment result from a single command.

The implementation objective is therefore:

> Build one canonical execution path from an immutable environment snapshot through a model adapter, the ITES security kernel, a sandboxed provider, complete trace capture and a versioned result report; then reuse that path for deterministic SLED, SLED-V and AgentDojo.

Do not add another benchmark, provider or policy family before this vertical slice exists. Generic wrappers that have not been exercised against pinned upstream systems should be treated as scaffolding, not completed integrations.

## 2. Inspection limits and evidence standard

The public repository was inspected through GitHub source views and its own status/audit documentation. A direct clone and full local test run could not be completed in the analysis environment because outbound DNS was unavailable. Claims in `docs/STATUS.md` that runtime validation, mypy and Ruff pass are therefore recorded as repository claims rather than independently reproduced results.

Every Codex task below has an evidence requirement. A task is complete only when its tests, trace fixture, experiment artefact or external-integration fixture exists. “The module exists” is not evidence of integration.

## 3. Current state

### 3.1 Implemented or substantially present

| Area | Current implementation | Assessment |
|---|---|---|
| Core values | Principals, permissions, resources, provenance, artefacts, actions, consent, sessions and chat policy | Useful foundation; security semantics still need consolidation |
| Canonical domain | `DataItem`, `EnvironmentSnapshot`, intent/decision/context values | Initial contract exists; not yet the sole runtime model |
| ITES | Rich mediator plus immutable `ExecutionState`; separate research MVP and compatibility path | Functionality exists, but there are overlapping semantics |
| Authorisation | Principal-intersection checks, action dispatch, visibility and consent | Contains correctness and modelling defects listed below |
| Evaluation | One-shot evaluator, bounded exhaustive evaluator, task/environment suites, traces, classification, statistics and reporting | Broad infrastructure; current exhaustive path is still bounded trace enumeration |
| Providers | Filesystem and Docker adapters | Prototype-level and still coupled to legacy environment construction |
| Policies | Internal policy contract, owner example and partial AWS-style adapter | Not sufficient for real IAM-compatibility claims |
| External benchmarks | Native adapter and generic AgentDojo/CaMeL/Dual-LLM command wrappers | Interfaces exist; real upstream fixtures and versioned integrations are missing |
| Tests | Unit and contract tests over core, authorisation, ITES, evaluation, policy and architecture | Useful but insufficiently end-to-end and adversarial |
| Documentation | Architecture, development guide, audit ledger, status, evaluation guidance, research reports | Stronger than executable evidence; some descriptions lag package migration |
| Archived paper | LaTeX, bibliography, figures and PDF under `paper/` | Preserve unchanged as the previous-year artefact |

### 3.2 Not implemented to result-ready standard

The following are the principal blockers to producing defensible new results:

1. A single authoritative security transition semantics used by both runtime and evaluation.
2. Correct empty-Principal-Context handling.
3. Separation of information provenance from read entitlement.
4. Explicit and deterministic proposal/branch semantics.
5. Complete mediation traces returned to callers and written to disk.
6. A model adapter implementation and structured proposal parser.
7. A safe interactive CLI and sandbox provider.
8. A reproducible experiment manifest and result writer.
9. A genuine, pinned AgentDojo integration using upstream task/tool/state semantics.
10. State-based SLED exploration with memoisation and counterexample reconstruction.
11. A formal SLED-V intermediate representation and first solver backend.
12. Cross-platform setup, CI and compute-cluster scripts.
13. New empirical results generated by the current repository.

## 4. P0 semantic defects

These must be resolved before any new benchmark number is reported.

### SEC-001: empty Principal Context currently authorises by vacuous truth

`all_principals_authorised` applies Python `all()` directly. An empty iterable therefore returns true. The application-layer authorisation facade repeats the same pattern.

**Required semantics**

- An empty Principal Context has no implicit authority.
- Primitive, visible, delegated and provider actions must be denied when the context is empty.
- An operation that genuinely originates from the trusted system must carry an explicit authenticated system principal; it must not use the empty set as a substitute.

**Acceptance tests**

- Empty context denies every primitive permission.
- Empty context cannot issue delegation, consent, messages or provider calls.
- A named system principal with an explicit permission can perform the corresponding internal operation.
- The MVP, rich mediator and application facade agree.

### SEC-002: provenance is being used as a read ACL

The canonical domain separates `DataItem.authors` and `DataItem.readers`, but the central action authoriser treats `artifact.provenance.principals` as the reader set. This conflates “who influenced the value” with “who may observe the value”.

**Required semantics**

Introduce a first-class read decision:

```python
@dataclass(frozen=True, slots=True)
class ReadRequest:
    principal_context: PrincipalContext
    artifact: Artifact[Any]
    environment: EnvironmentSnapshot
    purpose: str | None = None

@dataclass(frozen=True, slots=True)
class ReadDecision:
    allowed: bool
    reason_code: str
    evidence: Mapping[str, Any]
```

A `ReadPolicyPort` evaluates the request. The default domain policy uses `DataItem.readers`. Provenance is an input to audit and downstream authority propagation, not the ACL itself.

**Acceptance tests**

- A reader who is not an author can read.
- An author who is not a reader cannot read.
- Derived provenance does not automatically grant read access.
- Resource-backed artefacts use the policy adapter rather than their provenance set.
- Nested execution, messages and visible provider outputs use the same read-policy path.

### SEC-003: implicit consent collapses into authorisation

When no session is supplied, the mediator creates consent profiles allowing every permission already held by each participant. This makes missing consent configuration equivalent to broad automatic consent.

**Required semantics**

- Missing consent configuration must be fail-closed for effectful and user-visible actions.
- Internal no-op/stop operations may be allowed by an explicit default policy.
- The deployment config must select one of: `explicit`, `confirm_effectful`, or `test_permissive`.
- `test_permissive` must be rejected outside test/dev mode and stamped into traces.

### SEC-004: reported guarantees describe rejected proposals, not executed violations

A correctly blocked unauthorised proposal currently causes `primitive_actions_authorised=False`; similarly for unreadable nested proposals. This makes attacks look like failed guarantees even when complete mediation worked.

**Required result taxonomy**

Security invariants:

- `no_unauthorised_action_executed`
- `no_unauthorised_read_performed`
- `no_visibility_violation_emitted`
- `no_unconsented_effect_executed`
- `provenance_preserved`
- `call_budget_respected`

Diagnostics:

- `unauthorised_proposals_observed`
- `unreadable_nested_proposals_observed`
- `visibility_blocked_proposals`
- `consent_blocked_proposals`
- `malformed_proposals_observed`

A secure attack run may have non-zero diagnostics while every invariant holds.

### SEC-005: rich proposal semantics are not explicit or deterministic

The mediator converts model output to a `frozenset`, iterates it, and recursively updates shared aggregate state. The normative MVP instead sorts proposals and isolates sibling branches. A set cannot encode whether proposals are alternatives, an ordered plan, or concurrent effects.

**Required model**

```python
class ProposalMode(Enum):
    ALTERNATIVES = "alternatives"
    ORDERED_PLAN = "ordered_plan"

@dataclass(frozen=True, slots=True)
class ProposalBatch:
    id: str
    mode: ProposalMode
    proposals: tuple[Action[Any], ...]
```

- `ALTERNATIVES`: each proposal starts from the same parent security state. Results are separate branches.
- `ORDERED_PLAN`: proposals execute sequentially and effects are visible to later steps.
- Every proposal has a stable ID and canonical sort key.
- The LLM adapter must never return an unordered set as the semantic plan representation.

### SEC-006: decision provenance is overwritten

The mediator replaces every proposal’s decision principals with the full active influencer set. Conservative full-context binding is reasonable, but it is not precise causal decision provenance.

**Required terminology and data model**

Separate:

- `information_provenance`: sources that could have affected inputs;
- `authority_context`: conservative principals whose permissions constrain the action;
- `decision_attestation`: optional externally supported claim about the planner/controller that selected the action.

Until causal attribution is implemented, the authority context must remain conservative and must not be described as exact decision provenance.

### SEC-007: owner access bypasses permission checking

The owner helper has a shape-dependent branch that returns true for direct owner representation without checking the requested permission.

**Required semantics**

Ownership is policy evidence. It may cause a policy adapter to grant a named permission, but it must not bypass the general decision pipeline.

### SEC-008: runtime trace is accumulated but not returned

`ExecutionState` holds an immutable trace, but `ITESReport` does not return it. The one-shot evaluator writes only an `evaluation.completed` count record.

**Required semantics**

`MediationReport` must include:

```python
trace: ExecutionTrace
run_id: str
schema_version: str
policy_snapshot_id: str
model_snapshot_id: str
environment_snapshot_id: str
```

Every proposal and decision must be represented in the trace, including blocked and malformed proposals.

## 5. Target architecture

### 5.1 One executable security kernel

Create `src/conflux/mediation/` as the canonical security implementation, or rename the current `ites` package once migration is complete. The kernel must expose a pure transition function wherever possible:

```python
@dataclass(frozen=True, slots=True)
class KernelState:
    environment: EnvironmentSnapshot
    principal_context: PrincipalContext
    policy_snapshot_id: str
    consent_state: ConsentStateSnapshot
    call_budget: CallBudget
    trace: ExecutionTrace

@dataclass(frozen=True, slots=True)
class TransitionInput:
    batch: ProposalBatch
    model_call: ModelCallRecord

@dataclass(frozen=True, slots=True)
class TransitionResult:
    next_states: tuple[KernelState, ...]
    decisions: tuple[ActionDecision, ...]

class SecurityKernel(Protocol):
    def transition(self, state: KernelState, transition: TransitionInput) -> TransitionResult: ...
```

The interactive runtime, deterministic SLED, SLED-V and external benchmarks must all call this kernel. The research MVP becomes either:

- a small executable specification used in conformance tests; or
- a thin configuration of the same kernel.

It must not remain an independent production semantics.

### 5.2 Canonical dependency direction

```text
core value objects
    ↓
domain snapshots and typed actions
    ↓
policy/read/consent/visibility ports
    ↓
mediation security kernel
    ↓
application use cases
    ↓
adapters: models, providers, benchmarks, trace stores
    ↓
CLI and experiment runners
```

Evaluation may import canonical domain and mediation contracts. Mediation must not import evaluation, benchmark or provider implementations.

### 5.3 Canonical IDs and snapshots

Every reproducible run requires stable identifiers:

- principal ID;
- resource/data ID;
- artefact ID and content hash;
- action/proposal ID;
- model-call ID;
- parent branch ID;
- trace/run ID;
- policy snapshot hash;
- environment snapshot hash;
- model configuration hash;
- source commit.

Hashing must use canonical JSON and a documented algorithm. Python object `repr()` and set iteration order must not affect IDs.

## 6. Result-ready vertical slice

The first complete system must be deliberately small.

### Scenario

A local workspace contains:

- a user-authored task;
- a second-principal document with a malicious instruction;
- a confidential file;
- allowlisted read/write/message operations;
- explicit permissions and readers.

### Runtime

1. Load a declarative environment file.
2. Materialise `EnvironmentSnapshot` and artefacts.
3. Call either a scripted model or a structured local/API model adapter.
4. Parse a `ProposalBatch`.
5. Mediate every proposal through the canonical kernel.
6. Execute allowed operations against an in-memory or temporary-directory provider.
7. Write an append-only JSONL trace.
8. Write a versioned JSON result and a human-readable report.
9. Exit non-zero only for runtime/infrastructure failure, not because an attack proposal was securely blocked.

### Required CLI

```text
conflux demo --scenario examples/basic.yaml --model scripted
conflux chat --scenario examples/basic.yaml --model openai-compatible
conflux sled run --suite examples/sled-mvp.yaml --output runs/<id>
conflux verify --model examples/ites-model.yaml --property no-privilege-escalation
conflux benchmark agentdojo --config configs/agentdojo-smoke.yaml
conflux report runs/<id>/result.json
conflux doctor
```

Use `argparse` initially to avoid unnecessary dependencies. Add a console script in `pyproject.toml`.

## 7. Workstreams

## W0. Baseline and archival integrity

### W0.1 Freeze the archived paper

Keep the current `paper/` directory unchanged. Add `paper/ARCHIVED.md` containing:

- the commit/tag corresponding to the archived submission;
- the statement that its results refer to the previous prototype;
- the fact that post-paper architecture is not validated by those results.

Create the new manuscript under `manuscript/` rather than editing archived files in place.

### W0.2 Capture a repository baseline

Add `docs/BASELINE_2026-07.md` with current commit, validation commands, known defects and missing integrations. Run and retain:

```text
python -m pytest -q
python -m mypy src tests
python -m ruff check src tests
python scripts/audit_repository.py
```

If the current checkout does not pass, commit the raw logs before fixing so later claims are traceable.

## W1. Semantic repair and conformance

1. Implement SEC-001 through SEC-008.
2. Add `tests/semantics/` containing a table-driven semantic corpus.
3. Parameterise the same corpus over the research MVP and canonical kernel.
4. Delete or quarantine any compatibility path that cannot pass the corpus.
5. Add property-based tests using Hypothesis only after deterministic examples pass.

Minimum semantic corpus:

- empty context;
- one authorised principal;
- mixed authorised/unauthorised principals;
- reader-not-author;
- author-not-reader;
- derived artefact;
- nested accumulation;
- sibling isolation;
- ordered-plan state propagation;
- visibility denial;
- consent required/withheld/allowed;
- delegation scope/expiry/use-count;
- malformed proposal;
- provider failure;
- policy revocation between steps.

## W2. Canonical domain migration

1. Change provider and benchmark boundaries to accept `EnvironmentSnapshot` and `DataItem`.
2. Move legacy `Data`/`Environment` conversion to one compatibility adapter at ingestion only.
3. Remove compatibility imports from canonical providers and evaluation.
4. Replace duck-typed `Any` extraction in the main path with explicit protocols or dataclasses.
5. Add a migration map to `docs/STATUS.md` and delete each alias once no supported caller remains.

Acceptance condition: a dependency test fails if `conflux.adapters.providers`, `conflux.mediation`, or canonical evaluation imports `conflux.compatibility`.

## W3. Trace and result system

### Event schema

Required events:

- `run.started`, `run.completed`, `run.failed`;
- `model.requested`, `model.responded`, `model.parse_failed`;
- `proposal.observed`;
- `policy.read_decided`, `policy.action_decided`, `policy.visibility_decided`, `policy.consent_decided`;
- `action.allowed`, `action.blocked`, `action.executed`, `action.failed`;
- `branch.created`, `branch.completed`, `bound.reached`;
- `environment.changed`;
- `delegation.issued`, `delegation.consumed`, `delegation.revoked`.

Every event includes run ID, branch ID, sequence, timestamp, schema version and causal parent IDs.

### Result schema

A result must contain:

- manifest and hashes;
- security invariants;
- diagnostics;
- utility outcome;
- completeness/bounds;
- calls, tokens, latency and provider errors;
- raw trace path and checksum;
- software and upstream revisions.

Add JSON Schema files under `schemas/` and golden fixtures under `tests/fixtures/traces/`.

## W4. Interactive runtime

### W4.1 Scripted model adapter

Implement a deterministic adapter that maps model-call IDs or input signatures to `ProposalBatch` values. It is the reference adapter for tests and SLED fixtures.

### W4.2 OpenAI-compatible adapter

Implement a generic HTTP adapter for servers that expose an OpenAI-compatible chat/completions endpoint. This supports hosted APIs and local servers without hard-coding a vendor SDK. Configuration must include endpoint, model, timeout, structured-output mode and secret environment-variable name. Raw responses must be retained with configurable redaction.

### W4.3 Local Hugging Face adapter

Implement as an optional extra, not a mandatory dependency:

```toml
[project.optional-dependencies]
local-model = ["transformers", "torch", "accelerate"]
```

Support one documented causal model path first. Do not build a general inference framework.

### W4.4 Structured proposal schema

Models return JSON matching a strict schema. Unknown action types, resources or fields are blocked and traced. The parser must never use `eval`, permissive object hooks or fallback execution of model text.

### W4.5 Safe provider

Build `InMemoryProvider` and `TemporaryFilesystemProvider` before exposing Docker. Features:

- allowlisted operations;
- dry-run default;
- atomic writes;
- root confinement;
- stable error types;
- idempotency keys;
- precondition hashes;
- no shell invocation.

The Docker provider remains experimental and disabled by default.

## W5. Native SLED result pipeline

### W5.1 Reproduce previous environments

Translate the three previous-year environments into declarative, versioned fixture files. Preserve original semantics in a `legacy-reproduction` suite and create a corrected `canonical` suite for current semantics.

Never silently compare the corrected semantics with historical numbers as if they were the same experiment.

### W5.2 Deterministic controls

Include:

- ITES;
- no defence;
- union permissions;
- initiator only;
- latest input only;
- no read check.

Each negative control must have at least one fixture that produces a violation. This validates the evaluator rather than only ITES.

### W5.3 Run manifest

`experiments/manifests/*.yaml` records:

- suite version;
- Conflux commit;
- defence config;
- bounds;
- seed;
- model adapter;
- provider;
- policy snapshot;
- machine metadata;
- output directory.

### W5.4 Readiness experiment

Before attempting millions of traces, produce a small committed smoke result that includes:

- at least one authorised task;
- at least one blocked attack;
- at least one intentionally vulnerable defence counterexample;
- complete JSONL trace;
- generated table;
- rerun command.

## W6. SLED-MC: explicit-state model checking

The next SLED implementation should explore reachable states, not re-run every syntactic trace.

### State identity

A canonical state key contains only future-relevant fields:

- environment and policy state;
- authority context;
- artefact/provenance state;
- pending plan nodes;
- memory/delegation state;
- call/error budget;
- observations relevant to the checked property.

Full history is stored through predecessor edges for counterexample reconstruction.

### Algorithm

1. Breadth-first search for shortest counterexamples.
2. Deterministic transition ordering.
3. Visited-state memoisation.
4. Parent/action predecessor map.
5. Explicit verdicts: `SAFE`, `UNSAFE`, `BOUNDED_SAFE`, `UNKNOWN`.
6. Bound-reached states remain in reports; they are never dropped from denominators without a separate analysis.

### Required experiment

Compare old trace enumeration and new state exploration on the same fixtures:

- traces attempted;
- unique states;
- transitions;
- memory;
- runtime;
- counterexample length;
- verdict agreement within the old bound.

## W7. SLED-V: formal verification

### W7.1 Verification IR

Create `src/conflux/verification/ir.py` with finite, serialisable values:

```python
InitialStateSet
EnabledTransitions
TransitionRelation
ObservationFunction
SafetyProperty
GoalProperty
FairnessAssumption
```

No arbitrary callbacks or hidden mutable state are allowed in a model submitted for proof.

### W7.2 First properties

- no privilege escalation;
- no unauthorised read;
- provenance monotonicity;
- no implicit delegation;
- bounded resource use.

Confidentiality/noninterference is a separate later workstream; do not present authorised-read safety as full noninterference.

### W7.3 First backend

Implement SMT bounded model checking with Z3 as an optional extra. It should:

- encode a finite model for `k` steps;
- find a concrete violating trace;
- return `BOUNDED_SAFE` when none exists;
- record solver version, query hash and model.

### W7.4 Unbounded safety milestone

After the IR stabilises, add translation to nuXmv or an IC3/PDR-capable backend. A successful result must retain the inductive invariant or proof artefact where available. The first target is the finite canonical ITES model without unrestricted policy mutation.

### W7.5 Conformance

Instrument the runtime kernel and check that each observed transition is admitted by the verification IR. Add differential tests that execute the same state/action pair in both implementations. A formal model result must not be described as an implementation guarantee until conformance evidence exists.

## W8. Planning and SLED-Synth

Planning is useful but should follow semantic consolidation.

### Typed plan

```python
@dataclass(frozen=True, slots=True)
class PlanNode:
    id: str
    operation: str
    arguments: Mapping[str, JSONValue]
    preconditions: tuple[Predicate, ...]
    outcomes: tuple[OutcomeTransition, ...]
    required_reads: tuple[str, ...]
    required_permissions: tuple[str, ...]
    compensation: str | None
```

### Pipeline

1. Model proposes goal/plan candidates.
2. Schema validation.
3. Tool catalogue lookup from authenticated metadata.
4. Security annotation.
5. Model checking over all declared outcomes.
6. Optimisation for utility, authority footprint, sensitive observations, calls and irreversible effects.
7. Mediated execution.
8. Replanning only inside a preverified envelope.

Utility must be split into:

- possible secure completion;
- controller-achievable completion;
- benign-model completion under a stated competence contract.

## W9. Genuine AgentDojo integration

The current adapter should be renamed `agentdojo_like` unless it directly uses upstream AgentDojo structures.

### Integration contract

1. Pin an AgentDojo release/commit in `external/agentdojo.lock`.
2. Add installation instructions and licence notes.
3. Build an explicit translation table for users, tasks, tools, state, attacks and success criteria.
4. Preserve raw upstream task and result IDs.
5. Capture a real upstream output fixture.
6. Distinguish:
   - upstream setup/runtime failure;
   - model/parser failure;
   - policy block;
   - benchmark security failure;
   - utility failure.
7. Validate a small smoke subset in CI or a separately triggered integration job.
8. Do not use heuristic “try several field names” parsing in the versioned integration.

### Initial comparative experiment

Run:

- no defence;
- ITES with canonical provenance annotations;
- optionally one upstream baseline that can be executed reproducibly.

Report both native AgentDojo metrics and Conflux security/trace metrics. State clearly where provenance/ACS annotations were added and how that changes the benchmark assumptions.

## W10. Compute and reproducibility

### Laptop

Use the laptop for:

- unit/type/lint checks;
- deterministic scripted-model runs;
- small SLED-MC state spaces;
- AgentDojo smoke cases;
- interactive CLI;
- small quantised local models if memory permits.

Do not tie correctness tests to a GPU.

### TorrNodes

Treat hardware availability as unknown until discovered. Add `conflux doctor --json` and a cluster probe script that records:

```text
uname / OS
Python version
CPU and memory
nvidia-smi or equivalent
CUDA/driver versions
scheduler commands (sinfo/squeue/sbatch or alternatives)
container availability
filesystem quotas
network/API restrictions
```

If SLURM is available, add:

- `scripts/cluster/submit_experiment.sh`;
- one manifest per job;
- output under a run ID;
- stdout/stderr retention;
- deterministic array-job seeds;
- resumption by completed-case ledger;
- no secrets in job files.

Use cluster compute for real-model repetitions, large external benchmark sweeps, symbolic model checking and state-space experiments. Model weights and caches must use configurable paths.

## W11. CI, packaging and governance

1. Add platform-neutral validation through `python -m` commands or `nox`/`tox`; retain PowerShell as a convenience wrapper.
2. Add GitHub Actions for Linux Python 3.12.
3. Add optional jobs for local-model, Docker and external benchmarks; do not make unavailable services block core CI.
4. Add a coverage threshold after the semantic repair milestone.
5. Add architecture dependency tests against current package names.
6. Add release tags and changelog.
7. Add `SECURITY.md` and document that provider adapters are research prototypes.
8. Use pull requests for Codex changes, even as a solo project, so generated diffs have a review boundary.

## W12. Paper and evidence pipeline

Keep `paper/` as the immutable archived paper. Put the current manuscript in `manuscript/` with:

```text
manuscript/
    README.md
    conflux_fourth_year_2026.tex
    references.bib
    generated/
        tables/
        figures/
```

Generated tables and figures must be produced from `runs/*/result.json`; do not manually transcribe headline numbers.

The current paper must distinguish:

- previous-year ITES/SLED contribution and archived bounded results;
- fourth-year architecture and implementation work;
- semantic defects discovered during consolidation;
- evidence already obtained;
- unimplemented directions and planned experiments;
- revised novelty relative to Progent, PACT, PCAS/FORGE and other recent systems;
- formal-verification claims versus empirical benchmark claims.

## 8. Milestones and exit criteria

### M0 — Reproducible baseline

Exit criteria:

- current commit recorded;
- full validation logs retained;
- archived paper marked;
- known defects captured as failing tests or issues.

### M1 — Semantically correct kernel

Exit criteria:

- SEC-001 through SEC-008 resolved;
- semantic corpus passes on canonical kernel;
- MVP conformance tests pass for shared subset;
- no canonical runtime import from compatibility.

### M2 — Interactive vertical slice

Exit criteria:

- `conflux demo` works from a clean install;
- scripted model proposes an allowed and blocked action;
- temporary provider executes only the allowed action;
- trace and result are written and validate against schemas;
- run is deterministic.

### M3 — Native SLED readiness result

Exit criteria:

- legacy-reproduction and canonical fixture suites exist;
- negative controls produce expected violations;
- one committed smoke experiment is reproducible;
- current ITES results are generated by the current code, not copied from the archived paper.

### M4 — Real-model interaction

Exit criteria:

- OpenAI-compatible adapter works with one configured endpoint;
- local-model optional adapter works on one documented model or is explicitly deferred based on hardware;
- raw/model/parsed outputs are traceable;
- malformed model output fails closed.

### M5 — SLED-MC

Exit criteria:

- state memoisation and shortest counterexamples implemented;
- verdict schema implemented;
- performance comparison against trace enumeration complete;
- no incomplete state is silently discarded.

### M6 — AgentDojo integration

Exit criteria:

- upstream revision pinned;
- actual fixture captured;
- smoke tasks run end-to-end;
- native and Conflux metrics written;
- translation assumptions documented.

### M7 — SLED-V first proof experiment

Exit criteria:

- verification IR exists;
- Z3 bounded checker produces a counterexample for a vulnerable defence and bounded-safe result for ITES;
- solver artefacts retained;
- runtime/IR conformance tests pass on fixture transitions.

### M8 — First defensible results package

Exit criteria:

- experiment manifests, raw traces, result JSON, scripts, generated tables and environment details are archived;
- laptop/cluster execution is documented;
- paper draft imports generated artefacts;
- claims are scoped to the exact model, bounds and assumptions.

## 9. Recommended task order for Codex

Run tasks in this sequence:

1. Baseline and failing semantic tests.
2. Empty-context and read-policy repair.
3. Result taxonomy and trace return.
4. Proposal batch/branch semantics.
5. Canonical domain migration.
6. In-memory provider and scripted model.
7. CLI and result writer.
8. Native SLED fixtures and negative controls.
9. SLED-MC state exploration.
10. OpenAI-compatible model adapter.
11. AgentDojo real integration.
12. SLED-V IR and Z3 backend.
13. Planning/synthesis.
14. Additional policy/provider families.

Do not parallelise tasks that modify the security kernel until M1 is complete. After M1, model adapters, CLI, trace storage and experiment manifests can proceed in parallel against frozen contracts.

## 10. Definition of result-ready

Conflux is ready to begin headline experiments only when all of the following hold:

- a clean installation exposes a supported CLI;
- the current implementation has one security semantics;
- empty context and read policy are correct;
- every model proposal is completely mediated;
- blocked attacks do not count as invariant failures;
- traces contain enough information to replay decisions;
- deterministic controls validate the evaluator;
- results carry source/model/policy/environment versions;
- bounds and incomplete cases are explicitly reported;
- at least one external integration is based on a pinned real upstream version;
- archived previous-year results are not used as evidence for the refactored implementation.

## 11. Non-goals for the first results phase

- Full AWS IAM, GCP IAM or Entra compatibility.
- Production Docker execution with broad host authority.
- A web UI.
- A general multi-agent framework.
- Verification of arbitrary Python defences.
- Full information-flow noninterference.
- Multiple external benchmark integrations before AgentDojo is complete.
- Claims of organisational production readiness.

These can follow once the kernel and evidence pipeline are stable.
