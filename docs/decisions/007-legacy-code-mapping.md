# ADR 007: Legacy implementation mapping

Status: accepted

## Decision

The previous-project implementation is an archived semantics reference, not a
public compatibility target. Its concepts map as follows:

| Legacy concept | Conflux owner | Migration rule |
|---|---|---|
| `User` | `Principal` | identity uses stable IDs; policy owns permissions |
| `Data` | `domain.environment.DataItem` | scenario metadata is not provenance |
| `Environment` | `EnvironmentSnapshot` | providers expose snapshots through ports |
| `PrimitiveAction` | `core.actions.PrimitiveAction` | declarative action only |
| `LLMExecutionAction` | `NestedExecutionAction` | nested execution remains mediated |
| `MyLogic` | `application.MediationService` and canonical ITES | no direct provider side effects |
| `Evaluator` | `evaluation.Evaluator` | one-shot and exhaustive APIs stay distinct |

The old callback and predefined-logic shapes are available only through
`conflux.compatibility`. Canonical domain and ITES modules must not import them.

## Consequences

This preserves the research hypothesis and security invariants while allowing
the old implementation to be removed once callers and evidence are migrated.
The compatibility layer is transitional and must not gain new semantics.
