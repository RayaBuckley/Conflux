# Conflux Status

## At a glance

Conflux has a working offline security kernel that mediates every agent
effect through Principal Context authority checks. It can verify security
properties on finite models, generate authenticated plans, and translate
external benchmarks. Limited laptop evidence exists for Qwen planning and
AgentDojo pipeline execution; larger-model evaluation and delegation
activation remain future work. The detail below is for maintainers and
reviewers.

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
`research/output/validation/6fe6b584500e/`; [the baseline](BASELINE_2026-07.md)
defines what that result does and does not support. The matching GitHub run
passed all four supported operating-system/Python combinations.

Windows CI is now gating; CRLF determinism for evidence bundles is enforced
via `newline="\n"` on all evidence-generating `write_text` calls and a
`check_evidence_line_endings` audit check.

Native evidence added after that baseline is independently retained under
`research/output/runs/native-sled-reproduction-v1/`, linked to implementation commit
`d6d9857954ac7c7702fff64642d3ea9e7836948f`, and regenerates byte-for-byte.
COI-reduction evidence is retained under `research/output/runs/sled-coi-reduction-v1/`, linked
to generator commit `3c4e9884a93f84b62ddb5b1c7e52da84be073b97`. Its two
reference-interpreter fixtures agree and reduce at least one measured model
dimension. Z3 bounded verification with COI reduction confirmed equivalence
on both safe and unsafe fixtures; the reduced safe model drops one variable
and one rule, and the reduced unsafe model lifts the counterexample.

Laptop experimental evidence (Qwen2.5-1.5B-Instruct, RTX 4060) is retained
under `research/output/runs/`:

- `research/output/runs/smoke/`: scripted canonical SLED verified safe at depth 12
  (2 states, 1 transition each);
- `research/output/runs/native-sled-reproduction-v1/`: native SLED reproduction detecting
  five seeded monitor defects across three fixture pairs;
- `research/output/runs/direction-readiness-v1/security-mutations.json`: delegation
  verification complete, classified `bounded_evidence`, all seven mutants killed;
- `research/output/runs/sled-coi-reduction-v1/`: COI reduction on two IR fixtures (safe-noise
  and unsafe-control); safe verdict bounded safe, unsafe verdict produces
  counterexample, original and reduced verdicts agree;
- `research/output/runs/z3-agreement-v1/`: Z3 BMC agreement on the same two fixtures;
  reference interpreter, reduced model, and Z3 agree (safe returns `bounded_safe`
  vs `safe` semantically);
- `research/output/runs/coi-scaling-v1/`: COI scaling across 12 fixtures (0–16 noise
  variables); all original/reduced verdicts agree, Z3 agrees on all, reduction
  collapses noise variables while preserving the invariant;
- `research/output/runs/planning-pilot-1b5-v1/`: eight-cell planning pilot completed with
  Qwen2.5-1.5B-Instruct NF4 on RTX 4060; all cells `complete=True`; model is
  too small for high utility but the planning pipeline executes end-to-end;
- `research/output/runs/agentdojo-1b5-nf4-v1/`: six-cell AgentDojo comparison completed
  with Qwen2.5-1.5B-Instruct NF4; all six cells `complete=True` (benign:
  security=True, utility=False; attacked: security=False, utility=False);
  the 3B model produces malformed JSON; the 7B NF4 model timed out at 10 minutes.

The AgentDojo `important_instructions` attack required the pipeline name to
contain a recognised model identifier (fixed: pipeline renamed from
`conflux-self-hosted-*` to `conflux-local-*` to match the `local` model name
in AgentDojo's attack registry).

Offline direction evidence is retained under `research/output/runs/direction-readiness-v1/`.
It supplies bounded native mutation evidence and readiness-only planning and
AgentDojo matrices. Cedar readiness is separately retained under
`research/output/runs/cedar-differential-preflight-v1/`; its incomplete manifest and
`unavailable` Cedar cells are deliberate claim boundaries.

- observational confidentiality is verified via IR self-composition with
  Z3 BMC; the product IR doubles variables and rules in lockstep, adds
  confidentiality invariants (`observable == observable__prime`), and applies
  COI reduction; safe fixtures are bounded safe, unsafe fixtures produce
  counterexamples showing observation divergence; this is bounded evidence,
  not a noninterference proof;
- comparative defence verification has IR models of the Dual-LLM baseline,
  its native property Q (processor never executes), an ITES reference, and a
  defective requester-only controller; the Dual-LLM model satisfies Q but
  violates PE with a counterexample, while ITES preserves PE; these are
  finite IR models, not implementation-conformance evidence;

`docs/evidence/task-registry.json` is the machine-readable programme status. Remaining
research includes production policy/framework integrations, delegation
activation, richer argument-effect semantics, persistent-memory authority,
symbolic reasoning about arbitrary generated programs, and live model-backed
planning/AgentDojo evidence (the 1.5B model's structured output requires a
larger model or output-constraining post-processing).

## Foundational literature

The [foundational security literature
analysis](../../research/reports/analysis/2026-08-13-foundational-security-literature.md)
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

## Recent changes

Unreleased — 29 August 2026:

- Archived FLMSec evening revision package and SLED-V comprehension validation
  package to `research/reports/archive/`; updated the archive manifest with 17
  new artifacts across two new dated packages.
- Added RunPod remote access guide to `docs/reference/RUNPOD.md` with
  supervisor usage guidelines (single H100/H200 day-to-day, occasional
  short multi-GPU runs).
- Recorded the SLED-V comprehension programme (claim repair, tutorial,
  worked example, mutation curriculum, explainable outputs, CaMeL deep
  validation) in the task registry as deferred next-phase work.
- Recorded supervisor research pointers: Clark-Wilson integrity model
  relationship and LLMbda Calculus multi-CaMeL extension
  (arXiv:2602.20064) in deferred research.
- Fixed stale evidence links in the 2026-08-19 supervisor meeting
  consolidation (verify-coi-* → sled-coi-reduction-v1/z3-agreement-v1;
  agentdojo-qwen-1.5b → agentdojo-1b5-nf4-v1; planning-pilot-qwen-1.5b →
  planning-pilot-1b5-v1).
- Updated comparative defence model gap to reflect that CaMeL, Progent, and
  PACT finite IR abstractions now exist alongside Dual-LLM and ITES.

Unreleased — 31 July 2026:

- Stabilized archive validation across LF and CRLF checkouts while preserving
  Git-object identity and byte-exact binary checks.
- Updated GitHub Actions pins, diagnostics, timeouts, retained artifacts, and
  cross-platform matrix behavior.
- Added a concise contributor path, AI-agent trust guide, design rationale,
  documentation ownership model, and installed-wheel quick start.
- Archived all 18 original report artifacts without changing their Git blobs;
  added a source-qualified crosswalk and cohesive current analysis.
- Synchronized the current manuscript with implemented, bounded, optional, and
  future work; the previous paper remains immutable.
- Retained the consolidated 220-test, 90.25%-branch-coverage validation record.
