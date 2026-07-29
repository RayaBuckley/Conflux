# Conflux: Principal-Context Security, Evaluation and Verification for LLM Agents

**Work-in-progress fourth-year paper draft — 29 July 2026**

This manuscript is intentionally separate from the archived paper in `paper/`. It records work completed and planned during the fourth-year extension. Experimental placeholders are marked explicitly and must be replaced only by generated results from the current repository.

## Abstract

Large-language-model agents combine information from users, documents, tools and persistent services while performing externally visible actions. A system that executes every action with the authority of the initiating user can therefore allow information controlled by a lower-authority principal to influence a higher-authority operation. Previous work introduced Influence Tracking with Extrapolated Security (ITES), which accumulates the principals that may have influenced an execution and permits an action only when each such principal is authorised for it. It also introduced the System-Level Evaluator for Defences (SLED), a bounded exhaustive evaluator for worst-case model behaviour.

This fourth-year project develops those ideas into Conflux, a provider- and benchmark-independent research framework for principal-aware agent security. Work to date has decomposed the original prototype into immutable provenance-bearing artefacts, typed actions and resources, mediation and policy components, provider adapters, benchmark/evaluation abstractions, versioned trace records and an explicit clean-architecture migration layer. A repository audit, however, also reveals that architectural breadth has outpaced executable evidence: the rich mediator and normative MVP have overlapping semantics; read entitlement is not consistently separated from provenance; empty principal contexts require fail-closed treatment; external benchmark adapters lack pinned upstream fixtures; and the current result document remains a template rather than a new run.

The project therefore reframes its immediate contribution around a single executable security kernel, complete mediation traces, reproducible evaluation, and formal verification. The proposed SLED-V extension compiles a restricted white-box defence model into a transition system and returns `SAFE`, `UNSAFE`, `BOUNDED-SAFE`, or `UNKNOWN` with proof or counterexample artefacts. A complementary planning direction treats secure task completion as controller synthesis under authority constraints. This paper reports the implementation state, specifies the remaining work required for result-ready ITES/SLED and AgentDojo experiments, and defines the evaluation methodology for the forthcoming empirical and verification results.

## 1. Introduction

LLM agents process natural-language inputs whose provenance and authority differ. A user request, an email body, a retrieved web page and a tool result may all appear in the same model context, even though each is controlled by a different principal. Model-level prompt-injection defences attempt to make the model distinguish intended instructions from adversarial content, but their guarantees remain empirical and dependent on model behaviour. A system-level alternative is to assume that any processed information may influence the model and to constrain the resulting authority externally.

The previous project formalised this idea as ITES. For an execution influenced by principal set \(I\), ITES authorises action \(a\) exactly when

\[
  \forall p \in I,\; P(p,a),
\]

where \(P\) is the organisation's authorisation relation. Effective authority is therefore the intersection of the permissions of all influencing principals. If influence only accumulates, authority cannot increase. The previous project also introduced SLED, which treats the model as a nondeterministic black box and enumerates possible proposal sequences under a depth bound.

The fourth-year project has a broader engineering and research objective: turn the prototype into a framework that can be executed against real models and benchmark environments, while making the relationship between the formal security argument, the implementation and the evaluation explicit. The repository has made substantial progress toward that goal, but the central implementation challenge is no longer file decomposition. It is semantic consolidation and evidence.

This paper makes four intended contributions, subject to the completion and evaluation described later:

1. A canonical principal-context security kernel separating provenance, read policy, authorisation, consent and visibility.
2. A reproducible evaluation path from deterministic SLED environments to real-model and AgentDojo experiments.
3. SLED-MC and SLED-V, which replace bounded trace enumeration with state-based model checking and solver-backed verification over a declared model.
4. Authority-constrained planning, formulated as secure controller synthesis rather than unrestricted model-directed replanning.

## 2. Previous-year contribution and archived evidence

The archived project report and preprint introduced the access-control structure \((A,U,D,P,W,R)\), where \(P\) defines action permissions, \(W\) represents authorship or possible writers and \(R\) defines read access. ITES forms an execution's influence set from the provenance of its inputs and intersects the permissions of those principals. A separate read rule requires current influencers to be authorised to read proposed nested inputs.

The archived evaluator explored approximately 1.46 million bounded traces across three synthetic environments at maximum recursive depth three. It reported no successful privilege escalation or information-exfiltration violation and preserved the modelled secure goal actions. A material fraction of traces reached the depth bound and was excluded from the subsequent counts. These results are evidence about the previous prototype and its stated environments. They are not automatically evidence about the refactored Conflux repository.

The archived paper must therefore remain immutable. The current project will first reproduce the legacy experiment as a named compatibility suite, then run a corrected canonical suite. Any change in semantics, environment generation, trace classification or incomplete-case treatment will be reported rather than hidden behind a direct headline comparison.

