# Conflux Status

Purpose: record evidence-backed implementation status and prioritized follow-up
work. This is the source of truth for what is implemented, tested, blocked, or
planned; architecture belongs in `ARCHITECTURE.md`.

## Current state

- Core domain, provenance, action, policy, ITES, SLED, provider, and benchmark
  modules exist and are documented in the [audit ledger](AUDIT.md).
- Repository audit and static compilation pass.
- Python 3.12 setup is available through `scripts/setup.ps1`.
- Runtime validation passes after migrating callers to the canonical artifact,
  resource, provenance, ITES, policy, and evaluator contracts.
- Strict mypy and Ruff validation pass for the source and test tree.
- Clean-slate migration slice added: `conflux.domain`, `conflux.ports`,
  `conflux.application`, and `conflux.adapters`. These currently provide typed
  boundaries over the validated implementation; deeper caller migration is
  intentionally staged.

## Work status

| Area | Status | Evidence or next action |
|---|---|---|
| Domain model | Canonical contract implemented | provenance/resource regression tests |
| ITES mediation | Implemented with isolated reference path | named guarantee and nested-action tests |
| SLED evaluation | One-shot/exhaustive surfaces separated | evaluator/report type checks |
| Providers | Adapter prototypes | add boundary contract tests |
| External benchmarks | Optional adapters | require integration fixtures and assumptions |
| Documentation audit | In progress | keep ledger synchronized with changes |
| Clean-slate boundaries | Initial slice | migrate core/ITES/SLED callers incrementally |
| Evaluation trace contract | Initial versioned record | connect SLED trace writers and add golden fixtures |
| Provider-neutral environment | Initial contract | migrate provider and SLED callers from legacy environment types |

## Post-paper extensions

Organisational policy adapters, provider realism, external benchmark execution,
and AI development tooling extend beyond the archived paper. They must not be
described as paper-validated claims without reproducible evidence.
