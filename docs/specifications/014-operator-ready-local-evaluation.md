# Specification 014: Operator-Ready Local Evaluation

Status: accepted for implementation
Evidence date: 2026-08-03

## Goal and success criteria

Make validation independent of host-installed optional packages, make the
first self-hosted CPU experiment runnable from an already cached model, and
make formal and benchmark outputs understandable without reading internal
schemas. Success requires offline tests to remain deterministic in both core
and research environments, an eight-cell modeled planning pilot to stop for
human review, and every evidence claim to retain its runtime identity and
limitations.

## Current architecture and affected boundaries

`LocalModelPort` remains the only experiment-facing inference boundary.
`conflux.planning` consumes structured responses and applies modeled actions;
it never executes generated source. `conflux.verification` owns solver-facing
results. Benchmark adapters translate external suites but do not change ITES
semantics. The application and ITES layers remain independent of Hugging Face,
AgentDojo, Cedar, and solver packages.

The observed validation run collected 346 tests: 266 passed, 77 could not
create pytest temporary directories, and three depended incorrectly on
optional-package absence. These are validation-boundary defects, not 80
independent security failures. Local Z3 runs agreed with the reference COI
fixtures; nuXmv was unavailable; the retained AgentDojo fixture translated but
was not a Conflux experiment.

## Public interfaces and data flow

### Local artifacts and CPU pilot

An immutable `LocalArtifactManifest` identifies one exact local model snapshot
by model and tokenizer revisions plus canonical per-file sizes and SHA-256
digests. Resolution follows snapshot links only within the selected model
cache, rejects missing required artifacts, and never downloads or deletes.

`conflux model resolve transformers` writes a local resolved configuration.
`conflux plan pilot` validates that configuration and prints its eight-cell
matrix before optional `--execute-local` invocation. The pilot fixes two
scenarios, four planning modes, seed zero, deterministic decoding, one
semantic repetition, CPU placement, and modeled effects only. Output records
raw failure categories, tokens, latency, calls, utility, security decisions,
and completeness.

### Formal verification presentation

`conflux verify` retains canonical JSON and also writes a human-readable
summary. `SAFE`, `BOUNDED_SAFE`, `UNSAFE`, and `UNKNOWN` retain their existing
meanings. Z3 witnesses end at the first violated invariant. `UNKNOWN` includes
an actionable cause and never becomes a failed safety property.

### AgentDojo and Cedar

AgentDojo exposes distinct translation, preflight, and live-run paths. The
pilot matrix is benign and attacked execution under no defence, conservative
ITES annotations, and an explicitly non-deployable oracle profile. Trusted
tool schemas assign argument roles; benchmark output cannot assign authority.

Cedar is updated before live evidence to v4.12.0 at commit
`fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5`. Offline preflight remains
readiness evidence. Only a complete, identity-bound differential execution may
be classified as bounded parity evidence.

## Rationale and rejected alternatives

A repository-local validation temporary root is preferable to changing a
machine ACL: it is portable, least-privilege, and reproducible in CI. Optional
capability tests use injected probes because package installation is an
environment fact, not a semantic input to an offline unit test.

One canonical Transformers adapter avoids two loaders with different network
and failure behavior. A manifest is required because a model ID and revision
alone do not prove which local bytes were used. The first pilot is
Transformers-only because requiring a llama.cpp binary and converted GGUF
blocked feedback from an already cached model. The paired-runtime protocol
remains a later comparison.

Human summaries supplement rather than replace JSON so reviewability does not
weaken deterministic evidence. AgentDojo profiles are declared before results
to prevent post-hoc annotations. Ollama is not added because it would introduce
another runtime identity without helping the first CPU pilot.

## Security impact

Model output remains untrusted and schema constrained. Artifact resolution
does not execute files, contact a network, or accept cache-path escape.
Principal Context and provenance are evaluated at action time. Conservative
AgentDojo annotations add an external Principal only when external content
influences a state. Oracle annotations are evaluation metadata, not runtime
authority. Authorisation, read policy, visibility, and consent remain
independent. Delegation remains disabled for runtime consumption.

## Implementation sequence

1. Isolate validation temporary state and optional capability tests.
2. Remove the duplicate Hugging Face adapter and add deterministic artifact
   resolution to the canonical Transformers adapter.
3. Add the single-backend CPU planning pilot and stop after live generation
   for review.
4. Add verification summaries and shortest Z3 failure prefixes.
5. Split AgentDojo translation, preflight, and execution; add conservative and
   oracle profiles.
6. Update Cedar identity and add an operator-gated differential path.
7. Reconcile canonical documentation and claims; retain empirical output in a
   separate commit only after review.

## Expected file set and change budget

Changes are limited to existing owners under `src/conflux`, `tests`,
`schemas`, `scripts`, `examples`, `experiments`, `runs`, `docs`, and
`manuscript`. `.local/` is ignored operator state, not a new tracked owner.
One verification example directory and local-artifact schema are approved.
No new top-level directory or competing status, claim, architecture, roadmap,
or report document is approved.

## Tests and acceptance criteria

- Validation uses a unique local temporary root and passes with and without
  optional research packages.
- Unit tests cannot contact Hugging Face or load real weights.
- Artifact resolution covers exact revisions, stable hashes, required files,
  dangling links, cache escape, and incomplete unrelated downloads.
- Fake-backed execution covers all eight planning cells and all six AgentDojo
  cells without code execution.
- Verification covers readable verdicts, Z3 witness trimming, COI agreement,
  and actionable unavailable nuXmv output.
- Cedar covers exact v4.12.0 identity, hashes, supported features, no-shell
  invocation, timeout, disagreement, and absence.
- Audit, schema checks, deterministic regeneration, Ruff, strict mypy, branch
  coverage of at least 90%, wheel/CLI smoke, and `git diff --check` pass.

## Documentation and paper synchronisation

Existing development, integration, CLI, evaluation, status, and claim owners
are updated in place. Cached weights and preflight are readiness only. Local
solver output is exploratory until curated. Manuscript numbers remain
unchanged until a reviewed checksummed result bundle is committed separately.

## Assumptions and resolved decisions

- The laptop is treated as a 20-logical-CPU, approximately 16 GiB, CPU-only
  system for this milestone.
- The pinned SmolLM2 snapshot is already cached; no automatic acquisition or
  cleanup is permitted.
- AgentDojo remains 0.1.35 / benchmark v1.2.2.
- Cedar 4.12.0 is the first live parity target.
- nuXmv, llama.cpp, Ollama, GPU execution, and hosted models are not required.
- The project remains exploratory across planning, benchmarking, policy, and
  delegation rather than selecting one research direction.
