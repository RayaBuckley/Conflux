# Claim-to-Evidence Ledger

| Claim | Status | Origin | Evidence and limits |
| --- | --- | --- | --- |
| Empty/unknown context cannot authorise an effect | Implemented | Part B concept, Part C evidence | policy and ITES tests; assumes mediation cannot be bypassed |
| External tool output retains authenticated source provenance, not requesting user authority | Implemented | Part C | security model and provenance tests; ADR 024 |
| PC(output) ⊇ PC(execution inputs) (no laundering) | Implemented | Part B concept, Part C evidence | provenance monotonicity, persistence, and branch isolation tests; ADR 024 |
| ITES prevents authority amplification but not harm within authorised actions | Implemented (documentation) | Part C | authority-vs-harm distinction in security model and papers; ADR 024 |
| Authenticated provenance is in the TCB and does not grant organisational authority | Implemented | Part C | security model and threat model documentation; ADR 024 |
| Influence is never silently removed by nested execution | Implemented | Part B concept, Part C evidence | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | Part B concept, Part C evidence | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | Part B concept, Part C evidence | one transition kernel and branch-parent tests |
| Native SLED returns minimal counterexamples | Implemented within finite model | Part C | breadth-first checker tests |
| The current native reproduction detects the seeded monitor defects | Bounded evidence | Part C | `research/output/runs/native-sled-reproduction-v1/`: five of five defective monitors, each with a one-step witness; three fixture pairs and fixed finite bounds only |
| Dynamic effects are re-authorised at execution time | Implemented | Part C | planning runtime, revocation, certificate, and provider tests. **Replication, not a new mechanism**: arXiv:2610.04975 proves root-task safety for a version-bound witness on every goal-graph mutation with a reserve/commit recheck at one linearisation point, so effect-time re-authorisation is prior art for this row; see [the differentiation analysis](../../research/reports/analysis/2026-10-09-differentiation-threats.md) |
| Authority-bearing action arguments cannot borrow authority from content or consent | Implemented | Part C | trusted argument roles, pointwise Principal checks, fail-closed missing policy, and selector mutation tests |
| Redacted event views do not copy hidden payload fields | Implemented | Part C | deterministic audience projection and unsafe-redaction/hidden-error mutants; assumes callers use the canonical projector |
| Attribution is evidence-derived rather than model-asserted | Implemented | Part C | structured provenance/context/policy records and tests rejecting trusted model explanations |
| Scoped one-use delegation is modeled without activating authority transfer | Implemented model, runtime disabled | Part C | exact issuer/beneficiary/operation/resource/argument bindings, expiry, revocation, atomic idempotent consumption, lifecycle projection, and seven one-step mutant witnesses; ITES still denies delegation |
| The argument, disclosure, attribution, and delegation monitors reject their seeded defects | Bounded evidence | Part C | `research/output/runs/direction-readiness-v1/security-mutations.json`; the canonical finite models exhaust safely and every retained mutant has a one-transition witness under the recorded bounds |
| The installed offline vertical slice is runnable without credentials | Implemented | Part C | `research/output/validation/6fe6b584500e/`: clean-wheel doctor, demo, planning, SLED, and report smoke validation |
| The planning comparison executes no generated code | Implemented | Part C | `ModeledProgram` is inert validated data; architecture tests exclude evaluation, compilation, shell, import, and executor paths |
| The optional operational code adapter cannot exceed its declared envelope | Implemented at adapter boundary | Part C | container arguments, mount/path checks, and fail-closed sandbox tests; host/container implementation remains in the TCB and is not used by the planning comparison |
| Solver results match the supported runtime subset | Bounded evidence | Part C | serialisable IR, interpreter differential tests, optional Z3 backend |
| COI reduction preserves the selected fixture verdicts | Bounded evidence | Part C | `research/output/runs/sled-coi-reduction-v1/`: two finite IR fixtures agree under the independent reference interpreter; both reduce variables, rules, or reachable states, and the unsafe witness lifts; Z3 BMC with COI reduction confirms equivalence on both fixtures (safe: bounded safe, unsafe: counterexample found and lifted) |
| Z3 bounded model checking agrees with the reference interpreter | Bounded evidence | Part C | `research/output/runs/sled-coi-reduction-v1/`, `research/output/runs/z3-agreement-v1/`, `research/output/runs/coi-scaling-v1/`: Z3 BMC with COI reduction on safe and unsafe IR fixtures; safe models bounded safe, unsafe models produce counterexamples; original and reduced verdicts agree in all cases where the optional Z3 backend is available (`coi-scaling-v1` records `z3_measured` per row and sets `z3_all_agree` to null when no solver answered); scaling to 16 noise variables preserves all verdicts |
| The Cedar adapter is ready for a pinned differential run | Evaluation ready | Part C | `research/output/runs/cedar-differential-preflight-v1/` validates the bundle and corpus, translates PARC requests, and records oracle decisions; Cedar cells are explicitly unavailable and establish no parity |
| Cedar decisions match the in-memory oracle | Not yet evidenced | Part C | the exact 4.12.0 binary has not completed the retained differential matrix |
| Conflux is secure for unbounded deployments | Not claimed | Part C | finite bounds and abstractions do not prove unbounded deployments |
| AgentDojo integration preserves upstream semantics | Implemented for translation | Part C | pinned 0.1.35 structures and raw fixture; Conflux annotations are additional assumptions |
| AgentDojo establishes Conflux utility or efficacy | Bounded evidence | Part C | Expanded 30-cell matrix (5 tasks x 2 attacks x 3 defences) on 7 models. `research/output/runs/agentdojo-7b-v5/`: Qwen2.5-7B-Instruct NF4, 24/30 utility (80%), 30/30 security, passes >=70% competency gate. `research/output/runs/agentdojo-qwen3-4b-v2/`: Qwen3-4B-2507 NF4, 18/30 utility (60%), 30/30 security — improved from 0% (H100) with latest adapter fixes. `research/output/runs/agentdojo-3b-v4/`: Qwen2.5-3B, 6/30 utility (20%), 26/30 security. `research/output/runs/agentdojo-0b5-v1/`, `agentdojo-lfm2-1b2-v1/`, `agentdojo-granite-2b-v1/`, `agentdojo-llama-3b-v1/`: 0% utility, 100% security where complete. Qwen2.5-1.5B crashed during expanded run. Zero security violations across all completed runs and all models. Prior single-task results (6 cells) at `agentdojo-7b-v4/` showed 100% utility. Stratified selection (`research/experiments/manifests/agentdojo-stratified-selection-v1.json`, 36 strata): the four retained bundles `agentdojo-stratified-{banking,slack,travel,workspace}-v1/` hold 192 cells, 186 complete; at 0.5B every completed cell reports zero utility, so their security counts are vacuous, and slack's six incomplete cells are diagnosed parser failures, not adapter gaps. The banking bundle repeats protocol-exactly through its `RERUN.txt` command (fingerprint reproduced, zero cell differences). See `docs/evidence/VERIFICATION.md` sections 27-29. |
| Open-ended planning improves utility | Bounded evidence | Part C | `research/output/runs/planning-pilot-7b-v1/`: eight-cell pilot completed with Qwen2.5-7B-Instruct NF4; 7/8 cells `utility_completed=True` (only `blocked-action-recovery:dynamic_code` failed as `modeled_program_failed`); `research/output/runs/planning-pilot-3b-v1/`: 5/8 cells `utility_completed=True` (dynamic_code cells fail — model too small for code generation); `research/output/runs/planning-pilot-1b5-v1/`: all cells `model_failed` (model too small for structured JSON output; `error_detail` captured for each failure); H100 Qwen3-4B-2507 results (commit `a1fa168`, `research/output/runs/runpod-results/runpod-eval/planning/`): 24-cell expanded suite, 19/24 `utility_completed=True`, 4 `provider_failed` (negative-control `provider-failure-no-fallback` task), 1 `bound_reached` (`multi-step-dependency-chain:reactive`), all `security_violations=0`, structured JSON output including `dynamic_code` mode succeeds |
| Self-hosted model output is reproducible across hardware or runtimes | Not claimed | Part C | identity and sampling are recorded, but no model-generated bundle or cross-hardware comparison is retained |
| Cloud policy behaviour matches a provider | Not claimed | Part C | current AWS adapter is an explicit fail-closed subset |
| The current evidence pipeline handles allow, block, and vulnerable-control cases | Bounded evidence | Part C | `research/output/runs/smoke/`, two scripted cases, one one-step negative-control witness |
| Observational confidentiality holds on finite IR fixtures | Bounded evidence | Part C | IR self-composition with Z3 BMC; safe fixture bounded safe, unsafe fixture produces counterexample showing observation divergence; bounded to finite product state spaces; not a noninterference proof |
| Dual-LLM candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | Part C | `research/output/runs/defence-models-v1/result.json`: Dual-LLM native property (processor never executes) is bounded\_safe; PE property is unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| CaMeL candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | Part C | `research/output/runs/defence-models-v1/result.json`: CaMeL native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| Progent candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | Part C | `research/output/runs/defence-models-v1/result.json`: Progent native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| PACT candidate abstraction satisfies its own property Q but native Q does not imply PE | Bounded evidence | Part C | `research/output/runs/defence-models-v1/result.json`: PACT native property bounded\_safe; PE property unsafe with Z3 counterexample demonstrating non-implication; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| ITES preserves PE | Bounded evidence | Part B concept, Part C evidence | `research/output/runs/defence-models-v1/result.json`: ITES reference PE property is bounded\_safe; finite IR model |
| ITES defective requester-only controller violates PE | Bounded evidence | Part C | `research/output/runs/defence-models-v1/result.json`: requester-only PE property unsafe with Z3 counterexample; finite IR model |
| Part B 1.46M trace reproduction | Bounded historical reproduction | Part B, reproduced | `research/output/runs/native-sled-partb-reproduction-v1/result.json`: all three historical environments reproduce exact trace counts (422,535 + 996,451 + 43,621 = 1,462,607) under depth-three bounds; source: archived prototype `research/reports/archive/2026-06-01-original-prototype/main.py`; canonical-state compression: 1,462,607 raw traces → 31 unique canonical states; incomplete count differs from preprint due to simplified criterion; this is reproduction/conformance, not an unbounded security proof |
| Authority confinement does not guarantee semantic appropriateness of authorised choices | Documented semantics | Part C | ADR-025; security model distinguishes authority confinement from semantic judgement |
| Model-level defences are genuine empirical security but outside the authority TCB | Documented semantics | Part C | ADR-025; model/planner/classifier output cannot grant authority or narrow PC |
| Effective ACS includes only explicit valid delegation; runtime delegation remains disabled | Specified, runtime disabled | Part C | ADR-025; scoped delegation model exists but operational delegation is denied |
| SLED-V scaling: COI reduction never causes safe-to-unsafe verdict downgrade | Bounded evidence | Part C | `research/output/runs/sledv-scaling-v1/`: 28 fixtures across noise/principal/depth scaling families; no COI verdict downgrade on any fixture; Z3 BMC agrees with reference on all fixtures where Z3 is available; 5 fixtures show bounded_safe→safe upgrade from COI reduction |
| Expanded mutation benchmark: 26 mutants across 4 families, 100% kill rate | Bounded evidence | Part C | `research/output/runs/mutation-benchmark-v1/`: 4 disclosure (native SLED), 7 delegation (native SLED), 10 delegation IR (reference BFS + Z3 BMC + COI-reduced Z3 BMC), 5 synthesis (Z3 BMC); all killed within tested bound |
| Authenticated provenance recovers utility without soundness violations | Bounded evidence | Part C | `research/output/runs/provenance-precision-v1/`: 324 tasks across 4×4×3×3 parameter grid; C2 (authenticated) completion ≥ C1 (conservative) completion; C2 has zero enforcement soundness violations; C1 mean PC size > C2 mean PC size (overapproximation confirmed) |
| Planning diagnostic suite covers 22 scenario categories | Implemented | Part C | `research/experiments/suites/planning-diagnostic-v1.yaml`: 22 deterministic scenarios across 16 categories; all validated against planning-diagnostic-suite schema; 4 planning modes tested (reactive, static, dynamic, dynamic_code) |
| Three encodings of the delegation IR agree on every combination of the nine independent defects | Measured | Part C | `research/output/runs/delegation-defect-sweep-v1/`: 512 of 512 subsets agree by verdict class across the reference interpreter, Z3 and nuXmv, 511 carry an unsafe reference verdict, one raw difference against Z3 (the canonical body, `bounded_safe` vs `safe`) and none against nuXmv; agreement between three encodings of one IR is not a proof of the delegation semantics |
| Three encodings of the plan IR agree on a plan x effect-summary x bound grid | Measured | Part C | `research/output/runs/plan_ir/`: 36 of 36 readings agree by verdict class across the reference interpreter, Z3 and nuXmv, every reading states an expectation before measurement and meets it, 16 carry an unsafe reference verdict (unauthorised execution, and a capability violation for the code-execution plan) and every cleared reading is named in the bundle; the grid covers three plan shapes and one operation catalogue, not the open space of plans |

