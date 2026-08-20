# Repository Audit Ledger

| Area | Required evidence | Principal risk |
|---|---|---|
| `domain` | immutable-value and property tests | identity or provenance drift |
| ports/application/ITES | AST boundaries and policy/integration tests | authority bypass or decision conflation |
| evaluation/planning/verification | conformance, bounds, mutants, and replay tests | proof or capability overstatement |
| adapters/experiments | strict translation, failure, and regeneration tests | external drift or biased evidence |
| documentation | ownership, rationale, terminology, UTF-8, and link checks | competing or stale sources of truth |
| report archive | exact bytes, Git objects, lineage, duplicate, and task-crosswalk checks | historical evidence mutation |
| archived paper | canonical text/raw binary hashes and Git object checks | silent claim revision |
| scripts and CI | portable validation and installed-wheel smoke | guardrail or packaging drift |

`python scripts/audit_repository.py` is dependency-free. It enforces the AST
import direction and legacy-module removal; small public benchmark exports;
canonical documentation presence, links, encoding, rationale, and report-path
migration; every report task's source-qualified crosswalk; complete registry
dispositions and evidence paths; report and paper archive integrity; manuscript
separation; curated smoke checksums; and required schemas.

The report archive manifest covers every original artefact exactly once. It
checks repository-blob size, SHA-256, Git object identity, package ownership,
declared duplicate content, resolvable canonical successors, and acyclic
supersession. Archived prose is excluded from terminology and link rewriting;
current analysis remains subject to documentation checks.

The portable validator adds JSON Schema validation, deterministic smoke
regeneration, pytest with at least 90% branch coverage, Ruff, strict mypy,
wheel construction, and clean-environment CLI runs for doctor, mediation,
planning, SLED, and report rendering.

## Rationale

Text searches alone cannot distinguish imports from examples, archive evidence
from current claims, or secure blocks from failures. Structural and manifest-
driven checks make those boundaries explicit. The audit remains dependency-
free so it can fail early in a fresh checkout before optional tooling is
available; deeper behavioral evidence belongs in pytest and the installed-
wheel smoke.
