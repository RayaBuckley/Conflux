# Conflux Module Guide

> Migration notice: this legacy module map is retained for historical context.
> Use [ARCHITECTURE.md](ARCHITECTURE.md), [REFERENCE.md](REFERENCE.md), and
> [AUDIT.md](AUDIT.md) as the current sources of truth.

This is the high-level public map of the repository. Individual modules may
contain additional internal helpers that are not extension points.

## Dependency direction

```text
core → execution → auth/policy → ites → providers/benchmarks → sled reporting
```

`core` is the security-model source of truth. `sled` evaluates the model and
may depend on it, but core and ITES must not depend on benchmark code.

Every Python file has one primary responsibility. Abstract methods in adapter
and protocol files are intentional extension points; concrete security
behavior belongs in the canonical layers below.

## Domain and execution

- `core/principals.py`, `resources.py`, and `permissions.py` define security
  identities, protected objects, and permission values.
- `core/provenance.py` and `artifacts.py` define immutable information flow.
- `core/actions.py` defines the action taxonomy and proposals.
- `core/consent.py`, `chat_policy.py`, and `session.py` define consent,
  visibility, and execution-session context.
- `execution/operations.py` provides provenance-preserving transformations.

## Security and mediation

- `auth/authorisation.py` evaluates Principal Context authority.
- `policy/base.py` defines policy requests, decisions, and policy interfaces.
- `policy/adapters.py` and `policy/aws.py` adapt provider policy semantics.
- `ites/__init__.py` defines the ITES contract and result types.
- `ites/mediator.py`, `state.py`, and `properties.py` implement mediation,
  immutable execution state, and security properties.

## Evaluation and integration

- `sled/environment.py` and `scenario.py` model evaluation worlds.
- `sled/attack.py` defines attack extension points.
- `sled/defences/` contains comparison defences and the ITES adapter.
- `sled/evaluator.py`, `evaluation.py`, and `benchmark_runner.py` execute
  suites and branches.
- `sled/trace.py`, `task_classification.py`, `statistics.py`, and
  `reporting.py` produce observable outcomes.
- `providers/` materialises filesystem and Docker environments.
- `benchmarks/` integrates native and external benchmark systems.

The main extension interfaces are `ITES`, `Policy`, `PolicyAdapter`,
`ProviderAdapter`, `Attack`, `TaskSuite`, and the benchmark/external protocols.
Detailed contracts should be specified before adding new implementations.
