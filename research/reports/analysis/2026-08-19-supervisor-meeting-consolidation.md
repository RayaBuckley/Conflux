# Supervisor Meeting Consolidation

**Date:** 19 August 2026
**Status:** Meeting preparation; not a canonical specification
**Source:** Consolidation of canonical status, claims, task registry, and analysis reports
**Canonical owners:** Implementation status in [STATUS.md](../../../docs/evidence/STATUS.md); claim strength in [CLAIMS.md](../../../docs/evidence/CLAIMS.md); programme disposition in [task-registry.json](../../../docs/evidence/task-registry.json); formal verification in [SLED.md](../../../docs/reference/SLED.md); evaluation evidence in [EVALUATION.md](../../../docs/evidence/EVALUATION.md)

## 1. Project summary

Conflux is a research framework for principal-aware security in AI agents.
The core idea: when an LLM agent consumes information from multiple
principals, effective authority should be the intersection of all
influencing principals' permissions, not the requester's alone.

The central security rule:

    Allow(a, PC) iff PC ≠ ∅ ∧ ∀ p ∈ PC: ACSAllows(p, a)

The threat model is deliberately stronger than prompt-injection
evaluation: information supplied to an LLM may arbitrarily influence its
subsequent behaviour, so the security mechanism must not depend on the
model correctly recognising malicious instructions. Prompt injection is
one mechanism for creating influence; it is not itself the security
property. Privilege escalation — an action executed when at least one
influencing principal lacks permission — is the system-level security
objective.

## 2. Completed work

Work is organised by claim-strength hierarchy: implemented, bounded
evidence, evaluation ready, and deferred.

### 2.1 Canonical security migration (P0 repair) — implemented

- Immutable domain values: Principals, Principal Context, provenance,
  actions, resources, sessions, decisions
- Single pure ITES transition kernel with complete mediation
- Principal Context derived from trusted provenance at action time
- Four independent policy dimensions: authorisation, read, visibility,
  consent
- Legacy `core`, `auth`, `research`, and `compatibility` surfaces removed
- Five deliberately defective negative controls, each with one-step
  counterexamples

**Evidence:** [SECURITY_MODEL.md](../../../docs/reference/SECURITY_MODEL.md),
[tests/semantics/](../../../tests/semantics/),
[tests/test_policy_and_ites.py](../../../tests/test_policy_and_ites.py),
[NEGATIVE_CONTROLS.md](../../../docs/evidence/NEGATIVE_CONTROLS.md)

### 2.2 Offline result-ready path — implemented

- Certificate-bound execution for alternatives and ordered plans
- Authenticated open-ended dynamic planning: catalogues, immutable
  patches, explicit loops, subplans, bounded continuation, action-time
  re-authorisation
- Generated code is inert `ModeledProgram` data submitted to a
  capability-constrained container; fails closed when sandbox unavailable
- Deterministic scenarios, traces, schemas, manifests, negative
  controls, resumable jobs

**Evidence:** [Spec 015](../../../docs/decisions/015-open-ended-dynamic-planning.md),
[tests/planning/](../../../tests/planning/),
[output/runs/smoke/](../../../research/output/runs/smoke/)

### 2.3 Native SLED verification — bounded evidence

- Breadth-first explicit-state checker with canonical-state memoisation
- Explicit bounds (depth, state, transition, model-call); shortest
  counterexamples
- Retained native reproduction: three fixture pairs, detects all five
  seeded monitor defects with one-step witnesses, 60 transitions
- Legacy ~1.5 million-trace count retained as historical but marked
  non-comparable (different semantics: canonical states vs. trace
  enumeration)

**Evidence:** [output/runs/native-sled-reproduction-v1/](../../../research/output/runs/native-sled-reproduction-v1/),
linked to commit `d6d9857954ac`

### 2.4 Serialisable verification IR + COI reduction — bounded evidence

- Callback-free IR with reference interpreter, runtime differential
  tests
- Optional Z3 bounded model checking — confirmed equivalence on four IR
  fixtures (safe: bounded safe, unsafe: counterexample found and lifted)
- nuXmv Boolean-subset adapter (returns `UNKNOWN` when unsupported)
- Property-scoped COI reduction: closes over guards/assignment
  dependencies, preserves rule IDs, original/reduced verdicts agree, one
  lifted unsafe witness
- Z3 BMC with COI reduction confirmed equivalence on both safe and unsafe
  fixtures; reduced safe model drops one variable and one rule; reduced
  unsafe model lifts the counterexample

**Evidence:** [output/runs/sled-coi-reduction-v1/](../../../research/output/runs/sled-coi-reduction-v1/),
[output/runs/z3-agreement-v1/](../../../research/output/runs/z3-agreement-v1/)

