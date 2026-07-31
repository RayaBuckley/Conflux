# Conflux repository progress and dynamic-planning review

**Inspection date:** 30 July 2026  
**Repository:** `RayaBuckley/Conflux`, public `main` branch  
**Outputs:** this human-readable report and a separate Codex-oriented JSON task graph

## 1. Scope and confidence

This review examined the current public repository, its canonical documentation, the archived paper, the report suite, the 29 July implementation package, the present action/model/mediation interfaces, and primary planning literature. The public repository showed 147 commits at inspection time.

I did not successfully clone and execute the repository in this environment. Statements that the audit, tests, mypy and Ruff pass are therefore treated as repository self-report from `docs/STATUS.md`, not independently reproduced evidence. Code-level findings below are based on the source visible on `main`.

## 2. Executive assessment

Conflux has completed a large amount of **research synthesis, architecture design and implementation planning**. It has not yet completed the corresponding **semantic repair, canonical runtime, reproducible current results, SLED-MC/SLED-V implementation, genuine AgentDojo integration, or planning runtime**.

The project is now documentation-rich but evidence-poor. This is not primarily a problem of missing ideas. The report suite contains most of the right ideas, including a canonical security kernel, complete traces, state-based checking, conformance testing, real-model integration and authority-aware planning. The problem is that several overlapping reports and backlogs do not form a single status-controlled delivery system, and most acceptance evidence has not been produced.

Planning currently exists only as a late design workstream. The existing `PLAN-001` to `PLAN-003` tasks define a typed graph, pre-execution verification and authority-minimising selection. They do not implement the more realistic requirement established in this discussion: an open-ended plan that can ask an LLM what to do next, create or replace subplans, bind LLM-produced values into later actions, loop, recover from errors and execute arbitrary generated code when the environment permits it.

The recommended correction is to split planning into two layers:

1. **Dynamic planning runtime**, delivered soon after the canonical kernel and trace contracts. This supports realistic agents and empirical experiments.
2. **Plan verification and optimisation**, delivered later with SLED-MC/SLED-V. This proves or checks finite abstractions and must return `UNKNOWN` where arbitrary code or unbounded state cannot be analysed conclusively.

## 3. Current repository snapshot

The repository contains the expected research-software layers: `core`, `domain`, `auth`, `ites`, `evaluation`, `ports`, `application`, `adapters`, `execution`, `policy`, `research` and `compatibility`. The canonical architecture document correctly treats the model, provider and benchmark as adapters around the ITES security boundary.

However, the implementation remains transitional:

- `docs/STATUS.md` says clean-slate boundaries are only an initial slice and that provider, evaluation and benchmark callers still need migration.
- `PrimitiveAction` contains a permission, resource and provider-operation string, but no typed argument map, binding source or grounded/template distinction.
- `Proposal` includes primitive, nested, delegation, message, clarification, consent, stop and no-op actions. There is no plan or continuation type.
- `ModelPort` returns an unordered `frozenset[Action]` from input artifacts.
- `MediationService` is a thin delegate to `ITES.run`.
- The mediator still converts proposals to a `frozenset`, derives default consent from participants' permissions, overwrites proposal decision principals with the active influencer set, and returns a report without the accumulated execution trace.
- `all_principals_authorised` still uses `all(...)` directly, so an empty principal set is vacuously authorised.
- The read helper still treats artifact provenance principals as readers.
- The owner helper still has a direct-owner branch that returns true without checking the requested permission.
- `docs/MVP_RESULTS.md` explicitly remains a template pending an executable run.

These findings mean planning must not be bolted directly onto the current mediator as another action subtype. The plan executor must target the canonical security kernel proposed by the current technical specification.

## 4. Review of the report suite

### 4.1 Archived previous-year paper

**Document status:** complete and valuable.  
**Implementation status:** historical prototype only.

The archived paper and project report establish ITES, SLED and the bounded previous-year results. The current fourth-year draft correctly states that those results do not validate the refactored repository. The remaining governance task is to add `paper/ARCHIVED.md` with a stable commit or tag and move the current manuscript out of `reports/New/` into `manuscript/`.

### 4.2 `reports/REPO_REVIEW`

**Document status:** complete.  
**Implementation status:** partially translated into the new specification; fixes mostly open.

This review identified the important semantic and engineering problems: empty-context authority, provenance/read-ACL confusion, implicit consent, branch ambiguity, trace omission, provider and benchmark incompleteness, and lack of current empirical evidence. The 29 July technical specification incorporates these points well. `REPO_REVIEW` should now be marked as a retained audit input rather than another active implementation plan.

