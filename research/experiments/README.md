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
- Retained local sweep bundles live under `../output/runs/agentdojo-stratified-<suite>-v1/`:
  `banking` (12 cells, all complete) and `slack` (30 cells, 24 complete; `user_task_16` is refused
  as `malformed_output` because the 0.5B model answers that prompt with an empty tool call, which
  is a model-capability limit and not an adapter gap), `travel` and `workspace`. One sweep is
  `python scripts/run_agentdojo_sweep.py --suite all --model-config <run>/transformers.json` on the
  local nf4 0.5B model, which preflights and runs each suite from the frozen selection; each bundle
  carries a `SUMMARY.md`, and `docs/evidence/VERIFICATION.md` §27 records what they do and do not
  show.
- `../output/runs/three-way-agreement-v1/` is the verdict agreement bundle over the delegation IR
  family: the reference interpreter, Z3 and nuXmv IC3 decide the same eleven variants, and agreement
  is compared by verdict class while the raw verdicts stay per variant. Regenerate it with
  `python scripts/generate_three_way_agreement.py`; `--check` re-measures, compares against the
  retained bundle and writes nothing. `docs/evidence/VERIFICATION.md` §28 records what it does and
  does not show.
