# Conflux Status

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
- deterministic scenarios, traces, schemas, manifests, smoke evidence,
  negative controls, planning comparison aggregation, and resumable jobs are
  tested offline;
- self-hosted OpenAI-compatible and Transformers model ports have strict
  identity, network, local-cache, and structured-output contracts;
- AgentDojo and four-mode planning runners expose complete preflight matrices
  but have no retained model-generated results;
- planning `dynamic_code` evaluation uses inert modeled actions and effects;
  it never invokes the operational code adapter or another executor;
- the current manuscript is separate from the checksummed paper archive.

The pinned AgentDojo `0.1.35` / benchmark `v1.2.2` boundary translates exact
upstream suite and trace structures, preserves IDs and native metrics, retains
a raw upstream fixture, and rejects schema/version drift. The self-hosted
comparison runner is evaluation-ready. An operator has not yet retained its
benign/attacked, no-defence/ITES model result, so efficacy is not claimed.

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
dimension; no optional formal backend was available for that retained run.

`docs/task-registry.json` is the machine-readable programme status. Remaining
research includes live comparative evidence, production policy/framework
integrations, formal delegation, richer argument-effect semantics, persistent-memory
authority, and symbolic reasoning about arbitrary generated programs.

## Rationale

This page intentionally summarizes capability rather than reproducing task
rows, test output, or research claims. The task registry owns programme status,
retained artifacts own measurements, and the claim ledger owns claim strength;
keeping those roles separate makes drift visible.
