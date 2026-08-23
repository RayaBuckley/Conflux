# ADR 011: Open-ended dynamic plans

Status: accepted

## Context

`ProposalBatch.ORDERED_PLAN` is intentionally small: it mediates a fixed list
of already-grounded actions. It cannot represent values produced by earlier
nodes, branches, loops, subplans, or a model request for the next plan
fragment. Treating those behaviours as an enlarged action subtype would mix
untrusted planning with the ITES security boundary.

The archived 30 July 2026 dynamic-planning assessment requires realistic
planning while preserving action-time mediation and honest verification
claims.

## Decision

Conflux has two distinct planning surfaces:

1. `ProposalBatch.ORDERED_PLAN` remains the restricted, fixed-action semantic
   corpus used by the canonical kernel.
2. `conflux.planning` owns an open-ended, immutable plan program. It grounds
   one effect at a time and submits that effect to the existing application
   mediation service.

The planning domain separates:

- an authenticated `OperationSchema`;
- an `ActionTemplate` containing typed bindings;
- a `GroundAction` whose operation and arguments are fully resolved;
- a `Plan` containing typed nodes and explicit dependencies;
- a `PlanPatch` returned at a continuation point; and
- immutable `PlanExecutionState` and records.

A planner is a pure port. Natural-language text is never executable. Patches
may append nodes, replace an unstarted subtree, spawn a subplan, request an
approval node, or terminate. A patch cannot modify completed history.

Each grounded effect is constrained by the union of:

- invocation provenance;
- node and path-control provenance;
- branch-condition provenance; and
- provenance of every bound argument.

New nodes produced by a continuation conservatively inherit the complete
trusted provenance of the planner call. A later dataflow-sensitive refinement
must prove that it does not remove an influence. Model-supplied provenance is
never trusted.

Planning approval does not grant action authority. Every grounded effect is
converted to a canonical action, independently mediated at execution time,
bound to its exact decision certificate, and executed only through an
`ExecutorPort`. Policy revocation therefore takes effect between any two
nodes.

Generated code is data supplied to an authenticated `execute_code` operation.
Its capability envelope is separately authorised and enforced by a sandbox
adapter. An unavailable or unenforceable capability fails closed.

Runtime plans may be cyclic and operationally open-ended. Native SLED explores
a bounded worst-case abstraction of continuation patches and capability
effects. Formal adapters return `UNKNOWN` for unsupported effects or
unbounded domains. Neither runtime support nor bounded evidence is described
as a proof of arbitrary generated program semantics.

## Consequences

- The ITES kernel remains benchmark- and planner-independent.
- Planning is expressive without allowing planner output to bypass mediation.
- Trace schemas need plan, patch, binding, node, and sandbox events.
- Deterministic scripted planners are the conformance baseline.
- Real-model utility and external sandbox enforcement remain separately gated
  evidence claims.
- Earlier `PLAN-001` is narrowed to base plan types, `PLAN-002` to abstract
  verification, and `PLAN-003` to later optimisation. `PLAN-DYN-000..017`
  provide the active delivery graph.
