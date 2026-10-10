# Delegation defect sweep: every combination of the nine defects

Suite: delegation-ir-defect-space (`build_combined_delegation_ir` over all subsets), 512 subsets of 9 defects.
Source commit: `184bf21c8cbb42ee339fe3a963fe9a78b156d118`.

The population is closed by construction: every one of the 512 subsets of the defect space appears exactly once, so this is not a selected list of variants.

Verdict classes agree across all three backends on 512 of 512 subsets (0 class disagreements). Against the interpreter, the Z3 raw verdict strings agree on 511 and differ on 1 subset(s), which is the bounded checker's `bounded_safe` against the interpreter's `safe` on the canonical body: one class, two scopes of guarantee. The nuXmv IC3 verdicts agree with the interpreter as raw strings on 512 subset(s) and as classes on 512; a run without nuXmv records 0 unmeasured subset(s) and makes no three-way claim.

Positive control: 511 subsets carry an unsafe reference verdict, so an all-clear reading cannot come from a space that nothing can refute; the 1 subset(s) that are not refuted are recorded by id (delegation-ir:combined:none).

What this shows: on every subset of the nine-defect space the Z3 and nuXmv encodings reproduce the reference interpreter's verdict class, and all three backends refute every subset that names at least one defect.

What this does not show: Agreement between these three encodings on every subset of the defect space is not a proof of the delegation semantics: the reference interpreter is the definition, and the space is a closed set of edits to one consumption rule rather than every way a delegation system can go wrong.

Rerun: `python scripts/generate_delegation_defect_sweep.py`
Detail: `evidence.json` in this directory.
