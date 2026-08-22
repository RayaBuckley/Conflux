# Dynamic-planning example

Run the deterministic vertical slice from an installed package:

```text
conflux plan demo --output runs/plan-demo
```

The scripted planner first proposes an unauthorised write. ITES blocks it.
The declared continuation then appends a safe write and a safe-stop node while
also creating a diagnostic subplan. The safe write is grounded, re-authorised,
certificate-bound, and executed in memory. The output contains a versioned
result and deterministic replay trace; it performs no host filesystem effect.

## Node types

The plan graph supports the following node kinds:

| Node | Purpose |
|---|---|
| `model_call` | Invoke a model and bind its output |
| `action_template` | Ground and mediate an operation through ITES |
| `branch` | Explore alternative continuations from one parent |
| `loop` | Iterate over a binding set |
| `continue_planning` | Apply a plan patch and continue |
| `approval` | Gate on an external approval signal |
| `delegation` | Request a scoped delegation grant |
| `subplan` | Embed a nested plan with its own scope |
| `terminal` | Mark success, safe-stop, or failure |

## Multi-step flow

A typical multi-step plan proceeds as follows:

1. A `model_call` node proposes actions; the output is bound to artifact names.
2. An `action_template` node grounds the proposed action against the binding
   environment.
3. ITES mediates the grounded action: it checks authorisation, read, visibility,
   and consent at the current Principal Context.
4. If authorised, the action executes with a freshly issued decision certificate.
   If blocked, a `continue_planning` node applies a plan patch and the plan
   retries or stops.
5. The process repeats until a `terminal` node is reached.

Every grounded effect is re-mediated at action time. The planner cannot
manufacture authority; it can only propose actions that ITES then authorises
or blocks.

