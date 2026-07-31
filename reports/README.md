# Conflux Reports

This directory separates immutable research input from maintained analysis:

- `archive/` preserves every original report as repository evidence;
- `analysis/PROJECT_ANALYSIS.md` will provide the cohesive current synthesis;
- `analysis/AI_CONTEXT.md` will provide compact agent navigation;
- `analysis/task-crosswalk.json` will namespace historical task IDs.

Until analysis is present, use [current project status](../docs/STATUS.md) and
the [machine-readable task registry](../docs/task-registry.json) for
implementation state. Reports do not override code, tests, schemas, accepted
specifications, ADRs, or retained evidence.

## Why preserve and interpret separately?

The reports were written at different repository snapshots, use overlapping
task identifiers, and sometimes supersede one another. Editing them would erase
the evidence needed to understand those recommendations; treating them as
current would reintroduce stale claims. Archive integrity and current analysis
therefore have separate owners.

The maintained analysis should summarize a finding once, link its original
source, and point to canonical evidence. Mutable status remains exclusively in
`docs/task-registry.json`.
