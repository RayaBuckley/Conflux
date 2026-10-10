# Contribution provenance: Part B (third year) and Part C (fourth year)

- Type: evidence
- Status: generated
- Date: 2026-10-09
- Decision: [ADR 026](../decisions/026-continuation-and-contribution-provenance.md)
- Source: [`CLAIMS.md`](CLAIMS.md)

## Why this file exists

The fourth-year project (Part C) continues the third-year project (Part B) on the
same research line. The examiner of the fourth-year report must be able to see
which parts of the submitted work are third-year contributions and which are
fourth-year contributions. Presenting Part B results as new work would be a
misrepresentation; hiding the continuation would understate what Part C adds.

Paper submissions are different. A submission may present both phases as one
contribution, because the venue judges the contribution rather than the year in
which it was produced. Such a submission still states what was published or
submitted before.

## What Part B established

- The problem formulation: authority amplification through agent tool use, and the
  claim that provenance, not request provenance, should decide authority.
- ITES as a reference monitor, with Principal Context as the unit of authority and
  monotone influence as the invariant.
- SLED as bounded exploration of the induced state space, plus the bounded
  experiment over about 1.46 million traces and the twelve-category task taxonomy.
- The third-year report and preprint, archived under
  `research/reports/archive/2026-06-01-original-prototype/` and
  `research/publications/paper/`.

## What Part C adds

Canonical-state exploration with minimal counterexamples, formal verification
(SLED-V, IR-encoded verification, solver agreement) and the evidence pipeline that
records it, planning with re-authorisation at effect time, finer-grained authority
semantics (ADRs 024 and 025), comparative verification against published defences,
the claim-and-evidence infrastructure, the operational cost guard for the shared
GPU account, and the agent-security empirical programme.

## Reading the table

- `Part B` - established in the third year and cited as prior work.
- `Part B, reproduced` - a Part B result re-executed here, with the archive path in
  the row.
- `Part B concept, Part C evidence` - the mechanism is a third-year contribution and
  the implementation, test or proof in the row was produced in the fourth year. The
  concept is Part B; the evidence is Part C.
- `Part C` - new in the fourth year.

Part B evidence is immutable and stays in the archive. Where a Part C result reuses
a Part B fixture, the row names the archived source.

## Status of the FLMSec 2026 submission

A Part B result was written up during Part C and submitted to the FLMSec 2026
workshop. It was rejected, and the reviews gave two reasons: writing quality, and
limited empirical evidence. The project continues, and both reasons are now Part C
workstreams rather than reasons to resubmit the same text. The rejection is recorded
here so that a later submission can disclose its history honestly.

## The table

<!-- BEGIN GENERATED CONTRIBUTION TABLE -->

### Third-year results reproduced here (2 claims)

| Claim | Status | Evidence and limits |
| --- | --- | --- |
| Part B 1.46M trace reproduction | Bounded historical reproduction | `research/output/runs/native-sled-partb-reproduction-v1/result.json`: all three historical environments reproduce exact trace counts (422,535 + 996,451 + 43,621 = 1,462,607) under depth-three bounds; source: archived prototype `research/reports/archive/2026-06-01-original-prototype/main.py`; canonical-state compression: 1,462,607 raw traces → 31 unique canonical states; incomplete count differs from preprint due to simplified criterion; this is reproduction/conformance, not an unbounded security proof |
| Part B classification counters reproduce under a pinned hash seed | Bounded historical reproduction | `research/output/runs/native-sled-partb-classification-v1/`: the archived prototype classifier walks `frozenset` containers of strings, so its counters depend on `PYTHONHASHSEED`; with the seed pinned the env1 tuple (176,352 secure actions; 352,704 blocked PE; 2,118,454 secure tasks; 75,648 blocked PE tasks; 40,040 incomplete) reproduces at seeds 2 and 13 and the env3 tuple (45,488; 28,852; 141,342; 0; 19,755) at seeds 166 and 299; the env2 tuple is one admissible order sample that was not observed in the retained seeds 0 to 2, while the invariant `6 * incomplete + secure tasks` is constant across every observed seed (2,358,694; 5,710,862; 259,872) and holds for the historical triple; trace totals 1,462,607 match; this is reproduction of an order-dependent counter, not a new measurement |

### Third-year mechanisms with fourth-year evidence (6 claims)

| Claim | Status | Evidence and limits |
| --- | --- | --- |
| Empty/unknown context cannot authorise an effect | Implemented | policy and ITES tests; assumes mediation cannot be bypassed |
| PC(output) ⊇ PC(execution inputs) (no laundering) | Implemented | provenance monotonicity, persistence, and branch isolation tests; ADR 024 |
| Influence is never silently removed by nested execution | Implemented | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | one transition kernel and branch-parent tests |
| ITES preserves PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: ITES reference PE property is bounded\_safe; finite IR model |

