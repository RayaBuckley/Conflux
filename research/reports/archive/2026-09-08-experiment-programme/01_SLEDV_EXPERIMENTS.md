# SLED-V experiments

## Experiment V1 — Reduction scaling and preservation

### Goal

Quantify how much each state-space reduction helps while preserving verdicts and counterexamples.

### Baseline

Current repository evidence already includes COI reduction on safe/unsafe fixtures and a 12-fixture noise-scaling run. Do not recreate the same result under a different name. Extend the benchmark family to reductions not yet evidenced.

### Required reduction arms

Run at least:

1. no reduction;
2. COI only;
3. symmetry only;
4. partial-order reduction only;
5. authority-aware subsumption/antichain only, if a sound simulation relation can be justified;
6. COI + symmetry;
7. COI + POR;
8. all sound reductions together.

If a reduction is not yet implemented, create it as a separate implementation task and prove/test the preservation condition before including it in results.

### Fixture families

Generate parameterised finite models varying:

- principals: 2, 3, 4, 6, 8;
- resources: 2, 4, 8, 16;
- independent branches: 1, 2, 4, 8;
- policy-equivalent principals: 0%, 50%, 100%;
- irrelevant/noise state variables: 0, 4, 8, 16, 32;
- action classes: read, write, send, delete, nested execution;
- safe and deliberately unsafe variants.

At least one family must have substantial symmetry, and one must have substantial independent interleavings, otherwise the experiment cannot evaluate the relevant reductions.

### Metrics

For every cell retain:

- verdict;
- explored states;
- explored transitions;
- maximum frontier size;
- peak resident memory if measurable portably;
- wall-clock time;
- model construction time;
- solver time if applicable;
- reduced variable/rule counts;
- counterexample length for unsafe cells;
- whether lifted counterexample exactly replays in the unreduced model.

### Correctness controls

Each reduction must pass:

- safe verdict preservation;
- unsafe verdict preservation;
- counterexample lifting/replay;
- seeded-mutant detection;
- deterministic regeneration.

Do not accept speedups with any verdict mismatch.

### Analysis

Report median and geometric-mean speedup where appropriate, but retain raw per-cell values. For censored/time-limited cells, report timeout rather than substituting a numeric runtime. Plot explored states and runtime against model size for each reduction arm.

### Acceptance criterion

The experiment is complete when every implemented reduction has at least one fixture family where it is structurally applicable, all verdicts match the unreduced reference semantics, and the evidence bundle regenerates byte-for-byte apart from explicitly nondeterministic timing fields.

---

## Experiment V2 — Unbounded authority-confinement proof

### Goal

Obtain an unbounded safety result for the canonical finite ITES model, ideally via IC3/PDR, or produce a precise `UNKNOWN/UNSUPPORTED` boundary if the model/backend cannot support it.

### Property

The core safety invariant should be represented directly, not inferred from a proxy metric:

`Executed(a) -> PC is known/non-empty AND forall p in PC: ACS_effective(p,a) AND argument-authority checks pass`

Use the repository's current normative rule wording and operation schemas.

### Model requirements

The finite model must include at least:

- non-empty/unknown Principal Context handling;
- provenance accumulation;
- nested execution;
- sibling isolation;
- action-time policy recheck;
- pointwise authority-bearing argument checks;
- denial/fail-closed transitions;
- bounded finite policy state if policy mutation is represented.

The model must not smuggle the desired invariant into the transition relation in a way that makes the proof tautological. Include seeded defective variants where one guard is removed.

### Backend strategy

Preferred order:

1. inspect current nuXmv translation capability;
2. add a backend mode that uses an unbounded safety engine supported by the installed toolchain (e.g. IC3/PDR where available);
3. retain solver/backend version and exact command;
4. import verdict and counterexample/proof metadata into the standard result schema.

If nuXmv cannot expose a suitable proof mode cleanly, consider a separate backend rather than distorting the existing adapter.

### Mutation controls

At minimum test mutants that:

- allow empty PC;
- check only requester rather than all influencers;
- drop nested provenance;
- skip argument authority;
- skip execution-time recheck;
- merge sibling contexts;
- treat consent as authority.

The canonical model should be `SAFE`; every intentionally security-breaking mutant should be `UNSAFE` with a replayable witness. A mutant that remains safe must be investigated rather than force-fit.

### Acceptance criterion

A publishable result requires:

- one canonical model with an unbounded `SAFE` verdict from a documented solver algorithm;
- at least five meaningful unsafe mutants with counterexamples;
- an explicit finite-domain assumption statement;
- no depth parameter in the safety claim;
- a retained machine-readable model, command, solver version, and result.

If the backend cannot establish this, retain the negative result and document the exact blocker. Do not replace "unbounded" with a larger bound.

---

## Experiment V3 — Bounded vs unbounded scaling

### Goal

Show when bounded model checking is useful and when unbounded checking wins or fails.

### Design

For the same model family, compare:

- native explicit-state exploration;
- Z3 BMC at increasing depths;
- unbounded symbolic safety backend;
- each with and without COI.

Use both safe models and unsafe models whose shortest counterexample depths are deliberately placed at 1, 2, 4, 8, 16, and 32 transitions.

### Expected interpretation

BMC should find shallow bugs efficiently but cannot upgrade a safe result to an unbounded proof. The unbounded backend should demonstrate the assurance distinction even if it is slower on small bug-finding cases.
