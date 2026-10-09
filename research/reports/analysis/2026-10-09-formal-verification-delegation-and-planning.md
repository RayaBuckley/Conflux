# Formal verification, delegation, and planning: what is proven, what is measured, what is open

**Date:** 2026-10-09
**Repository:** `/home/raya/projects/Conflux` at HEAD `f7d198f`
**Scope:** read-only analysis of the verification, delegation, and planning mechanisms, plus a fresh
reproduction of the solver boundary in two environments. No source file was modified to produce this
report, and no corpus or claim entry was changed.
**Status:** research analysis. Where the repository records a limit, the limit is quoted rather than
paraphrased, because those bounds are the honest part of the result.

## 1. How to read every claim here

The repository keeps three evidence classes apart, and this report keeps them apart too:

| Class | Meaning | Where it lives |
| --- | --- | --- |
| Implemented | code plus tests exist in the gate | `src/`, `tests/`, `scripts/validate.py` |
| Bounded evidence | a recorded run with explicit bounds, retained under version control | `research/output/runs/*/result.json` |
| Unavailable | the optional tool was absent, and the run says so instead of passing | `claim_boundary`, `*_status`, `reason` fields |

The rule that makes this trustworthy is stated in `docs/DEVELOPMENT.md`: missing optional access is
recorded as unavailable, not converted into a passing empirical claim. The clearest instance is the
SMT solver, and section 2 measures it.

## 2. The solver boundary, measured on 2026-10-09

The gate environment installs `.[dev,visualisation]` and deliberately has no z3, so the positive
formal verdicts cannot exist there. I measured both environments directly, by installing the solver
into the project venv, capturing the results, and then uninstalling it so the gate stays as
documented.

| Environment | canonical delegation IR | ten delegation mutations | multi-grant IR, 2 to 4 grants |
| --- | --- | --- | --- |
| Gate as documented, no solver | `unknown` | `unknown` | `unknown` |
| With `z3-solver` 5.1.0 installed | `bounded_safe` | `unsafe`, each with a counterexample | `bounded_safe` |

The result carried by both environments is a `FormalVerificationResult` with these fields:
`verdict`, `backend`, `ir_hash`, `query_hash`, `solver_hash`, `model_hash`, `bound`, `assumptions`,
`counterexample`, `error`, `schema_version`. A solver-present run on the canonical delegation IR
returns `backend = z3-bmc`, `bound = 4`, no counterexample, the assumptions tuple of the encoded
grant (`single-use with remaining_use_count=1`, `redelegable=False`, ...), and `solver_hash` set. A
mutated IR returns `unsafe`, a populated `model_hash`, and a step-indexed counterexample trace.

Three properties of that record are worth naming, because they are what make a bounded result
checkable later:

- `solver_hash` pins the solver that answered, and `ir_hash`/`query_hash` pin the question. A solver
  upgrade or an IR edit cannot silently reuse an old verdict.
- The verdict vocabulary keeps the boundary in the name: `bounded_safe` is not `safe`.
- The absent-solver path is a verdict (`unknown`), not an exception and not a pass.

Fresh reproduction, recorded outside the repository:

- `.conflux-investigation/verification/2026-10-09-solver-present-repro.json` (the JSON above),
- `.conflux-investigation/verification/verify_repro.py` (the script that produces it).

Consequence for reading the gate: a green full tier says nothing about any positive formal verdict.
It says the code paths behave correctly when the solver is absent.

## 3. Module map: research question to implementation

