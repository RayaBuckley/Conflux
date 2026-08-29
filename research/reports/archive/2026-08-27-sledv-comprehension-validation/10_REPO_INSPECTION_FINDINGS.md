# Repository Inspection Findings Relevant to This Programme

**Inspection date:** 27 August 2026  
**Branch:** public `main`

## 1. Existing architecture is already suitable for a comprehension-first phase

The repository describes native SLED as breadth-first exploration of a typed transition system with canonical future-relevant state, predecessor edges, explicit bounds, and shortest discovered counterexamples. It already reserves `SAFE` for exhausted finite state spaces, uses `BOUNDED_SAFE` when configured bounds truncate exploration, and returns `UNKNOWN` on modelling/backend failures.

This means the first educational task does not require a redesign. The concepts can be taught directly from the current implementation.

## 2. The verification stack has two useful independent layers

The repository separates native SLED from a callback-free serialisable verification IR. The IR has:
- a reference interpreter;
- optional Z3 bounded checking;
- a nuXmv subset adapter;
- property-scoped cone-of-influence reduction.

This separation is useful for validation because agreement between independently implemented checking paths is stronger evidence of verifier correctness than one implementation checking itself.

It still does not establish model fidelity.

## 3. The repository itself already states the correct limitation

The comparative-verification design document explicitly says external-defence claims must be validated against papers and implementations before publication. It also says to model one contemporary defence deeply and only then add further defences.

That design should now become an enforced workflow rather than guidance.

## 4. There is a concrete claim mismatch in the current code

`src/conflux/verification/defence_models.py` says its factories “faithfully encode” small finite instances of contemporary defences and its docstrings directly assert PE vulnerabilities.

At the same time, the comparative-verification report says such claims require validation.

This should be repaired immediately. The implementation can remain; the evidential label must change.

## 5. Tests currently validate the abstractions, not the external systems

`tests/test_defence_models.py` checks that candidate CaMeL, Progent, PACT, Dual-LLM and ITES IRs return expected finite-model verdicts. These tests are useful for regression and verifier development.

They do not, by themselves, show:
- that the CaMeL model matches CaMeL;
- that the “native property Q” exactly matches the published guarantee;
- that omitted mechanisms cannot invalidate a PE witness;
- that reference implementations reproduce the witness.

The test naming should reflect this distinction.

## 6. The claim ledger is more conservative than some implementation comments

The ledger explicitly labels comparative results as bounded evidence and says they are finite IR models, not implementation-conformance evidence. That is good.

The next improvement is to add the missing middle category: **model-fidelity evidence**.

## 7. Current SLED-V documentation is technically accurate but not pedagogical enough

`docs/reference/SLED.md` is an effective reference page for someone who already knows model checking. It introduces BFS, canonical state, invariants, BMC, COI, self-composition, and property hierarchy compactly.

It is not sufficient as the researcher's first introduction because:
- it moves quickly from core state exploration into solver/reduction terminology;
- it does not walk one concrete example through all layers;
- it does not explicitly teach the distinction between verifier correctness, model fidelity, and implementation conformance.

A separate tutorial is preferable to making the reference document much longer.

## 8. Existing negative controls are an underused educational asset

The repository already contains defective variants and mutation evidence. These should become a prediction-first comprehension exercise. The researcher should predict a minimal witness before execution.

## 9. The safest near-term paper result is internal validation, not broad comparison

Until external models are validated, the strongest SLED-V story is:
- continuity with historical SLED;
- exact reproduction where retained;
- state-based checking;
- minimal counterexamples;
- seeded defective ITES variants;
- reference-interpreter/solver agreement on supported finite fixtures;
- explicit boundedness.

External models can be restored incrementally after fidelity review.