### 4.3 `reports/SLED_REVIEW`

**Document status:** comprehensive research landscape.  
**Implementation status:** not started.

The report gives a credible path from bounded trace enumeration to explicit-state model checking, symbolic backends, conformance checking, confidentiality properties and secure controller synthesis. No current `conflux.verification` or `conflux.planning` source package is visible. The report has therefore advanced the research agenda, not the implementation.

### 4.4 Literature, novelty and related-work reports

**Document status:** largely complete.  
**Implementation status:** not applicable.

The literature package is one of the strongest completed workstreams. It narrows the novelty claim appropriately relative to Progent, PACT, PCAS/FORGE, CaMeL and other systems. Before submission, the recent references and any automatically assembled BibTeX records still need reconciliation with Zotero.

### 4.5 Earlier Codex manifests and research backlog

**Document status:** complete historical artefacts.  
**Implementation status:** mixed and not machine-verifiable.

The old action manifest and research backlog remain useful, but they are not explicitly superseded and there is no mapping from their task IDs to the current implementation backlog. This creates duplicate sources of apparent truth.

### 4.6 29 July implementation technical specification

**Document status:** current primary implementation specification.  
**Implementation status:** mostly future work.

This is a strong document. It correctly prioritises semantic consolidation, a single kernel, trace/result schemas, deterministic and real-model runtimes, native SLED, AgentDojo, SLED-MC, SLED-V, CI and evidence generation.

Its planning section is now too restrictive. It defines one generic `PlanNode`, assumes verification of declared outcomes before execution and permits replanning only inside a preverified envelope. That is suitable for controller synthesis, but not sufficient for a realistic general agent. It does not define:

- operation schema versus template versus grounded action;
- provenance for individual argument bindings;
- a continuation request and plan-patch protocol;
- recursive or cyclic plans;
- subplan creation and replacement;
- arbitrary code execution as a mediated operation;
- plan/node/path provenance;
- real-model planner records;
- plan-specific trace events;
- worst-case SLED semantics for arbitrary continuations;
- the boundary between runtime expressiveness and verification completeness.

### 4.7 29 July Codex implementation backlog

**Document status:** current machine-readable task plan.  
**Implementation status:** predominantly unimplemented.

The backlog appears to contain 46 tasks. It is well structured around dependencies and acceptance criteria. It nevertheless has four governance defects:

1. The technical specification requires `SEC-001` through `SEC-008`, but the JSON contains only `SEC-001` through `SEC-007`. `TRACE-001` overlaps `SEC-008`, but no alias is declared.
2. Tasks have no `status`, `evidence_paths`, `completed_commit`, `completed_at` or `verified_at` fields.
3. The recommended placement described by `reports/New/README.md` has not been completed.
4. `PLAN-001` to `PLAN-003` cover a closed graph, verification and optimisation only.

The structured JSON accompanying this report supplies a replacement planning task graph with explicit dependencies and acceptance criteria.

### 4.8 Fourth-year paper draft

**Document status:** substantial and appropriately cautious.  
**Implementation status:** result sections pending.

The draft clearly separates previous-year results from current implementation claims and explicitly leaves generated-result placeholders. This is good practice. The planning contribution must be rewritten if the project adopts open-ended continuation. It should describe Conflux as supporting an expressive dynamic planner operationally, with SLED checking a bounded or abstract model rather than claiming that every arbitrary program is statically verified.

### 4.9 Canonical docs and current result template

`docs/ARCHITECTURE.md`, `docs/STATUS.md`, `docs/EVALUATION.md` and `docs/AUDIT.md` provide useful governance, but STATUS is qualitative and not linked to task IDs or retained evidence logs. `docs/MVP_RESULTS.md` explicitly has no current result. The root README also contains stale package paths (`providers`, `sled`, `benchmarks`) rather than the current adapter/evaluation layout.

## 5. Progress by implementation area