### Fourth-year contributions (Part C) (42 claims)

| Claim | Status | Evidence and limits |
| --- | --- | --- |
| External tool output retains authenticated source provenance, not requesting user authority | Implemented | security model and provenance tests; ADR 024 |
| ITES prevents authority amplification but not harm within authorised actions | Implemented (documentation) | authority-vs-harm distinction in security model and papers; ADR 024 |
| Authenticated provenance is in the TCB and does not grant organisational authority | Implemented | security model and threat model documentation; ADR 024 |
| Native SLED returns minimal counterexamples | Implemented within finite model | breadth-first checker tests |
| The current native reproduction detects the seeded monitor defects | Bounded evidence | `research/output/runs/native-sled-reproduction-v1/`: five of five defective monitors, each with a one-step witness; three fixture pairs and fixed finite bounds only |
| Dynamic effects are re-authorised at execution time | Implemented | planning runtime, revocation, certificate, and provider tests. **Replication, not a new mechanism**: arXiv:2610.04975 proves root-task safety for a version-bound witness on every goal-graph mutation with a reserve/commit recheck at one linearisation point, so effect-time re-authorisation is prior art for this row; see [the differentiation analysis](../../research/reports/analysis/2026-10-09-differentiation-threats.md) |
| Authority-bearing action arguments cannot borrow authority from content or consent | Implemented | trusted argument roles, pointwise Principal checks, fail-closed missing policy, and selector mutation tests |
| Redacted event views do not copy hidden payload fields | Implemented | deterministic audience projection and unsafe-redaction/hidden-error mutants; assumes callers use the canonical projector |
| Attribution is evidence-derived rather than model-asserted | Implemented | structured provenance/context/policy records and tests rejecting trusted model explanations |
| Scoped one-use delegation is modeled without activating authority transfer | Implemented model, runtime disabled | exact issuer/beneficiary/operation/resource/argument bindings, expiry, revocation, atomic idempotent consumption, lifecycle projection, and seven one-step mutant witnesses; ITES still denies delegation |
| The argument, disclosure, attribution, and delegation monitors reject their seeded defects | Bounded evidence | `research/output/runs/direction-readiness-v1/security-mutations.json`; the canonical finite models exhaust safely and every retained mutant has a one-transition witness under the recorded bounds |
| The installed offline vertical slice is runnable without credentials | Implemented | `research/output/validation/6fe6b584500e/`: clean-wheel doctor, demo, planning, SLED, and report smoke validation |
| The planning comparison executes no generated code | Implemented | `ModeledProgram` is inert validated data; architecture tests exclude evaluation, compilation, shell, import, and executor paths |
| The optional operational code adapter cannot exceed its declared envelope | Implemented at adapter boundary | container arguments, mount/path checks, and fail-closed sandbox tests; host/container implementation remains in the TCB and is not used by the planning comparison |
| Solver results match the supported runtime subset | Bounded evidence | serialisable IR, interpreter differential tests, optional Z3 backend |
| COI reduction preserves the selected fixture verdicts | Bounded evidence | `research/output/runs/sled-coi-reduction-v1/`: two finite IR fixtures agree under the independent reference interpreter; both reduce variables, rules, or reachable states, and the unsafe witness lifts; Z3 BMC with COI reduction confirms equivalence on both fixtures (safe: bounded safe, unsafe: counterexample found and lifted) |
| Z3 bounded model checking agrees with the reference interpreter | Bounded evidence | `research/output/runs/sled-coi-reduction-v1/`, `research/output/runs/z3-agreement-v1/`, `research/output/runs/coi-scaling-v1/`: Z3 BMC with COI reduction on safe and unsafe IR fixtures; safe models bounded safe, unsafe models produce counterexamples; original and reduced verdicts agree in all cases where the optional Z3 backend is available (`coi-scaling-v1` records `z3_measured` per row and sets `z3_all_agree` to null when no solver answered); scaling to 16 noise variables preserves all verdicts |
| The Cedar adapter is ready for a pinned differential run | Evaluation ready | `research/output/runs/cedar-differential-preflight-v1/` validates the bundle and corpus, translates PARC requests, and records oracle decisions; Cedar cells are explicitly unavailable and establish no parity |
| Cedar decisions match the in-memory oracle | Not yet evidenced | the exact 4.12.0 binary has not completed the retained differential matrix |
| Conflux is secure for unbounded deployments | Not claimed | finite bounds and abstractions do not prove unbounded deployments |
| AgentDojo integration preserves upstream semantics | Implemented for translation | pinned 0.1.35 structures and raw fixture; Conflux annotations are additional assumptions |
| AgentDojo establishes Conflux utility or efficacy | Bounded evidence | Expanded 30-cell matrix (5 tasks x 2 attacks x 3 defences) on 7 models. `research/output/runs/agentdojo-7b-v5/`: Qwen2.5-7B-Instruct NF4, 24/30 utility (80%), 30/30 security, passes >=70% competency gate. `research/output/runs/agentdojo-qwen3-4b-v2/`: Qwen3-4B-2507 NF4, 18/30 utility (60%), 30/30 security — improved from 0% (H100) with latest adapter fixes. `research/output/runs/agentdojo-3b-v4/`: Qwen2.5-3B, 6/30 utility (20%), 26/30 security. `research/output/runs/agentdojo-0b5-v1/`, `agentdojo-lfm2-1b2-v1/`, `agentdojo-granite-2b-v1/`, `agentdojo-llama-3b-v1/`: 0% utility, 100% security where complete. Qwen2.5-1.5B crashed during expanded run. Zero security violations across all completed runs and all models. Prior single-task results (6 cells) at `agentdojo-7b-v4/` showed 100% utility. Stratified selection (`research/experiments/manifests/agentdojo-stratified-selection-v1.json`, 36 strata): the four retained bundles `agentdojo-stratified-{banking,slack,travel,workspace}-v1/` hold 192 cells, 186 complete; at 0.5B every completed cell reports zero utility. The cause differs by suite: the local adapter mediates exactly two operations (`search_emails`, `delete_file`, pinned in `research/experiments/suites/agentdojo-tool-schemas-v1.json`), so cells in banking, slack and travel block on `unsupported_tool` (travel records 90 blocks and slack 6 blocks; the 0.5B banking bundle carries no augmentation stream, only zero utility with 24 utility failures) and their security counts are vacuous for that adapter reason, while the workspace bundle's zero utility follows from 18 `provider_failed` augmentation outcomes (upstream tool errors such as `No emails found`, not model failures; its `failure_counts.model` is 0), 20 blocked calls and 6 `unsupported_arguments` calls. Slack's six incomplete cells are recorded as `model` failures in the bundle and reclassified as parser failures in section 27. The 14B RunPod run measures the same limit directly: `research/output/runs/runpod-h100-14b-stratified/agentdojo-stratified-workspace-v1/` holds 78 cells (77 complete) with utility 1/78 and 156 `unsupported_tool` blocks, and `runpod-h100-14b-stratified/agentdojo-stratified-banking-v1/` holds 24 cells with utility 0 and 192 `unsupported_tool` blocks, recorded as 24 `policy` failures by the pre-fix fold in `agentdojo_local.py` (`cell_failures()` now counts out-of-scope refusals as `adapter`, so the bundles predate that fix). The 14B five-task pilot `research/output/runs/runpod-h100-14b-v1/` is fully mediated: utility 18/30 (60%), security 30/30. The 0.5B banking pilot bundle (12 cells, section 27) repeats protocol-exactly through its `RERUN.txt` command (fingerprint reproduced, zero cell differences). See `docs/evidence/VERIFICATION.md` sections 27-29 and 32. |
| Open-ended planning improves utility | Bounded evidence | `research/output/runs/planning-pilot-7b-v1/`: eight-cell pilot completed with Qwen2.5-7B-Instruct NF4; 7/8 cells `utility_completed=True` (only `blocked-action-recovery:dynamic_code` failed as `modeled_program_failed`); `research/output/runs/planning-pilot-3b-v1/`: 5/8 cells `utility_completed=True` (dynamic_code cells fail — model too small for code generation); `research/output/runs/planning-pilot-1b5-v1/`: all cells `model_failed` (model too small for structured JSON output; `error_detail` captured for each failure); H100 Qwen3-4B-2507 results (commit `a1fa168`, `research/output/runs/runpod-results/runpod-eval/planning/`): 24-cell expanded suite, 19/24 `utility_completed=True`, 4 `provider_failed` (negative-control `provider-failure-no-fallback` task), 1 `bound_reached` (`multi-step-dependency-chain:reactive`), all `security_violations=0`, structured JSON output including `dynamic_code` mode succeeds |
| Self-hosted model output is reproducible across hardware or runtimes | Not claimed | identity and sampling are recorded, but no model-generated bundle or cross-hardware comparison is retained |
| Cloud policy behaviour matches a provider | Not claimed | current AWS adapter is an explicit fail-closed subset |
| The current evidence pipeline handles allow, block, and vulnerable-control cases | Bounded evidence | `research/output/runs/smoke/`, two scripted cases, one one-step negative-control witness |
| Observational confidentiality holds on finite IR fixtures | Bounded evidence | IR self-composition with Z3 BMC; safe fixture bounded safe, unsafe fixture produces counterexample showing observation divergence; bounded to finite product state spaces; not a noninterference proof |
| Dual-LLM candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: Dual-LLM native property (processor never executes) is bounded\_safe; PE property is unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| CaMeL candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: CaMeL native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| Progent candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: Progent native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| PACT candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: PACT native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| ITES defective requester-only controller violates PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: requester-only PE property unsafe with Z3 counterexample; finite IR model |
| Authority confinement does not guarantee semantic appropriateness of authorised choices | Documented semantics | ADR-025; security model distinguishes authority confinement from semantic judgement |
| Model-level defences are genuine empirical security but outside the authority TCB | Documented semantics | ADR-025; model/planner/classifier output cannot grant authority or narrow PC |
| Effective ACS includes only explicit valid delegation; runtime delegation remains disabled | Specified, runtime disabled | ADR-025; scoped delegation model exists but operational delegation is denied |
| SLED-V scaling: COI reduction never causes safe-to-unsafe verdict downgrade | Bounded evidence | `research/output/runs/sledv-scaling-v1/`: 28 fixtures across noise/principal/depth scaling families; no COI verdict downgrade on any fixture; Z3 BMC agrees with reference on all fixtures where Z3 is available; 5 fixtures show bounded_safe→safe upgrade from COI reduction |
| nuXmv IC3 proves the recorded safety invariants on the finite delegation IR subsets | Bounded evidence | `research/output/runs/ic3-unbounded-v1/`: 689 models drawn from the recorded families (rendered at each model's recorded bound) re-rendered to SMV and checked with nuXmv 2.2.0 `check_invar_ic3`; 99 safe and 590 unsafe verdicts, no errors and no timeouts; 663 distinct IR fingerprints and 468 distinct rendered models; refutations keep no witness length (nuXmv reports the abstract trace only) and 23 models are degenerate after rendering (no transition rules), so their `safe` verdict is vacuous and auto-flagged in `trivial_models`; this is a bounded proof over hand-written finite IR, not an unbounded deployment claim |
| Expanded mutation benchmark: 26 mutants across 4 families, 100% kill rate | Bounded evidence | `research/output/runs/mutation-benchmark-v1/`: 4 disclosure (native SLED), 7 delegation (native SLED), 10 delegation IR (reference BFS + Z3 BMC + COI-reduced Z3 BMC), 5 synthesis (Z3 BMC); all killed within tested bound |
| Authenticated provenance recovers utility without soundness violations | Bounded evidence | `research/output/runs/provenance-precision-v1/`: 351 tasks across 117 populated cells of the 3×4×3×4 parameter grid (workflow depth × possible authors × heterogeneity × actual contributors), 3 repetitions per cell; C2 (authenticated) completion 0.593 ≥ C1 (conservative) 0.493; C2 has zero enforcement soundness violations; C1 mean PC 8.62 > C2 mean PC 3.08 (overapproximation confirmed) |
| Planning diagnostic suite covers 22 scenario categories | Implemented | `research/experiments/suites/planning-diagnostic-v1.yaml`: 22 deterministic scenarios across 16 categories; all validated against planning-diagnostic-suite schema; 4 planning modes tested (reactive, static, dynamic, dynamic_code) |
| Three encodings of the delegation IR agree on every combination of the nine independent defects | Measured | `research/output/runs/delegation-defect-sweep-v1/`: 512 of 512 subsets agree by verdict class across the reference interpreter, Z3 and nuXmv, 511 carry an unsafe reference verdict, one raw difference against Z3 (the canonical body, `bounded_safe` vs `safe`) and none against nuXmv; agreement between three encodings of one IR is not a proof of the delegation semantics |
| Three encodings of the plan IR agree on a plan x effect-summary x bound grid | Measured | `research/output/runs/plan_ir/`: 36 of 36 readings agree by verdict class across the reference interpreter, Z3 and nuXmv, every reading states an expectation before measurement and meets it, 16 carry an unsafe reference verdict (unauthorised execution, and a capability violation for the code-execution plan) and every cleared reading is named in the bundle; the grid covers three plan shapes and one operation catalogue, not the open space of plans |

Ledger rows: 50 (Part B: 0, Part B, reproduced: 2, Part B concept, Part C evidence: 6, Part C: 42).

<!-- END GENERATED CONTRIBUTION TABLE -->

## Reproduce

```bash
python scripts/generate_contribution_table.py          # regenerate the table
python scripts/generate_contribution_table.py --check  # fail if the table drifts
```

`tests/test_contribution_provenance.py` runs the `--check` form, so a claim added to
the ledger without regenerating this file fails the gate.
