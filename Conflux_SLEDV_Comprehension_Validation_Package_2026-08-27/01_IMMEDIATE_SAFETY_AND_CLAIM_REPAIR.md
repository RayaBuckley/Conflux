# Immediate Safety and Claim Repair

## Objective

Prevent the repository and workshop paper from accidentally treating AI-authored comparative models as faithful representations before they have been independently validated.

## Why this is necessary

The repository already contains the right caution in the comparative-verification research design: external-defence claims must be validated against papers and implementations before publication, and only systems that can be represented faithfully enough should be included.

However, the implementation file currently describes its factories as faithfully encoding the external defences. Tests also use strong names such as “CaMeL satisfies its own property Q but violates Conflux PE”. These are stronger than the current evidence supports.

This is a claim-governance defect, even if the code itself is useful.

## Tasks

### 1. Relabel comparative models

In `src/conflux/verification/defence_models.py`:

- replace language such as “faithfully encodes” with “small finite abstraction intended for hypothesis generation and verifier testing”;
- use `*-inspired` or `*-candidate-abstraction` identifiers until validation is complete;
- state that the abstraction is **not implementation-conformance evidence**;
- remove assertions in docstrings that an external system has a PE vulnerability unless that follows from validated source semantics.

Do not delete the models. They remain valuable fixtures.

### 2. Relabel tests

In `tests/test_defence_models.py`:

- distinguish tests of the **model** from claims about the named defence;
- e.g. rename conceptual descriptions from “CaMeL violates PE” to “current CaMeL candidate abstraction admits a PE counterexample”;
- preserve tests that ensure the verifier returns the expected result for the abstraction;
- add a marker or metadata field `validation_status = "unvalidated_external_abstraction"`.

### 3. Update claim ledger

For each external defence:

- status must be `preliminary model`, `unvalidated abstraction`, or equivalent;
- evidence should state what is actually established: “the current finite IR fixture has property X”;
- explicitly state that this does not establish the published defence or reference implementation has property X.

ITES reference and intentionally defective ITES controls can retain stronger language where they are traced to Conflux semantics.

### 4. Add a model-fidelity registry

Create a machine-readable registry, e.g.

`docs/evidence/defence-model-fidelity.json`

with fields:

```json
{
  "model_id": "camel-candidate-v1",
  "external_system": "CaMeL",
  "status": "unvalidated",
  "supported_fragment": [],
  "primary_sources": [],
  "source_to_rule_traceability": [],
  "published_examples_passed": 0,
  "published_examples_total": 0,
  "differential_cases_passed": 0,
  "differential_cases_total": 0,
  "known_omissions": [],
  "approved_for_publication_claims": false
}
```

### 5. Add a hard publication gate

Repository audit should fail if:

- an unvalidated external model is described as “faithful”, “verified CaMeL”, “CaMeL is unsafe”, etc.;
- manuscript tables promote an external-model verdict when `approved_for_publication_claims` is false.

## Acceptance criteria

- Existing models still run.
- No model is deleted merely because validation is incomplete.
- Tests distinguish verifier behaviour from external-system truth.
- The claim ledger and manuscript cannot silently over-promote an unvalidated abstraction.
- A human can inspect one registry entry and immediately know the evidential status.