### 2.5 Security extensions (Spec 013) — implemented

- **Argument-level policy:** trusted operation schemas assign immutable
  argument roles; authority-bearing selectors checked pointwise for
  every Principal; model output cannot assign roles
- **Event disclosure:** audience-specific levels (none/existence/
  redacted/full), deterministic projection
- **Structured attribution:** evidence-derived from provenance/context/
  policy; model explanations explicitly untrusted
- **Scoped delegation model:** exact, expiring, revocable, one-use grants
  with deterministic lifecycle evidence and seven killed mutants;
  operational delegation unconditionally denied pending activation
- **Cedar adapter (v4.12.0):** strict differential corpus, PARC
  translation, binary-identity preflight; Cedar not invoked, parity not
  claimed

**Evidence:** [output/runs/direction-readiness-v1/security-mutations.json](../../../research/output/runs/direction-readiness-v1/security-mutations.json),
[output/runs/cedar-differential-preflight-v1/](../../../research/output/runs/cedar-differential-preflight-v1/)

### 2.6 AgentDojo integration — implemented / bounded evidence (model-failed)

- Pinned AgentDojo 0.1.35 / benchmark v1.2.2 boundary
- Six-cell local runner (benign/attacked × no-defence/conservative-ITES/
  oracle)
- Fake-backed conformance passes
- Qwen2.5-1.5B-Instruct: all six cells `model_failed` (1.5B model wraps
  JSON in markdown fences, preventing structured tool-call parsing)
- Qwen2.5-7B-Instruct NF4: single cell validated (status=complete,
  security=True, utility=False, model_calls=4); full comparison deferred
  to GPU availability
- Raw upstream trace retained (47s benign inference)

**Evidence:** [output/runs/agentdojo-1b5-nf4-v1/](../../../research/output/runs/agentdojo-1b5-nf4-v1/),
[experiments/agentdojo.lock](../../experiments/agentdojo.lock),
[tests/test_agentdojo_runner.py](../../../tests/test_agentdojo_runner.py)

### 2.7 Planning comparison — implemented / bounded evidence (model-failed)

- Four-mode planning: reactive, static, dynamic, dynamic_code
- 32-cell runner, inert ModeledProgram validation
- Qwen2.5-1.5B-Instruct: all eight cells `model_failed` (same JSON
  parse issue)
- Offline modeled fixtures are mechanics evidence only

**Evidence:** [output/runs/planning-pilot-1b5-v1/](../../../research/output/runs/planning-pilot-1b5-v1/),
[tests/test_planning_runner.py](../../../tests/test_planning_runner.py)

### 2.8 Model adapters — evaluation ready

- Self-hosted OpenAI-compatible and Transformers model ports
- Strict identity, network (loopback default), local-cache,
  structured-output contracts
- No hosted-service fallback; CI uses fakes and downloads nothing

**Evidence:** [src/conflux/adapters/models/](../../../src/conflux/adapters/models/),
[tests/test_local_models.py](../../../tests/test_local_models.py)

### 2.9 Foundational literature integration — partial

- Classical IFC/integrity lineage identified and integrated across
  documentation (Biba, LOMAC, Denning, Sabelfeld & Myers, Myers & Liskov
  Dec-IFC, declassification, endorsement, noninterference)
- **Novelty audit:** 15 claims assessed — 3 survive, 8 partially
  anticipated, 1 survives as math, 3 survive as non-claims/provisional
- **Literature matrix:** 9 Priority A works, 6 Priority B, 5 Priority C
- **Observational confidentiality design:** self-composition approach
  via product IR + Z3 BMC (designed, not implemented)
- 7 unsafe claim formulations identified and documented
- Primary-source bibliography verification still deferred

**Evidence:** [2026-08-13-foundational-security-literature.md](2026-08-13-foundational-security-literature.md),
[2026-08-16-novelty-audit.md](2026-08-16-novelty-audit.md),
[2026-08-16-literature-matrix.md](2026-08-16-literature-matrix.md),
[2026-08-16-observational-confidentiality-design.md](2026-08-16-observational-confidentiality-design.md)

### 2.10 Formal semantics and property-based testing — implemented

- Expanded semantic corpus, mutants, and mutation-killing tests
- Hypothesis property-based tests for domain algebraic laws
- Adversarial fixtures (Mallory scenario)
- WSL-based nuXmv runner added

**Evidence:** Commits `479a129`, `3c4520f`, `5fdd60c`, `c132528`;
[tests/semantics/](../../../tests/semantics/)

### 2.11 Baseline validation — implemented