## 3. Related work and revised positioning

System-level agent security now includes several approaches that constrain tool use, execution plans, provenance or causal history. CaMeL separates privileged planning from untrusted-data processing and enforces developer policies in a custom interpreter. Dual-LLM designs similarly isolate a privileged planner from quarantined processing. More recent systems such as Progent, PACT and PCAS/FORGE contribute argument-sensitive policy checking, finer-grained provenance or causal dependency graphs. These systems make it inappropriate to claim that Conflux is the first system-level, provenance-based or privilege-oriented agent defence.

The narrower proposed contribution is a principal-context calculus that derives collective authority from authenticated provenance and an existing authorisation system, while treating delegation, confidentiality, consent, safety and visibility as distinct mechanisms. This distinction matters. Provenance records who may have influenced a value; it is not itself a read ACL. Authorisation records whether an operation is institutionally permitted; it is not consent. A causal graph can be finer-grained than a whole-call principal set, but it still needs a rule for combining authority when multiple principals contribute to an authority-bearing argument.

Conflux also differs in its intended evaluation target. Behavioural benchmarks such as AgentDojo execute finite tasks and attacks, which is valuable for realism and model utility. SLED's intended role is to evaluate a declared system-level enforcement model under arbitrary well-typed model proposals. The two approaches are complementary: external benchmarks test practical integration and utility, while SLED-V can prove properties only of the explicit abstraction and assumptions it receives.

## 4. Conflux architecture

### 4.1 Domain model

The repository now contains immutable principals, permissions, resources, provenance objects, artefacts and typed action families. A canonical `DataItem` separates authors from readers and can be materialised as a provenance-bearing artefact. `EnvironmentSnapshot` provides a provider-neutral environment boundary. Additional values represent sessions, consent profiles, visibility policy, action decisions and evaluation traces.

This decomposition is a substantial improvement over the original single-file prototype. It enables independent tests, typed boundaries and adapters for providers or benchmarks. It also creates a migration problem: legacy evaluation `Data`/`Environment` types, canonical domain types and compatibility translations currently coexist. The target architecture permits conversion only at ingress. The security kernel and all supported adapters then operate on the canonical types.

### 4.2 Security decisions

The canonical mediation path must make five decisions explicitly:

1. **Provenance propagation:** which principals and resources may have influenced each artefact.
2. **Read policy:** whether the current principal context may observe a candidate input.
3. **Action authorisation:** whether every constraining principal is authorised for the parameterised action.
4. **Consent:** whether automatic execution is accepted by the relevant decision principals.
5. **Visibility:** whether the action or output may be observed in the current channel.

The implementation must preserve their evidence separately in the trace. A single Boolean “allowed” result is insufficient for research analysis and operational audit.

### 4.3 Proposal semantics

The current rich mediator accepts a set of proposals, but a set does not distinguish alternatives from a plan. Conflux will introduce an explicit `ProposalBatch`:

- `ALTERNATIVES` creates independent branches from the same parent state;
- `ORDERED_PLAN` executes a deterministic sequence with state propagation.

This resolves ambiguity around sibling isolation, shared call budgets and ordering. It also gives SLED a well-defined transition relation and allows real models to return structured plans without relying on Python hash order.

### 4.4 Complete mediation and traceability

Every proposal, including malformed and blocked proposals, will produce a trace event. A result records the environment, policy, model and software snapshots; causal branch identifiers; decisions; provider effects; bounds; and raw trace checksum. Security invariants will describe executed effects, while separate diagnostics count attempted invalid proposals. This prevents the current error in which a securely blocked attack can make a reported “guarantee” false.

## 5. Implementation audit

### 5.1 Work completed

The current repository has implemented or scaffolded:

- immutable provenance-bearing values and action taxonomy;
- a rich ITES mediator and immutable execution state;
- a small executable MVP semantics under a research namespace;
- one-shot and bounded exhaustive evaluation paths;
- representative-environment compression;
- trace, classification, statistics and reporting models;
- filesystem and Docker provider prototypes;
- a partial AWS-style policy adapter;
- native and external benchmark adapter boundaries;
- strict type/lint configuration and a repository audit ledger;
- documentation for architecture, evaluation and AI-assisted development.

### 5.2 Correctness gaps discovered

The audit identified several issues that must be fixed before new results:

- Empty principal sets pass intersection checks by vacuous truth.
- The action authoriser can treat provenance principals as readers despite the canonical model having an independent reader relation.
- A shape-dependent owner branch can bypass permission evaluation.
- Default consent grants every permission already held by each participant.
- The mediator overwrites model-provided decision principals with the full influence set without distinguishing conservative authority context from exact causal provenance.
- Rich proposal iteration is unordered and recursive branches update shared aggregate state.
- A blocked invalid proposal can make a reported security guarantee false.
- The detailed `ExecutionState` trace is not returned in the final ITES report.

