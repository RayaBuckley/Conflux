# Experiment Definitions

Tracked experiment inputs live here; local outputs belong in
`experiments/local-runs/` or ignored `runs/` directories. A curated evidence
bundle is committed only when it contains a manifest, raw trace, versioned
result, generated summary, checksums, and one rerun command.

- `suites/legacy-reproduction/` reconstructs the three archived-paper
  environment descriptions using the previous prototype's author/trust
  assumptions. It does not reproduce or validate archived numerical claims.
- `suites/canonical/` expresses corrected Principal Context, reader, and
  pointwise-authority semantics. Results from the two suites are not directly
  comparable without an explicit semantic-difference analysis.
- `manifests/` records immutable run parameters and source commits.
- `manifests/agentdojo-stratified-selection-v1.json` freezes which (suite, user
  task, injection vector) pairs an AgentDojo breadth sweep executes; regenerate and
  check it with `python scripts/select_agentdojo_tasks.py [--check]`.
