# Claim-to-Evidence Ledger

| Claim | Status | Evidence and limits |
| --- | --- | --- |
| Empty/unknown context cannot authorise an effect | Implemented | policy and ITES tests; assumes mediation cannot be bypassed |
| Influence is never silently removed by nested execution | Implemented | immutable provenance and monotonic-context tests |
| Provenance is not a read ACL | Implemented | separate read port and reader/author inversion tests |
| Branches are isolated alternatives | Implemented | one transition kernel and branch-parent tests |
| Native SLED returns minimal counterexamples | Implemented within finite model | breadth-first checker tests |
| The current native reproduction detects the seeded monitor defects | Bounded evidence | `research/output/runs/native-sled-reproduction-v1/`: five of five defective monitors, each with a one-step witness; three fixture pairs and fixed finite bounds only |
| Dynamic effects are re-authorised at execution time | Implemented | planning runtime, revocation, certificate, and provider tests |
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
| Z3 bounded model checking agrees with the reference interpreter | Bounded evidence | `research/output/runs/sled-coi-reduction-v1/`, `research/output/runs/z3-agreement-v1/`, `research/output/runs/coi-scaling-v1/`: Z3 BMC with COI reduction on safe and unsafe IR fixtures; safe models bounded safe, unsafe models produce counterexamples; original and reduced verdicts agree in all cases; scaling to 16 noise variables preserves all verdicts |
| The Cedar adapter is ready for a pinned differential run | Evaluation ready | `research/output/runs/cedar-differential-preflight-v1/` validates the bundle and corpus, translates PARC requests, and records oracle decisions; Cedar cells are explicitly unavailable and establish no parity |
| Cedar decisions match the in-memory oracle | Not yet evidenced | the exact 4.12.0 binary has not completed the retained differential matrix |
| Conflux is secure for unbounded deployments | Not claimed | finite bounds and abstractions do not prove unbounded deployments |
| AgentDojo integration preserves upstream semantics | Implemented for translation | pinned 0.1.35 structures and raw fixture; Conflux annotations are additional assumptions |
| AgentDojo establishes Conflux utility or efficacy | Bounded evidence | `research/output/runs/agentdojo-1b5-nf4-v1/`: six-cell protocol executed with Qwen2.5-1.5B-Instruct NF4 on RTX 4060; all six cells completed (benign: security=True, utility=False; attacked: security=False, utility=False); 1.5B model is too small to complete tasks but the pipeline runs end-to-end including attack injection and ITES mediation; the 3B model produces malformed JSON output; the 7B NF4 model timed out at 10 minutes on this GPU |
| Open-ended planning improves utility | Bounded evidence | `research/output/runs/planning-pilot-1b5-v1/`: eight-cell pilot completed with Qwen2.5-1.5B-Instruct NF4; all cells `complete=True`; model is too small for high utility but the planning pipeline executes end-to-end |
| Self-hosted model output is reproducible across hardware or runtimes | Not claimed | identity and sampling are recorded, but no model-generated bundle or cross-hardware comparison is retained |
| Cloud policy behaviour matches a provider | Not claimed | current AWS adapter is an explicit fail-closed subset |
| The current evidence pipeline handles allow, block, and vulnerable-control cases | Bounded evidence | `research/output/runs/smoke/`, two scripted cases, one one-step negative-control witness |
| Observational confidentiality holds on finite IR fixtures | Bounded evidence | IR self-composition with Z3 BMC; safe fixture bounded safe, unsafe fixture produces counterexample showing observation divergence; bounded to finite product state spaces; not a noninterference proof |
| Dual-LLM candidate abstraction satisfies its own property Q but admits PE counterexample | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: Dual-LLM native property (processor never executes) is bounded\_safe; PE property is unsafe with Z3 counterexample; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| CaMeL candidate abstraction satisfies its own property Q but admits PE counterexample | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: CaMeL native property bounded\_safe; PE property unsafe with Z3 counterexample; unvalidated finite IR abstraction, not the published system; fidelity: `docs/evidence/defence-model-fidelity.json` |
| Progent candidate abstraction satisfies its own property Q but admits PE counterexample | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: Progent native property bounded\_safe; PE property unsafe with Z3 counterexample; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| PACT candidate abstraction satisfies its own property Q but admits PE counterexample | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: PACT native property bounded\_safe; PE property unsafe with Z3 counterexample; unvalidated finite IR abstraction; fidelity: `docs/evidence/defence-model-fidelity.json` |
| ITES preserves PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: ITES reference PE property is bounded\_safe; finite IR model |
| ITES defective requester-only controller violates PE | Bounded evidence | `research/output/runs/defence-models-v1/result.json`: requester-only PE property unsafe with Z3 counterexample; finite IR model |
| Part B 1.46M trace reproduction | Reproduced | `research/output/runs/native-sled-partb-reproduction-v1/result.json`: all three historical environments reproduce exact trace counts (422,535 + 996,451 + 43,621 = 1,462,607); source: archived prototype `research/reports/archive/2026-06-01-original-prototype/main.py`; canonical-state compression: 1,462,607 raw traces → 31 unique canonical states; incomplete count differs from preprint due to simplified criterion |

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

## Rationale

Claim strength is kept separate from implementation status because passing
code tests can establish behavior without establishing deployment security or
empirical utility. Every numerical statement therefore points to retained
evidence, and missing live evidence remains visible rather than inferred.
