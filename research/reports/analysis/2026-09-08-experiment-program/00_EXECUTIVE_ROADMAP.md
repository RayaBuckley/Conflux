# Executive experiment roadmap

## Research questions

The programme should answer the following questions in roughly this order.

### RQ1 — Can SLED-V provide materially stronger assurance than bounded trace/state exploration?

Target result: an unbounded `SAFE` verdict for the canonical finite ITES authority-confinement model using a symbolic safety algorithm such as IC3/PDR, or a precise explanation of why the current IR/backend cannot establish it.

### RQ2 — Which state-space reductions preserve Conflux security properties and how much do they help?

Measure symmetry reduction, partial-order reduction, cone-of-influence reduction, and authority-aware subsumption independently and cumulatively. Existing COI evidence is a baseline, not the end result.

### RQ3 — How faithfully does the executable ITES kernel implement the verified transition semantics?

Target result: implementation-conformance evidence, not just agreement between hand-written finite models.

### RQ4 — What properties do contemporary system-level defences actually establish under aligned finite models?

Compare each defence under both its native property and Conflux's PE/authority-confinement property. The aim is non-implication and property comparison, not a rhetorical claim that another system is "insecure" under a different threat model.

### RQ5 — What security/utility trade-off does Conflux have with capable real models?

Run the pinned AgentDojo pipeline with a model that can reliably complete multi-turn tool use and the benchmark's answer format. Measure native security, native utility, Conflux mediation outcomes, overhead, and failure categories.

### RQ6 — Does planning recover useful work by reducing unnecessary influence without weakening authority confinement?

Compare existing planning modes on task completion, observations, Principal Context size, blocked actions, calls/tokens/latency, and security outcomes.

### RQ7 — Do persistent memory and richer argument semantics expose new failure modes that Principal Context can prevent or constrain?

Build small formal models first. Add runtime support only when the semantics are clear.

### RQ8 — Can scoped delegation be activated without weakening the central authority invariant?

Only attempt after the delegation lifecycle, policy parity, certificate binding, expiry/revocation, and verification obligations are covered.

## Priority tiers

### P0 — Must complete before broad new features

- Freeze a clean baseline and rerun deterministic evidence.
- Add unbounded-verification backend support or prove the current backend limitation precisely.
- Build implementation-conformance tests from ITES runtime transitions to the verification IR.
- Run a capable-model AgentDojo experiment.
- Run the planning utility experiment with a model that passes structured-output preflight.

### P1 — Strong thesis extensions

- Symmetry + partial-order + authority-aware reduction experiments.
- Comparative defence verification with source-validated abstractions.
- Persistent-memory authority model and delayed-influence experiment.
- Richer argument-effect semantics on a small typed operation set.

### P2 — Only after P0/P1 evidence is stable

- Runtime delegation activation.
- Cedar/provider differential parity beyond readiness.
- Larger production integrations.

## Recommended paper/result structure

A strong fourth-year evaluation chapter could contain four result families:

1. **Verification strength:** bounded vs unbounded, counterexamples, reduction scaling.
2. **Model faithfulness:** implementation-conformance and mutation detection.
3. **Comparative semantics:** native-property vs PE-property results for multiple defences.
4. **Empirical utility:** AgentDojo and planning experiments with capable models.

This is preferable to a long list of loosely connected extensions.
