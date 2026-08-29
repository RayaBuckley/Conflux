# AI Coder Master Implementation Brief

## Mission

Improve epistemic reliability of the SLED-V research programme. Do not add verification sophistication merely because it is implementable.

## Priority order

1. Repair overclaims around external-defence model fidelity.
2. Produce researcher-facing comprehension material.
3. Build one tiny end-to-end worked verification example.
4. Add prediction-first mutation exercises.
5. Make verifier outputs self-explanatory.
6. Validate one external defence deeply.
7. Update paper claims only after evidence gates pass.

## Non-goals

Do not:
- add another solver backend;
- add more external defences;
- add partial-order reduction or symmetry;
- activate delegation;
- broaden planning;
- generate headline comparative tables from unvalidated models;
- rewrite historical evidence;
- silently alter expected results after running tests.

## Evidence discipline

For every task distinguish:
- implementation evidence;
- finite-model verification evidence;
- model-fidelity evidence;
- implementation-conformance evidence;
- empirical evidence.

A passing unit test about a candidate CaMeL IR establishes behaviour of that IR, not behaviour of CaMeL.

## Human review points

Stop and surface a review artifact when:
- interpreting an ambiguous external-paper rule;
- selecting the external defence's native property;
- deciding whether an omission can affect PE;
- accepting a source-to-model mapping as exact;
- classifying a differential disagreement;
- approving an external model for publication;
- changing manuscript claim strength.

## Commit structure

Prefer separate commits:
1. claim/fidelity labelling;
2. comprehension tutorial;
3. worked example;
4. mutation curriculum/evidence;
5. explainable verifier outputs;
6. CaMeL source specification;
7. CaMeL conformance fixtures;
8. optional differential adapter;
9. paper/claim updates.

Each commit should pass repository validation.

## Final report

At completion, produce:
- changed files;
- validation commands/results;
- evidence artifacts;
- unresolved ambiguities;
- claims strengthened;
- claims weakened;
- items requiring researcher review;
- recommended next research step.

The correct outcome may be that an existing external-defence counterexample is withdrawn. Treat discovery of an inaccurate model as progress, not failure.
