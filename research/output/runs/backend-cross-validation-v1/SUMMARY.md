# Cross-backend validation: z3 against the reference interpreter

Suite: delegation-ir-variants (`all_delegation_ir_variants`), 11 variants.
Source commit: `8978a3bdac29f35809f871e9b6a7dbd216637de0`.

Verdict classes agree on 11 of 11 variants (0 class disagreements). The raw verdict strings agree on 10; they differ on 1 variant(s), which is the bounded checker's `bounded_safe` against the interpreter's `safe`: one class, two scopes of guarantee. Both strings and both comparisons are recorded per variant.

Positive control: 10 variant(s) carry an unsafe reference verdict, so an all-clear reading cannot come from a family that nothing can refute. Every variant was measured by z3.

What this shows: the z3 encoding reproduces the reference interpreter's verdict class on every
variant in this fixed, hand-built family.

What this does not show: it is not a proof of the IR semantics. The reference interpreter is
the definition the encoding is checked against, the family is an enumeration rather than a
closed grammar, and agreement on it says nothing about variants outside it.

Rerun: `python scripts/generate_backend_cross_validation.py`
Detail: `evidence.json` in this directory.
