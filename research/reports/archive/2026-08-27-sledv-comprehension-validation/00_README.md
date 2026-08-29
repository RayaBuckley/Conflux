# Conflux SLED-V Comprehension and Comparative-Model Validation Package

**Purpose:** give an AI coder a constrained, evidence-first programme for making the existing SLED-V work understandable to the project author and making comparative defence models publishable only when their fidelity is independently supported.

## Core principle

Do **not** add new formal-verification features until the existing verification stack can be explained and manually checked end-to-end.

The immediate research risks are epistemic, not implementation breadth:

1. **SLED-V ownership risk:** sophisticated verification code exists, but the researcher must be able to explain what a state, transition, invariant, bound, verdict, counterexample, IR encoding, reference interpretation, and solver result mean.
2. **Comparative-model validity risk:** finite models of external defences currently exist, but a model written by an AI coder is not evidence that the external defence has that behaviour.
3. **Claim-layer risk:** a correct verifier applied to an inaccurate model still produces an irrelevant result.
4. **Paper risk:** claims that outrun researcher understanding or model validation are difficult to defend under review.

## Required outcome

At the end of this programme, the repository should contain:

- a researcher-facing SLED-V tutorial based entirely on small Conflux examples;
- one manually derivable worked model represented identically at the conceptual, native-SLED, verification-IR, reference-interpreter, and Z3 levels;
- a suite of deliberately defective ITES models whose counterexamples are predicted in advance;
- human-readable verification reports that state exactly what each verdict does and does not prove;
- a formal separation between verifier correctness, model fidelity, and implementation conformance;
- comparative external-defence models relabelled as **unvalidated abstractions** until validated;
- one deeply validated external defence model before any broad comparative claim is restored;
- source-to-model traceability, published-example tests, and differential/reference-implementation tests where possible;
- manuscript wording that reflects the evidence level.

## Suggested order

1. Execute `01_IMMEDIATE_SAFETY_AND_CLAIM_REPAIR.md`.
2. Execute `02_SLEDV_RESEARCHER_COMPREHENSION.md`.
3. Execute `03_WORKED_EXAMPLE_AND_MUTATION_CURRICULUM.md`.
4. Execute `04_HUMAN_REVIEWABLE_VERIFICATION_OUTPUTS.md`.
5. Execute `05_COMPARATIVE_MODEL_VALIDATION.md`.
6. Use `06_CaMeL_DEEP_VALIDATION_PROTOCOL.md` for the first external defence.
7. Apply `07_PAPER_AND_CLAIM_POLICY.md`.
8. Gate completion using `08_ACCEPTANCE_CHECKLIST.md`.

The package deliberately prioritises depth over adding more verification backends, reductions, defences, or experiments.