These findings do not refute the abstract ITES intersection theorem. They show why the fourth-year contribution must include implementation conformance rather than assuming that a refactoring preserves the abstract model.

### 5.3 Integration gaps

The package has no required runtime dependencies, no console entry point and no implemented model adapter in the canonical adapter directory. The application mediation service is a thin delegate. The current AgentDojo-facing types are primarily Conflux-native environment wrappers; external wrappers depend on configurable commands and heuristic output translation. Providers still materialise legacy environment structures. The checked-in MVP result file remains a template pending an executable run.

The first engineering milestone is therefore an end-to-end vertical slice rather than another abstraction layer.

## 6. Result-ready runtime

The first supported runtime will use a deterministic scripted model and a temporary sandbox provider. A scenario file defines principals, data, readers, permissions and allowed operations. The model returns a strict JSON proposal batch. The security kernel evaluates each proposal, the provider executes allowed effects, and the runtime writes a JSONL trace and versioned result.

The CLI will expose:

```text
conflux demo
conflux chat
conflux sled run
conflux verify
conflux benchmark agentdojo
conflux report
conflux doctor
```

A generic OpenAI-compatible HTTP adapter will provide the first real-model path. A Hugging Face adapter will be optional because local hardware and model dependencies should not affect core correctness tests. Malformed model output, unknown resources and unsupported actions fail closed.

## 7. Evaluation methodology

### 7.1 Deterministic semantic evaluation

A table-driven semantic corpus will test the same restricted behaviours against the executable specification and the canonical kernel. Cases include empty contexts, mixed permissions, separate authors/readers, nested accumulation, branch isolation, consent, visibility, delegation, policy revocation and provider errors.

Negative-control defences are essential. The evaluator must find violations for union-permission, initiator-only, latest-input-only and no-read-check baselines. A tool that only reports ITES as secure has not demonstrated that it can detect an incorrect defence.

### 7.2 Native SLED experiments

The historical environments will be translated into versioned fixtures. Two suites will be retained:

- `legacy-reproduction`, preserving the previous prototype assumptions;
- `canonical`, using corrected semantics and current trace/result schemas.

The primary metrics are:

- unauthorised effects executed;
- unauthorised reads performed;
- visible confidentiality violations;
- secure task reachability;
- false blocking;
- incomplete/bound-reached states;
- calls, transitions, unique states, memory and runtime.

Invalid proposals observed are diagnostics, not security failures.

### 7.3 Real-model experiments

Real-model runs measure practical utility and attack behaviour, not the core worst-case guarantee. The manifest records endpoint/provider, model revision, sampling settings, structured-output method, seed where supported, raw response hash, tokens and latency. Repetitions and confidence intervals are required for stochastic results.

A laptop is sufficient for scripted runs, smoke tests and small quantised models. TorrNodes should be used for repeated large-model experiments or large verification jobs only after a hardware/scheduler probe records the actual environment. No GPU capability is assumed in advance.

### 7.4 AgentDojo

The first external benchmark integration will pin a real AgentDojo revision, preserve upstream task IDs and result artefacts, and explicitly translate users, tools, state, attacks and success criteria. Native AgentDojo utility/security metrics and Conflux trace metrics will both be reported. The provenance and access-control annotations added by Conflux will be documented because they alter the information available to the defence.

## 8. SLED-MC and SLED-V

### 8.1 From traces to states

Current SLED enumerates bounded proposal sequences. Many syntactically different histories can reach the same future-relevant state. SLED-MC will instead perform deterministic breadth-first reachability with a visited-state table and predecessor edges. This supports shortest counterexamples and makes reductions measurable.

A state contains the environment/policy snapshot, authority context, artefact/provenance state, pending plan nodes, memory/delegation state, budgets and relevant observations. Full history is not part of state identity unless the checked policy is history-sensitive.

### 8.2 Verdicts

SLED-V will use explicit verdicts:

- `SAFE`: every state in the declared model satisfies the property;
- `UNSAFE`: a concrete counterexample exists;
- `BOUNDED-SAFE`: no violation exists within a stated bound;
- `UNKNOWN`: unsupported semantics, timeout or abstraction prevents a conclusion;
- `IMPLEMENTATION-CONFORMS`: observed runtime transitions refine the verified model under the stated mapping.

A white-box implementation is not automatically decidable. Conflux will define a restricted verification IR rather than claim to verify arbitrary Python.

### 8.3 Properties

Initial safety properties are:

\[
AG\;\neg\texttt{ExecutedUnauthorisedAction},
\]

\[
AG\;(\texttt{Execute}(a) \Rightarrow \forall p \in PC,\; P(p,a)),
\]

\[
AG\;\neg\texttt{UnauthorisedRead},
\]

