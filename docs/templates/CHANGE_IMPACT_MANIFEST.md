# Change-impact manifest

```text
Task:
Research question affected:
Security invariants affected:
Canonical source files:
Expected implementation files:
Expected tests:
Expected evidence:
Claims potentially affected:
Literature potentially affected:
Threat-model assumptions affected:
Explicit non-changes:
Commit plan:
```

## Purpose

Makes omissions mechanically discoverable. For non-trivial accepted
work, complete this manifest before implementation.

## Audit rules

- Changes to security-kernel packages require an explicit security-impact
  declaration.
- Changes to verification semantics require relevant verification
  tests/docs to be considered.
- Changes to evidence schemas require regeneration/schema tests.
- Changes to manuscript numerical claims require retained evidence
  references.
- Security semantics cannot be changed solely by editing descriptive
  documentation.