- 31 July 2026 baseline at commit `6fe6b584500e`: 416 tests (current),
  90.25% branch coverage (baseline snapshot)
- All 13 JSON Schema checks, deterministic regeneration, Ruff, strict
  mypy, wheel build, CLI smoke
- Cross-platform CI: all four OS/Python combinations passed
- Manuscript CI: passed

**Evidence:** [output/validation/6fe6b584500e/](../../../research/output/validation/6fe6b584500e/),
[BASELINE_2026-07.md](../../../docs/evidence/BASELINE_2026-07.md)

## 3. Claim strength summary

| Category | Status | Key limitation |
|---|---|---|
| Core ITES security invariants | Implemented | Assumes correct provenance, ACS, complete mediation |
| Native SLED counterexamples | Bounded evidence | Finite fixtures only; not deployment security |
| COI reduction preserves verdicts | Bounded evidence | Two IR fixtures; optional solver unavailable |
| Z3 BMC agrees with reference interpreter | Bounded evidence | Four IR fixtures; bounded only |
| AgentDojo efficacy | Bounded evidence (model-failed) | 1.5B model can't parse JSON; 7B single-cell only |
| Planning utility | Bounded evidence (model-failed) | Same model issue; offline fixtures only |
| Cedar parity | Evaluation ready | Cedar not invoked; no parity claim |
| Delegation activation | Implemented model, runtime disabled | Requires Cedar parity + all gates |
| Maximal permissiveness (RQ1) | Theorem survives | Correct within PE definition; not a novelty claim |
| Unbounded verification (RQ2) | Not established | Finite bounds only; no IC3/PDR backend |
| Comparative defence verification (RQ3) | Research design only | No defences modelled yet |
| Observational confidentiality (RQ7) | Designed | Self-composition approach; not implemented |
| Implementation conformance (RQ9) | Not established | No conformance/replay layer |

## 4. Planned work (prioritised)

### P1: Live model evidence (immediate)

- Dual-backend laptop smoke (16-cell protocol ready, operator-gated) —
  integration check, not efficacy
- AgentDojo full six-cell comparison with 7B+ model or
  output-constraining post-processing
- Four-mode planning comparison with a capable model
- Each live run must retain exact model/runtime identities, raw traces,
  checksums, and failures

### P2: Cedar differential execution

- Run pinned Cedar 4.12.0 binary against retained differential corpus
- Establish parity or identify disagreements with the in-memory oracle
- This is the gate for delegation activation

### P3: Formal verification extensions

- Implement observational confidentiality self-composition (design
  complete, tractable for existing fixtures: ≤16 product states)
- Obtain IC3/PDR-capable backend for unbounded verification (nuXmv via
  WSL runner exists)
- Reduction ablations: partial-order reduction, Principal symmetry,
  authority-aware subsumption (each needs preservation argument)
- Controller synthesis experiment on finite instances — synthesise
  maximally permissive safe controller, compare with ITES

### P4: Comparative defence verification

- Model one contemporary defence deeply (CaMeL preferred if semantics
  sufficiently available, or Dual-LLM baseline)
- Verify defence's own intended property + check Conflux PE
- Retain minimal counterexamples where properties differ
- Depth over breadth

### P5: Literature and novelty

- Primary-source bibliography verification (Priority A entries)
- Targeted prior-art searches: Dec-IFC with organisational authority,
  compound-principal authorization, low-water-mark over permission sets
- Manuscript structural revision (requires operator gate after
  primary-source reading)

### P6: Security model extensions

- Richer operation-specific argument-effect semantics beyond selector
  authorisation
- Origin-bound persistent-memory authority
- Delegation activation (gated on Cedar parity + all certificate/
  visibility/attribution/expiry/revocation gates)

## 5. Key decisions for supervisor

1. **Model strategy:** The 1.5B model is too small for structured output.
   Options: (a) get GPU access for a 7B+ model, (b) implement
   markdown-fence stripping post-processing for smaller models (commit
   `750eb76` already strips fences in the Transformers adapter — verify
   whether this resolves the issue), or (c) use a cloud API for
   structured-output experiments only.

2. **Thesis scope:** The suggested thesis core is RQ1 + RQ2 + (RQ3 or
   RQ4) + empirical support from RQ5/AgentDojo. Should observational
   confidentiality (RQ7) be promoted given the design work is complete?

3. **Cedar/delegation:** Is Cedar parity + delegation activation a thesis
   milestone or future work? The infrastructure is ready but the binary
   hasn't been run.

4. **Comparative verification:** Which defence to model first — CaMeL
   (richest semantics) or a simpler Dual-LLM baseline?

