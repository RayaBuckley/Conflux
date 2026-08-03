# Conflux Project Analysis

Snapshot: 2 August 2026. This document reconciles the archived report corpus
with the repository after the canonical migration, dynamic-planning, and
evidence-first evaluation programmes. It is analysis, not a normative
specification or status registry.

## Evidence and authority

Use sources in this order:

1. executable code, tests, schemas, and retained generated evidence;
2. accepted specifications and ADRs;
3. current architecture, operation, status, and claim documentation;
4. this analysis;
5. immutable archived reports and the archived previous paper.

`docs/task-registry.json` owns current programme dispositions.
`docs/CLAIMS.md` owns claim strength. A conflict between sources is a defect to
reconcile, not permission to promote a historical or convenient statement.

## How the project evolved

| Evidence package | Contribution | Current interpretation |
|---|---|---|
| 27 July engineering/SLED reviews | Identified migration defects and proposed model-checking work | Security defects and the canonical kernel are repaired; formal-methods limits remain relevant |
| 27 July literature v1 | Initial taxonomy and action list | Superseded by the corrected research landscape |
| 27 July research landscape v2 | Positioned Conflux and expanded the research backlog | Primary related-work input; recent citations still need source validation |
| 29 July implementation programme | Defined M0–M8, paper separation, runtime, schemas, and evidence gates | Implemented programme surfaces; historical task status is superseded by the registry |
| 30 July planning supplement | Assessed progress and specified open-ended planning | Planning design is implemented; the report did not execute the repository and is not current evidence |
| 31 July evidence-first evaluation | Required self-hosted model protocols and retained native SLED evidence | Native evidence is retained; model-dependent runners are evaluation-ready without empirical efficacy claims |
| 2 August fourth-year direction | Proposed planning, delegation, argument policy, disclosure, attribution, verification reduction, benchmark, PDP, and governance work | Reconciled by specification 013; COI reduction is first, delegation stays disabled until its gates pass |

The package metadata and exact source files are in
[the archive manifest](../archive/MANIFEST.json).

## Current security and architecture

Conflux now has immutable domain values, independent injected policy
dimensions, one pure ITES transition kernel, action-time Principal Context,
certificate-bound execution, deterministic branch semantics, and no legacy
`core`, `auth`, `research`, or `compatibility` import surfaces.

| Aspect | Status and evidence | Rationale | Limitation / next decision |
|---|---|---|---|
| Empty or mixed Principal Context | Implemented; policy, ITES, corpus, and mutant tests | Prevent vacuous or borrowed authority | Authentication and complete provenance remain trusted |
| Provenance and read access | Implemented as separate values and policies | Origin is not an ACL | Argument-role precision remains conservative |
| Alternatives and ordered plans | Implemented with isolation and per-step re-authorisation | A proposal batch cannot pre-grant future effects | Formal delegation remains denied |
| Failure behavior | Errors, unsupported actions, stale decisions, and exhausted bounds fail explicitly | Uncertainty is not permission | Availability and security outcomes remain distinct |

The normative contract is [the security model](../../docs/SECURITY_MODEL.md),
not this summary.

## Runtime, planning, and code execution

The offline vertical slice includes strict YAML scenarios, a scripted model,
an in-memory executor, dry-run confined filesystem writes, deterministic
traces, and an installed CLI. Open-ended plans use authenticated operation
catalogues, typed bindings, immutable graph patches, explicit bounded loops,
continuations, subplans, outcome validation, and deterministic authority-
minimising selection. Every grounded effect returns through ITES.

Generated code is treated as data submitted to a bounded container capability.
The adapter validates command construction and fails closed when its runtime is
absent; it is not a proof against container or kernel compromise. Live
filesystem effects require confinement and precondition hashes.

## SLED and formal verification

Native SLED performs deterministic breadth-first exploration of the shared
transition kernel with state deduplication, retained bounds, and shortest
counterexamples. Its `SAFE` verdict applies only to an exhausted finite model;
truncation produces `BOUNDED_SAFE` and modelling failure produces `UNKNOWN`.

The serialisable verification IR, reference interpreter, runtime differential
tests, optional Z3 bounded backend, and nuXmv Boolean subset are implemented.
This is bounded and conformance-scoped evidence, not an unbounded proof of the
Python runtime or arbitrary generated programs. Hyperproperties and stronger
unbounded models remain research work. Property-preserving cone-of-influence
reduction is the selected next verification increment; partial-order and
Principal-symmetry reductions remain deferred until their stronger
independence assumptions are explicit.

## Evaluation and integrations

Versioned schemas, deterministic trace/result records, experiment manifests,
negative controls, smoke evidence, four-mode planning aggregation, hardware
discovery, and resumable jobs are present and tested offline. Security, utility,
provider failure, and incompleteness remain separate.

The OpenAI-compatible and Hugging Face adapters are optional and untrusted.
AgentDojo is pinned to package `0.1.35` and benchmark `v1.2.2`; its exact suite
and trace structures translate without permissive aliases. The retained raw
fixture proves translation behavior only. No live model or no-defence-versus-
ITES efficacy result is claimed.

## Related-work position

Conflux does not claim to originate system-level agent mediation, provenance
tracking, privilege control, or prompt-injection defence. Its narrower focus is
collective Principal Context derived from authenticated influence and
interpreted through organisational policy, with shared operational and bounded
verification semantics.

The useful comparison axes are model robustness, architectural isolation,
information flow, policy expressiveness, provenance granularity, delegation,
persistent state, and verification strength. Recent report citations and
reported numbers require primary-source validation before publication; the
current bibliography state is recorded in `manuscript/REFERENCES.md`.

## Claim strength

| Strength | Current examples | Required wording |
|---|---|---|
| Implemented behavior | Fail-closed context, independent policies, branch isolation, action-time checks | State the trusted assumptions and regression evidence |
| Bounded evidence | Native SLED, retained smoke run, solver-facing conformance | State model, bounds, abstraction, and verdict |
| Translation evidence | Pinned AgentDojo fixture and adapter | Do not infer efficacy or upstream policy ground truth |
| Hypothesis or gated result | Planning utility, live-model security, unbounded verification | State that matching retained evidence is absent |

The [claim ledger](../../docs/CLAIMS.md) is authoritative.

## Remaining programme

Priority work is staged evidence, not another broad architectural rewrite:

1. reduce the serialisable verification IR by a checked cone of influence and
   retain original-versus-reduced evidence;
2. run the deliberately small dual-backend laptop planning smoke, then stop
   for human review before wider model work;
3. extend the implemented trusted argument roles, audience disclosure, and
   conservative attribution with a pinned policy decision point;
4. validate a pinned local Cedar subset against the in-memory oracle;
5. retain the implemented scoped delegation model while runtime use stays
   disabled until parity, visibility, attribution, and certificate gates pass;
6. generate manuscript tables and figures only from retained result JSON.

Unavailable credentials, model weights, container engines, solver binaries, or
cluster schedulers remain explicit gates. They do not justify simulated live
claims.

## Update procedure

When a new report arrives, add a new immutable archive package and manifest
entries. Namespace its tasks in `task-crosswalk.json`, update this analysis only
where interpretation changes, and update the canonical task registry or claim
ledger rather than copying their state here. Run the repository audit and
portable validator before accepting the change.