and provenance/delegation invariants. Full observational confidentiality is a hyperproperty and will be reported separately from access safety.

The first solver backend will use bounded SMT checking to find short counterexamples. An IC3/PDR-capable backend is the intended route to an unbounded safety result for the finite canonical ITES model. Proof artefacts, solver versions and model hashes will be retained.

### 8.4 Implementation conformance

A proof about a model is not a proof about Python. The runtime will emit transition records that can be translated into the verification IR. Differential tests will apply identical states and actions to the kernel and model. Formal claims will remain model-scoped until this conformance layer passes.

## 9. Authority-constrained planning

Under a fully adversarial model assumption, universal task completion is impossible because the model may always return no useful proposal. Utility should therefore be divided into:

- possible secure completion;
- controller-achievable completion under all modelled provider outcomes;
- benign-model completion under an explicit competence contract.

A typed planner will propose a graph whose nodes contain operation, arguments, preconditions, outcomes, required reads/permissions and compensation. Security is a hard constraint. The optimiser then minimises authority footprint, sensitive observations, calls, latency and irreversible effects.

Error recovery is part of the plan. `PermissionDenied` may lead to safe abort, approval request or a predeclared lower-authority alternative; it must not cause an unconstrained search for stronger credentials. Runtime replanning is permitted only inside a previously verified envelope or after re-verification.

## 10. Expected experiments

The intended fourth-year research questions are:

1. How much do state memoisation, symmetry, partial-order reduction and authority-aware subsumption reduce SLED's state space?
2. Can an IC3/PDR backend prove the finite ITES privilege-escalation invariant without a recursion-depth bound?
3. Can runtime traces be shown to conform to the verified transition relation?
4. How do corrected principal-context semantics affect security and secure-task utility relative to the archived prototype?
5. How does ITES perform on an explicitly annotated AgentDojo subset relative to no-defence and selected system-level baselines?
6. Does authority-minimising planning reduce unnecessary observations and false blocking without weakening security?
7. Which forms of delegation, memory and policy mutation remain within a decidable or practically verifiable subset?

## 11. Results

### 11.1 Repository validation

**TODO generated result:** current commit, platform, test count, coverage, mypy, Ruff and audit outcomes.

### 11.2 Semantic conformance

**TODO generated result:** corpus size, kernel/MVP agreement, discovered counterexamples and resolved defects.

### 11.3 Native SLED

**TODO generated tables:** legacy reproduction, canonical suite, negative controls, incomplete states and performance.

### 11.4 SLED-MC/SLED-V

**TODO generated tables:** unique states versus traces, runtime/memory, bounded and unbounded verdicts, proof/counterexample artefacts.

### 11.5 Real models and AgentDojo

**TODO generated tables:** model configurations, utility, attack outcomes, policy blocks, parser failures, cost/latency and confidence intervals.

No numerical claim should be added to this section by hand. Tables should be generated from versioned result JSON files.

## 12. Limitations

ITES assumes sound principal authentication, provenance tracking, policy state and complete mediation. It does not prevent harmful actions that every influencing principal is already authorised to perform, nor does it guarantee alignment with subjective user intent. A conservative principal context may over-approximate causal influence and block useful tasks. Delegation can intentionally increase usable authority and therefore requires its own scoped semantics. Access safety does not by itself establish noninterference. Formal verification is only as strong as the declared transition model and implementation-conformance evidence. External benchmarks remain finite empirical evaluations, and provenance annotations can change their threat model.

Provider prototypes are not production isolation boundaries. In particular, Docker access can imply broad host authority. Production execution would require least-privilege credentials, capability tokens, idempotency, approval state, transaction/compensation, tenant isolation and tamper-evident audit storage.

## 13. Project plan

The implementation order is:

1. Record a reproducible baseline and freeze the archived paper.
2. Repair empty-context, read-policy, guarantee, proposal and trace semantics.
3. Consolidate one canonical runtime and remove compatibility imports from supported paths.
4. Deliver an interactive scripted-model vertical slice.
5. Reproduce a small native SLED result with negative controls.
6. Add state-based SLED-MC.
7. Add a real-model adapter.
8. Integrate a pinned AgentDojo subset.
9. Add SLED-V's verification IR and SMT backend.
10. Add controller synthesis and authority-minimising planning.

## 14. Conclusion

Conflux has advanced from a monolithic prototype to a broad research architecture, but its next contribution depends on consolidation rather than further scaffolding. The immediate goal is a single principal-context security kernel with correct read and empty-context semantics, explicit proposal modes, complete traces and reproducible experiments. This foundation enables two complementary evaluation paths: realistic model/benchmark experiments and formal verification over a restricted transition model. The resulting project can make stronger and more precise claims than either a finite attack benchmark or a large bounded trace count alone, while remaining explicit about assumptions, abstractions and implementation evidence.