5. **Novelty framing:** The audit shows the core mechanism is partially
   anticipated by Biba/LOMAC/Dec-IFC. The defensible formulation is
   "applies low-water-mark contamination to AI agents using authenticated
   principal provenance and an existing ACS." Is this framing
   acceptable, or should targeted prior-art searches be completed first?

6. **Next sprint:** Should the next sprint prioritise getting one clean
   live model result, or deepening the formal verification work?

## 6. Honest assessment

### Strengths

- Exceptionally disciplined claim management — every claim points to
  retained evidence with explicit bounds
- Clean architectural separation: domain → ports → application → ITES
  → evaluation/verification
- No fabricated results; unavailable capabilities fail explicitly
- Strong test coverage (416 tests, 90.25% branch coverage at baseline)
  with cross-platform CI
- Foundational literature work is thorough and intellectually honest
  about novelty
- The maximality theorem survives the novelty audit as a mathematical
  result

### Gaps

- No successful live model evaluation (the biggest risk for a compelling
  thesis)
- No unbounded verification result (RQ2 remains open)
- No comparative defence has been modelled (RQ3 is research design only)
- Cedar parity not established (delegation activation blocked)
- Primary-source literature verification deferred
- The manuscript has "generated result pending" placeholders

### Recommended next sprint priorities

1. Get one clean AgentDojo result with a 7B+ model (even partial)
2. Execute the Cedar differential (infrastructure is ready)
3. Implement the observational confidentiality self-composition (design
   is complete, tractable)
4. Begin modelling CaMeL for comparative verification

## 7. Questions to ask at the meeting

### Formal methods

- Is maximal permissiveness best framed through supervisory control,
  safety games, or another formalism?
- Which backend is best suited to unbounded finite-state safety here:
  IC3/PDR, BDDs, k-induction, custom SMT?
- Can Principal-Context monotonicity justify an antichain/subsumption
  relation?
- What is required to prove a partial-order or symmetry reduction sound?

### Security / IFC

- Is Principal Context best understood as an integrity label,
  provenance set, authority context, or a combination?
- Which Biba/LOMAC/declassification/endorsement results transfer cleanly?
- How should explicit delegation be formalised without undermining the
  base invariant?
- What observation model is needed for confidentiality/noninterference?

### LLM-agent security

- Which contemporary defence has sufficiently precise semantics to model
  faithfully?
- Which AgentDojo tasks expose meaningful authority distinctions?
- Which real workflows distinguish PE prevention from prompt-injection
  prevention?
- What baseline would make a comparative result credible?

## 8. What to avoid spending the meeting on

- Source-tree naming
- Broad productionisation
- Speculative cloud integrations
- Adding many benchmarks
- Minor documentation formatting

The useful output is criticism of the threat model, theorem,
formalisation, experimental design, and comparison methodology.

## Relationship to existing documentation

This consolidation is consistent with and folds in:

- [STATUS.md](../../../docs/evidence/STATUS.md) — implementation status
- [CLAIMS.md](../../../docs/evidence/CLAIMS.md) — claim strength and novelty
  qualification
- [task-registry.json](../../../docs/evidence/task-registry.json) — programme
  disposition
- [RESEARCH_OVERVIEW.md](../../../docs/research/RESEARCH_OVERVIEW.md) — research
  problem and direction
- [RESEARCH_QUESTIONS.md](../../../docs/research/RESEARCH_QUESTIONS.md) — RQ
  prioritisation
- [SLED.md](../../../docs/reference/SLED.md) — verification and property hierarchy
- [EVALUATION.md](../../../docs/evidence/EVALUATION.md) — evaluation evidence
  boundary
- [REVIEWER_MEETING_CHECKLIST.md](REVIEWER_MEETING_CHECKLIST.md) —
  original meeting preparation checklist
- [MAXIMAL_SECURITY_AND_SYNTHESIS.md](MAXIMAL_SECURITY_AND_SYNTHESIS.md)
  — maximality formalisation
- [COMPARATIVE_DEFENCE_VERIFICATION.md](COMPARATIVE_DEFENCE_VERIFICATION.md)
  — comparative defence research design
- [RESULTS_AND_EXPERIMENT_PLAN.md](RESULTS_AND_EXPERIMENT_PLAN.md) —
  experiment programme
- [2026-08-16-novelty-audit.md](2026-08-16-novelty-audit.md) — novelty
  risk assessment
- [2026-08-16-literature-matrix.md](2026-08-16-literature-matrix.md) —
  classical literature comparison
- [2026-08-16-observational-confidentiality-design.md](2026-08-16-observational-confidentiality-design.md)
  — confidentiality verification design