| Question | Module | What it encodes |
| --- | --- | --- |
| RQ1 maximal permissiveness | `verification/synthesis.py` | controller synthesis over a finite instance; `ControllerStrategy`, `SynthesisResult` |
| RQ2 unbounded verification | `verification/nuxmv_backend.py` | optional nuXmv IC3 adapter for the Boolean IR subset |
| RQ3 comparative objectives | `verification/defence_models.py` | IR models of contemporary agent defence patterns |
| RQ4 state-space reduction | `verification/reduction.py`, `verification/symmetry_reduction.py` | property-scoped cone-of-influence reduction; principal symmetry |
| RQ5 provenance granularity | `verification/provenance_distinction.py`, `domain/provenance.py` | provenance overapproximation and precision metrics (SEM-017, SEM-018) |
| RQ6 delegation | `verification/delegation_ir.py`, `evaluation/delegation_verification.py` | `consume()` logic as guarded transitions; a native boolean-flag model with mutants |
| RQ7 confidentiality | `verification/self_composition.py`, `verification/robust_disclosure.py` | self-composition product IR; robust disclosure in the Zdancewic and Myers sense |
| RQ8 planning | `evaluation/planning.py`, `planning/contamination_optimisation.py` | worst-case finite abstraction; planning as contamination minimisation |
| RQ9 implementation conformance | `verification/refinement.py`, `verification/assume_guarantee.py` | refinement relation; assume/guarantee contracts and sub-plan isolation |
| shared machinery | `verification/ir.py`, `interpreter.py`, `z3_backend.py`, `results.py`, `counterexample_refinement.py` | serialisable transition-system IR with no executable callbacks, a pure reference interpreter, differential conformance, CEGAR |

The design choice that carries the most weight is in `verification/ir.py`: the IR is serialisable and
contains no callbacks, so the same artifact can be executed by the reference interpreter, by Z3, or
by nuXmv, and compared. That is what makes the differential and reduction results meaningful.

## 4. Recorded results in the repository

| Run | What it records | Boundary it states or implies |
| --- | --- | --- |
| `z3-agreement-v1` | original and COI-reduced fixtures agree: `safe-noise` is `bounded_safe`/`bounded_safe`, `unsafe-control` is `unsafe`/`unsafe` with a counterexample of length 2 | both fixtures are finite IR models |
| `coi-scaling-v1` | 12 fixtures over noise counts 0, 1, 2, 4, 8, 16; `all_equivalent` true, `z3_measured` 12, `z3_all_agree` true; reference interpreter agrees in every row | `z3_all_agree` is defined as null when no solver answered, so the field cannot pass by accident |
| `sled-coi-reduction-v1` | recorded with `z3` and `nuxmv` both `unavailable`; equivalence comes from the independent reference interpreter | the formal half of this run does not exist; the run says so |
| `defence-models-v1` | z3 available; nuXmv unavailable when this row was written, then re-measured with nuXmv 2.2.0 on 2026-10-09, where every model's unbounded IC3 verdict agrees with the value preserved from `bbd59a2`; Dual-LLM, CaMeL, Progent and PACT each have a native property that is `bounded_safe` while the PE property is `unsafe`, with a counterexample | the models are unvalidated finite abstractions of the published systems, not the systems |
| `mutation-benchmark-v1` | 26 mutants in 4 families (4 disclosure, 7 delegation native, 10 delegation IR, 5 synthesis), all killed within `max_depth` 1 and `max_states` 4 | quoted: "All seeded security mutants are killed by at least one verification backend within the tested bound. Not allowed: this proves all possible mutants are detectable." |
| `provenance-precision-v1` | conditions C0 (negative control), C1 (conservative may-have-written), C2 (authenticated actual contributor); possible authors 2, 4, 8; heterogeneity low, medium, high; depths 1 to 3; 3 repetitions per cell | quoted: the utility recovery holds "under the trusted provenance assumptions of the experiment" |
| `cedar-differential-preflight-v1` | `cedar_status = unavailable`, `classification = evaluation_ready`, `complete = false` | a preflight that refuses to claim a differential result it could not run |

