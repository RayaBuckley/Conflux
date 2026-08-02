# Public API Reference

- `conflux.domain`: Principal, PrincipalContext, Provenance, Artifact,
  ResourceRef, trusted `OperationArgumentSchema`, immutable `ActionArgument`,
  typed actions, `ProposalBatch`, disclosure and attribution records,
  independent decisions, sessions, and snapshots.
- `conflux.ports`: model, action/argument/read/visibility/consent policy,
  environment, executor, and trace protocols.
- `conflux.policy`: deterministic offline policies, including pointwise
  argument grants and audience disclosure levels.
- `conflux.application`: DecisionPipeline and MediationService.
- `conflux.ites`: TransitionKernel, MediatingITES, branch state, traces,
  per-step certificates, authorised plans, assessments, and reports.
- `conflux.evaluation`: ExplicitStateChecker, bounds, verdicts, properties, and
  evaluation services, including selector/disclosure/attribution mutants.
- `conflux.verification`: serialisable finite-state IR, reference interpreter,
  `reduce_cone_of_influence`, checked reduction comparisons, and optional Z3
  and nuXmv backends.
- `conflux.adapters`: provider, policy, and benchmark translations.

Stable offline adapters are `ScriptedModel`, `load_scenario`,
`InMemoryExecutor`, and `ConfinedFilesystemExecutor`. The filesystem executor
is dry-run by default and live writes require a matching precondition hash.
See [Deterministic Runtime](RUNTIME.md) for the fail-closed contract.

The installed `conflux` entry point exposes the supported runtime and native
verification workflows. See the [CLI contract](CLI.md) for commands and exit
codes.

There are no compatibility imports from `core`, `auth`, `research`, or
`compatibility`.
