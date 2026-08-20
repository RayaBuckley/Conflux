# Conflux Status

## At a glance

Conflux has a working offline security kernel that mediates every agent
effect through Principal Context authority checks. It can verify security
properties on finite models, generate authenticated plans, and translate
external benchmarks. Live model evidence and delegation activation remain
future work. The detail below is for maintainers and reviewers.

The canonical migration and P0 security repair are complete. Immutable values
live in `domain`; ITES has one transition kernel; Principal Context is derived
from trusted provenance at action time; policy dimensions remain independent;
and the legacy `core`, `auth`, `research`, and `compatibility` surfaces are
absent.

The offline result-ready path is implemented:

- alternatives and ordered plans use certificate-bound execution;
- open-ended plans use authenticated catalogues, immutable patches, explicit
  loops, subplans, bounded continuation, and action-time re-authorisation;
- generated code is data submitted to a capability-constrained container
  operation and fails closed when the sandbox is unavailable;
- native SLED explores deterministic finite states, retains bounds, and emits
  shortest counterexamples;
- the retained native reproduction pairs three legacy/canonical fixtures,
  detects all five seeded monitor defects, and records historical discrepancies;
- the serialisable verification IR has interpreter conformance, optional Z3
  bounded checking, and a nuXmv adapter that returns `UNKNOWN` when unsupported;
- property-scoped COI reduction closes over transition dependencies, retains
  stable rule IDs, compares original and reduced reference verdicts, and has a
  checksummed two-fixture evidence bundle with one lifted unsafe witness;
- trusted operation schemas assign immutable argument roles; authority-bearing
  selectors are authorised pointwise for every Principal, and their provenance
  is included in the action-time Principal Context;
- event disclosure has audience-specific levels and deterministic redaction;
  structured attribution derives from provenance and policy evidence, while
  model explanations remain explicitly untrusted;
- scoped delegation is represented by exact, expiring, revocable, one-use
  grants with deterministic lifecycle evidence and mutation-tested bounds;
  operational delegation remains unconditionally denied pending activation
  evidence;
- the optional Cedar 4.12.0 adapter, strict differential corpus, PARC
  translation, binary-identity preflight, and offline readiness bundle are
  implemented; Cedar was not invoked, so parity is not claimed;
- deterministic scenarios, traces, schemas, manifests, smoke evidence,
  negative controls, planning comparison aggregation, and resumable jobs are
  tested offline;
- self-hosted OpenAI-compatible and Transformers model ports have strict
  identity, network, local-cache, and structured-output contracts;
- AgentDojo, four-mode planning, and the dual-backend laptop smoke have
  checksummed preflight matrices whose cells remain explicitly unavailable;
  they contain no model-generated results;
- planning `dynamic_code` evaluation uses inert modeled actions and effects;
  it never invokes the operational code adapter or another executor;
- the current manuscript is separate from the checksummed paper archive.

The pinned AgentDojo `0.1.35` / benchmark `v1.2.2` boundary translates exact
upstream suite and trace structures, preserves IDs and native metrics, retains
a raw upstream fixture, and rejects schema/version drift. Its six-cell local
runner compares benign/attacked input under no defence, conservative ITES, and
an explicitly non-deployable oracle profile. Fake-backed conformance passes,
but an operator has not retained a model result, so efficacy is not claimed.

Likewise, local model weights and servers, Z3, nuXmv, Docker code execution,
AgentDojo execution, and scheduler submission are optional capabilities. Their
absence produces an explicit unavailable or `UNKNOWN` outcome. No live model,
solver-binary, cluster, AgentDojo, or planning-efficacy result has been
fabricated.

## Validated baseline

The 31 July 2026 repository baseline at commit `6fe6b584500e` passed 220 tests with
90.25% branch coverage, all 13 schemas, deterministic regeneration, Ruff,
strict mypy, wheel build, and installed `doctor`, `demo`, `plan demo`,
`sled run`, and `report` smoke checks. The authoritative record is
`artifacts/validation/6fe6b584500e/`; [the baseline](BASELINE_2026-07.md)
defines what that result does and does not support. The matching GitHub run
passed all four supported operating-system/Python combinations.

