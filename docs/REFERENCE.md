# Conflux Reference

Purpose: define the canonical concepts and public API ownership. This is the
reference layer between the high-level architecture and source docstrings.

Owner: the maintainers of `src/conflux`; update this document when a public
contract changes. Detailed operational behavior belongs in source docstrings
and tests, not here.

## Canonical concepts

- `Principal`: an entity that can influence execution or hold authority.
- `Principal Context`: the principals derived from the provenance of the
  information influencing an action.
- `Provenance`: immutable causal metadata carried by artifacts.
- `Artifact`: a value plus provenance and visibility metadata.
- `Resource`: a protected provider object targeted by an action.
- `Permission`: an atomic capability evaluated by policy.
- `Action`: a proposed primitive, nested, delegation, visibility, consent, or
  control operation.
- `ITES`: the canonical mediation boundary.
- `SLED`: the evaluation framework for ITES and comparison defences.

## Public API ownership

| API area | Owning package | Detail |
|---|---|---|
| Domain values | `conflux.core` | `docs/ARCHITECTURE.md` and module docstrings |
| Provenance-preserving derivation | `conflux.execution` | `execution/operations.py` |
| Authority and action decisions | `conflux.auth` | `auth/authorisation.py` |
| Policy translation | `conflux.policy` | `policy/base.py` and adapters |
| Defence mediation | `conflux.ites` | `ites/__init__.py`, `mediator.py` |
| Provider translation | `conflux.providers` | provider interfaces and implementations |
| Evaluation | `conflux.sled` | evaluator, traces, statistics, reporting |
| External benchmark translation | `conflux.benchmarks` | native and external adapters |

During the clean-slate migration, `conflux.domain` is the preferred import
surface for new provider-neutral code. `conflux.application` owns use-case
facades and `conflux.ports` owns Protocol interfaces. Existing `core`, `ites`,
and `sled` exports remain supported until their callers are migrated; they are
not permission to add new cross-layer dependencies.

`ites.mvp`, `ites.reference`, and the one-shot SLED evaluator are compatibility
or research harnesses. They must delegate to or translate into canonical types
and must not silently redefine security semantics.

## Reading below this level

Use the [module ledger](AUDIT.md) to locate a file, then read its module
docstring and linked tests. Use [Glossary](GLOSSARY.md) for terminology and
[Architecture](ARCHITECTURE.md) for dependency and security invariants.