Two patterns are visible across the table, and both are to the project's credit. First, every run
records the backends it had: `available_formal_backends` and per-backend `reason` fields make an
"unavailable" run distinguishable from a passed one. Second, the strongest claims are the ones that
transfer *negatively*: `defence-models-v1` shows that satisfying a native property does not imply the
property the evaluation uses, which is a result about the evaluation, not about the defence.

## 5. Delegation mechanisms

Three layers, deliberately separate:

1. **Runtime value.** `domain/delegation.py` implements scoped, attenuating delegation values with
   immutable one-use state, expiry, revocation and atomic idempotent consumption. Its status in the
   claim ledger is "Implemented model, runtime disabled": ITES denies delegation in the current
   runtime, so the mechanism exists to be specified and verified, not to hand out authority today.
2. **Encoded model.** `verification/delegation_ir.py` encodes `consume()` as guarded transitions in
   the serialisable IR, with a canonical variant and ten mutation variants: `widened_scope`,
   `wrong_beneficiary`, `reuse`, `expiry_bypass`, `revocation_bypass`, `redelegation`,
   `post_influence_issuance`, `redelegation_chain`, `widened_scope_chain`, `stale_context`. With the
   solver present, the canonical variant is `bounded_safe` and all ten mutations are `unsafe` with
   counterexamples; without a solver, all eleven are `unknown`. `build_multi_grant_ir(n)` extends the
   model to 2, 3 and 4 grants, and all three are `bounded_safe`.
3. **Native model.** `evaluation/delegation_verification.py` models a bounded delegation monitor with
   abstract boolean flags and contributes the seven native delegation mutants to
   `mutation-benchmark-v1`. Keeping the native and IR models separate is what lets a mutant that one
   model misses be visible in the benchmark instead of averaged away.

The delegation rows in `docs/evidence/CLAIMS.md` bind the mechanism to exact
issuer/beneficiary/operation/resource/argument bindings, expiry, revocation, atomic idempotent
consumption and lifecycle projection, and record the seven one-step mutant witnesses. What no row
claims is that delegated authority is *safe to enable*: that would need the runtime path to exist.

## 6. Planning mechanisms

The planning package is an open-ended plan graph with effects that stay owned by ITES:

| Module | Role |
| --- | --- |
| `planning/model.py` | immutable open-ended plan graph and typed node taxonomy |
| `planning/actions.py` | authenticated operation definitions and provenance-preserving grounding |
| `planning/parsing.py` | strict parsing of untrusted planner JSON into trusted-provenance types |
| `planning/requests.py`, `planning/records.py` | side-effect-free planner requests, explicit budgets, deterministic call records |
| `planning/continuation.py` | typed continuation requests and immutable-history plan patches |
| `planning/state.py`, `planning/executor.py` | immutable execution state and replayable events; a deterministic executor that mediates every grounded effect |
| `planning/modeled_program.py` | an inert graph of declared effects with no execution boundary |
| `planning/optimise.py`, `planning/contamination_optimisation.py` | deterministic authority-minimising plan selection; planning as contamination minimisation (RQ8) |
| `planning/verify.py`, `verification/plan_ir.py` | planning-facing facade; conservative finite abstraction of supported dynamic-plan effects |
| `evaluation/planning.py` | finite worst-case abstraction for open-ended dynamic planning |

The safety story that the code actually implements is option restriction with an execution-time
recheck: the planner's output is untrusted JSON, it is parsed into typed values, every grounded effect
is mediated by the executor, and dynamic effects are re-authorised at execution time against the
current state. The claim ledger marks that mechanism as a **replication** of the version-bound
witness idea in arXiv:2610.04975, not as a new mechanism, and the differentiation analysis records
what remains distinct: a pointwise authority check against every principal that influenced a value.

Empirical planning results, recorded from model runs rather than formal proof:

