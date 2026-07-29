# ADR 007: Legacy implementation mapping

Status: superseded by ADR 008

## Decision

The previous-project implementation is an archived semantics reference, not a
public compatibility target. Its concepts map as follows:

| Legacy concept | Conflux owner | Migration rule |
|---|---|---|
| `User` | `Principal` | identity uses stable IDs; policy owns permissions |
| `Data` | `domain.environment.DataItem` | scenario metadata is not provenance |
| `Environment` | `EnvironmentSnapshot` | providers expose snapshots through ports |
| `PrimitiveAction` | `domain.actions.PrimitiveAction` | declarative action only |
| `LLMExecutionAction` | `NestedExecutionAction` | nested execution remains mediated |
| `MyLogic` | `application.MediationService` and canonical ITES | no direct provider side effects |
| `Evaluator` | `evaluation.Evaluator` | one-shot and exhaustive APIs stay distinct |

The old callback and predefined-logic shapes were temporarily exposed through
`conflux.compatibility`. ADR 008 completed their removal.

## Consequences

The migration retained this mapping as historical evidence. All callers now use
the canonical domain and ITES APIs; no compatibility layer remains.
