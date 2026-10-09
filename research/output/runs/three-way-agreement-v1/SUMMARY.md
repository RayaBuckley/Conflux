# Three-way verdict agreement on the delegation IR family

- Command: `python scripts/generate_three_way_agreement.py`
- Re-check: `python scripts/generate_three_way_agreement.py --check` (writes nothing; compares a
  fresh run against this bundle, ignoring the timestamp)
- Artefact: `result.json`
- Inputs: the eleven `delegation_ir` variants from `src/conflux/verification/delegation_ir.py`

## Result

The reference interpreter, the Z3 bounded model checker and the nuXmv IC3 backend agree on all
eleven variants once verdicts are compared by class. The raw verdict strings are kept per variant,
because `bounded_safe` and `safe` state different scopes of guarantee.

| Variant | Reference | Z3 | nuXmv |
| --- | --- | --- | --- |
| `delegation-ir:canonical` | `safe` | `bounded_safe` | `safe` |
| the other ten mutations | `unsafe` | `unsafe` | `unsafe` |

nuXmv was the real binary, version 2.2.0 (from `nuXmv -h`), not vendored into the repository and
installed user-locally; its version
is folded into `solver_hash` on every row. Ten of eleven variants are refuted, so the battery is a
positive control and not a set of trivially safe cases. A second invocation under `--check`
reproduced every verdict.

## Limits

- Three tools agreeing is evidence about the encodings, not a proof of the IR semantics: all three
  read the same IR, and the Z3 result is bounded.
- A backend that does not run is recorded `unavailable` and never counted as agreeing. On a host
  without `nuXmv`, `nuxmv_measured` is 0 and `all_agree` is `null`.
- Agreement covers the eleven enumerated variants, not every IR the schema admits.