Native evidence added after that baseline is independently retained under
`runs/native-sled-reproduction-v1/`, linked to implementation commit
`d6d9857954ac7c7702fff64642d3ea9e7836948f`, and regenerates byte-for-byte.
COI-reduction evidence is retained under `runs/sled-coi-reduction-v1/`, linked
to generator commit `3c4e9884a93f84b62ddb5b1c7e52da84be073b97`. Its two
reference-interpreter fixtures agree and reduce at least one measured model
dimension. Z3 bounded verification with COI reduction confirmed equivalence
on both safe and unsafe fixtures; the reduced safe model drops one variable
and one rule, and the reduced unsafe model lifts the counterexample.

Laptop experimental evidence (Qwen2.5-1.5B-Instruct, RTX 4060) is retained
under `runs/`:

- `runs/sled-canon-env01/`, `env02/`, `env03/`: canonical SLED verified safe
  at depth 12 (2 states, 1 transition each);
- `runs/delegation-v2/`: delegation verification complete, classified
  `bounded_evidence`, all mutants killed;
- `runs/verify-coi-safe/` and `verify-coi-unsafe/`: Z3 BMC with COI
  reduction on security-monitor IR; safe verdict bounded safe, unsafe
  verdict produces counterexample, original/reduced agree;
- `runs/verify-coi-original-safe/` and `verify-coi-original-unsafe/`: Z3 BMC
  with COI reduction on the larger safe-noise and unsafe-control IR fixtures
  from `sled-coi-reduction-v1`; reduction removes the noise variable and
  toggle/increment rules, both verdicts agree with originals;
- `runs/planning-pilot-qwen-1.5b/`: four-mode planning pilot completed; all
  eight cells `model_failed` (1.5B model wraps JSON in markdown fences);
- `runs/agentdojo-qwen-1.5b/`: six-cell AgentDojo comparison completed; all
  six cells `model_failed` (same JSON parse issue); raw upstream log
     retained with 47 s benign inference trace.

A Qwen2.5-7B-Instruct NF4 model (RTX 4060, 8 GiB VRAM) validated on a single
AgentDojo cell (status=complete, security=True, utility=False, model_calls=4)
after adapter fixes for BitsAndBytesConfig import, generator caching, and
concatenated JSON parsing. The full six-cell comparison is deferred to GPU
availability.

Offline direction evidence is retained under `runs/direction-readiness-v1/`.
It supplies bounded native mutation evidence and readiness-only planning and
AgentDojo matrices. Cedar readiness is separately retained under
`runs/cedar-differential-preflight-v1/`; its incomplete manifest and
`unavailable` Cedar cells are deliberate claim boundaries.

`docs/task-registry.json` is the machine-readable programme status. Remaining
research includes production policy/framework integrations, delegation
activation, richer argument-effect semantics, persistent-memory authority,
symbolic reasoning about arbitrary generated programs, and live model-backed
planning/AgentDojo evidence (the 1.5B model's structured output requires a
larger model or output-constraining post-processing).

## Foundational literature

The [foundational security literature
analysis](../../reports/analysis/2026-08-13-foundational-security-literature.md)
identifies the classical integrity and IFC lineage (Biba, LOMAC, Denning,
declassification, endorsement, noninterference) underlying Principal Context
and ITES. This lineage is now integrated into the research positioning (see
[related work](../research/RELATED_WORK.md), [research overview](../research/RESEARCH_OVERVIEW.md),
[ADR 012](../decisions/012-foundational-security-lineage.md), and the [SLED-V
property hierarchy](../reference/SLED.md)). A novelty audit and primary-source bibliography
verification remain deferred research; no novelty claim should assert the
absence of classical precedent without prior-art verification.

## Rationale

This page intentionally summarizes capability rather than reproducing task
rows, test output, or research claims. The task registry owns programme status,
retained artifacts own measurements, and the claim ledger owns claim strength;
keeping those roles separate makes drift visible.
