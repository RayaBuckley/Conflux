# Conflux Status

Purpose: record evidence-backed implementation status and prioritized follow-up
work. This is the source of truth for what is implemented, tested, blocked, or
planned; architecture belongs in `ARCHITECTURE.md`.

## Current state

- Core domain, provenance, action, policy, ITES, SLED, provider, and benchmark
  modules exist and are documented in the [audit ledger](AUDIT.md).
- Repository audit and static compilation pass.
- Python 3.12 setup is available through `scripts/setup.ps1`.
- Runtime tests currently expose legacy API inconsistencies in artifacts,
  resources, provenance, ITES compatibility behavior, and policy adapters.
- Full validation is therefore not yet a passing definition of done.

## Work status

| Area | Status | Evidence or next action |
|---|---|---|
| Domain model | Repair in progress | tests define missing compatibility contracts |
| ITES mediation | Implemented with compatibility paths | reconcile report/declaration semantics |
| SLED evaluation | Implemented with one-shot/exhaustive surfaces | document and test ownership |
| Providers | Adapter prototypes | add boundary contract tests |
| External benchmarks | Optional adapters | require integration fixtures and assumptions |
| Documentation audit | In progress | keep ledger synchronized with changes |

## Post-paper extensions

Organisational policy adapters, provider realism, external benchmark execution,
and AI development tooling extend beyond the archived paper. They must not be
described as paper-validated claims without reproducible evidence.
