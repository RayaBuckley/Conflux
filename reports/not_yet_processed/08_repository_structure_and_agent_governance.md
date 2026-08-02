# Repository Structure and Agent Governance

## What this direction is

This direction is about making the codebase understandable to supervisors and contributors while keeping AI agents from generating unnecessary files, duplicate abstractions, or parallel documentation.

It is not a feature direction in itself. It is the discipline that makes the feature work reviewable.

## Why it matters

The project already has significant scaffolding. That is useful, but scaffolding becomes a liability when it outgrows the validated core.

For a project built with AI assistance, the key risk is not syntax. It is plausible but unnecessary structure: extra files, extra layers, extra wrappers, and extra documentation that look professional but do not add evidence.

## Analysis

A good repository for this project should have:
- one canonical security model,
- one canonical execution kernel,
- one canonical trace format,
- one canonical claim ledger,
- one canonical architecture document,
- and one canonical experiment location.

Everything else should either be a clearly named adapter, a clearly named experiment, or an archived historical artefact.

The codebase should be structured so that a reviewer can answer three questions quickly:
1. What is guaranteed?
2. What evidence supports that guarantee?
3. Which files implement the guarantee?

That implies:
- domain values are immutable and boring,
- transition logic is isolated,
- adapters are thin and explicit,
- experiments are reproducible,
- generated outputs stay out of source control unless curated,
- superseded files are deleted or archived rather than left in place.

AI agents should be given task contracts with an expected file set. If a change unexpectedly creates many files, the task should stop for review.

## Rationale

This direction is valuable because it preserves future velocity. The easiest way for a research repository to become unmanageable is to let every new idea create a new layer, folder, or documentation stream.

Good repository governance gives you:
- easier review,
- fewer semantic duplicates,
- clearer supervision,
- lower merge risk,
- and less cleanup later.

## Constraints

The repository should avoid:
- `utils.py` and `helpers.py` as catch-all modules,
- duplicate docs for the same concept,
- placeholder packages with no consumers,
- hidden compatibility layers that never get deleted,
- and experiments committed as ad hoc notebooks or temporary dumps.

## Open questions

- What is the minimum set of top-level folders that still keeps the project comprehensible?
- Which docs should be canonical, and which should be archived?
- What should be generated on demand instead of committed?
- Where should experiment manifests live relative to source code?

## Suggested first increment

Define a file ownership map and a task template that tells AI agents exactly which files may change, which evidence files must be retained, and which new files require human approval.