## Reading the Origin column

`Origin` separates the third-year project (Part B) from the fourth-year project
(Part C) for the examiner of the fourth-year report, as decided in
[ADR 026](../decisions/026-continuation-and-contribution-provenance.md):

- `Part B` - established in the third-year project; cited as prior work.
- `Part B, reproduced` - a Part B result re-executed here, with the archive path
  and the reproduction artefact recorded in the row.
- `Part B concept, Part C evidence` - the mechanism the row constrains was
  introduced in Part B; the implementation, test or proof cited in the row was
  produced in Part C. The concept is a third-year contribution and the evidence
  is a fourth-year contribution.
- `Part C` - new in the fourth-year project.

Part B contributions are the problem formulation, ITES as the reference monitor,
Principal Context and monotone influence, SLED enumeration, the twelve-category
task taxonomy, and the bounded trace experiments over about 1.46 million traces.
Evidence artefacts are Part C unless the row says otherwise, because this
repository was created after the Part B project ended. A paper submission may
present both phases as one contribution; the examiner-facing table may not.

## Novelty qualification

Claims involving the novelty of monotonic authority reduction, provenance-based
restriction, or source-sensitive context must be qualified against the
classical IFC and integrity literature. The authority-intersection rule is
structurally analogous to Biba's low-water-mark contamination; intersection
over permission sets is a standard meet in the powerset lattice; authorised
reads do not establish noninterference; and source-set taint and
provenance-aware policy enforcement have extensive prior literature. See
[ADR 012](../decisions/012-foundational-security-lineage.md), the
[foundational security literature
analysis](../../research/reports/analysis/2026-08-13-foundational-security-literature.md),
the [novelty audit](../../research/reports/analysis/2026-08-16-novelty-audit.md),
and the [literature verification
protocol](../research/LITERATURE_VERIFICATION_PROTOCOL.md) for the detailed
comparison and candidate distinctions that may survive prior-art search.