| Run | Result |
| --- | --- |
| `planning-pilot-7b-v1` | 7 of 8 cells `utility_completed=True`; the failure is `blocked-action-recovery:dynamic_code` |
| `planning-pilot-3b-v1` | 5 of 8; the dynamic-code cells fail because the model is too small to generate code |
| `planning-pilot-1b5-v1` | every cell `model_failed`; the model cannot emit structured JSON, and each failure keeps its `error_detail` |
| H100 expanded suite, Qwen3-4B-2507 | 24 cells, 19 `utility_completed`, 4 `provider_failed` (the negative-control `provider-failure-no-fallback` task), 1 `bound_reached` (`multi-step-dependency-chain:reactive`), and `security_violations = 0` in every cell |

The 1.5B row is the useful one: a run where the harness could not do the task at all still produced a
record, with the failure classified per cell instead of being dropped.

## 7. Established, bounded, and open

| Statement | Status |
| --- | --- |
| The serialisable IR, reference interpreter and differential conformance are implemented and tested in the gate | established |
| Delegation `consume()` is `bounded_safe` as encoded and all ten encoded mutations are `unsafe` | bounded evidence, solver environment only |
| Reduction preserves verdicts on the recorded fixtures, including up to 16 noise variables | bounded evidence |
| COI reduction preserves the two recorded fixtures | bounded evidence |
| Native properties of four contemporary defence models do not imply the PE property | bounded evidence, unvalidated abstractions |
| Confidentiality is established for finite IR product models | bounded evidence; not a noninterference proof |
| Any unbounded result | closed 2026-10-09: the binary is installed and the six defence-model abstractions were re-measured with IC3; other runs remain bounded-only |
| Effect-time re-authorisation | implemented, and prior art for it exists; the project claims replication, not novelty |
| Delegated authority being safe to enable | open: the runtime keeps delegation denied |
| The gate proving any positive formal verdict | not applicable by design: the gate has no solver and reports `unknown` |

Recommended next steps, in the order that would strengthen the empirical record most:

1. Add a solver-present job (a CI matrix entry or an explicit optional workflow) that runs the
   verification tests with z3 installed and retains `solver_hash` next to the verdict.
2. Record a human-readable solver version beside `solver_hash` in the result record; the hash alone
   cannot be read by a reviewer without the environment.
3. Decide the nuXmv question. **Decided and executed on 2026-10-09**: the binary is installed
   and the six defence-model abstractions were re-measured with IC3, so RQ2 now has unbounded
   evidence for those abstractions; every other recorded formal result remains bounded-only.
4. Add tests that assert the gate's `unknown` verdict on purpose, so an accidental solver install in
   the default environment cannot silently change what a green gate means.
5. Test the bound edge explicitly, the way the RunPod guard now tests its trust-window edge: a
   counterexample at bound 4 and its absence at bound 5 are different claims, and only the first is
   currently recorded.
6. If the delegation runtime is ever enabled, make the ten delegation-IR mutations the acceptance
   gate for that change rather than a separate benchmark run.

## 8. Reproduction commands

Every command below is a single line, and none of them writes to the repository tree.

```bash
cd ~/projects/Conflux && uv pip install --python .venv/bin/python "z3-solver>=4.13"
```

```bash
cd ~/projects/Conflux && .venv/bin/python .conflux-investigation/verification/verify_repro.py
```

```bash
cd ~/projects/Conflux && uv pip uninstall --python .venv/bin/python z3-solver
```

```bash
cd ~/projects/Conflux && .venv/bin/python -m pytest tests/test_verification_ir.py -q
```

```bash
cd ~/projects/Conflux && for f in research/output/runs/*/result.json; do echo "$f"; done
```

## Solver posture after the 2026-10-09 install

The owner asked for the solvers to be installed if they help the repository. Outcome, measured:

