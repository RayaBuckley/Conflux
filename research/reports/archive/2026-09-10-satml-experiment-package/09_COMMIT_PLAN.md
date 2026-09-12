# Atomic Commit Plan

Follow repository commit discipline. Every implementation commit should pass the relevant checks independently. Generated evidence must not be committed in the same commit as the code that generates it.

## Commit 1 - experiment specifications only

Add formal tracked specs/manifests for the SaTML experiment programme.

Security impact: none.

## Commit 2 - shared deterministic experiment record/aggregation extensions

Only if existing infrastructure lacks fields required by these experiments. Prefer backward-compatible schema extension and version bump over parallel formats.

Security impact: none; research/evidence infrastructure only.

## Commit 3 - SLED-V scaling generator/harness

Add parameterised finite fixtures and runner. Include tests for deterministic regeneration, expected verdicts, timeout recording, and historical anchors.

Security impact: none to runtime; verifies security semantics.

## Commit 4 - SLED-V scaling evidence

Commit curated evidence bundle separately, including manifest, raw data, summary, plots/tables if repository convention allows, checksums, rerun command.

Security impact: none.

## Commit 5 - mutation suite expansion

Add isolated mutants and expected-verdict tests. Never weaken production runtime.

Security impact: none to canonical runtime; synthetic verification fixtures only.

## Commit 6 - mutation evidence

Retain full bounded result bundle and witnesses.

Security impact: none.

## Commit 7 - provenance precision experiment implementation

Add deterministic organisation/workflow generator and conditions. Reuse canonical ITES checker.

Security impact: none to canonical runtime; evaluates provenance precision assumptions.

## Commit 8 - provenance precision evidence

Retain generated data/result bundle and figures.

Security impact: none.

## Commit 9 - AgentDojo competency gate and suite selection

Only make integration changes needed for upstream correctness. Any task/evaluator changes require explicit justification and upstream-semantic conformance tests.

Security impact: none to core ITES; benchmark integration only.

## Commit 10 - AgentDojo evidence

Commit or archive retained model evidence according to repository size/privacy policy. Include failures and raw trace references.

Security impact: none.

## Commit 11 - planning scenario suite expansion

Add mode-independent scenario goals and evaluator metrics. Do not change security kernel.

Security impact: none to ITES authority boundary.

## Commit 12 - planning evidence

Retain deterministic and live-model evidence separately if useful.

Security impact: none.

## Commit 13 - Cedar/confidentiality optional implementation

Only if needed for fixture expansion or exact pinned execution support.

Security impact: none to core runtime unless adapter correctness is changed; state exact boundary.

## Commit 14 - optional evidence

Retain Cedar/confidentiality outputs.

Security impact: none.

## Commit 15 - aggregate paper figures/tables

Add deterministic aggregation and generated manuscript inputs. Test that every number traces to an evidence bundle.

Security impact: none.

## Commit 16 - claims/status/manuscript update

Update `docs/evidence/CLAIMS.md`, `docs/evidence/STATUS.md`, relevant experiment registry, and manuscript interpretation. Use bounded language exactly matching retained evidence.

Security impact: none; documentation only.

## Before every commit

- inspect staged diff;
- run targeted tests;
- run Ruff/mypy for changed modules;
- inspect generated evidence when semantics/evaluation changed;
- confirm no secrets or model credentials are retained.

## Before final merge

Run `python scripts/validate.py` and regenerate all deterministic central figures/tables from a clean tree.