The 2026-10-09 agent-security differentiation pass reads six near-contemporary
papers in full and names what they take away from this repository's claims. Three
results matter for wording. arXiv:2610.04975 (unrefereed) already proves the
version-bound witness plus commit-boundary recheck that row 10 of this ledger
describes, so that row is a replication. arXiv:2610.06966 already proves
execution-boundary authorisation soundness under contract-fidelity assumptions,
so no claim of that shape may be made here. CaMeLoT, ToolFence and ACE remove the
novelty of plan-time and per-call checking, but each rests on oracle-labelled or
judge-relative labels, which is where the provenance argument in
[ADR 024](../decisions/024-external-provenance-and-authority-bounds.md) keeps its
ground. Ten claim shapes are named as unsafe to use at all. The full record,
including the per-paper quotes and the unverified list, is
[the differentiation analysis](../../research/reports/analysis/2026-10-09-differentiation-threats.md).

Structured per-source verification records, including key findings,
limitations, and novelty-impact assessments for the nine Priority A
foundational works and eight modern agent works, are recorded in
[`research/reports/analysis/literature_corpus.json`](../../research/reports/analysis/literature_corpus.json)
and validated by `tests/test_literature_corpus.py`. The corpus tracks 114
sources; the nine Priority A classical works have been verified to
`scholar_metadata` depth with abstract and key sections read. Full
primary-source reading of the complete texts remains an operator action.

