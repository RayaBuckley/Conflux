# Acceptance Checklist

## Phase A — immediate claim repair

- [ ] Comparative model module no longer claims unvalidated models are faithful.
- [ ] External-defence test names/docstrings refer to candidate abstractions.
- [ ] Fidelity registry exists.
- [ ] Claim ledger distinguishes model result from external-system result.
- [ ] Manuscript cannot promote an unapproved external model.

## Phase B — SLED-V comprehension

- [ ] `SLEDV_FOR_PROJECT_AUTHOR.md` exists.
- [ ] Original SLED → native SLED → IR → solver relationship is explained.
- [ ] Every core term has a Conflux example and code pointer.
- [ ] SAFE / BOUNDED_SAFE / UNSAFE / UNKNOWN are understood and documented.
- [ ] Verifier correctness / model fidelity / implementation conformance are separate.
- [ ] Researcher can answer the comprehension questions without repository lookup.

## Phase C — worked example

- [ ] Alice/Mallory scenario manually derived.
- [ ] Same scenario represented in native SLED.
- [ ] Same scenario represented in IR.
- [ ] Reference interpreter state exploration shown.
- [ ] Z3 BMC explained for the same scenario.
- [ ] Outputs agree or discrepancies are documented.

## Phase D — prediction-first mutants

- [ ] requester-only;
- [ ] permission union;
- [ ] stale context;
- [ ] empty context;
- [ ] sibling leakage.
- [ ] Predictions are timestamped/retained before execution.
- [ ] Counterexamples are compared against predictions.
- [ ] At least one deliberately surprising case is discussed if discovered.

## Phase E — explainable outputs

- [ ] Every verdict states exact claim boundary.
- [ ] Bounds are always visible.
- [ ] UNSAFE includes human-readable witness.
- [ ] External abstraction status warning is automatic.
- [ ] JSON and Markdown derive from same structured result.

## Phase F — first external defence

- [ ] CaMeL source specification completed.
- [ ] Security-critical source rules human-reviewed.
- [ ] Current-model discrepancy analysis completed.
- [ ] Supported fragment defined.
- [ ] Native property mapped to actual source claim.
- [ ] Published examples converted to tests.
- [ ] All in-fragment examples agree.
- [ ] Reference implementation differential attempted where feasible.
- [ ] Candidate PE witness manually source-traced.
- [ ] Fidelity registry updated.
- [ ] Publication approval explicitly recorded.

## Phase G — paper

- [ ] Methodology explains three correctness layers.
- [ ] No unvalidated external model is a headline result.
- [ ] SLED-V wording is finite/bounded where appropriate.
- [ ] Negative controls are used as verifier-validation evidence.
- [ ] External comparison wording distinguishes property mismatch from vulnerability.
