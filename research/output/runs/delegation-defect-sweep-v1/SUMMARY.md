# Delegation defect sweep: every combination of the nine defects

Suite: delegation-ir-defect-space (`build_combined_delegation_ir` over all subsets), 512 subsets of 9 defects.
Source commit: `1dc84cc80719210d2f4018829af433acc8232722`.

The population is closed by construction: every one of the 512 subsets of the defect space appears exactly once, so this is not a selected list of variants.

Verdict classes agree on 512 of 512 subsets (0 class disagreements). The raw verdict strings agree on 511; they differ on 1 subset(s), which is the bounded checker's `bounded_safe` against the interpreter's `safe` on the canonical body: one class, two scopes of guarantee.

Positive control: 511 subsets carry an unsafe reference verdict, so an all-clear reading cannot come from a space that nothing can refute; the 1 subset(s) that are not refuted are recorded by id (delegation-ir:combined:none).

What this shows: on every subset of the nine-defect space the z3 encoding reproduces the reference interpreter's verdict class, and both backends refute every subset that names at least one defect.

What this does not show: Agreement between these two encodings on every subset of the defect space is not a proof of the delegation semantics: the reference interpreter is the definition, and the space is a closed set of edits to one consumption rule rather than every way a delegation system can go wrong.

Rerun: `python scripts/generate_delegation_defect_sweep.py`
Detail: `evidence.json` in this directory.
