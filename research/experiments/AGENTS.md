# Experiments guidance

Experiments holds manifest definitions, test suites, baselines, and the pinned
AgentDojo lock. Experiment manifests are versioned inputs; retained run output
lives under `output/runs/`.

- `manifests/`: YAML and JSON manifests that parameterise experiment runs.
- `suites/`: canonical scenario suites, legacy reproduction suites, and
  benchmark-specific corpora.
- `baselines/`: immutable baseline results for comparison.
- `agentdojo.lock`: pins the AgentDojo version, Git tag, commit, and benchmark
  version.

When adding experiment definitions:

- Keep manifests schema-checked and deterministic. Every manifest must have a
  corresponding schema in `schemas/`.
- Do not embed live model output or credentials in experiment definitions.
- Local run output goes under `experiments/local-runs/` (gitignored) or
  `output/runs/` (curated fixtures only).
