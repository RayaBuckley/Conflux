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