The archived paper and report packages are historical evidence, not status
sources of truth. `research/reports/analysis/` reconciles them without promoting their
snapshot claims.
The M3 smoke result is pipeline-readiness evidence only; it is not promoted to
a deployment-security or external-utility claim.

## Solver-boundary claims

Rows 26 and 37–42 depend on the optional Z3 backend. `coi-scaling-v1` and
`defence-models-v1` record per-row solver provenance and count their summary
values over measured rows only: `z3_measured`, with `z3_all_agree` null when no
row was measured; and `pe_measured`, `pe_unknown`, `native_measured`,
`native_unknown`, with `pe_safe`, `pe_unsafe` and `native_satisfied` covering
measured verdicts only. A run without Z3 records the backend as unavailable and
makes no agreement or satisfaction claim, and an UNKNOWN verdict is never counted
as safe or satisfied. The retained bundles record Z3 as available and measured. `defence-models-v1` was
re-measured on 2026-10-09 on a host with nuXmv 2.2.0, so its `nuxmv_verdict` fields carry
real unbounded IC3 verdicts instead of UNKNOWN, and the fresh verdicts agree model by
model with the measurement previously preserved from revision `bbd59a2`: the retained
provenance block was superseded by a reproducible one, not dropped. No claim rests on
nuXmv alone, because the `pe_*` and `native_*` counters are computed over the Z3 verdicts
and the reference interpreter; the IC3 rows corroborate them without a bound.

Row 47 measures the same optional Z3 backend over a closed population: every subset of the nine
independent delegation defects is built and compared, so its agreement count is not over a chosen list.
The bundle records both the raw and the class comparison per subset, the one raw difference in the space
(the canonical body, `bounded_safe` against `safe`), and the single subset that is not refuted, by id.
The claim is still about two encodings of one IR against a reference interpreter, not about delegation
semantics as such.

## Rationale

Claim strength is kept separate from implementation status because passing
code tests can establish behavior without establishing deployment security or
empirical utility. Every numerical statement therefore points to retained
evidence, and missing live evidence remains visible rather than inferred.