| Area | Current state | Assessment |
|---|---|---|
| Domain/provenance/action scaffolding | Present | Useful base, but still split across core/domain/compatibility |
| Rich ITES mediator | Present | Not yet the canonical corrected semantics |
| Normative MVP | Present | Valuable executable specification; conformance harness absent |
| Semantic repair | Specified | Several defects visibly remain in current source |
| Trace/result system | Partial types | Full mediation trace not returned; schemas/golden fixtures absent |
| Interactive runtime/CLI | Specified | No supported end-to-end path visible |
| Current reproducible results | Absent | MVP result is a template |
| External benchmarks | Adapter scaffolding | No pinned genuine AgentDojo fixture/result path yet |
| SLED-MC | Specified | No verification package visible |
| SLED-V | Specified | No IR or solver backend visible |
| Paper | Strong draft | Results and generated artefact pipeline pending |
| Planning | Three late tasks | No implementation; current design is too closed |

## 6. Required dynamic-plan semantics

### 6.1 Expressiveness target

A Conflux plan should be an extensible program, not a fixed sequence. It must support:

- model calls that produce provenance-bearing values;
- action templates whose parameters bind literals, artifacts or prior node outputs;
- conditional branches and explicit loops;
- tool and provider actions;
- approval and delegation requests;
- a `ContinuePlanningNode` that asks an LLM what the next step should be;
- plan patches that append nodes, replace a subtree, spawn a subplan or terminate;
- arbitrary generated code passed to an authenticated code-execution operation;
- safe stopping and explicit budget exhaustion.

The LLM may propose any plan or code. It does not gain authority by doing so. Every grounded effect remains mediated at execution time.

### 6.2 Core type split

The action model should distinguish:

```python
OperationSchema      # authenticated operation definition
ActionTemplate       # operation plus unresolved argument bindings
GroundAction         # all arguments resolved; ready for mediation
ExecutedAction       # ground action plus provider result
```

A plan should distinguish value production from effects:

```python
PlanNode = (
    ModelCallNode
    | ActionTemplateNode
    | BranchNode
    | LoopNode
    | ContinuePlanningNode
    | ApprovalNode
    | DelegationNode
    | SubplanNode
    | TerminalNode
)
```

The current `PrimitiveAction` can become a compatibility representation for a `GroundAction`, but it should not remain the only representation of parameterised operations.

### 6.3 Continuation protocol

At a continuation point, the runtime constructs a typed request containing:

- current goal;
- current immutable plan and completed-node summary;
- selected provenance-bearing observations;
- authenticated operation catalogue;
- current authority/visibility context as system metadata;
- remaining step, call, token, time and effect budgets;
- the error or outcome that triggered replanning.

The planner returns a typed `PlanPatch`. Unparsed natural language is never executable. A malformed patch is traced and fails closed or causes a bounded repair request.

### 6.4 Provenance and authority

At minimum, track separately:

- **plan-generation provenance**: inputs to the LLM call that generated a plan or patch;
- **node control provenance**: information that determines whether and how a node executes;
- **branch-condition provenance**;
- **argument provenance** for every bound value;
- **invocation provenance**: principals causing this plan instance to run;
- **decision attestation**: optional evidence about the planner/controller identity.

For an executed effect, the conservative authority context is the union of relevant control, invocation and argument provenance. A continuation never resets authority. Any observation supplied to a continuation constrains the new nodes whose control flow it can affect.

A first implementation may conservatively attach the entire planner-call context to every node in the returned patch. A later research contribution can use explicit dataflow to reduce unnecessary propagation while proving that the refinement is sound.

### 6.5 Arbitrary code execution

Arbitrary code execution is compatible with ITES when represented correctly:

```python
execute_code(
    runtime,
    source_artifact,
    input_mounts,
    output_contract,
    capability_envelope,
)
```

The generated source may contain arbitrary valid code. The trusted operation and sandbox define its authority. The capability envelope must cover filesystem mounts, network destinations, credentials, subprocesses, time, memory, processes and output size.

ITES authorises the grounded operation and envelope. The sandbox enforces it. Conflux does not need to prove that the source is benign before allowing code that is already confined to effects all influencing principals may perform.

For SLED, arbitrary source code is not enumerated instruction by instruction. It is abstracted as nondeterministically producing any read, write, message, process or network effect allowed by the capability envelope. This is conservative and preserves the worst-case philosophy.

### 6.6 Execution loop

1. Generate or load the initial typed plan.
2. Select ready nodes deterministically.
3. Execute value-producing nodes and create artifacts.
4. Resolve action templates.
5. Form the grounded action and authority context.
6. Mediate read, authorisation, consent and visibility decisions.
7. Execute only allowed provider effects.
8. Record node, action and environment transitions.
9. On a continuation node or declared error transition, request a plan patch.
10. Validate and apply the patch.
11. Repeat until goal, safe stop, failure or explicit bound.