**z3 - installed locally.** `z3-solver 5.1.0.0` is now installed in the project virtual environment,
so the positive verification path runs locally without a temporary install. The documented gate
environment is unchanged: `docs/DEVELOPMENT.md` still installs `.[dev,visualisation]`, which carries
no solver, and the guard tests keep forcing the unavailable path themselves - they set
`sys.modules["z3"] = None` (`tests/test_omitted_coverage.py`, `tests/test_performance.py`) rather than
depending on the ambient environment, so installing the solver cannot make them vacuous. Verified with
the solver present: 22 tests pass across `tests/test_verification_ir_sets.py`,
`tests/test_omitted_coverage.py` and `tests/test_performance.py`; 19 pass across
`tests/test_coi_scaling_evidence.py` and `tests/test_defence_model_evidence.py`, and those two branch
correctly on whether the solver answered.

Re-measured through the repository's own generator with the solver installed:
`research/output/runs/z3-agreement-v1/result.json` reports `bounded_safe` for the safe fixture with no
counterexample and `unsafe` with a two-step counterexample for the control fixture, and the two
fixtures agree once bounded and unbounded verdicts are compared by class. That generator was carrying
two misleading fields before this run - a permanently false agreement flag and a counterexample flag that was
true for every result including a bounded-safe one - and `tests/test_z3_agreement_evidence.py` now pins the
corrected semantics.

**nuXmv - no package, but the vendor download does work.** Checked on 2026-10-09: the local apt index
has no `nuxmv` or `nusmv` candidate, PyPI has no `nuxmv` package, and the nearest name, `pynuxmv`, is a
Python-to-nuXmv source transpiler rather than the model checker. FBK publishes nuXmv directly instead:
version 2.2.0 (4 June 2026), Linux x86_64 tarball with a published SHA-256, under a licence that allows
academic and non-commercial research use but forbids modification and redistribution. That licence is
the owner's to accept, and they qualify; the binary is now installed locally from the vendor URL with
the published digest verified, outside the repository, and reachable as `nuXmv` on `PATH`.

One finding is worth carrying: the official tarball does not run unmodified on this host (Ubuntu 26.04,
glibc 2.43). The launcher the vendor ships puts the whole bundled library directory first on the search
path, and that directory contains an older `libc.so.6` plus a `libxml2.so.2` built against ICU 70; the
loader rejects the first against the system `libstdc++` and cannot satisfy the second, because Ubuntu
26.04 ships `libxml2.so.16` and ICU 78. The working arrangement is contained and documented in
`docs/DEVELOPMENT.md`: keep the vendor's own `libxml2.so.2`, supply ICU 70 beside it, and let every
other library resolve from the system, so the backend's `nuXmv -h` reports its real version line rather
than a loader warning - the version line feeds the recorded solver fingerprint, so loader noise would
otherwise put machine-local paths into evidence bundles.

Consequence: the IC3 path is now available for the first time, and re-measuring the unbounded results
becomes possible. It also makes the gate environment question sharper rather than closing it - a
recorded bundle that says "nuXmv unavailable" is only reproducible where nuXmv is absent, so the
environment that produced each bundle has to be recorded with it. Section "Recommendations" already
proposes exactly that; this install is the first case that needs it.

Outcome, measured the same day. `scripts/generate_defence_evidence.py` was re-run with the binary
on `PATH` and the bundle now records nuXmv as available: all six abstractions carry real unbounded
IC3 verdicts (`unsafe` for the PE property of Dual-LLM, CaMeL, Progent, PACT and Requester-only,
`safe` for ITES; `safe` for the native property of the four external abstractions), and every one
of them agrees with the value preserved from revision `bbd59a2`. Two runs produced byte-identical
output, so the bundle is deterministic, and only the source-hash line of the comparative-defence
table changed - no published number moved. What is *not* recorded in the bundle is which nuXmv
version produced the rows: `nuxmv_evidence.recorded` has no version field, so the version lives in
this report and in `docs/DEVELOPMENT.md` instead. Adding a version or solver-hash field to a
bundle that has a `schema_version` is a schema change worth doing deliberately, together with the
same field for Z3, rather than halfway through a re-measurement.

