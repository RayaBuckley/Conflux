# Specification 017: Evidence-first Evaluation

Type: specification
Status: accepted for implementation on `main`

## Goal and success criteria

Exercise the existing security, evaluation, benchmark, and planning surfaces
without weakening the canonical ITES transition semantics. The first delivery
retains deterministic native SLED evidence and makes AgentDojo and planning
experiments ready for deliberate self-hosted-model runs. A missing model,
private server, optional package, or operator decision remains an explicit
unavailable outcome rather than an inferred result.

## Authority and affected boundaries

This specification is the maintained successor to the immutable report in
`research/reports/archive/2026-07-31-evidence-first-evaluation/`. It replaces that
report's hosted, credentialed endpoint assumption with self-hosted models and
replaces executable generated code with a serialisable modeled-program IR.

The affected owners are experiment protocols and schemas, model adapters,
native evaluation, benchmark translation, planning evaluation, CLI preflight,
retained evidence, the task registry, claims, and the current manuscript. The
domain and canonical ITES security kernel do not change.

## Evidence and status decisions

Every curated experiment uses a resolved, versioned manifest that records its
track, suite, schema, source commit, inputs, bounds, repetitions, environment,
model identity when applicable, failures, completeness, and checksums. Raw
events, normalized results, a generated summary, and a rerun command remain
separate files. Summaries and manuscript inputs are generated only from the
normalized retained result.

`evaluation_ready` means a runner and offline conformance evidence exist but
no empirical model run is retained. `bounded_evidence` means a finite retained
run supports only the stated configuration and bounds. Neither status implies
a general security or utility guarantee.

Existing version-one smoke evidence remains readable. New result kinds use
strict version-two schemas; unknown versions and fields fail closed.

## Self-hosted model boundary

A shared local-model port accepts a serialisable model specification. Two
optional adapters implement it:

- an OpenAI-compatible adapter for a loopback server or an explicitly enabled
  private GPU endpoint;
- a Transformers adapter that loads already-local model artifacts in process.

The specification records backend, model and tokenizer identities, revision,
weight-manifest digest, prompt-template version, seed, decoding parameters,
context limit, device, dtype, and runtime version. The default network scope is
loopback. Private remote access requires an explicit flag. Reported and
configured identities must match. There is no hosted-provider fallback or
provider credential contract.

Transformers loading uses `local_files_only=True` and
`trust_remote_code=False`. Model caches and weights are not repository
artifacts. Missing dependencies, artifacts, endpoints, identity mismatches,
malformed output, exhausted context, and unsupported calls are distinct
fail-closed outcomes.

## Native SLED reproduction

Legacy-reproduction and canonical fixtures remain separate paired suites.
They execute from identical parents against the canonical monitor and each
negative control. An evaluation-only abstract state classifies proposals as
proposed, authorised, blocked, modeled-executed, provider-failed, or
incomplete. It never invokes the production executor.

A separate canonical oracle evaluates safety so a defective monitor cannot
define its own success. Results include verdicts, unique states, transitions,
duplicates, bounds, counterexample length, blocked and modeled-executed
effects, mutant detection, and semantic discrepancies. Historical values are
source-qualified; disagreement is retained and explained rather than repaired
to fit the old number.

## AgentDojo runner

The pinned upstream version, workspace task, and injection case are fixed in a
protocol. The same local-model specification is used for benign and attacked
cases under no-defence and ITES mediation. Translation preserves upstream IDs
and raw output, adds provenance and Principal Context only in a separate
augmentation stream, denies unknown tools and provenance, and binds every
mediated tool effect to its exact certificate.

Setup, model, parser, policy, security, tool, utility, and incomplete failures
remain separate. This delivery provides validation, preflight, execution, and
normalization but does not retain model-generated results.

## Planning comparison and modeled programs

The fixed comparison modes are:

- `reactive`: propose one next action and then replan;
- `static`: propose one initial plan without revision;
- `dynamic`: propose an initial plan and bounded authenticated patches;
- `dynamic_code`: produce a bounded `ModeledProgram` graph of existing typed
  actions with declared reads and writes.

`ModeledProgram` is inert data. No code string is evaluated, imported,
compiled, passed to a shell, or sent to an executor. Its effects are mediated
at action time and applied only to a deterministic in-memory abstract state.
All outputs use the term `modeled`, never `executed`, for this transition.

The diagnostic suite covers direct authority, data-dependent choice,
unnecessary sensitive reads, mixed Principals, revocation, blocked-action
recovery, provider-failure recovery, and securely impossible completion.
Metrics separate utility, security, blocking, reads, Principal Context and
authority footprints, model calls, tokens, latency, replans, graph growth,
bounds, parsing, and validation failures.

## CLI and operator consent

`sled reproduce` is offline. Model-dependent `benchmark agentdojo` and
`plan compare` commands validate and print their entire run matrix and resource
bounds by default. They contact or load a model only with `--execute-local`.
`doctor --local-model-config` performs the same boundary checks without
claiming a successful experiment.

## Failure modes and non-goals

- Unsupported or incomplete records are retained and excluded only by an
  explicit, counted reason.
- Raw upstream AgentDojo data is never rewritten with Conflux annotations.
- Public-network model endpoints, implicit downloads, hosted fallbacks, real
  generated-code execution, sandboxing, benchmark-specific domain behavior,
  and changes to canonical ITES semantics are out of scope.
- Model-generated AgentDojo and planning results remain unsupported claims
  until an operator retains a complete evidence bundle.

## Tests and acceptance

Acceptance requires strict schema and round-trip tests, deterministic hashes,
v1 compatibility, fake-endpoint and mocked-Transformers adapter tests,
identity and network-scope rejection, paired SLED fixtures, oracle-independent
negative-control witnesses, AgentDojo provenance/certificate conformance, all
four planning modes, and proof that modeled programs have no execution path.

The native SLED bundle must regenerate byte-for-byte. Repository audit, Ruff,
strict mypy, pytest with at least 90% branch coverage, wheel CLI smoke,
portable validation, and `git diff --check` must pass. Generated evidence is
committed after its generator.

## Rationale

Self-hosted interfaces make experiments portable from a small laptop model to
a private GPU service while keeping model identity and operator intent
explicit. Separating runner readiness from retained evidence prevents a tested
adapter from becoming a fabricated empirical claim. Modeled programs preserve
the research question about plan expressiveness without adding an unnecessary
arbitrary-code execution boundary before its security semantics are defined.