## 7. Relationship to existing planning work

CaMeL demonstrates the security value of extracting explicit control and data flow into an interpreter, but its core protection prevents untrusted data from changing program flow. Conflux's target is more expressive: untrusted observations may cause replanning, but every new plan fragment inherits their principal context and every effect is still mediated.

ReAct is the closest behavioural baseline for the requested runtime because it interleaves reasoning, actions and observations. ReWOO provides a useful closed-plan efficiency baseline because it separates planning from observations. LLM+P demonstrates the benefit of translating a natural-language problem into a formal planning representation and using a trusted planner. The proposed Conflux runtime can compare all three patterns:

- reactive next-action generation;
- closed plan-first execution;
- open-ended plans with explicit continuation;
- optional symbolic validation or optimisation.

## 8. How the existing plan backlog should change

The current planning tasks should be replaced or narrowed:

- Existing `PLAN-001` becomes only the base plan schema task.
- Existing `PLAN-002` becomes abstract plan verification, not a prerequisite for all runtime planning.
- Existing `PLAN-003` remains the later optimisation task.

Dynamic-plan runtime tasks must be added for action binding, continuation patches, planner ports, plan execution, provenance, mediation, code sandboxing, trace events, deterministic and real planners, adversarial tests, SLED integration and experiments.

The accompanying JSON defines `PLAN-DYN-000` through `PLAN-DYN-017`. The critical implementation order is:

1. Fix proposal modes, authority terminology, trace return and canonical kernel.
2. Define action grounding, plans and patches.
3. Implement a deterministic plan executor and scripted planner.
4. Integrate every grounded effect with the kernel.
5. Add code execution under a capability envelope.
6. Add a deterministic demo and plan-specific tests.
7. Add a real structured LLM planner.
8. Add worst-case SLED planning semantics and formal abstractions.
9. Add authority-aware optimisation.

## 9. First defensible planning experiment

The first experiment should compare four configurations on the same tasks:

1. **Reactive:** the model proposes the next action after every observation.
2. **Static plan:** the model produces a complete plan before observations.
3. **Dynamic plan:** the model produces a plan with explicit continuation nodes.
4. **Dynamic plan plus code:** the planner may generate and execute sandboxed code.

Measure separately:

- executed unauthorised effects and reads;
- blocked invalid proposals;
- task completion and safe abort;
- false blocking;
- LLM calls, tokens and latency;
- number and size of plan patches;
- maximum plan depth and node count;
- maximum Principal Context size;
- sensitive observations;
- provider and code failures;
- bound-reached runs;
- replay and trace completeness.

A useful initial task family is repository inspection and repair: inspect files, decide the next diagnostic step, generate a script, execute it in a confined workspace, inspect output, modify a file and run tests. This requires real replanning and code execution while retaining a clear provider boundary.

## 10. Main recommendations

1. Keep semantic repair and the canonical kernel as the immediate P0 work.
2. Introduce dynamic planning immediately after the deterministic vertical slice, rather than waiting for the whole SLED-V stack.
3. Keep plan verification and optimisation after SLED-MC/SLED-V contracts stabilise.
4. Treat arbitrary code as a mediated operation with a capability envelope, not as an exception to the security model.
5. Never let replanning reset provenance or authority context.
6. Update the paper from “replanning only in a preverified envelope” to “open-ended replanning with per-effect mediation; verification is bounded or abstract when necessary.”
7. Consolidate all reports into one lifecycle-controlled task registry with evidence links and supersession metadata.
8. Do not begin headline experiments until current result JSON, raw traces, negative controls and environment/model/source snapshots are reproducible.

## 11. Sources inspected

Repository sources:

- <https://github.com/RayaBuckley/Conflux/>
- `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/MVP_RESULTS.md`
- `reports/REPO_REVIEW`, `reports/SLED_REVIEW`, the literature/research reports, and `reports/New/*`
- `src/conflux/core/actions.py`, `src/conflux/ports/model.py`, `src/conflux/application/mediate.py`, `src/conflux/ites/mediator.py`, `src/conflux/auth/authorisation.py`

Primary planning references:

- CaMeL, *Defeating Prompt Injections by Design*: <https://arxiv.org/abs/2503.18813>
- ReAct: <https://arxiv.org/abs/2210.03629>
- ReWOO: <https://arxiv.org/abs/2305.18323>
- LLM+P: <https://arxiv.org/abs/2304.11477>
