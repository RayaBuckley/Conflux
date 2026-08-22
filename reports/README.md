# Conflux Reports

This directory separates immutable research input from maintained analysis:

- `archive/` preserves every original report as repository evidence;
- [Project analysis](analysis/PROJECT_ANALYSIS.md) provides the cohesive current synthesis;
- [AI context](analysis/AI_CONTEXT.md) provides compact agent navigation;
- `analysis/task-crosswalk.json` namespaces historical task IDs.

Use [current project status](../docs/evidence/STATUS.md) and the
[machine-readable task registry](../docs/evidence/task-registry.json) for implementation
state. Reports do not override code, tests, schemas, accepted specifications,
ADRs, or retained evidence.

## Why preserve and interpret separately?

The reports were written at different repository snapshots, use overlapping
task identifiers, and sometimes supersede one another. Editing them would erase
the evidence needed to understand those recommendations; treating them as
current would reintroduce stale claims. Archive integrity and current analysis
therefore have separate owners.

The maintained analysis should summarize a finding once, link its original
source, and point to canonical evidence. Mutable status remains exclusively in
`docs/evidence/task-registry.json`.

## Analysis reports

| Report | Path |
|--------|------|
| Foundational security literature | [analysis/2026-08-13-foundational-security-literature.md](analysis/2026-08-13-foundational-security-literature.md) |
| Maximal security and synthesis | [analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md](analysis/MAXIMAL_SECURITY_AND_SYNTHESIS.md) |
| Comparative defence verification | [analysis/COMPARATIVE_DEFENCE_VERIFICATION.md](analysis/COMPARATIVE_DEFENCE_VERIFICATION.md) |
| Results and experiment plan | [analysis/RESULTS_AND_EXPERIMENT_PLAN.md](analysis/RESULTS_AND_EXPERIMENT_PLAN.md) |
| GLM synthesis brief | [analysis/GLM_SYNTHESIS_BRIEF.md](analysis/GLM_SYNTHESIS_BRIEF.md) |
| Reviewer meeting checklist | [analysis/REVIEWER_MEETING_CHECKLIST.md](analysis/REVIEWER_MEETING_CHECKLIST.md) |
| Supervisor meeting consolidation | [analysis/2026-08-19-supervisor-meeting-consolidation.md](analysis/2026-08-19-supervisor-meeting-consolidation.md) |
