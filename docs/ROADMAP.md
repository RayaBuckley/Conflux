# Conflux Roadmap

> Migration notice: roadmap ownership moved to [STATUS.md](STATUS.md).

This roadmap records planned work and its current maturity. Statuses are
`proposed`, `specified`, `in progress`, `implemented`, or `deferred`.

## Core security model

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Harden Principal Context derivation and mixed-context authorisation | specified | Core provenance and authorisation | Invariants have explicit tests and documented policy semantics. |
| Deliver typed ITES MVP semantics and branch-safe exploration | in progress | Provenance, actions, SLED | Operational semantics, exhaustive synthetic tests, and reproducible results exist. |
| Model delegation without silently broadening authority | proposed | Actions, consent, policy | Delegation is explicit, bounded, traceable, and tested. |
| Expand provenance for recursive and derived execution | in progress | Execution and ITES state | Provenance survives all supported transformations and nested calls. |

## ITES and execution

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Complete authorisation, visibility, and consent separation | specified | ITES mediator | Each decision has an independent interface and regression suite. |
| Add provider-backed primitive execution | proposed | ProviderAdapter, policy | Execution is mediated and traceable across supported providers. |
| Define stable nested-execution protocol | proposed | Actions, execution state | Recursive calls have explicit inputs, budgets, traces, and outcomes. |

## Policy and providers

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Strengthen policy adapter contracts | specified | Policy interfaces | Adapters expose deterministic requests, decisions, and failure semantics. |
| Add realistic organisational policy scenarios | proposed | Policy, providers, SLED | Scenarios cover ownership, teams, delegation, and mixed Principal Contexts. |
| Expand filesystem and Docker integration coverage | in progress | Provider adapters | Integration tests cover allowed, denied, and failure paths. |

## SLED and benchmarks

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Expand attack and defence scenario catalogue | in progress | SLED task suites | New scenarios remain benchmark-independent and have expected outcomes. |
| Improve traces, metrics, and report comparison | specified | Trace and reporting modules | Results are serialisable, comparable, and useful for research analysis. |
| Complete external benchmark adapters | proposed | Canonical result schema | External traces map without weakening Conflux security semantics. |

## Reproducibility and research tooling

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Add reproducible experiment entry points | proposed | SLED runners and reporting | Configured runs produce versioned metadata and stable result files. |
| Define result schema and artifact layout | specified | Benchmark results | Results can be inspected, compared, and regenerated from documented inputs. |
| Synchronise architecture claims with paper notes | in progress | Architecture and glossary | Paper terminology and claims match tested implementation behaviour. |

## Developer and agent environment

| Work | Status | Dependencies | Completion criteria |
|---|---|---|---|
| Maintain documentation hub, ADRs, and agent templates | implemented | Repository guidance | Agents can discover rules, specifications, tests, and decisions. |
| Establish coverage baseline and validation reporting | in progress | pytest-cov | Coverage is reported consistently without committing generated output. |
| Add CI validation using the documented workflow | proposed | Stable validation script | Pull requests run tests, coverage, Ruff, and mypy. |
