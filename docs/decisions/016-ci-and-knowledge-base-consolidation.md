# Specification 016: CI and Knowledge-base Consolidation

Type: specification
Status: accepted for implementation on `main`

## Goal and success criteria

Restore trustworthy Windows/Linux validation and make the repository's current
architecture, evidence, and research status understandable without consulting
overlapping historical reports. Success means that all supported CI jobs run
to completion, the installed offline program is exercised end to end, archived
source material is integrity protected, and every current document has one
clear responsibility.

## Current architecture and affected boundaries

The security-domain and ITES APIs are not changed. The affected boundaries are
repository audit, GitHub Actions, installed-wheel validation, documentation,
report evidence, and the current manuscript.

The failing Linux audit is caused by archived text checksums being calculated
from platform-specific working-tree bytes. Git stores the authoritative paper
objects, while checkout line endings are presentation detail. Matrix
`fail-fast` then cancels the remaining independent jobs.

## Evidence and ownership decisions

Repository truth is interpreted in this order:

1. code, tests, schemas, and retained generated evidence;
2. accepted specifications and architecture decision records;
3. current architecture, operation, status, and claim documentation;
4. current report-derived analysis;
5. immutable archived reports and the archived previous paper.

A disagreement between levels is a defect to reconcile, not permission to
silently select a convenient claim. `docs/evidence/task-registry.json` owns programme
status and `docs/evidence/CLAIMS.md` owns claim strength. New documentation must extend
an existing owner where possible rather than create a competing summary.

## Archive contracts

The paper manifest records, per file, a checksum mode, SHA-256 digest, and Git
blob identity. UTF-8 text uses LF-canonical content so CRLF and LF checkouts are
equivalent; binary content uses exact bytes. An index-object change, semantic
text edit, binary edit, missing file, or unsupported mode fails validation.
The files under `research/publications/paper/` remain unmodified.

The 18 original report artefacts move into five dated packages under
`research/reports/archive/`. Their repository blobs must not change. The report manifest
records the original and archive path, package, media type, repository-blob
size and SHA-256, Git blob ID, role, duplicate relationship, limitations, and
supersession links. Original and archive paths are unique; supersession links
resolve without cycles; known duplicate files remain separately preserved and
declared.

Raw task IDs are source-local. `research/reports/analysis/task-crosswalk.json` assigns a
source-qualified ID to every report task and points to the canonical registry
or an explicit explanatory disposition. It does not become another status
registry.

## Documentation and manuscript decisions

The root README is a short runnable entry point. `WORKFLOW.md` is the human
workflow, while `docs/AI_AGENT_GUIDE.md` is the concise machine-collaboration
contract. The documentation hub routes readers by goal and records ownership.
Core explanatory documents include a compact rationale section and link to
ADRs for history instead of repeating it.

`research/reports/analysis/PROJECT_ANALYSIS.md` is the sole cohesive interpretation of
the archived reports. `AI_CONTEXT.md` supplies only navigation, trust order,
invariants, and refresh instructions. Normative behavior stays in code,
schemas, specifications, and ADRs.

The canonical current paper remains the LaTeX source under `research/publications/manuscript/`.
Implementation statements must link to repository evidence; numerical results
are filled only from retained result or validation artefacts. Live-model,
AgentDojo, solver-binary, container, and cluster results remain explicitly
gated when unavailable.

## CI and runnable-program decisions

GitHub Actions use immutable commits of the current GitHub-maintained action
releases, read-only repository permissions, explicit timeouts, and
`fail-fast: false`. The portable matrix remains Python 3.12 and 3.13 on Windows
and Linux. Coverage evidence is retained even when another job fails.

Installed-wheel validation runs `doctor`, `demo`, `plan demo`, `sled run`, and
`report` in a temporary environment without credentials or network access.
Security denials remain successful application outcomes; unavailable optional
backends remain explicit non-success outcomes.

## Failure modes

- Unknown archive schemas, modes, package references, or task mappings fail.
- Archived report blobs that differ from their pre-move object IDs fail.
- Current documents with broken local links, encoding damage, obsolete report
  paths, or missing required rationale fail.
- Optional external capabilities never become core CI requirements.
- CI cancellation caused by a separate matrix failure is not accepted as test
  evidence.

## Tests and acceptance criteria

- Unit tests cover LF/CRLF equivalence, semantic and binary mutations, missing
  archive entries, and object-identity failures.
- Audit tests cover report uniqueness, checksums, duplicates, acyclic lineage,
  source-qualified task coverage, documentation ownership, links, encoding,
  terminology, and obsolete paths.
- The installed wheel completes all documented offline commands and validates
  their output evidence.
- The portable validator passes audit, schema and golden regeneration, pytest
  with at least 90% branch coverage, Ruff, strict mypy, wheel build/install,
  and CLI smoke.
- All four supported CI matrix jobs and the manuscript build succeed.
- `git diff --check` passes and the final `main` worktree is clean.

## Delivery and evidence

Changes are committed atomically on `main`; upstream history is not rewritten.
The CI repair is pushed and observed before documentation migration. Generated
validation evidence is committed separately from the implementation it
measures. The final status and manuscript cite only that retained evidence.
