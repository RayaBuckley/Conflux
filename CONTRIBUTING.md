# Contributing to Conflux

Conflux changes are reviewed first for security-model correctness, then policy
faithfulness, reproducibility, extensibility, and performance. Small,
decision-complete commits are preferred because authority bugs often hide in
otherwise routine refactors.

## Before changing code

1. Read the affected architecture, security, and public-interface documents.
2. Inspect existing tests and accepted decisions; do not infer behavior from a
   historical report.
3. Write or update a feature specification when behavior, trust, evidence, or
   a public interface changes.
4. State how Principal Context, provenance, authorisation, read access,
   visibility, consent, delegation, and failure handling are affected.

### Rationale

This ordering exposes security decisions before implementation makes them
expensive to revise. It also gives future contributors and agents a compact
intent record without duplicating current status.

## Set up and run

Use Python 3.12+. Windows users can run `.\scripts\setup.ps1`; other platforms
can create a virtual environment and install `.[dev]` as shown in the
[quick start](README.md#run-the-offline-system).

Run a focused test while developing, for example:

```sh
python -m pytest -q tests/test_policy_and_ites.py
python -m ruff check src tests scripts
python -m mypy src tests scripts --no-error-summary
```

Before committing a coherent change, run:

```sh
python scripts/audit_repository.py
python scripts/validate.py
git diff --check
```

The validator checks documentation and architecture, schemas, deterministic
evidence, branch coverage, formatting, strict types, wheel contents, and the
installed offline CLI.

## Test security behavior

Add a regression test for every changed invariant. Where relevant, cover
allow, deny, empty and mixed Principal Contexts, provenance accumulation,
immutability, nested execution, revocation, policy/provider failure, bound
exhaustion, deterministic evidence, and absence of side effects during
exploration. External adapters also need malformed, unsupported, and missing-
dependency cases.

### Rationale

High aggregate coverage cannot prove that a fail-closed branch was exercised.
Explicit adversarial and failure cases make the intended denial observable and
protect the distinction between security, utility, and infrastructure errors.

## Keep documentation small and authoritative

- Update an existing canonical owner before creating a new document.
- Explain why a decision exists and link to its ADR or specification.
- Put mutable task state only in `docs/task-registry.json` and claim strength
  only in `docs/CLAIMS.md`.
- Do not edit archived paper or report evidence. Add current interpretation
  outside the archive.
- Do not enter numerical claims without retained, reproducible evidence.

Use one commit per coherent change. Do not combine generated evidence with the
implementation that produces it. Review the staged diff for permission
broadening, hidden trust assumptions, benchmark shortcuts, secrets, and stale
documentation before committing.
