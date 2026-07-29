# Public API Reference

- `conflux.domain`: Principal, PrincipalContext, Provenance, Artifact,
  ResourceRef, typed actions, `ProposalBatch`, independent decisions, sessions,
  and snapshots.
- `conflux.ports`: model, policy, environment, executor, and trace protocols.
- `conflux.policy`: deterministic offline policies.
- `conflux.application`: DecisionPipeline and MediationService.
- `conflux.ites`: TransitionKernel, MediatingITES, branch state, traces,
  per-step certificates, authorised plans, assessments, and reports.
- `conflux.evaluation`: ExplicitStateChecker, bounds, verdicts, properties, and
  evaluation services.
- `conflux.adapters`: provider, policy, and benchmark translations.

Stable offline adapters are `ScriptedModel`, `load_scenario`,
`InMemoryExecutor`, and `ConfinedFilesystemExecutor`. The filesystem executor
is dry-run by default and live writes require a matching precondition hash.
See [Deterministic Runtime](RUNTIME.md) for the fail-closed contract.

There are no compatibility imports from `core`, `auth`, `research`, or
`compatibility`.
