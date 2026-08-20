# Claim-to-Evidence Ledger

| Claim | Status | Evidence and limits |
|---|---|---|
| Empty/unknown context cannot authorise an effect | Implemented | policy and ITES tests; assumes mediation cannot be bypassed |
| Influence is never silently removed by nested execution | Implemented | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | one transition kernel and branch-parent tests |
| Native SLED returns minimal counterexamples | Implemented within finite model | breadth-first checker tests |
| The current native reproduction detects the seeded monitor defects | Bounded evidence | `runs/native-sled-reproduction-v1/`: five of five defective monitors, each with a one-step witness; three fixture pairs and fixed finite bounds only |
| Dynamic effects are re-authorised at execution time | Implemented | planning runtime, revocation, certificate, and provider tests |
| Authority-bearing action arguments cannot borrow authority from content or consent | Implemented | trusted argument roles, pointwise Principal checks, fail-closed missing policy, and selector mutation tests |
| Redacted event views do not copy hidden payload fields | Implemented | deterministic audience projection and unsafe-redaction/hidden-error mutants; assumes callers use the canonical projector |
| Attribution is evidence-derived rather than model-asserted | Implemented | structured provenance/context/policy records and tests rejecting trusted model explanations |
| Scoped one-use delegation is modeled without activating authority transfer | Implemented model, runtime disabled | exact issuer/beneficiary/operation/resource/argument bindings, expiry, revocation, atomic idempotent consumption, lifecycle projection, and seven one-step mutant witnesses; ITES still denies delegation |
| The argument, disclosure, attribution, and delegation monitors reject their seeded defects | Bounded evidence | `runs/direction-readiness-v1/security-mutations.json`; the canonical finite models exhaust safely and every retained mutant has a one-transition witness under the recorded bounds |
| The installed offline vertical slice is runnable without credentials | Implemented | `artifacts/validation/6fe6b584500e/`: clean-wheel doctor, demo, planning, SLED, and report smoke validation |
| The planning comparison executes no generated code | Implemented | `ModeledProgram` is inert validated data; architecture tests exclude evaluation, compilation, shell, import, and executor paths |
| The optional operational code adapter cannot exceed its declared envelope | Implemented at adapter boundary | container arguments, mount/path checks, and fail-closed sandbox tests; host/container implementation remains in the TCB and is not used by the planning comparison |
| Solver results match the supported runtime subset | Bounded evidence | serialisable IR, interpreter differential tests, optional Z3 backend |
| COI reduction preserves the selected fixture verdicts | Bounded evidence | `runs/sled-coi-reduction-v1/`: two finite IR fixtures agree under the independent reference interpreter; both reduce variables, rules, or reachable states, and the unsafe witness lifts; Z3 BMC with COI reduction confirms equivalence on both fixtures (safe: bounded safe, unsafe: counterexample found and lifted) |
| Z3 bounded model checking agrees with the reference interpreter | Bounded evidence | `runs/verify-coi-safe/`, `runs/verify-coi-unsafe/`, `runs/verify-coi-original-safe/`, `runs/verify-coi-original-unsafe/`: four IR fixtures verified with Z3 BMC and COI reduction; safe models bounded safe, unsafe models produce counterexamples; original and reduced verdicts agree in all cases |
| The Cedar adapter is ready for a pinned differential run | Evaluation ready | `runs/cedar-differential-preflight-v1/` validates the bundle and corpus, translates PARC requests, and records oracle decisions; Cedar cells are explicitly unavailable and establish no parity |
| Cedar decisions match the in-memory oracle | Not yet evidenced | the exact 4.12.0 binary has not completed the retained differential matrix |
| Conflux is secure for unbounded deployments | Not claimed | finite bounds and abstractions do not prove unbounded deployments |
| AgentDojo integration preserves upstream semantics | Implemented for translation | pinned 0.1.35 structures and raw fixture; Conflux annotations are additional assumptions |
| AgentDojo establishes Conflux utility or efficacy | Bounded evidence (model-failed) | `runs/agentdojo-qwen-1.5b/`: six-cell protocol executed with Qwen2.5-1.5B-Instruct; all six cells `model_failed` (1.5B model wraps JSON in markdown code fences, preventing structured tool-call parsing); raw upstream trace retained; efficacy not established but the protocol and mediation pipeline are exercised end-to-end |
| Open-ended planning improves utility | Bounded evidence (model-failed) | `runs/planning-pilot-qwen-1.5b/`: four-mode pilot completed with Qwen2.5-1.5B-Instruct; all eight cells `model_failed` (1.5B model wraps JSON in markdown code fences); offline modeled fixtures are mechanics evidence only |
| Self-hosted model output is reproducible across hardware or runtimes | Not claimed | identity and sampling are recorded, but no model-generated bundle or cross-hardware comparison is retained |
| Cloud policy behaviour matches a provider | Not claimed | current AWS adapter is an explicit fail-closed subset |
| The current evidence pipeline handles allow, block, and vulnerable-control cases | Bounded evidence | `runs/smoke/`, two scripted cases, one one-step negative-control witness |

### Novelty qualification

Claims involving the novelty of monotonic authority reduction, provenance-based
restriction, or source-sensitive context must be qualified against the
classical IFC and integrity literature. The authority-intersection rule is
structurally analogous to Biba's low-water-mark contamination; intersection
over permission sets is a standard meet in the powerset lattice; authorised
reads do not establish noninterference; and source-set taint and
provenance-aware policy enforcement have extensive prior literature. See
[ADR 012](../decisions/012-foundational-security-lineage.md) and the
[foundational security literature
analysis](../../reports/analysis/2026-08-13-foundational-security-literature.md)
for the detailed comparison and candidate distinctions that may survive
prior-art search.

The archived paper and report packages are historical evidence, not status
sources of truth. `reports/analysis/` reconciles them without promoting their
snapshot claims.
The M3 smoke result is pipeline-readiness evidence only; it is not promoted to
a deployment-security or external-utility claim.

## Rationale

Claim strength is kept separate from implementation status because passing
code tests can establish behavior without establishing deployment security or
empirical utility. Every numerical statement therefore points to retained
evidence, and missing live evidence remains visible rather than inferred.
